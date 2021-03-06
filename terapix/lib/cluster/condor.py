"""
:mod:`condor` --- Condor Library
================================

This library provides convenient classes for working with the `Condor`_ clustering 
system. The :mod:`terapix.lib.cluster.condor` module provides helper classes and 
methods to deal with submission files (to easily generate them) and monitor running 
jobs.

.. _Condor: http://www.cs.wisc.edu/condor/

.. automodule:: terapix.lib.cluster
   :members:
"""

# vim: set ts=4

from django.conf import settings
from django.http import HttpRequest
import django.http
#
from terapix.lib.cluster import ClusterClient, ClusterQueue, ClusterJob
from terapix.youpi.models import *
from terapix.exceptions import *
from terapix.lib.common import get_temp_dir
#
import types, time, os.path
import os, string, re
import xml.dom.minidom as dom
import base64, marshal

class CondorError(Exception): pass

class CondorCSF(object):
    """
    Base class for generating a *Condor submission file*.  Youpi extends this class with 
    :class:`~terapix.lib.cluster.condor.YoupiCondorCSF`.
    """
    # Static header
    _csfHeader = """#
# Condor submission file
# Please not that this file has been generated automatically by Youpi
# DO NOT MODIFY.
#
# %(description)s
#

universe                = vanilla
executable              = %(exec)s
transfer_executable     = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_output_files   = NOP
log                     = %(log)s
error                   = %(error)s
output                  = %(out)s
notification            = Error
transfer_input_files    = %(transfer)s
%(more)s
%(requirements)s
%(queues)s
"""
    attrs = ['_executable', '_desc', '_transfer_input_files', '_queues']

    @staticmethod
    def getSubmitFilePath(caption):
        """
        Returns the path to Condor submit file path.
        Each call generates a new filename so that no file gets overwritten.
        The returned name should then be used by plugins to add some content to it.

        `caption` is  a short word that will be appended to the final file name. It 
        returns a path to unique Condor submit file path.
        """
        if type(caption) not in types.StringTypes:
            raise TypeError, 'caption must be a string'
        path = os.path.join(settings.BASE_TEMP_DIR, "CONDOR-%s-%s.csf" % (caption, time.time()))
        return path

    @staticmethod
    def getLogFilenames(caption):
        """
        Returns a dictionnary with entries for the log, error and output filenames 
        that should be used by plugins generating Condor submission files.

        The returnes dictionnary has the following keys: ``log``, ``error`` and ``out``.
        """
        if type(caption) not in types.StringTypes:
            raise TypeError, caption
        pattern = os.path.join(settings.CONDOR_LOG_DIR, caption.upper() + '.%s.$(Cluster).$(Process)')

        return {
            'log'   : pattern % "log",
            'error' : pattern % "err",
            'out'   : pattern % "out",
        }

    def __init__(self, desc = None, **kargs):
        """
        Constructor. Initialises internal data structures.

        An optional description `desc` can be supplied.
        """
        for attribute in self.attrs:
            self.__dict__[attribute] = ''

        if desc:
            if type(desc) not in types.StringTypes:
                raise TypeError, "desc parameter must be a string"
            self._desc = desc

        self.__dict__['_queues'] = []
        self.data = {}

    def updateData(self):
        """
        Updates data dictionary to be used when rendering the CSF's content
        """
        self.data = {
            'description'   : self._desc, 
            'exec'          : self._executable, 
            'transfer'      : self._transfer_input_files,
            'more'          : '',
            'requirements'  : '',
        }
        queues_csf = ''
        for queue in self._queues:
            if queue.has_key('args'): queues_csf += "arguments = %s\n"  % queue['args']
            if queue.has_key('env'): queues_csf += "environment = %s\n" % '; '.join(['%s=%s' % (k.upper(), v) for k,v in queue['env'].iteritems()])
            queues_csf += 'queue\n\n'

        # Adds queues related information
        self.data.update(queues = queues_csf)
        # Adds log filenames
        self.data.update(self.getLogFilenames('job'))

    def __repr__(self):
        return "<Condor Submission File exec: %s desc: %s>" % (self._executable, self._desc)

    def addQueue(self, queue_args = None, queue_env = None):
        """
        Queues a Condor job, with optional arguments `queue_args` and `queue_env`.
        `queue_args` is a string of any argument that must be passed to the Condor executable.
        `queue_env` is a dictionary of variables used to define environment variables to be passed 
        to Condor at job execution.

        A dictionary of data associated with the newly created queue is returned. It can be empty 
        if no `queue_args` or `queue_env` has been provided. Or it can have ``args`` and ``env`` 
        keys if those two input parameters have been provided.
        """
        if queue_args and (type(queue_args) not in types.StringTypes):
            raise TypeError, 'queue_args must be a string'

        if queue_env:
            if (type(queue_env) != types.DictType):
                raise TypeError, 'queue_env must be a dictionary'
            for k,v in queue_env.iteritems():
                if (type(k) not in types.StringTypes) or (type(v) not in types.StringTypes):
                    raise TypeError, 'Environment arguments keys and values must be strings:' + str(type(k)) + str(type(v))

        queue_data = {}
        if queue_args: queue_data['args'] = queue_args
        if queue_env: queue_data['env'] = queue_env
        self._queues.append(queue_data)

        return queue_data

    def removeQueue(self, idx):
        """
        Remove a queue from Condor's queue list.

        `idx` is the index of the queue in the list. Raises ``IndexError`` if `idx` 
        is out or range.
        """
        if type(idx) != types.IntType:
            raise TypeError, "idx must be a positive integer"
        try:
            del self._queues[idx]
        except IndexError:
            raise IndexError, "No queue at position %d to remove. Index out of range" % idx

    def write(self, filename):
        """
        Write the Condor submission file content (as returned by 
        :func:`getSubmissionFileContent` to a file named ``filename``.
        """
        f = open(filename, 'w')
        f.write(self.getSubmissionFileContent())
        f.close()

    def getSubmissionFileContent(self):
        """
        Return the submission file content. Always returns a valid Condor submission 
        file structure, even if no queue was added with :func:`addQueue` (which is 
        the default).
        """
        self.updateData()
        return self._csfHeader % self.data

    def setExecutable(self, filename):
        """
        Set executable ``filename`` to use with Condor. Raises ``TypeError`` if it's 
        not a string.
        """
        if type(filename) not in types.StringTypes:
            raise TypeError, "Executable must be of type 'string', not %s" % type(filename)
        self._executable = filename

    def setTransferInputFiles(self, files):
        """
        Set a list of input ``files`` to be transferred by Condor (available 
        as the *transfer_input_files* CSF directive).

        Raises a ``TypeError`` exception if ``files`` is not a list of strings.
        """
        if type(files) != types.ListType:
            raise TypeError, "Must be a list of path to files to transfer"

        for file in files:
            if type(file) not in types.StringTypes:
                raise TypeError, "File '%s' must be of type 'string', not %s" % (file, type(file))

        self._transfer_input_files = ', '.join(files)


