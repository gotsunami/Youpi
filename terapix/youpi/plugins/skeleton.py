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

#
# Mandatory data members
#
# def __getCondorSubmissionFile(self, request)		: generates a suitable Condor submission file
# def getResultEntryDescription(self, task)			: returns custom result entry description for a task.
# def getSavedItems(self, request)					: returns a user's saved items for this plugin 
# def getTaskInfo(self, request)					: returns information about a finished processing task. Used on the results page.
# def process(self, request)						: generates and submits a Condor submission file (CSF)
# def reprocessAllFailedProcessings(self, request)	: returns parameters to allow reprocessing of failed processings
# def saveCartItem(self, request)					: save cart item's custom data to DB
#

import sys, os.path, re, time, string
import marshal, base64, zlib
#
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *
from terapix.youpi.models import *
from terapix.youpi.auth import read_proxy
import terapix.lib.cluster.condor as condor
#
from django.conf import settings

class Skeleton(ProcessingPlugin):
	"""
	This plugin does nothing but can serve as a base for writing processing plugins
	"""
	def __init__(self):
		ProcessingPlugin.__init__(self)

		self.id = 'skel'
		self.optionLabel = 'Skeleton (DEMO)'
		self.description = 'Skeleton DEMO processing'
		# Item prefix in processing cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SKEL'
		self.index = 65535

		self.template = 'plugins/skeleton.html' 						# Main template, rendered in the processing page
		self.itemCartTemplate = 'plugins/skeleton_item_cart.html' 		# Template for custom rendering into the processing cart
		self.jsSource = 'plugins/skeleton.js' 							# Custom javascript

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
		post = request.POST

		cluster_ids = []
		error = condorError = '' 

		try:
			csfPath = self.__getCondorSubmissionFile(request)
			pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_submit %s 2>&1" % csfPath))
			data = pipe.readlines()
			pipe.close()
			cluster_ids.append(self.getClusterId(data))
		except CondorSubmitError, e:
			condorError = str(e)
		except Exception, e:
			error = "Error while processing item: %s" % e

		return {'ClusterIds': cluster_ids, 'Error': error, 'CondorError': condorError}

	def __getCondorSubmissionFile(self, request):
		"""
		Generates a suitable Condor submission file for processing self.command jobs on the cluster.
		"""

		post = request.POST
		try:
			#
			# Retreive your POST data here
			#
			resultsOutputDir = post['ResultsOutputDir']
			itemId = str(post['ItemId'])
		except Exception, e:
				raise PluginError, "POST argument error. Unable to process data: %s" % e

		now = time.time()
		# Condor submission file
		csfPath = condor.CondorCSF.getSubmitFilePath(self.id)
		csf = open(csfPath, 'w')

		# Content of YOUPI_USER_DATA env variable passed to Condor
		# At least those 3 keys
		userData = {'Descr' 			: str("%s trying %s" % (self.optionLabel, self.command)),		# Mandatory for Active Monitoring Interface (AMI)
					'Kind'	 			: self.id,														# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 			: str(request.user.id),											# Mandatory for AMI, WP
					'ItemID' 			: itemId, 
					'ResultsOutputDir'	: str(resultsOutputDir)											# Mandatory for WP
				} 

		#
		# Generate CSF
		#
		cluster = condor.YoupiCondorCSF(request, self.id, desc = self.optionLabel)

		# Real command to perform here
		args = ''
		for x in range(self.jobCount):
			# Mandatory for WP
			userData['JobID'] = self.getUniqueCondorJobId()
			encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
			cluster.addQueue(
				queue_args = str("%(data)s %(command)s" % {'data': encUserData, 'command': self.command,}),
				queue_env = {'YOUPI_USER_DATA': encUserData,}
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

		# Error log content
		if task.error_log:
			err_log = str(zlib.decompress(base64.decodestring(task.error_log)))
		else:
			err_log = ''

		return {	'TaskId'	: str(taskid),
					'Title' 	: str("%s" % self.description),
					'User' 		: str(task.user.username),
					'Success' 	: task.success,
					'ClusterId'	: str(task.clusterId),
					'Start' 	: str(task.start_date),
					'End' 		: str(task.end_date),
					'Duration' 	: str(task.end_date-task.start_date),
					'Log' 		: err_log
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
			itemID = str(post['ItemId'])
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		items = CartItem.objects.filter(kind__name__exact = self.id).order_by('-date')
		if items:
			itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
		else:
			itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'Descr' : "Runs %d %s commands on the cluster" % (self.jobCount, self.command),
				 'resultsOutputDir' : resultsOutputDir }
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
		items, filtered = read_proxy(request, CartItem.objects.filter(kind__name__exact = self.id).order_by('-date'))
		res = []
		for it in items:
			data = marshal.loads(base64.decodestring(str(it.data)))
			res.append({'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username'			: str(it.user.username),
						'descr' 			: str(data['Descr']),
						'itemId' 			: str(it.id), 
						'resultsOutputDir' 	: str(self.getUserResultsOutputDir(request)),
						'name' 				: str(it.name) })
		return res
