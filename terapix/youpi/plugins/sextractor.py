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

import sys, os.path, re, time, string, re, glob
import marshal, base64, zlib
import xml.dom.minidom as dom
#
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *
from terapix.youpi.models import *
from terapix.youpi.auth import read_proxy
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
		self.optionLabel = 'Sources extractor'
		self.description = 'Sextractor'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SEX'
		self.index = 1

		self.template 			= 'plugins/sextractor.html' 							# Main template, rendered in the processing page
		self.itemCartTemplate 	= 'plugins/sextractor_item_cart.html' 					# Template for custom rendering into the shopping cart
		self.jsSource 			= 'plugins/sextractor.js' 								# Custom javascript
		self.isAstromatic 		= True													# Part of the www.astromatic.net software suite (Scamp, Swarp, Sextractor...)

	def saveCartItem(self, request):
		post = request.POST
		
		try:
			idList					= eval(post['IdList'])
			itemID					= str(post['ItemId'])
			
			flagPath			 	= post['FlagPath']
			weightPath 				= post['WeightPath']
			psfPath 				= post['PsfPath']

			dualMode		 		= int(post['DualMode'])
			dualImage 				= post['DualImage']
			dualWeightPath 			= post['DualWeightPath']
			dualFlagPath		 	= post['DualFlagPath']

			config 					= post['Config']
			param 					= post['Param']
			resultsOutputDir 		= post['ResultsOutputDir']

		except Exception, e:
				raise PluginError, "POST argument error. Unable to process data:  %s" %e

		items = CartItem.objects.filter(kind__name__exact = self.id).order_by('-date')
		if items:
			itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
		else:
			itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' 				: idList,
				 'weightPath' 			: weightPath,
				 'flagPath' 			: flagPath,
				 'psfPath' 				: psfPath,
				 'dualMode' 			: dualMode,
				 'dualImage' 			: dualImage,
				 'dualweightPath' 		: dualWeightPath,
				 'dualflagPath' 		: dualFlagPath,
				 'resultsOutputDir'		: resultsOutputDir, 
				 'config' 				: config,
				 'param' 				: param,
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
						'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username' 			: str(it.user.username),
						'idList' 			: str(data['idList']), 
						'weightPath' 		: str(data['weightPath']), 
						'flagPath' 			: str(data['flagPath']), 
						'psfPath' 			: str(data['psfPath']), 
						'dualMode'			: int(data['dualMode']),
						'itemId' 			: str(it.id), 
						'dualImage'		 	: str(data['dualImage']), 
						'dualweightPath' 	: str(data['dualweightPath']), 
						'dualflagPath' 		: str(data['dualflagPath']), 
						'resultsOutputDir' 	: str(self.getUserResultsOutputDir(request, data['resultsOutputDir'], it.user.username)),
						'name' 				: str(it.name),
						'config' 			: str(data['config']),
						'param' 			: str(data['param']),
						})

		return res 

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
			raise PluginError, "POST argument error. Unable to process data. %s" % e
		
		cluster_ids = []
		k = 1
		error = condorError = '' 
		
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

		stats = {	'TaskSuccessCount' 	: [tasks_success, "%.2f" % (float(tasks_success)/len(tasks)*100)],
					'TaskFailureCount' 	: [tasks_failure, "%.2f" % (float(tasks_failure)/len(tasks)*100)],
					'Total' 			: len(tasks) }

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
			itemId 					= str(post['ItemId'])

			weightPath 				= post['WeightPath']
			flagPath	 			= post['FlagPath']
			psfPath 				= post['PsfPath']

			dualMode 				= post['DualMode']
			dualImage 				= post['DualImage']
			dualFlagPath	 		= post['DualFlagPath']
			dualWeightPath 			= post['DualWeightPath']

			config 					= post['Config']
			param 					= post['Param']
			taskId 					= post.get('TaskId', '')
			resultsOutputDir 		= post['ResultsOutputDir']
			reprocessValid 			= int(post['ReprocessValid'])
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data: %s" % e
		
		#
		# File selection and storage.(for the configuration file and the parameter file)
		#
		# Rules: 	if sexId has a value, then the  file content is retreive
		# 			from the existing Sextractor processing. Otherwise, the  file content
		#			is fetched by name from the File objects in database.
		#
		# 			Selected file content is finally saved to a regular file.
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

		# Sex config file
		customrc = os.path.join('/tmp/', "sex-config-%s.rc" % now)
		sexrc = open(customrc, 'w')
		sexrc.write(contconf)
		sexrc.close()
	
		# Sex param file
		custompc = os.path.join('/tmp/', "sex-param-%s.pc" % now)
		sexpc = open(custompc, 'w')
		sexpc.write(contparam)
		sexpc.close()

		# Condor submission file
		csfPath = condor.Condor.getSubmitFilePath(self.id)
		images = Image.objects.filter(id__in = idList)

		xmlName = self.getConfigValue(contconf.split('\n'), 'XML_NAME')
		xmlRootName = xmlName[:xmlName.rfind('.')]
			
		# Content of YOUPI_USER_DATA env variable passed to Condor
		userData = {'Kind'	 				: self.id,							# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 				: str(request.user.id),				# Mandatory for AMI, WP
					'ItemID' 				: itemId,
					'SubmissionFile'		: csfPath, 
					'ConfigFile' 			: customrc, 
					'ParamFile' 			: custompc, 
					'Descr' 				: '',								# Mandatory for Active Monitoring Interface (AMI) - Will be filled later
					'Weight' 				: str(weightPath), 
					'Flag'	 				: str(flagPath), 
					'Psf'		 			: str(psfPath), 
					'DualMode' 				: int(dualMode),
					'DualImage' 			: str(dualImage),
					'DualWeight' 			: str(dualWeightPath), 
					'DualFlag'	 			: str(dualFlagPath), 
				} 
	
		#Dual Mode check

		if dualMode == '1':
			imgdual = Image.objects.filter(id = dualImage)
			path2 = os.path.join(imgdual[0].path, imgdual[0].name + '.fits')
			userData['DualImage'] =	str(path2)

		step = 0 							# At least step seconds between two job start

		# Generate CSF
		cluster = condor.YoupiCondorCSF(request, self.id, desc = self.optionLabel)
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
			path = os.path.join(img.path, img.name + '.fits')

			# WEIGHT checks
			if weightPath:
				if os.path.isdir(weightPath):
					#then catch the img.name + "_weight.fits"
					weight = os.path.join(weightPath, img.name + '_weight.fits')

				elif os.path.isfile(weightPath):
					weight = weightPath

			# flag checks
			if flagPath:
				if os.path.isdir(flagPath):
					#then catch the img.name + "_weight.fits"
					flag = os.path.join(flagPath, img.name + '_flag.fits')

				elif os.path.isfile(flagPath):
					flag = flagPath

			
			# PSF checks
			if psfPath:
				if os.path.isdir(psfPath):
					#then catch the img.name + "_weight.fits"
					psf = os.path.join(psfPath, img.name + '.psf')

				elif os.path.isfile(psfPath):
					psf = psfPath

			#Dual WEIGHT checks
			if dualWeightPath:
				if os.path.isdir(dualWeightPath):
					#then catch the img.name + "_weight.fits"
					dualWeight = os.path.join(dualWeightPath, img.name + '_weight.fits')

				elif os.path.isfile(dualWeightPath):
					dualWeight = dualWeightPath

			#Dual flag checks
			if dualFlagPath:
				if os.path.isdir(dualFlagPath):
					#then catch the img.name + "_weight.fits"
					dualFlag = os.path.join(dualFlagPath, img.name + '_flag.fits')

				elif os.path.isfile(dualFlagPath):
					dualFlag = dualFlagPath

			#
			# $(Cluster) and $(Process) variables are substituted by Condor at CSF generation time
			# They are later used by the wrapper script to get the name of error log file easily
			#
			userData['ImgID'] = str(img.id)

			if dualMode == '1':
				userData['Descr'] = str("%s of %s (Dual Mode), %s" % (self.optionLabel, img.name, xmlRootName))		# Mandatory for Active Monitoring Interface (AMI)
			else:
				userData['Descr'] = str("%s of %s (Single Mode), %s" % (self.optionLabel, img.name, xmlRootName))		# Mandatory for Active Monitoring Interface (AMI)

			userData['ResultsOutputDir'] = str(os.path.join(resultsOutputDir, img.name))
			# Mandatory for WP
			userData['JobID'] = self.getUniqueCondorJobId()

			# Parameters to use for each job
			try:
				xslPath = re.search(r'file://(.*)$', self.getConfigValue(contconf.split('\n'), 'XSL_URL')).group(1)
				sex_params = "-XSL_URL %s" % (os.path.join(	settings.WWW_SEX_PREFIX, 
															request.user.username, 
															userData['Kind'], 
															userData['ResultsOutputDir'][userData['ResultsOutputDir'].find(userData['Kind'])+len(userData['Kind'])+1:],
															os.path.basename(xslPath)) )
			except TypeError, e:
				# No custom XSL_URL value
				sex_params = ''

			sex_params += " -WRITE_XML YES "

			# Adds weight support 
			if weightPath:
				if not os.path.exists(weight):
					raise PluginError, "the weight file %s doesn't exists" % weight
				else:
					sex_params += "-WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE %s" % weight
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
					sex_params += "-WEIGHT_TYPE NONE, MAP_WEIGHT -WEIGHT_IMAGE NONE, %s" % dualWeight

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
					sex_params += "-FLAG_IMAGE NONE,%s" % dualFlag
				
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
					'encuserdata' 		: encUserData, 
					'condor_transfer'	: "%s %s" % (settings.CMD_CONDOR_TRANSFER, settings.CONDOR_TRANSFER_OPTIONS),
					'sextractor'		: settings.CMD_SEX,
					'images_arg'		: images_arg,
					'params'			: sex_params,
					'config'			: os.path.basename(customrc),
					'param'				: os.path.basename(custompc),
				}),
				queue_env = {
					'USERNAME'				: request.user.username,
					'TPX_CONDOR_UPLOAD_URL'	: settings.FTP_URL + userData['ResultsOutputDir'] + '/',
					'YOUPI_USER_DATA'		: encUserData,
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

		task = Processing_task.objects.filter(id = taskid)[0]
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
			history.append({'User' 			: str(st.user.username),
							'Success' 		: st.success,
							'Start' 		: str(st.start_date),
							'Duration' 		: str(st.end_date-st.start_date),
							'Hostname' 		: str(st.hostname),
							'TaskId'		: str(st.id),
							})

		thumbs = glob.glob(os.path.join(str(task.results_output_dir),'tn_*.png')) 
		if data.thumbnails:
			thumbs = [ thumb for thumb in thumbs]

		return {	'TaskId'				: str(taskid),
					'Title' 				: str("%s" % task.title),
					'User' 					: str(task.user.username),
					'Success' 				: task.success,
					'Start' 				: str(task.start_date),
					'End' 					: str(task.end_date),
					'Duration' 				: str(task.end_date-task.start_date),
					'WWW' 					: str(data.www),
					'ResultsOutputDir' 		: str(task.results_output_dir),
					'ResultsLog'			: sexlog,
					'Config' 				: str(zlib.decompress(base64.decodestring(data.config))),
					'Param' 				: str(zlib.decompress(base64.decodestring(data.param))),
					'Previews'				: thumbs,
					'HasThumbnails'			: data.thumbnails,
					'FITSImages'			: [str(os.path.join(img.path, img.name + '.fits')) for img in imgs],
					'ClusterId'				: str(task.clusterId),
					'History'				: history,
					'Log' 					: err_log,
					'Weight'				: str(data.weightPath),
					'DualWeight'			: str(data.dualweightPath),
					'Flag'					: str(data.flagPath),
					'DualFlag'				: str(data.dualflagPath),
					'Psf'					: str(data.psfPath),
					'DualMode'				: str(data.dualMode),
					'DualImage'				: str(data.dualImage),
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
