##############################################################################
#
# Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
#                    Mathias Monnerville <monnerville@iap.fr>
#                    Gregory Semah <semah@iap.fr>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
##############################################################################

# vim: set ts=4

from django.conf import settings
from django.http import HttpRequest
import django.http
#
from terapix.lib.cluster import Cluster
from terapix.youpi.models import *
from terapix.exceptions import *
#
import types, time, os.path
import os, string, re
import xml.dom.minidom as dom
import base64, marshal

class CondorError(Exception): pass

class CondorCSF(Cluster):
	"""
	Base class for generating a Condor submission file. This class can be 
	used from the CLI.
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

		@param caption a short word that will be appended to the final file name
		@return Path to a non existing file
		"""
		if type(caption) != types.StringType:
			raise TypeError, caption
		return "%s/CONDOR-%s-%s.csf" % (settings.CONDOR_LOG_DIR, str(caption), time.time())

	@staticmethod
	def getLogFilenames(caption):
		"""
		Returns a dictionnary with entries for the log, error and output filenames 
		that should be used by plugins generating Condor submission files.
		@return Dictionnary with paths to Condor log files
		"""

		if type(caption) != types.StringType:
			raise TypeError, caption
		pattern = os.path.join(settings.CONDOR_LOG_DIR, caption.upper() + '.%s.$(Cluster).$(Process)')

		return {
			'log'	: pattern % "log",
			'error'	: pattern % "err",
			'out'	: pattern % "out",
		}

	def __init__(self, desc = None, **kargs):
		Cluster.__init__(self)

		for attribute in self.attrs:
			self.__dict__[attribute] = ''

		if desc:
			if type(desc) != types.StringType:
				raise TypeError, "desc parameter must be a string"
			self._desc = desc

		self.__dict__['_queues'] = []
		self.data = {}

	def updateData(self):
		"""
		Updates data dictionary to be used when rendering the CSF's content
		"""
		self.data = {
			'description'	: self._desc, 
			'exec'			: self._executable, 
			'transfer'		: self._transfer_input_files,
			'more'			: '',
			'requirements'	: '',
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
		Queues a Condor job, with optional arguments queue_args and queue_env environment.
		@param queue_args string of any argument that must be passed to the executable
		@param queue_env dictionary of variables used to define environment variables
		@return dictionary of data associated with the newly created queue
		"""
		if queue_args and (type(queue_args) != types.StringType):
			raise TypeError, 'queue_args must be a string'

		if queue_env:
			if (type(queue_env) != types.DictType):
				raise TypeError, 'queue_env must be a dictionary'
			for k,v in queue_env.iteritems():
				if type(k) != types.StringType or type(v) != types.StringType:
					raise TypeError, 'Environment arguments keys and values must be strings'

		queue_data = {}
		if queue_args: queue_data['args'] = queue_args
		if queue_env: queue_data['env'] = queue_env
		self._queues.append(queue_data)

		return queue_data

	def removeQueue(self, idx):
		"""
		Remove queue for active Condor queue list
		@param idx index of the queue in the list
		"""
		if type(idx) != types.IntType:
			raise TypeError, "idx must be a positive integer"
		try:
			del self._queues[idx]
		except IndexError:
			raise IndexError, "No queue at position %d to remove. Index out of range" % idx

	def write(self, filename):
		f = open(filename, 'w')
		f.write(self.getSubmissionFileContent())
		f.close()

	def getSubmissionFileContent(self):
		self.updateData()
		return self._csfHeader % self.data

	def setExecutable(self, filename):
		if type(filename) != types.StringType:
			raise TypeError, "Executable must be of type 'string', not %s" % type(filename)
		self._executable = filename

	def setTransferInputFiles(self, files):
		if type(files) != types.ListType:
			raise TypeError, "Must be a list of path to files to transfer"

		for file in files:
			if type(file) != types.StringType:
				raise TypeError, "File '%s' must be of type 'string', not %s" % (file, type(file))

		self._transfer_input_files = ', '.join(files)


class YoupiCondorCSF(CondorCSF):
	"""
	Processing plugins use this class to easily generate a Condor submission file needed for 
	submitting their jobs.
	"""
	def __init__(self, request, pluginId, desc = None):
		CondorCSF.__init__(self, desc)
		if not isinstance(request, HttpRequest):
			raise TypeError, "request must be an HttpRequest object"
		if type(pluginId) != types.StringType:
			raise TypeError, 'pluginId must be a string'

		self.__request = request
		self.__id = pluginId
		self.setExecutable(os.path.join(settings.TRUNK, 'terapix', 'script', 'wrapper_processing.py'))

	@property
	def request(self):
		return self.__request

	@property
	def id(self):
		return self.__id

	def getSubmissionFileContent(self):
		"""
		Fully override parent definition
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
			'requirements'	: self.getRequirementString(),
			'more' : "initialdir = %s\nnotify_user = %s" % (os.path.join(settings.TRUNK, 'terapix', 'script'), settings.CONDOR_NOTIFY_USER)
		})
		self.data.update(self.getLogFilenames(self.__id))

		return self._csfHeader % self.data

	def __repr__(self):
		return "<Youpi Condor Submission File exec: %s desc: %s>" % (self._executable, self._desc)

	def setTransferInputFiles(self, files):
		"""
		Adds Youpi required files such as local_conf.py, settings.py, DBGeneric.py and NOP
		"""
		if type(files) != types.ListType:
			raise TypeError, "Must be a list of path to files to transfer"
		submit_file_path = os.path.join(settings.TRUNK, 'terapix')
		for file in ('local_conf.py', 'settings.py', 'private_conf.py', os.path.join('script', 'DBGeneric.py'), 'NOP'): 
			files.append(os.path.join(submit_file_path, file))

		super(YoupiCondorCSF, self).setTransferInputFiles(files)

	def getRequirementString(self):
		"""
		Realtime and powerful Condor requirement string generation
		"""
		post = self.__request.POST
		try:
			condorSetup = post['CondorSetup']
		except Exception, e:
			raise CondorError, "POST argument error. Unable to process data."

		vms = get_condor_status()

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


