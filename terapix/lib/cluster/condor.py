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

class Condor(Cluster):
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
# Computed Req string
%(requirements)s
"""
	attrs = ['_executable', '_desc', '_transfer_input_files']

	@staticmethod
	def getSubmitFilePath(caption):
		"""
		Returns the path to Condor submit file path.
		Each call generates a new filename so that no file gets overwritten.
		The returned name should then be used by plugins to add some content to it.
		@param caption a short word that will be appended to the final file name
		@return Path to a non existing file
		"""
		return "%s/CONDOR-%s-%s.csf" % (settings.CONDOR_LOG_DIR, str(caption), time.time())

	@staticmethod
	def getLogFilenames(caption):
		"""
		Returns a dictionnary with entries for the log, error and output filenames 
		that should be used by plugins generating Condor submission files.
		@return Dictionnary with paths to Condor log files
		"""

		pattern = os.path.join(settings.CONDOR_LOG_DIR, str(caption).upper() + '.%s.$(Cluster).$(Process)')

		return {
			'log'	: pattern % "log",
			'error'	: pattern % "err",
			'out'	: pattern % "out",
		}

	def __init__(self, desc = None, **kargs):
		Cluster.__init__(self)

		for attribute in self.attrs:
			self.__dict__[attribute] = None

		if desc:
			self._desc = str(desc)

	def updateData(self):
		self.data = {
			'description'	: self._desc, 
			'exec'			: self._executable, 
			'transfer'		: self._transfer_input_files,
			'requirements'	: self.getRequirementString(),
		}
		self.data.update(self.getLogFilenames(self.id))

	def __str__(self):
		self.updateData()
		return self._csfHeader % data

	def __repr__(self):
		return "<Condor Submission File exec: %s desc: %s>" % (self._executable, self._desc)

	def write(self, filename):
		pass

	def getSubmissionFileContent(self):
		return "%s" % self

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


class YoupiCondor(Condor):
	def __init__(self, request, pluginId, desc = None):
		Condor.__init__(self, desc)
		self.request = request
		self.id = pluginId

	def getSubmissionFileContent(self):
		if not self._transfer_input_files:
			# Add at least required files
			self.setTransferInputFiles([])
		self.updateData()
		self.data.update({
			'more' : "initialdir = %s\nnotify_user = %s" % (os.path.join(settings.TRUNK, 'terapix', 'script'), settings.CONDOR_NOTIFY_USER)
		})
		return self._csfHeader % self.data

	def __repr__(self):
		return "<Youpi Condor Submission File exec: %s desc: %s>" % (self._executable, self._desc)

	def setTransferInputFiles(self, files):
		"""
		Adds Youpi required files such as local_conf.py, settings.py, DBGeneric.py and NOP
		"""
		submit_file_path = os.path.join(settings.TRUNK, 'terapix')
		for file in ('local_conf.py', 'settings.py', os.path.join('script', 'DBGeneric.py'), 'NOP'): 
			files.append(os.path.join(submit_file_path, file))

		super(YoupiCondor, self).setTransferInputFiles(files)

	def getRequirementString(self):
		"""
		Realtime and powerful Condor requirement string generation
		"""
		post = self.request.POST
		try:
			condorSetup = post['CondorSetup']
		except Exception, e:
			raise CondorError, "POST argument error. Unable to process data."

		vms = get_condor_status()

		if condorSetup == 'default':
			dflt_setup = marshal.loads(base64.decodestring(self.request.user.get_profile().dflt_condor_setup))
			# Check Behaviour: policy or selection
			if not dflt_setup.has_key(self.id):
				raise CondorError, "No default Condor setup found for '%s' plugin." % self.optionLabel

			db = dflt_setup[self.id]['DB']
			if db == 'policy':
				pol = CondorNodeSel.objects.filter(label = dflt_setup[self.id]['DP'], is_policy = True)[0]
				req = get_requirement_string(pol.nodeselection, vms)
			else:
				# Default behaviour is 'selection'
				req = get_requirement_string_from_selection(dflt_setup[self.id]['DS'])

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
		custom_req = self.request.user.get_profile().custom_condor_req
		if custom_req: req = "%s && (%s))" % (req[:-1], custom_req)

		return req


def get_condor_status():
	"""
	This function is usefull to get a list of hosts attached to condor (part of the cluster) in real time.
	A list of lists is returned : [[ vm_full_name1, state1], [vm_full_name2, state2]...]

	short_host_name may be one of 'mix3', 'mix4' etc.
	state is one of 'Idle' or 'Running'.
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
	"""

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

	# Sanitize
	params = params.replace('*', '.*')
	params = params.split('#')
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

