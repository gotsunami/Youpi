# vim: set ts=4

import sys, os.path, re, time, string
import marshal, base64, zlib
from stat import *
import cjson as json
#
from django.conf import settings
from django.core.cache import cache
#
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *
from terapix.youpi.auth import read_proxy
from terapix.youpi.models import *
import terapix.lib.cluster.condor as condor
from lib.common import get_tpx_condor_upload_url

class Stiff(ProcessingPlugin):
    """
    This plugin for Stiff
    """
    def __init__(self):
        ProcessingPlugin.__init__(self)

        self.id = 'stiff'
        self.optionLabel = 'Stiff'
        self.description = 'FITS to TIFF image conversion'
        # Item prefix in processing cart. This should be short string since
        # the item ID can be prefixed by a user-defined string
        self.itemPrefix = 'STIFF'
        self.index = 65535

        self.template = 'plugins/stiff.html'                        # Main template, rendered in the processing page
        self.itemCartTemplate = 'plugins/stiff_item_cart.html'      # Template for custom rendering into the processing cart
        self.jsSource = 'plugins/stiff.js'                          # Custom javascript

        # Will queue jobCount jobs on the cluster
        self.jobCount = 5
        self.command = '/usr/bin/uptime'

    def process(self, request):
        """
        Do the job.
        1. Generates a condor submission file
        2. Executes condor_submit on that file
        3. Returns info related to ClusterId and number of jobs submitted
        """
        from terapix.youpi.pluginmanager import manager

        try:
            idList = eval(request.POST['IdList'])   # List of lists
        except Exception, e:
            raise PluginError, "POST argument error. Unable to process data."

        cluster_ids = []
        error = condorError = '' 
        k = 1

        try:
            for imgList in idList:
                if not len(imgList):
                    continue
                csfPath = self.__getCondorSubmissionFile(request, imgList)
                cluster_ids.append(manager.cluster.submit(csfPath))
                k += 1
        except CondorSubmitError, e:
            condorError = str(e)
        except Exception, e:
                error = "Error while processing list #%d: %s" % (k, e)

        return {'ClusterIds': cluster_ids, 'Error': error, 'CondorError': condorError}

    def __getCondorSubmissionFile(self, request, idList):
        """
        Generates a suitable Condor submission file for processing self.command jobs on the cluster.
        """

        post = request.POST
        try:
            itemId = str(post['ItemId'])
            config = post['Config']
            taskId = post.get('TaskId', '')
            resultsOutputDir = post['ResultsOutputDir']
            reprocessValid = int(post['ReprocessValid'])
        except Exception, e:
                raise PluginError, "POST argument error. Unable to process data: %s" % e

        #
        # Config file selection and storage.
        #
        # Rules:    if taskId has a value, then the config file content is retreived
        #           from the existing Stiff processing. Otherwise, the config file content
        #           is fetched by name from the ConfigFile objects.
        #
        #           Selected config file content is finally saved to a regular file.
        #
        try:
            if len(taskId):
                config = Plugin_stiff.objects.filter(task__id = int(taskId))[0]
                content = str(zlib.decompress(base64.decodestring(config.config)))
            else:
                config = ConfigFile.objects.filter(kind__name__exact = self.id, name = config)[0]
                content = config.content
        except IndexError:
            # Config file not found, maybe one is trying to process data from a saved item 
            # with a delete configuration file
            raise PluginError, "The configuration file you want to use for this processing has not been found " + \
                "in the database... Are you trying to process data with a config file that has been deleted?"
        except Exception, e:
            raise PluginError, "Unable to use a suitable config file: %s" % e

        now = time.time()

        # Condor submission file
        cluster = condor.YoupiCondorCSF(request, self.id, desc = self.optionLabel)
        csfPath = cluster.getSubmitFilePath()
        tmpDir = os.path.dirname(csfPath)
        csf = open(csfPath, 'w')

        # Swarp config file
        customrc = cluster.getConfigFilePath()
        strc = open(customrc, 'w')
        strc.write(content)
        strc.close()

        # Content of YOUPI_USER_DATA env variable passed to Condor
        # At least those 3 keys
        userData = {'Descr'             : '',                                                           # Mandatory for Active Monitoring Interface (AMI)
                    'Kind'              : self.id,                                                      # Mandatory for AMI, Wrapper Processing (WP)
                    'UserID'            : str(request.user.id),                                         # Mandatory for AMI, WP
                    'ItemID'            : itemId, 
                    'ConfigFile'        : customrc, 
                    'ResultsOutputDir'  : str(resultsOutputDir)                                         # Mandatory for WP
                } 

        # Set up default files to delete after processing
        self.setDefaultCleanupFiles(userData)
        # Also remove *.fits and *.xml
        userData['RemoveFiles'].extend(['*.fits', '*.xml'])

        #
        # Pre-processing script runned by condor_transfer.pl
        #
        preProcFile = os.path.join(tmpDir, "%s-preprocessing-%s.py" % (self.id, time.time()))
        pf = open(preProcFile, 'w')
        pcontent = """#!/usr/bin/env python

# AUTOMATICALLY GENERATED SCRIPT. DO NOT EDIT

import os, glob, sys, time, pyfits
from settings import *

def debug(msg):
    print "[YWP@%s] %s" % ("%02d:%02d:%02d" % time.localtime(time.time())[3:6], msg)
    sys.stdout.flush()

# PRE-PROCESSING stuff go there

imgName = glob.glob('*.fits')[0][:-5]
tmpImage = "%s-ok.fits" % imgName
hdulist = pyfits.open(imgName + '.fits')
hdulist.close()
# Is it a MEF? 
if len(hdulist) > 1:
    debug("MEF detected. Swarping")
    os.system("%s -IMAGEOUT_NAME %s %s.fits 2>&1" % (CMD_SWARP, tmpImage, imgName))
    debug("Swarp complete")
else:
    os.rename(imgName + '.fits', tmpImage)
debug("Running Stiff on previous stack")
os.system("%s -c %s -OUTFILE_NAME %s.tif -COMPRESSION_TYPE JPEG -IMAGE_TYPE TIFF-PYRAMID %s 2>&1" % (CMD_STIFF, '""" + os.path.basename(customrc) + """', imgName, tmpImage))
debug("Stiff complete")
"""

        pf.write(pcontent)
        pf.close()
        RWX_ALL = S_IRWXU | S_IRWXG | S_IRWXO 
        os.chmod(preProcFile, RWX_ALL)

        #
        # Generate CSF
        #
        cluster.setTransferInputFiles([customrc, 
            os.path.join(settings.TRUNK, 'terapix', 'lib', 'common.py'),
            preProcFile,
        ])

        images = Image.objects.filter(id__in = idList)
        # One image per job queue
        for img in images:
            # Stores real image name (as available on disk)
            userData['RealImageName'] = str(img.filename)
            path = os.path.join(img.path, userData['RealImageName'] + '.fits')

            #
            # $(Cluster) and $(Process) variables are substituted by Condor at CSF generation time
            # They are later used by the wrapper script to get the name of error log file easily
            #
            userData['ImgID'] = str(img.id)
            userData['Descr'] = str("%s of image %s" % (self.optionLabel, img.name))        # Mandatory for Active Monitoring Interface (AMI)
            # Mandatory for WP
            userData['JobID'] = self.getUniqueCondorJobId()

            # Base64 encoding + marshal serialization
            # Will be passed as argument 1 to the wrapper script
            try:
                encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
            except ValueError:
                raise ValueError, userData

            image_args = "%(encuserdata)s %(condor_transfer)s -l %(image)s -- ./%(preprocscript)s" % {
                'image': path,
                'encuserdata'       : encUserData, 
                'condor_transfer'   : "%s %s" % (settings.CMD_CONDOR_TRANSFER, settings.CONDOR_TRANSFER_OPTIONS),
                'preprocscript'     : os.path.basename(preProcFile),
            }

            # Finally, adds Condor queue
            cluster.addQueue(
                queue_args = str(image_args), 
                queue_env = {
                    'TPX_CONDOR_UPLOAD_URL' : get_tpx_condor_upload_url(resultsOutputDir), 
                    'YOUPI_USER_DATA'       : base64.encodestring(marshal.dumps(userData)).replace('\n', '')
                }
            )

        cluster.write(csfPath)
        return csfPath

    def getTaskInfo(self, request):
        """
        Returns information about a finished processing task. Used on the results page.
        """

        post = request.POST
        try:
            taskid = post['TaskId']
        except Exception, e:
            raise PluginError, "POST argument error. Unable to process data."

        task, filtered = read_proxy(request, Processing_task.objects.filter(id = taskid))
        if not task:
            return {'Error': str("Sorry, you don't have permission to see this result entry.")}
        task = task[0]
        img = Rel_it.objects.get(task__id = taskid).image
        data = Plugin_stiff.objects.get(task__id = taskid)

        # Jobs History
        stiff_history = Rel_it.objects.filter(image__id = img.id, task__kind__name = self.id).order_by('-id')
        history = []
        for h in stiff_history:
            history.append({
                'User'      : str(h.task.user.username),
                'Success'   : h.task.success,
                'Start'     : str(h.task.start_date),
                'Duration'  : str(h.task.end_date-h.task.start_date),
                'Hostname'  : str(h.task.hostname),
                'TaskId'    : str(h.task.id),
            })

        # Error log content
        if task.error_log:
            err_log = str(zlib.decompress(base64.decodestring(task.error_log)))
        else:
            err_log = ''

        config = zlib.decompress(base64.decodestring(data.config))

        return {    'TaskId'    : str(taskid),
                    'Title'     : str("%s" % self.description),
                    'User'      : str(task.user.username),
                    'Success'   : task.success,
                    'ClusterId' : str(task.clusterId),
                    'Start'     : str(task.start_date),
                    'End'       : str(task.end_date),
                    'Duration'  : str(task.end_date-task.start_date),
                    'Log'       : err_log,
                    'Tags'      : [[str(t.name), str(t.style)] for t in img.tags()],
                    'History'   : history,
                    'ImgName'   : str(img.name),
                    'ImgPath'   : str(img.path),
                    'ResultsOutputDir'  : str(task.results_output_dir),
                    'Config'            : str(config),
            }

    def getResultEntryDescription(self, task):
        """
        Returns custom result entry description for a task.
        task: django object

        returned value: HTML tags allowed
        """

        return "%s <tt>%s</tt>" % (self.optionLabel, self.command)

    def saveCartItem(self, request):
        """
        Save cart item's custom data to DB
        """

        post = request.POST
        try:
            idList = eval(post['IdList'])
            itemID = str(post['ItemId'])
            resultsOutputDir = post['ResultsOutputDir']
            config = post['Config']
        except Exception, e:
            raise PluginError, ("POST argument error. Unable to process data: %s" % e)

        items = CartItem.objects.filter(kind__name__exact = self.id).order_by('-date')
        if items:
            itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
        else:
            itemName = "%s-%d" % (itemID, len(items)+1)

        # Custom data
        data = { 
            'resultsOutputDir'  : resultsOutputDir,
            'idList'            : idList, 
            'config'            : config,
        }
        sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')

        profile = request.user.get_profile()
        k = Processing_kind.objects.filter(name__exact = self.id)[0]
        cItem = CartItem(kind = k, name = itemName, user = request.user, mode = profile.dflt_mode, group = profile.dflt_group)
        cItem.data = sdata
        cItem.save()

        return "Item %s saved" % itemName

    def reprocessAllFailedProcessings(self, request):
        """
        Returns parameters to allow reprocessing of failed processings
        """
        # FIXME: TODO
        pass

    def getSavedItems(self, request):
        """
        Returns a user's saved items for this plugin 
        """
        from terapix.youpi.views import get_entity_permissions
        # Full cart items count to be stored in the cache
        full_count = CartItem.objects.filter(kind__name__exact = self.id).count()
        saved = cache.get(self.id + '_saved_items')
        if saved:
            if cache.get(self.id + '_saved_items_num') == full_count:
                return saved

        items, filtered = read_proxy(request, CartItem.objects.filter(kind__name__exact = self.id).order_by('-date'))
        res = []
        for it in items:
            data = marshal.loads(base64.decodestring(str(it.data)))
            res.append({
                'date'              : "%s %s" % (it.date.date(), it.date.time()), 
                'username'          : str(it.user.username),
                'idList'            : str(data['idList']), 
                'itemId'            : str(it.id), 
                'resultsOutputDir'  : str(data['resultsOutputDir']),
                'name'              : str(it.name),
                'config'            : str(data['config']),
                'perms'             : json.encode(get_entity_permissions(request, 'cartitem', it.id)),
            })

        cache.set(self.id + '_saved_items_num', full_count)
        cache.set(self.id + '_saved_items', res)
        return res

    def getReprocessingParams(self, request):
        """
        Returns all information for reprocessing a stiff job
        """
        try:
            taskId = request.POST['TaskId']
        except KeyError, e:
            raise PluginError, 'Bad parameters'

        data = Plugin_stiff.objects.get(task__id = int(taskId))
        rels = Rel_it.objects.filter(task__id = int(taskId))
        # Must be a list of list
        idList = [[int(r.image.id) for r in rels]]

        return {
                'resultsOutputDir'  : str(self.getUserResultsOutputDir(request, data.task.results_output_dir, data.task.user.username)),
                'idList'            : str(idList), 
        }