class YoupiCondorCSF(CondorCSF):
    """
    Processing plugins use this class to easily generate a suitable Condor submission file 
    for submitting their jobs.
    
    This class implements business logic for Youpi. The default executable is set to 
    use the :mod:`terapix.script.wrapper_processing` script.

    The *request* parameter is the current :class:`~django.http.HttpRequest` instance to use.
    The *pluginId* parameter is the plugin internal name. A class:`TypeError` exception is 
    raised if it's not a string. The *desc* parameter is a description.
    """
    def __init__(self, request, pluginId, desc = None):
        CondorCSF.__init__(self, desc)
        if not isinstance(request, HttpRequest):
            raise TypeError, "request must be an HttpRequest object"
        if type(pluginId) not in types.StringTypes:
            raise TypeError, 'pluginId must be a string'

        self.__request = request
        self.__id = pluginId
        self.setExecutable(os.path.join(settings.TRUNK, 'terapix', 'script', 'wrapper_processing.py'))

    @property
    def request(self):
        """
        The Django :class:`~django.http.HttpRequest` associated instance, as 
        supplied to the constructor.
        """
        return self.__request

    @property
    def id(self):
        """
        The plugin id, as supplied to the constructor with *pluginId*.
        """
        return self.__id

    def getConfigFilePath(self):
        """
        Return a path to a new Condor configuration file used for this processing.
        Each call generates a new filename so that no file gets overwritten.

        Returns a path to a new file. The returned name should then be used 
        by plugins to add some content to it.
        """
        return os.path.join(get_temp_dir(self.__request.user.username, self.__id), "%s-%s.rc" % (self.__id.upper(), time.time()))


    def getSubmitFilePath(self):
        """
        Overrides the :func:`~terapix.lib.cluster.condor.CondorCSF.getSubmitFilePath` 
        static function (not static anymore).
        """
        return os.path.join(get_temp_dir(self.__request.user.username, self.__id), "CONDOR-%s-%s.csf" % (self.__id, time.time()))

    def getLogFilenames(self, unused=None, user=None, date=None):
        """
        Overrides the :func:`~terapix.lib.cluster.condor.CondorCSF.getLogFilenames` 
        static function (not static anymore).

        .. todo:: fixme

        The *unused* parameter is unused (here for signature constraint only), *user* is 
        the current Django logged in :class:`~django.contrib.auth.models.User`, *date* is 
        a custom :class:`~datetime.date` object.

        Returns a dictionnary with entries for the log, error and output filenames 
        that should be used by plugins generating Condor submission files. The 
        dictionnary has the ``log``, ``error`` and ``out`` keys.
        """
        import datetime
        if date and not isinstance(date, datetime.date):
            raise TypeError, "Bad date"

        if user:
            username = user.username
        else:
            username = self.__request.user.username
        if date:
            pattern = os.path.join(get_temp_dir(username, self.__id, False), str(date),  self.__id.upper() + '.%s')
        else:
            pattern = os.path.join(get_temp_dir(username, self.__id), self.__id.upper() + '.%s.$(Cluster).$(Process)')

        return {
            'log'   : pattern % "log",
            'error' : pattern % "err",
            'out'   : pattern % "out",
        }

    def getSubmissionFileContent(self):
        """
        Overrides the :func:`~terapix.lib.cluster.condor.CondorCSF.getSubmissionFileContent` 
        function to provide a custom ``PATH`` environment to all defined queues.

        Returns the Condor submission file content.
        """
        if not self._transfer_input_files:
            # Add at least required files
            self.setTransferInputFiles([])

        # Supply a suitable PATH environment variable to all queues
        # Must be done _before_ calling updateData()
        for queue in self._queues:
            if not queue.has_key('env'): queue['env'] = {}
            # FIXME: define PATH in settings.py
            queue['env']['PATH'] = '/usr/local/bin:/usr/bin:/bin:/opt/bin:/opt/condor/bin'

        self.updateData()
        self.data.update({
            'requirements'  : self.getRequirementString(),
            'more' : "initialdir = %s\nnotify_user = %s" % (os.path.join(settings.TRUNK, 'terapix', 'script'), settings.CONDOR_NOTIFY_USER)
        })
        self.data.update(self.getLogFilenames())

        return self._csfHeader % self.data

    def __repr__(self):
        return "<Youpi Condor Submission File exec: %s desc: %s>" % (self._executable, self._desc)

    def setTransferInputFiles(self, files):
        """
        Overrides :func:`~terapix.lib.cluster.CondorCSF.setTransferInputFiles` by appending 
        required modules to the *files* list parameter: ``local_conf.py``, ``settings.py``, 
        ``lib/common.py``, ``script/DBGeneric.py`` and ``NOP``.
        """
        if type(files) != types.ListType:
            raise TypeError, "Must be a list of path to files to transfer"
        submit_file_path = os.path.join(settings.TRUNK, 'terapix')
        for file in ('local_conf.py', 'settings.py', 'private_conf.py', os.path.join('lib', 'common.py'), os.path.join('script', 'DBGeneric.py'), 'NOP'): 
            files.append(os.path.join(submit_file_path, file))

        super(YoupiCondorCSF, self).setTransferInputFiles(files)

    def getRequirementString(self):
        """
        Build a requirement string suitable for Condor, using defined node policies 
        and selection to build a dynamic list of target machines.

        Returns a requirement string ready to be merged into the submission file.

        .. seealso:: Function :func:`~terapix.lib.cluster.condor.CondorClient.getStatus`.
        """
        post = self.__request.POST
        try:
            condorSetup = post['CondorSetup']
        except Exception, e:
            raise CondorError, "POST argument error. Unable to process data."

        from terapix.youpi.pluginmanager import manager
        vms = manager.cluster.getStatus()

        if condorSetup == 'default':
            dflt_setup = marshal.loads(base64.decodestring(self.__request.user.get_profile().dflt_condor_setup))
            # Check Behaviour: policy or selection
            if not dflt_setup.has_key(self.__id):
                raise CondorError, "No default Condor setup found for '%s' plugin (id: %s)." % (self._desc, self.__id)

            db = dflt_setup[self.__id]['DB']
            if db == 'policy':
                pol = CondorNodeSel.objects.filter(label = dflt_setup[self.__id]['DP'], is_policy = True)[0]
                req = get_requirement_string(pol.nodeselection, vms)
            else:
                # Default behaviour is 'selection'
                req = get_requirement_string_from_selection(dflt_setup[self.__id]['DS'])

        elif condorSetup == 'custom':
            try:
                c_policy = str(post['Policy'])
                c_selection = None
            except Exception, e:
                try:
                    c_selection = str(post['Selection'])
                    c_policy = None
                except Exception, e:
                    raise CondorError, 'condorSetup POST argument error. Unable to process data'

            if c_policy:
                pol = CondorNodeSel.objects.filter(label = c_policy, is_policy = True)[0]
                req = get_requirement_string(pol.nodeselection, vms)
            else:
                req = get_requirement_string_from_selection(c_selection)

        # Add any custom Condor requirements, if any
        custom_req = self.__request.user.get_profile().custom_condor_req
        if custom_req: req = "%s && (%s))" % (req[:-1], custom_req)

        return req


