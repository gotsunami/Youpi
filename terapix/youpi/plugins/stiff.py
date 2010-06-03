##############################################################################
#
# Copyright (c) 2008-2010 Terapix Youpi development team. All Rights Reserved.
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

		self.template = 'plugins/stiff.html' 						# Main template, rendered in the processing page
		self.itemCartTemplate = 'plugins/stiff_item_cart.html' 		# Template for custom rendering into the processing cart
		self.jsSource = 'plugins/stiff.js' 							# Custom javascript

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
		try:
			idList = eval(request.POST['IdList'])	# List of lists
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		cluster_ids = []
		error = condorError = '' 
		k = 1

		try:
			for imgList in idList:
				if not len(imgList):
					continue
				csfPath = self.__getCondorSubmissionFile(request, idList)
				pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_submit %s 2>&1" % csfPath))
				data = pipe.readlines()
				pipe.close()
				cluster_ids.append(self.getClusterId(data))
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
		# Rules: 	if taskId has a value, then the config file content is retreived
		# 			from the existing Stiff processing. Otherwise, the config file content
		#			is fetched by name from the ConfigFile objects.
		#
		# 			Selected config file content is finally saved to a regular file.
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

		# Swarp config file
		customrc = self.getConfigurationFilePath()
		strc = open(customrc, 'w')
		strc.write(content)
		strc.close()

		# Condor submission file
		csfPath = condor.CondorCSF.getSubmitFilePath(self.id)
		csf = open(csfPath, 'w')

		# Content of YOUPI_USER_DATA env variable passed to Condor
		# At least those 3 keys
		userData = {'Descr' 			: '',															# Mandatory for Active Monitoring Interface (AMI)
					'Kind'	 			: self.id,														# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 			: str(request.user.id),											# Mandatory for AMI, WP
					'ItemID' 			: itemId, 
					'ResultsOutputDir'	: str(resultsOutputDir)											# Mandatory for WP
				} 

		# Set up default files to delete after processing
		self.setDefaultCleanupFiles(userData)

		#
		# Generate CSF
		#
		cluster = condor.YoupiCondorCSF(request, self.id, desc = self.optionLabel)
		cluster.setTransferInputFiles([customrc, 
			os.path.join(settings.TRUNK, 'terapix', 'lib', 'common.py'),
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
			userData['Descr'] = str("%s of %s" % (self.optionLabel, img.name))		# Mandatory for Active Monitoring Interface (AMI)
			# Mandatory for WP
			userData['JobID'] = self.getUniqueCondorJobId()

			# Base64 encoding + marshal serialization
			# Will be passed as argument 1 to the wrapper script
			try:
				encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
			except ValueError:
				raise ValueError, userData

			image_args = "%(encuserdata)s %(condor_transfer)s /usr/local/bin/qualityFITS -vv" % {
				'encuserdata'		: encUserData, 
				'condor_transfer'	: "%s %s" % (settings.CMD_CONDOR_TRANSFER, settings.CONDOR_TRANSFER_OPTIONS),
			}

			image_args += " -c %s" % os.path.basename(customrc)
			
			# Adding output directory options if the image is from multiple ingestion
			# (same pysical image but different names)
			# the real physical image is used for processing but the results will be contained in a
			# different directory, to prevent confusion between instances
			if userData['RealImageName'] != str(img.name):
				image_args += " -o %s" % os.path.join(img.name, 'qualityFITS')
	
			image_args += " %s" % path

			# Finally, adds Condor queue
			cluster.addQueue(
				queue_args = str(image_args), 
				queue_env = {
					'TPX_CONDOR_UPLOAD_URL'	: settings.FTP_URL + resultsOutputDir, 
					'YOUPI_USER_DATA'		: base64.encodestring(marshal.dumps(userData)).replace('\n', '')
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