def get_condor_status():
	"""
	This function is usefull to get a list of hosts attached to condor (part of the cluster) in real time.
	A list of lists is returned : [[ vm_full_name1, state1], [vm_full_name2, state2]...]

	short_host_name may be one of 'mix3', 'mix4' etc.
	state is one of 'Idle' or 'Running'.

	@return list of cluster nodes (vms)
	"""

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
	return vms

def get_requirement_string(params, vms):
	"""
	Returns Condor's requirement string for a *POLICY*
	For params, allowed criteria are among: MEM, DSK, HST, SLT

	@params string of params like 'MEM,G,1,G'
	@params list vms available cluster nodes
	"""
	if type(params) != types.StringType:
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
		'M'	: 1,
		'G'	: 1024,
		'T'	: 1024 * 1024
	}

	# Check params validity
	params = params.replace('*', '.*')
	params = params.split('#')
	for p in params:
		d = p.split(',')
		if len(d) != 4:
			# Wrong format
			raise ValueError, "Malformed parameter: '%s'" % p
		if d[0] not in ('MEM', 'DSK', 'HST', 'SLT'):
			raise ValueError, "Invalid parameter name: '%s'. Must be one of MEM, DSK, HST or SLT" % d[0]
		if d[1] not in cdeserial:
			raise ValueError, "Invalid comparator letter: '%s'" % d[1]
		if d[3] not in sdeserial:
			raise ValueError, "Invalid unit letter: '%s'" % d[3]

	# vms must be a list of lists
	for vm in vms:
		if type(vm) != types.ListType:
			raise TypeError, "Invalid node info. Should be a list, not '%s'" % vm
		for i in vm:
			if type(i) != types.StringType:
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
	Returns Condor's requirement string for a *SELECTION*
	@param selName - string: name of node selection
	"""
	if type(selName) != types.StringType:
		raise TypeError, 'selName must be a String'

	try:
		sel = CondorNodeSel.objects.filter(label = selName, is_policy = False)[0]
	except IndexError:
		raise CondorError, "No selection named '%s' found" % selName

	hosts = marshal.loads(base64.decodestring(sel.nodeselection))
	req = 'Requirements = (('
	for host in hosts:
		req += """Name == "%s" || """ % host
	req = req[:-3] + '))'

	return req

class CondorQueue(object):
	"""
	Handles a Condor processing queue
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

	class CondorJob(object):
		"""
		Describe a Condor job
		"""
		def __init__(self, classAds):
			"""
			@param classAds dictionary sets class ads names and values for the current Condor job
			Every key/value is stored as a property
			"""
			if type(classAds) != types.DictType:
				raise TypeError, "classAds parameter must be a dictionary"
			self.__dict__['classAds'] = classAds

			for k, v in classAds.iteritems():
				self.__dict__[k] = v

		def __setattr__(self, name, value):
			"""
			Prevents overwritting class Ads properties
			"""
			if self.classAds.has_key(name):
				raise AttributeError, "Can't set attribute (this is a Condor class ad)"
			self.__dict__[name] = value

		def __repr__(self):
			msg = ''
			if self.isRunning(): msg = " on %s since %s" % (self.RemoteHost, self.getJobDuration())
			return "<CondorJob %s.%s is %s%s>" % (self.ClusterId, self.ProcId, self.JobStatusFull.lower(), msg)

		def isRunning(self):
			"""
			Whether the job is running
			"""
			return int(self.JobStatus) == 2

		def getJobDuration(self):
			"""
			Returns the job runtime duration
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
			Remove the job from the Condor queue
			"""
			pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_rm %s.%s"  % (self.ClusterId, self.ProcId)))
			data = pipe.readlines()
			pipe.close()

	@property
	def condor_q_path(self):
		return self.__condor_q_bin

	def __init__(self, envPath = None, globalPool = False):
		"""
		@param envPath Path to the condor_q binary
		@param globalPool Get queues of all the submitters in the Condor system
		"""
		if envPath:
			if type(envPath) != types.StringType:
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
		Returns a tuple with a list of current active Condor jobs and 
		the number of jobs is that list.
		@return Tuple (CondorJob list, jobs count)
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
			jobs.append(self.CondorJob(params))

		return tuple(jobs), len(jobs)

	def removeJob(self, job):
		"""
		Remove a job from the Condor queue.
		@param job CondorJob instance
		"""
		if not isinstance(job, self.CondorJob):
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