def get_requirement_string(params, vms):
    """
    Returns Condor's requirement string for a *POLICY*.
    For params, allowed criteria are one of: MEM, DSK, HST, SLT

    *params* is a string of params like 'MEM,G,1,G'. *vms* is a list 
    of available cluster node.
    """
    if type(params) not in types.StringTypes:
        raise TypeError, "params must be a string"
    if type(vms) != types.ListType:
        raise TypeError, "vms must be a list"

    # De-serialization mappings
    cdeserial = {
        'G' : '>=',
        'L' : '<=',
        'E' : '='
    }
    sdeserial = {
        'M' : 1,
        'G' : 1024,
        'T' : 1024 * 1024
    }

    # Check params validity
    params = params.replace('*', '.*')
    params = params.split('#')
    for p in params:
        d = p.split(',')
        if len(d) > 4:
            # Wrong format
            raise ValueError, "Malformed parameter: '%s'" % p
        if d[0] not in ('MEM', 'DSK', 'HST', 'SLT'):
            raise ValueError, "Invalid parameter name: '%s'. Must be one of MEM, DSK, HST or SLT" % d[0]
        if len(d) == 4 and d[3] not in sdeserial:
            raise ValueError, "Invalid unit letter: '%s'" % d[3]

    # vms must be a list of lists
    for vm in vms:
        if type(vm) != types.ListType:
            raise TypeError, "Invalid node info. Should be a list, not '%s'" % vm
        for i in vm:
            if type(i) not in types.StringTypes:
                raise TypeError, "'%s' must be a string, not %s" % (i, type(i))

    nodes = [vm[0] for vm in vms]

    crit = {}
    for p in params:
        d = p.split(',')
        if not crit.has_key(d[0]):
            crit[d[0]] = []
        crit[d[0]].append(d[1:])

    req = 'Requirements = ('

    # Memory
    if crit.has_key('MEM'):
        req += '('
        for mem in crit['MEM']:
            comp, val, unit = mem
            req += "Memory %s %d && " % (cdeserial[comp], int(val)*sdeserial[unit])
        req = req[:-4] + ')'

    # Disk
    if crit.has_key('DSK'):
        if req[-1] == ')':
            req += ' && '
        req += '('
        for dsk in crit['DSK']:
            comp, val, unit = dsk
            req += "Disk %s %d && " % (cdeserial[comp], int(val)*sdeserial[unit])
        req = req[:-4] + ')'

    # Host name
    vm_sel = []
    if crit.has_key('HST'):
        for hst in crit['HST']:
            comp, val = hst
            for vm in nodes:
                m = re.search(val, vm)
                if m:
                    if comp == 'M':
                        vm_sel.append(vm)
                else:
                    if comp == 'NM':
                        vm_sel.append(vm)

    # Filter slots
    if crit.has_key('SLT'):
        for slt in crit['SLT']:
            comp, selname = slt
            sel = CondorNodeSel.objects.filter(label = selname)[0]
            data = marshal.loads(base64.decodestring(sel.nodeselection))
            if not crit.has_key('HST') and comp == 'NB':
                vm_sel = nodes
            for n in data:
                # Belongs to
                if comp == 'B':
                    vm_sel.append(n)
                else:
                    if n in vm_sel:
                        try:
                            while 1:
                                vm_sel.remove(n)
                        except:
                            pass

    # Finally build host selection
    if vm_sel:
        if req[-1] == ')':
            req += ' && '
        req += '('
        for vm in vm_sel:
            req += "Name == \"%s\" || " % vm
        req = req[:-4] + ')'
    
    req += ')'
    return req

