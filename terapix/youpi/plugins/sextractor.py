# vim: set ts=4

import sys, os.path, re, time, string, re, glob
import marshal, base64, zlib
import xml.dom.minidom as dom
#
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *
from terapix.youpi.models import *
from terapix.youpi.auth import read_proxy
from lib.common import get_static_url, get_tpx_condor_upload_url
import terapix.lib.cluster.condor as condor
#
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render_to_response 
from django.template import RequestContext

class Sextractor(ProcessingPlugin):
    """
    Sextractor plugin

    Source extractor for FITS image
    - Need FITS image
    - Produce catalogs
    """
    def __init__(self):
        ProcessingPlugin.__init__(self)
        #
        # REQUIRED members (see doc/writing_plugins/writing_plugins.pdf)
        #
        self.id = 'sex'
        self.optionLabel = 'Sextractor'
        self.description = 'Sources extractor'
        # Item prefix in processing cart. This should be short string since
        # the item ID can be prefixed by a user-defined string
        self.itemPrefix = 'SEX'
        self.index = 1

        self.template           = 'plugins/sextractor.html'                             # Main template, rendered in the processing page
        self.itemCartTemplate   = 'plugins/sextractor_item_cart.html'                   # Template for custom rendering into the processing cart
        self.jsSource           = 'plugins/sextractor.js'                               # Custom javascript
        self.isAstromatic       = True                                                  # Part of the www.astromatic.net software suite (Scamp, Swarp, Sextractor...)

    def saveCartItem(self, request):
        post = request.POST
        
        try:
            idList                  = eval(post['IdList'])
            itemID                  = str(post['ItemId'])
            
            flagPath                = post['FlagPath']
            weightPath              = post['WeightPath']
            psfPath                 = post['PsfPath']

            dualMode                = int(post['DualMode'])
            dualImage               = post['DualImage']
            dualWeightPath          = post['DualWeightPath']
            dualFlagPath            = post['DualFlagPath']

            config                  = post['Config']
            param                   = post['Param']
            resultsOutputDir        = post['ResultsOutputDir']

        except Exception, e:
                raise PluginError, "POST argument error. Unable to process data:  %s" %e

        items = CartItem.objects.filter(kind__name__exact = self.id).order_by('-date')
        if items:
            itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
        else:
            itemName = "%s-%d" % (itemID, len(items)+1)

        # Custom data
        data = { 'idList'               : idList,
                 'weightPath'           : weightPath,
                 'flagPath'             : flagPath,
                 'psfPath'              : psfPath,
                 'dualMode'             : dualMode,
                 'dualImage'            : dualImage,
                 'dualweightPath'       : dualWeightPath,
                 'dualflagPath'         : dualFlagPath,
                 'resultsOutputDir'     : resultsOutputDir, 
                 'config'               : config,
                 'param'                : param,
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
        pass

    def getSavedItems(self, request):
        """
        Returns a user's saved items. 
        """
        # per-user items
        items, filtered = read_proxy(request, CartItem.objects.filter(kind__name__exact = self.id).order_by('-date'))
        res = []
        for it in items:
            data = marshal.loads(base64.decodestring(str(it.data)))
            res.append({
                        'date'              : "%s %s" % (it.date.date(), it.date.time()), 
                        'username'          : str(it.user.username),
                        'idList'            : str(data['idList']), 
                        'weightPath'        : str(data['weightPath']), 
                        'flagPath'          : str(data['flagPath']), 
                        'psfPath'           : str(data['psfPath']), 
                        'dualMode'          : int(data['dualMode']),
                        'itemId'            : str(it.id), 
                        'dualImage'         : str(data['dualImage']), 
                        'dualweightPath'    : str(data['dualweightPath']), 
                        'dualflagPath'      : str(data['dualflagPath']), 
                        'resultsOutputDir'  : str(self.getUserResultsOutputDir(request, data['resultsOutputDir'], it.user.username)),
                        'name'              : str(it.name),
                        'config'            : str(data['config']),
                        'param'             : str(data['param']),
                        })

        return res 

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
            raise PluginError, "POST argument error. Unable to process data. %s" % e
        
        cluster_ids = []
        k = 1
        error = condorError = info = '' 
        
        try:
            dualMode = request.POST['DualMode']
        except Exception, e:
            raise PluginError, "%s" % e
        
        if dualMode == '1':
            idList = eval('[[' + str(idList[0][0]) + ']]')
        try:
            for imgList in idList:
                if not len(imgList):
                    continue
                csfPath = self.__getCondorSubmissionFile(request, imgList)
                cluster_ids.append(manager.cluster.submit(csfPath))
                k += 1
        except CondorSubmitError, e:
                condorError = str(e)
        except PluginAllDataAlreadyProcessed:
                info = 'This item has already been fully processed. Nothing to do.'
        except Exception, e:
                error = "Error while processing list #%d: %s" % (k, e)

        return {'ClusterIds': cluster_ids, 'NoData': info, 'Error': error, 'CondorError': condorError}

    def getOutputDirStats(self, outputDir):
        """
        Return some sextractor-related statistics about processings from outputDir.
        """

        headers = ['Task success', 'Task failures', 'Total processings']
        cols = []
        tasks = Processing_task.objects.filter(results_output_dir = outputDir)
        tasks_success = tasks_failure = 0
        for t in tasks:
            if t.success == 1:
                tasks_success += 1
            else:
                tasks_failure += 1

        stats = {   'TaskSuccessCount'  : [tasks_success, "%.2f" % (float(tasks_success)/len(tasks)*100)],
                    'TaskFailureCount'  : [tasks_failure, "%.2f" % (float(tasks_failure)/len(tasks)*100)],
                    'Total'             : len(tasks) }

        return stats

    def __getCondorSubmissionFile(self, request, idList):
        """
        Generates a suitable Condor submission for processing /usr/bin/uptime jobs on the cluster.

        Note that the sexId variable is used to bypass the config variable: it allows to get the 
        configuration file content for an already processed image rather by selecting content by config 
        file name.
        """
        post = request.POST
        try:
            itemId                  = str(post['ItemId'])
            weightPath              = post['WeightPath']
            flagPath                = post['FlagPath']
            psfPath                 = post['PsfPath']
            dualMode                = post['DualMode']
            dualImage               = post['DualImage']
            dualFlagPath            = post['DualFlagPath']
            dualWeightPath          = post['DualWeightPath']
            config                  = post['Config']
            param                   = post['Param']
            taskId                  = post.get('TaskId', '')
            resultsOutputDir        = post['ResultsOutputDir']
            reprocessValid          = int(post['ReprocessValid'])
        except Exception, e:
            raise PluginError, "POST argument error. Unable to process data: %s" % e

        #
        # File selection and storage.(for the configuration file and the parameter file)
        #
        # Rules:    if sexId has a value, then the  file content is retreive
        #           from the existing Sextractor processing. Otherwise, the  file content
        #           is fetched by name from the File objects in database.
        #
        #           Selected file content is finally saved to a regular file.
        #
        try:
            if len(taskId):
                config, param = Plugin_sex.objects.filter(id = int(taskId))[0]
                contconf = str(zlib.decompress(base64.decodestring(config.config)))
                contparam = str(zlib.decompress(base64.decodestring(param.param)))
            else:
                config = ConfigFile.objects.filter(kind__name__exact = self.id, name = config, type__name__exact = 'config')[0]
                param = ConfigFile.objects.filter(kind__name__exact = self.id, name = param, type__name__exact = 'param')[0]
                contconf = config.content
                contparam = param.content
        except IndexError:
            # File not found, maybe one is trying to process data from a saved item 
            # with a delete file
            raise PluginError, "The file you want to use for this processing has not been found " + \
                "in the database... Are you trying to process data with a file that has been deleted?"
        except Exception, e:
            raise PluginError, "Unable to use a suitable  file: %s" % e

        now = time.time()

        # Condor submission file
        cluster = condor.YoupiCondorCSF(request, self.id, desc = self.optionLabel)
        csfPath = cluster.getSubmitFilePath()
        tmpDir = os.path.dirname(csfPath)

        # Sex config file
        customrc = os.path.join(tmpDir, "sex-config-%s.rc" % now)
        sexrc = open(customrc, 'w')
        sexrc.write(contconf)
        sexrc.close()
    
        # Sex param file
        custompc = os.path.join(tmpDir, "sex-param-%s.pc" % now)
        sexpc = open(custompc, 'w')
        sexpc.write(contparam)
        sexpc.close()

        images = Image.objects.filter(id__in = idList)
        if not images:
            raise CondorSubmitError, 'Image list is empty: no match (are you using a selection pointing to deleted images?)'

        # Shall we skip this processing (already successful with same parameters?)
        if not reprocessValid:
            skip_processing = False
            from django.db import connection
            cur = connection.cursor()
            cur.execute("""
SELECT p.id FROM youpi_processing_task AS p, youpi_processing_kind AS k, youpi_rel_it AS r 
WHERE p.kind_id = k.id 
AND k.name = '%s' 
AND p.success = 1
AND r.task_id = p.id
AND r.image_id IN (%s)
ORDER BY p.id DESC
""" % (self.id, ','.join([str(id) for id in idList])))
            res = cur.fetchall()
            if res:
                # Checks for current image selection
                for r in res:
                    task = Processing_task.objects.get(pk = r[0])
                    rels = Rel_it.objects.filter(task = task)
                    reimgs = [int(rel.image_id) for rel in rels]
                    if reimgs != idList: continue
                    sex = Plugin_sex.objects.get(task = task)
                    conf = str(zlib.decompress(base64.decodestring(sex.config)))
                    par = str(zlib.decompress(base64.decodestring(sex.param)))
                    if  conf == contconf and  par == contparam and weightPath == sex.weightPath and flagPath == sex.flagPath and \
                        psfPath == sex.psfPath and dualWeightPath == sex.dualweightPath and dualImage == sex.dualImage and dualFlagPath == sex.dualflagPath:
                        skip_processing = True
                        break
            if skip_processing:
                raise PluginAllDataAlreadyProcessed

        xmlName = self.getConfigValue(contconf.split('\n'), 'XML_NAME')
        xmlRootName = xmlName[:xmlName.rfind('.')]
            
        # Content of YOUPI_USER_DATA env variable passed to Condor
        userData = {'Kind'                  : self.id,                          # Mandatory for AMI, Wrapper Processing (WP)
                    'UserID'                : str(request.user.id),             # Mandatory for AMI, WP
                    'ItemID'                : itemId,
                    'SubmissionFile'        : csfPath, 
                    'ConfigFile'            : customrc, 
                    'ParamFile'             : custompc, 
                    'Descr'                 : '',                               # Mandatory for Active Monitoring Interface (AMI) - Will be filled later
                    'Weight'                : str(weightPath), 
                    'Flag'                  : str(flagPath), 
                    'Psf'                   : str(psfPath), 
                    'DualMode'              : int(dualMode),
                    'DualImage'             : str(dualImage),
                    'DualWeight'            : str(dualWeightPath), 
                    'DualFlag'              : str(dualFlagPath), 
                } 

        # Set up default files to delete after processing
        self.setDefaultCleanupFiles(userData)
    
        #Dual Mode check

        if dualMode == '1':
            imgdual = Image.objects.filter(id = dualImage)[0]
            path2 = os.path.join(imgdual.path, imgdual.filename + '.fits')
            userData['DualImage'] = str(path2)

        step = 0                            # At least step seconds between two job start

        # Generate CSF
        cluster.setTransferInputFiles([
            customrc,
            custompc,
            os.path.join(settings.TRUNK, 'terapix', 'youpi', 'plugins', 'conf', 'sex.default.conv'),
            os.path.join(settings.TRUNK, 'terapix', 'youpi', 'plugins', 'conf', 'sex.default.nnw'),
        ])

        #
        # Delaying job startup will prevent "Too many connections" MySQL errors
        # and will decrease the load of the node that will receive all qualityFITS data
        # results (PROCESSING_OUTPUT) back. Every job queued will be put to sleep StartupDelay 
        # seconds
        #
        userData['StartupDelay'] = step
        userData['Warnings'] = {}

        # One image per job
        for img in images:
            # Stores real image name (as available on disk)
            userData['RealImageName'] = str(img.filename)

            path = os.path.join(img.path, userData['RealImageName'] + '.fits')

            # WEIGHT checks
            if weightPath:
                if os.path.isdir(weightPath):
                    weight = os.path.join(weightPath, userData['RealImageName'] + '_weight.fits')
                elif os.path.isfile(weightPath):
                    weight = weightPath
                else:
                    raise CondorSubmitError, "Bad weight path '%s' for image %s" % (weightPath, img)

            # flag checks
            if flagPath:
                if os.path.isdir(flagPath):
                    flag = os.path.join(flagPath, userData['RealImageName'] + '_flag.fits')
                elif os.path.isfile(flagPath):
                    flag = flagPath
            
            # PSF checks
            if psfPath:
                if os.path.isdir(psfPath):
                    psf = os.path.join(psfPath, userData['RealImageName'] + '.psf')
                elif os.path.isfile(psfPath):
                    psf = psfPath

            # Dual WEIGHT checks
            if dualWeightPath:
                if os.path.isdir(dualWeightPath):
                    dualWeight = os.path.join(dualWeightPath, imgdual.filename + '_weight.fits')
                elif os.path.isfile(dualWeightPath):
                    dualWeight = dualWeightPath

            # Dual flag checks
            if dualFlagPath:
                if os.path.isdir(dualFlagPath):
                    dualFlag = os.path.join(dualFlagPath, imgdual.filename + '_flag.fits')
                elif os.path.isfile(dualFlagPath):
                    dualFlag = dualFlagPath

            #
            # $(Cluster) and $(Process) variables are substituted by Condor at CSF generation time
            # They are later used by the wrapper script to get the name of error log file easily
            #
            userData['ImgID'] = str(img.id)

            if dualMode == '1':
                userData['Descr'] = str("%s of %s (Dual Mode), %s" % (self.optionLabel, img.name, xmlRootName))     # Mandatory for Active Monitoring Interface (AMI)
            else:
                userData['Descr'] = str("%s of %s (Single Mode), %s" % (self.optionLabel, img.name, xmlRootName))       # Mandatory for Active Monitoring Interface (AMI)

            userData['ResultsOutputDir'] = resultsOutputDir
            # Mandatory for WP
            userData['JobID'] = self.getUniqueCondorJobId()

            # Parameters to use for each job
            sex_params = ''
            try:
                url = self.getConfigValue(contconf.split('\n'), 'XSL_URL')
                xslPath = re.search(r'file://(.*)$', url)
                if xslPath:
                    # This is a local (or NFS) path, Youpi will serve it
                    sex_params = "-XSL_URL %s" % os.path.join(
                        get_static_url(userData['ResultsOutputDir']),
                        request.user.username, 
                        userData['Kind'], 
                        userData['ResultsOutputDir'][userData['ResultsOutputDir'].find(userData['Kind'])+len(userData['Kind'])+1:],
                        os.path.basename(xslPath.group(1))
                    )
                else:
                    # Copy attribute as is
                    if url: sex_params = "-XSL_URL " + url
            except TypeError, e:
                pass
            except AttributeError, e:
                pass

            # Adds weight support 
            if weightPath:
                if not os.path.exists(weight):
                    raise PluginError, "the weight file %s doesn't exists" % weight
                else:
                    sex_params += " -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE %s" % weight
                    #support for dual weight
                    if dualWeightPath:
                        if not os.path.exists(dualWeight):
                            raise PluginError, "the dual weight file %s doesn't exists" % dualWeight
                        else:
                            sex_params += ",%s" % (dualWeight)
            elif (not weightPath and dualWeightPath):
                if not os.path.exists(dualWeight):
                    raise PluginError, "the dual weight file %s doesn't exists" % dualWeight
                else:
                    sex_params += " -WEIGHT_TYPE NONE, MAP_WEIGHT -WEIGHT_IMAGE NONE, %s" % dualWeight

            # Adds flag support 
            if flagPath:
                if not os.path.exists(flag):
                    raise PluginError, "the flag file %s doesn't exists" % flag
                else:
                    sex_params += " -FLAG_IMAGE %s" % flag
                    #support for dual weight
                    if dualFlagPath:
                        if not os.path.exists(dualFlag):
                            raise PluginError, "the dual flag file %s doesn't exists" % dualFlag
                        else:
                            sex_params += ",%s" % dualFlag
            elif (not flagPath and dualFlagPath):
                if not os.path.exists(dualFlag):
                    raise PluginError, "the dual flag file %s doesn't exists" % dualFlag
                else:
                    sex_params += " -FLAG_IMAGE NONE,%s" % dualFlag
                
            # Adds psf support 
            if psfPath:
                if not os.path.exists(psf):
                    raise PluginError, "the psf file %s doesn't exists" % psf
                else:
                    sex_params += " -PSF_NAME %s" % psf

            # Base64 encoding + marshal serialization
            # Will be passed as argument 1 to the wrapper script
            try:
                encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
            except ValueError:
                raise ValueError, userData

            if dualMode == '1':
                # Use dual mode
                images_arg = "%s,%s" % (path, path2)
            else:
                images_arg = path

            cluster.addQueue(
                queue_args = str("%(encuserdata)s %(condor_transfer)s %(sextractor)s %(images_arg)s %(params)s -c %(config)s -PARAMETERS_NAME %(param)s" % {
                    'encuserdata'       : encUserData, 
                    'condor_transfer'   : "%s %s" % (settings.CMD_CONDOR_TRANSFER, settings.CONDOR_TRANSFER_OPTIONS),
                    'sextractor'        : settings.CMD_SEX,
                    'images_arg'        : images_arg,
                    'params'            : sex_params,
                    'config'            : os.path.basename(customrc),
                    'param'             : os.path.basename(custompc),
                }),
                queue_env = {
                    'USERNAME'              : request.user.username,
                    # TPX_CONDOR_UPLOAD_URL needs img.name + '/' at the end to create one directory by image name
                    'TPX_CONDOR_UPLOAD_URL' : get_tpx_condor_upload_url(resultsOutputDir) + img.name + '/', 
                    'YOUPI_USER_DATA'       : encUserData,
                }
            )

        cluster.write(csfPath)
        return csfPath

    def autoProcessSelection(self, request):
        """
        Looks for mandatory data for being able to process an image selection with Sextractor 
        automatically. Checks are performed in the following order:
        1. Gets the list of images for that selection
        2. Looks for a config file with the name of this selections and use it if found. If not, uses 
           the default config file for the job. Emits a warning.
        @return a dictionary
        """
        post = request.POST
        try:
            selName = request.POST['SelName']
            weightPath = request.POST['WeightPath']
            flagPath = request.POST['FlagPath']
            psfPath = request.POST['PsfPath']
            param = request.POST['Param']
            dualMode = int(request.POST['DualMode'])
            dualImage = request.POST['DualImage']
            dualWeightPath = request.POST['DualWeightPath']
            dualFlagPath = request.POST['DualFlagPath']
            addDefaultToCart = int(request.POST['AddDefaultToCart'])
        except Exception, e:
            raise PluginError, "POST argument error. Unable to process data."

        warnings = []
        # 1. List of images matching that selection
        try:
            sel = ImageSelections.objects.filter(name = selName)[0]
        except Exception, e:
            raise PluginError, 'Bad selection name: ' + selName
        idList = marshal.loads(base64.decodestring(sel.data))[0]

        # 2. Looks for a config file matching the selection name
        config = ConfigFile.objects.filter(name = selName, type__name = 'config')
        if not config:
            config = 'default'
            warnings.append("Config file %s not found, using default" % selName)
        else:
            config = selName

        # The following result set will be used on the client side to add an item in 
        # the processing cart
        res = {
            'selName'               : selName,
            'weightPath'            : weightPath,
            'flagPath'              : flagPath,
            'psfPath'               : psfPath,
            'param'                 : param,
            'idList'                : str([[int(id) for id in idList]]), # Must be a list of one list of integers (not long)
            'config'                : config,
            'warning'               : warnings,
            'imgCount'              : len(idList),
            'addDefaultToCart'      : addDefaultToCart,
            # Dual image mode
            'dualMode'              : dualMode,
            'dualImage'             : dualImage,
            'dualWeightPath'        : dualWeightPath,
            'dualFlagPath'          : dualFlagPath,
        }
        return res

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
        data = Plugin_sex.objects.filter(task__id = taskid)[0]
        
        # Error log content
        if task.error_log:
            err_log = str(zlib.decompress(base64.decodestring(task.error_log)))
        else:
            err_log = ''

        if data.log:
            sexlog = str(zlib.decompress(base64.decodestring(data.log)))
        else:
            sexlog = ''

        # Get related images
        rels = Rel_it.objects.filter(task__id = taskid)
        imgs = [r.image for r in rels]


        sexHistory = Rel_it.objects.filter(image__in = imgs, task__kind__name = self.id).order_by('task')
        # Finds distinct tasks
        tasksRelated = []
        for sh in sexHistory:
            if sh.task not in tasksRelated:
                tasksRelated.append(sh.task)

        gtasks = []
        # Remove all tasks than depends on more images
        for t in tasksRelated:
            r = Rel_it.objects.filter(task = t)
            if len(r) == len(imgs):
                gtasks.append(t)

        history = []
        for st in gtasks:
            history.append({'User'          : str(st.user.username),
                            'Success'       : st.success,
                            'Start'         : str(st.start_date),
                            'Duration'      : str(st.end_date-st.start_date),
                            'Hostname'      : str(st.hostname),
                            'TaskId'        : str(st.id),
                            })

        thumbs = glob.glob(os.path.join(str(task.results_output_dir),'tn_*.png')) 
        if data.thumbnails:
            thumbs = [ thumb for thumb in thumbs]

        return {    'TaskId'                : str(taskid),
                    'Title'                 : str("%s" % task.title),
                    'User'                  : str(task.user.username),
                    'Success'               : task.success,
                    'Start'                 : str(task.start_date),
                    'End'                   : str(task.end_date),
                    'Duration'              : str(task.end_date-task.start_date),
                    'WWW'                   : str(data.www),
                    'ResultsOutputDir'      : str(task.results_output_dir),
                    'ResultsLog'            : sexlog,
                    'Config'                : str(zlib.decompress(base64.decodestring(data.config))),
                    'Param'                 : str(zlib.decompress(base64.decodestring(data.param))),
                    'Previews'              : thumbs,
                    'HasThumbnails'         : data.thumbnails,
                    'FITSImages'            : [str(os.path.join(img.path, img.filename + '.fits')) for img in imgs],
                    'ClusterId'             : str(task.clusterId),
                    'History'               : history,
                    'Log'                   : err_log,
                    'Weight'                : str(data.weightPath),
                    'DualWeight'            : str(data.dualweightPath),
                    'Flag'                  : str(data.flagPath),
                    'DualFlag'              : str(data.dualflagPath),
                    'Psf'                   : str(data.psfPath),
                    'DualMode'              : str(data.dualMode),
                    'DualImage'             : str(data.dualImage),
        }


    def getResultEntryDescription(self, task):
        """
        Returns custom result entry description for a task.
        task: django object

        returned value: HTML tags allowed
        """

        return "%s <tt>%s</tt>" % (self.optionLabel, self.command)

    def setDefaultConfigFiles(self, defaultCF):
        """
        Alter the default config files list with an entry for the 
        Sextractor parameter file.
        """

        defaultCF.append({'path': os.path.join(settings.PLUGINS_CONF_DIR, self.id + '.param.default'), 'type': 'param'})
        return defaultCF

    def reports(self):
        """
        Adds reporting capabilities to Sextractor plugin
        """

        rdata = None
        return rdata

    def getReport(self, request, reportId):
        """
        Generates a report.
        @param reportId report Id as returned by the reports() function
        """
        post = request.POST
        return HttpResponseNotFound('Report not found.')