def get_requirement_string_from_selection(selName):
    """
    Returns Condor's requirement string for a *selection*.
    *selName* is the name of a node selection.

    Raises a ``CondorError`` exception is selName is an unknown exception.
    """
    if type(selName) not in types.StringTypes:
        raise TypeError, 'selName must be a String'

    try:
        sel = CondorNodeSel.objects.filter(label = selName, is_policy = False)[0]
    except IndexError:
        raise CondorError, "No selection named '%s' found" % selName

    hosts = marshal.loads(base64.decodestring(sel.nodeselection))
    req = 'Requirements = (('
    for host in hosts:
        req += """Name == "%s" || """ % host
    req = req[:-4] + '))'

    return req


class CondorJob(ClusterJob):
    """
    Define a simple Condor job entity.  The *classAds* keyword parameters set class ads names 
    and values for the current Condor job. They are stored as read-only properties (thus can 
    only be set during object creation). This feature is used to ensure the jobs list returned 
    by the :func:`~terapix.lib.cluster.condor.CondorQueue.getJobs` function cannot be altered.

    .. versionchanged:: 0.7.1
       *classAds* is a keyword parameter, no more a dictionnary.
    """
    def __init__(self, **classAds):
        self.__dict__['classAds'] = classAds

        for ad in ('JobStatus', 'JobStartDate'):
            if not classAds.has_key(ad):
                raise ValueError, "Missing %s key in the classAds" % ad

        for k, v in classAds.iteritems():
            self.__dict__[k] = v

        # These values get updated by CondorQueue
        if not hasattr(self, 'ClusterId'):
            self.__dict__['RemoteHost'] = 'unknown'
            self.__dict__['ClusterId'] = '??'
            self.__dict__['ProcId'] = '??'
            self.__dict__['JobStatusFull'] = str(classAds['JobStatus'])

    def __setattr__(self, name, value):
        """
        Prevents overwritting class Ads properties
        """
        if self.classAds.has_key(name):
            raise AttributeError, "Can't set attribute '%s' (this is a read-only Condor class ad)" % name
        self.__dict__[name] = value

    def __repr__(self):
        msg = ''
        if self.isRunning(): msg = " on %s" % self.RemoteHost
        return "<CondorJob %s.%s is %s%s>" % (self.ClusterId, self.ProcId, self.JobStatusFull.lower(), msg)

    def isRunning(self):
        """
        Returns ``True`` if the job is running.
        """
        return int(self.JobStatus) == 2

    def getJobDuration(self):
        """
        Returns the job's runtime duration, formatted as a string matching HH:MM:SS 
        or ``None`` if the job has been submitted but is not running yet.
        """
        try:
            secs = time.time() - int(self.JobStartDate)
        except TypeError:
            # Job not running yet
            return None

        h = m = 0
        s = int(secs)
        if s > 60:
            m = s/60
            s = s%60
            if m > 60:
                h = m/60
                m = m%60
        return "%02d:%02d:%02d" % (h, m, s)

    def remove(self):
        """
        Remove the job from the current Condor queue.
        """
        if not self.isRunning():
            return False
        pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_rm %s.%s"  % (self.ClusterId, self.ProcId)))
        data = pipe.readlines()
        pipe.close()
        return True

class CondorQueue(ClusterQueue):
    """
    Handles a Condor processing queue. *envPath* is a provided path environment that can 
    be used to locate the ``condor_q`` binary; *globalPool* is a boolean specifying whether 
    queues of all submitters are queried.
    """
    __condor_q_bin = 'condor_q'
    # Interesting class Ads
    # Do NOT change class ads order, see the getJobs() function
    __condor_q_classAds = ('ClusterId', 'ProcId', 'JobStatus', 'RemoteHost', 'JobStartDate', 'Env')
    __condor_q_args = ''

    def __repr__(self):
        jobs, count = self.getJobs()
        if count > 0:
            msg = "%d job" % count
            if count > 1: msg += 's'
        else:
            msg = 'no job'
        return "<Condor queue, %s>" % msg

    @property
    def condor_q_path(self):
        return self.__condor_q_bin

    def __init__(self, envPath = None, globalPool = False):
        if envPath:
            if type(envPath) not in types.StringTypes:
                raise TypeError, "envPath must be a string"
            self.__condor_q_bin = os.path.join(settings.CONDOR_BIN_PATH, self.__condor_q_bin)

        if globalPool:
            if type(globalPool) != types.BooleanType:
                raise TypeError, "globalPool must be a boolean"
            self.__condor_q_args += ' -global'

        # Builds condor_q CLI arguments
        cliArgs = ''
        cAdsLen = len(self.__condor_q_classAds)
        for i in range(cAdsLen):
            if i < cAdsLen - 1: sep = '||'
            else: sep = '\n'
            cliArgs += "-format \"%s" + sep + "\" " + self.__condor_q_classAds[i] + ' '
        self.__condor_q_args = cliArgs

    def getJobs(self):
        """
        Returns a tuple of a list of current active Condor jobs and 
        the number of jobs is that list.
        """
        pipe = os.popen(self.__condor_q_bin + ' ' + self.__condor_q_args)
        # Raw data
        data = pipe.readlines()
        pipe.close()

        # Build CondorJob instances
        jobs = []
        for info in data:
            parts = info.split('||')
            params = {}
            if len(parts) < len(self.__condor_q_classAds):
                # This happens when no given class ad is available 
                # from Condor for a job. Most often it means that 
                # the job is not yet running... so we have to rebuild 
                # a correct 'parts' list
                k = 0
                for ad in self.__condor_q_classAds:
                    if ad in ('RemoteHost', 'JobStartDate'):
                        parts.insert(k, None)
                    k += 1

            for k in range(len(self.__condor_q_classAds)):
                try:
                    params[self.__condor_q_classAds[k]] = parts[k]
                except IndexError:
                    print info
                    raise

            if 'JobStatus' in self.__condor_q_classAds:
                status = int(params['JobStatus'])
                if status == 2: status_full = 'Running'
                elif status == 5: status_full = 'Hold'
                else: status_full = 'Idle'
                params['JobStatusFull'] = status_full

            # Adds new job
            jobs.append(CondorJob(**params))
        return tuple(jobs), len(jobs)

    def removeJob(self, job):
        """
        Remove a job from the Condor queue. Raises a :class:`TypeError` exception 
        if *job* is not a :class:`~terapix.lib.cluster.condor.CondorJob` instance.
        """
        if not isinstance(job, CondorJob):
            raise TypeError, "job must be a CondorJob instance"
        job.remove()

class YoupiCondorQueue(CondorQueue):
    """
    Handles a Condor processing queue for Youpi: only jobs with a YOUPI_USER_DATA env variable are 
    are Youpi jobs.
    """
    def __init__(self, envPath = None, globalPool = False):
        CondorQueue.__init__(self, envPath, globalPool)

    def getJobs(self):
        """
        Override CondorQueue.getJobs() in order to keep only Youpi-related jobs.
        """
        jobs, count = super(YoupiCondorQueue, self).getJobs()
        youpiJobs = []
        for job in jobs:
            if job.Env.find('YOUPI_USER_DATA') >= 0:
                youpiJobs.append(job)
        del jobs

        # Set user data
        for job in youpiJobs:
            m = re.search('YOUPI_USER_DATA=(.*?)$', job.Env)
            userData = m.groups(0)[0]
            c = userData.find(';')
            if c > 0: userData = userData[:c]
            job.UserData = marshal.loads(base64.decodestring(str(userData)))

        return tuple(youpiJobs), count

class CondorClient(ClusterClient):
    """
    .. versionadded:: 0.7.1

    Implementation of a Condor client inheriting the :class:`~terapix.lib.cluster.ClusterClient` class.
    """
    def _shell_submit(self, filepath):
        """
        Actually executes the ``condor_submit`` program and returns all *stdout* content (
        splitted into lines).
        """
        pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, 'condor_submit %s 2>&1' % filepath))
        # submit_content is a list with 2 or 3 elements of content as returned by condor_submit command 
        # (i.e. 2 or 3 lines of plain text)
        res = pipe.readlines()
        pipe.close()
        return res

    def submit(self, filepath, shell_submit=None):
        """
        Submit a job on the cluster. *filepath* is the absolute path to the Condor submission 
        file. By default, the job is submitted using the ``condor_submit`` program. 
        
        A different action can be performed using the *shell_submit* parameter which is the name of 
        a callable function that actually returns the expected string data, splitted into lines.
        
        Raises a :class:`CondorSubmitError` exception if an error occured during jobs submission 
        or a *tuple* ``(count, cluster Id)`` where *count* is the number of single jobs submitted 
        and *cluster Id* is the unique cluster identifier associated with that submission.
        """
        if type(filepath) not in types.StringTypes:
            raise TypeError, "filepath must be a string"

        if shell_submit is None:
            shell_submit = self._shell_submit
        else:
            if type(shell_submit) != types.FunctionType:
                raise TypeError, 'shell_submit must be a callable'

        res = shell_submit(filepath)
        count = cid = 0
        try:
            # Only last line is of interest
            data = res[-1].strip()
            m = re.match(r'^(?P<count>\d+?) .*? (?P<cluster>\d+?)$', data[:-1])
            count = m.group('count')
            cid = m.group('cluster')
        except Exception, e:
            raise CondorSubmitError, "Condor error in submit():\n%s" % e
        return count, cid

    def getStatus(self):
        """
        Returns a list of all available Condor nodes and status by calling the 
        ``condor_status`` command::

            [[vm_full_name1, state1], [vm_full_name2, state2], ...]

        where *stateN* is either *Idle* or *Running*. This function uses Django 
        caching facilities and caches the results for several minutes.
        """
        from django.core.cache import cache
        vms = cache.get('condor_status')
        if vms:
            return vms
        pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, 'condor_status -xml'))
        data = pipe.readlines()
        pipe.close()

        doc = dom.parseString(string.join(data))
        nodes = doc.getElementsByTagName('c')

        vms = []
        cur = 0
        for n in nodes:
            data = n.getElementsByTagName('a')
            for a in data:
                if a.getAttribute('n') == 'Name':
                    name = a.firstChild.firstChild.nodeValue
                    vms.append([str(name), 0])
                elif a.getAttribute('n') == 'Activity':
                    status = a.firstChild.firstChild.nodeValue
                    vms[cur][1] = str(status)
                    cur += 1
        cache.set('condor_status', vms, 60*5) # 5 minutes
        return vms

class YoupiCondorClient(CondorClient):
    """
    .. versionadded:: 0.7.1

    A :class:`~terapix.lib.cluster.condor.CondorClient` version suitable for Youpi, using a 
    :class:`~terapix.lib.cluster.condor.YoupiCondorQueue` as its default job queue. Can be 
    easily used with the :class:`~terapix.youpi.pluginmanager.ApplicationManager`::

        manager = ApplicationManager()
        manager.setClusterClient(YoupiCondorClient()) 

    This way, jobs can be submitted in a generic way::

        manager.cluster.submit(csfPath)

    and live monitoring of a queue is achieved with::

        jobs, jobCount = manager.cluster.queue.getJobs()
    """
    def __init__(self):
        CondorClient.__init__(self)
        self.setQueue(YoupiCondorQueue())

    def submit(self, filepath):
        """
        To be API compatible with existing code, call its super :func:`CondorClient.submit` 
        function then returns a dictionnary  with the *count* and *clusterId* keys.
        """
        count, clusterId = super(YoupiCondorClient, self).submit(filepath)
        return {'count': count, 'clusterId' : clusterId}

