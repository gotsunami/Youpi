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

import os, sys, os.path, re, time, string
import marshal, base64, zlib
from stat import *
#
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *
from terapix.youpi.models import *
from terapix.settings import *
from terapix.youpi.auth import read_proxy
#
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render_to_response 
from django.template import RequestContext

class Swarp(ProcessingPlugin):
	"""
	Plugin for Swarp
	"""
	def __init__(self):
		ProcessingPlugin.__init__(self)

		self.id = 'swarp'
		self.optionLabel = 'Image stacking'
		self.description = 'Resampling and coaddition'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SWARP'
		self.index = 50

		self.template = 'plugins/swarp.html' 						# Main template, rendered in the processing page
		self.itemCartTemplate = 'plugins/swarp_item_cart.html' 		# Template for custom rendering into the shopping cart
		self.jsSource = 'plugins/swarp.js' 							# Custom javascript
		self.isAstromatic = True									# Part of the www.astromatic.net software suite (Scamp, Swarp, Sextractor...)

		# Decomment to disable the plugin
		#self.enable = False

	def process(self, request):
		"""
		Do the job.
		1. Generates a condor submission file
		2. Executes condor_submit on that file
		3. Returns info related to ClusterId and number of jobs submitted
		"""

		try:
			idList = eval(request.POST['IdList'])	# List of lists
			headDataPaths = request.POST['HeadDataPaths'].split(',')
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data: %s" % e

		cluster_ids = []
		k = 0
		error = condorError = '' 

		try:
			for imgList in idList:
				if not len(imgList):
					continue
				csfPath = self.__getCondorSubmissionFile(request, imgList, headDataPaths[k])
				pipe = os.popen(os.path.join(CONDOR_BIN_PATH, "condor_submit %s 2>&1" % csfPath)) 
				data = pipe.readlines()
				pipe.close()
				cluster_ids.append(self.getClusterId(data))
				k += 1
		except CondorSubmitError, e:
				condorError = str(e)
		except Exception, e:
				error = "Error while processing list #%d: %s" % (k+1, e)

		return {'ClusterIds': cluster_ids, 'Error': error, 'CondorError': condorError}

	def getOutputDirStats(self, outputDir):
		"""
		Return some skeleton-related statistics about processings from outputDir.
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

	def __getCondorSubmissionFile(self, request, idList, headDataPath):
		"""
		Generates a suitable Condor submission for processing images on the cluster.

		Note that the taskId variable is used to bypass the config variable: it allows to get the 
		configuration file content for an already processed image rather by selecting content by config 
		file name.

		headDataPath is a path to (possibly an empty string) .head files to use with current image 
		selection.
		"""

		post = request.POST
		try:
			itemId = str(post['ItemId'])
			weightPath = post['WeightPath']
			config = post['Config']
			taskId = post.get('TaskId', '')
			resultsOutputDir = post['ResultsOutputDir']
			reprocessValid = int(post['ReprocessValid'])
			useQFITSWeights = int(post['UseQFITSWeights'])
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data: %s" % e

		# Builds realtime Condor requirements string
		req = self.getCondorRequirementString(request)

		#
		# Config file selection and storage.
		#
		# Rules: 	if taskId has a value, then the config file content is retreive
		# 			from the existing Swarp processing. Otherwise, the config file content
		#			is fetched by name from the ConfigFile objects.
		#
		# 			Selected config file content is finally saved to a regular file.
		#
		try:
			if len(taskId):
				config = Plugin_swarp.objects.filter(task__id = int(taskId))[0]
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

		# At least step seconds between two job start
		step = 0 							

		# Swarp config file
		customrc = self.getConfigurationFilePath()
		swrc = open(customrc, 'w')
		swrc.write(content)
		swrc.close()

		# Condor submission file
		csfPath = self.getCondorSubmitFilePath()
		csf = open(csfPath, 'w')

		# Swarp file containing a list of images to process (one per line)
		images = Image.objects.filter(id__in = idList)
		swarpImgsFile = os.path.join('/tmp/', "swarp-imglist-%s.rc" % time.time())
		imgPaths = [img.name + '.fits' for img in images]
		swif = open(swarpImgsFile, 'w')
		swif.write(string.join(imgPaths, '\n'))
		swif.close()

		xmlName = self.getConfigValue(content.split('\n'), 'XML_NAME')
		xmlRootName = xmlName[:xmlName.rfind('.')]

		# Content of YOUPI_USER_DATA env variable passed to Condor
		userData = {'Kind'	 			: self.id,						# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 			: str(request.user.id),			# Mandatory for AMI, WP
					'ResultsOutputDir'	: str(resultsOutputDir),		# Mandatory for WP
					'ItemID' 			: itemId,
					'SubmissionFile'	: csfPath, 
					'ConfigFile' 		: customrc, 
					'WeightPath'		: str(weightPath), 
					'UseQFITSWeights'	: int(useQFITSWeights),
					'HeadPath'			: 'No .head files used',		# Default value
					'UseHeadFiles'		: 0,							# Default value
					'Descr'				: "%s of %d FITS images, %s" % (self.optionLabel, len(images), str(xmlRootName)),	# Mandatory for AMI
					'JobID' 			: self.getUniqueCondorJobId(),
					'StartupDelay'		: step,
		} 

		#
		# Write userdata.conf which olds the remaining information needed by the wrapper processing script
		# This file must only holds a serialized Python dictionary which will be merged by the WP script with 
		# the userData dictionary passed as its first argument
		#
		bigUserData = {'ImgID': idList}
		userdataFile = "%s-userdata-%s.conf" % (self.id, time.time())
		userData['BigUserData'] = userdataFile # Pass the name to the WP script
		udf = open(os.path.join('/tmp/', userdataFile), 'w')
		udf.write(base64.encodestring(marshal.dumps(bigUserData)).replace('\n', ''))
		udf.close()

		submit_file_path = os.path.join(TRUNK, 'terapix')

		# Get filenames for Condor log files (log, error, out)
		logs = self.getCondorLogFilenames()

		# Weight maps support
		if useQFITSWeights:
			weight_files = self.getWeightPathsFromImageSelection(request, idList)
			weight_files = string.join([dat[1] for dat in weight_files], ', ')
		else:
			weight_files = string.join([os.path.join(weigthPath, img.name + '_weight.fits.fz') for img in images], ', ')

		# .head files support
		head_files = os.path.join(submit_file_path, 'NOP')
		if len(headDataPath):
			head_files = string.join([os.path.join(headDataPath, img.name + '.head') for img in images], ', ')
			userData['HeadPath'] =  str(headDataPath)
			userData['UseHeadFiles'] =  1

		# List of all input files to be transferred (for -l option of condor_transfer.pl)
		transferFile = "swarp-transfer-%s.rc" % time.time()
		tf = open(os.path.join('/tmp/', transferFile), 'w')
		tf.write(weight_files.replace(', ', '\n'))			# Weights	
		tf.write('\n' + head_files.replace(', ', '\n'))		# Heads
		tf.write('\n' + string.join([os.path.join(img.path, img.name + '.fits') for img in images], '\n')) # Images
		tf.close()

		#
		# Pre-processing script runned by condor_transfert.pl
		# This is mandatory in order to be able to uncompress the weight maps
		# preProcFile is filled later
		#
		preProcFile = os.path.join('/tmp/', "swarp-preprocessing-%s.py" % time.time())
		
	 	# Generates CSF
		condor_submit_file = """
#
# Condor submission file
# Please not that this file has been generated automatically by Youpi
# http://clix.iap.fr/youpi/
#

# Plugin: %(description)s

executable              = %(wrapper)s/wrapper_processing.py
universe                = vanilla
transfer_executable     = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_input_files    = %(settings)s/settings.py, %(dbgeneric)s/DBGeneric.py, %(config)s, %(userdata)s, %(swarplist)s, %(transferfile)s, %(preprocfile)s, %(nop)s/NOP
initialdir				= %(initdir)s
transfer_output_files   = NOP
log                     = %(log)s
error                   = %(errlog)s
output                  = %(outlog)s
notification            = Error
notify_user             = monnerville@iap.fr
# Computed Req string
%(requirements)s
""" % {	
	'description'	: self.description,
	'wrapper' 		: os.path.join(submit_file_path, 'script'),
	'settings' 		: submit_file_path, 
	'dbgeneric' 	: os.path.join(submit_file_path, 'script'),
	'config' 		: customrc,
	'swarplist' 	: swarpImgsFile,
	'nop' 			: submit_file_path, 
	'initdir' 		: os.path.join(submit_file_path, 'script'),
	'requirements' 	: req,
	'log'			: logs['log'],
	'errlog'		: logs['error'],
	'outlog'		: logs['out'],
	'transferfile'  : os.path.join('/tmp/', transferFile),
	'userdata'		: os.path.join('/tmp/', userdataFile),
	'preprocfile'	: preProcFile,
}

		csf.write(condor_submit_file)

		# Base64 encoding + marshal serialization
		# Will be passed as argument 1 to the wrapper script
		try:
			encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
		except ValueError:
			raise ValueError, userData

		xslPath = re.search(r'file://(.*)$', self.getConfigValue(content.split('\n'), 'XSL_URL')).group(1)
		swarp_params = "-XSL_URL %s" % os.path.join(WWW_SWARP_PREFIX, 
													request.user.username, 
													userData['Kind'], 
													userData['ResultsOutputDir'][userData['ResultsOutputDir'].find(userData['Kind'])+len(userData['Kind'])+1:],
													os.path.basename(xslPath)
										)

		# Now generates the preprocessing Python script needed to be able 
		# to uncompress all .fz weight maps
		pf = open(preProcFile, 'w')
		pcontent = """#!/usr/bin/env python

# AUTOMATICALLY GENERATED SCRIPT. DO NOT EDIT

import os, glob, sys

# PRE-PROCESSING stuff go there
fzs = glob.glob('*.fits.fz')
for fz in fzs:
	print "SWARP PREPROCESSING: uncompressing", fz
	os.system(" """[:-1] + CMD_IMCOPY + """ %s %s" % (fz, fz[:-3]))

# Finally run swarp
"""
		pcontent += """
exit_code = os.system("%(swarp)s %(params)s @%(imgsfile)s -c %(config)s 2>&1")
sys.exit(exit_code)
""" % {
	'swarp'			: CMD_SWARP,
	'params'		: swarp_params,
	'imgsfile'		: os.path.basename(swarpImgsFile),
	'config'		: os.path.basename(customrc),
}
		pf.write(pcontent)
		pf.close()
		RWX_ALL = S_IRWXU | S_IRWXG | S_IRWXO 
		os.chmod(preProcFile, RWX_ALL)

		condor_submit_entry = """
arguments               = %(encuserdata)s /usr/local/bin/condor_transfert.pl -l %(transferfile)s -- ./%(preprocscript)s
# YOUPI_USER_DATA = %(userdata)s
environment             = USERNAME=%(user)s; TPX_CONDOR_UPLOAD_URL=%(tpxupload)s; PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin:/opt/condor/bin; YOUPI_USER_DATA=%(encuserdata)s
queue""" %  {	'encuserdata' 	: encUserData, 
				'swarp'			: CMD_SWARP,
				'params'		: swarp_params,
				'config'		: os.path.basename(customrc),
				'userdata'		: userData, 
				'transferfile'  : transferFile,
				'user'			: request.user.username,
				'imgsfile'		: os.path.basename(swarpImgsFile),
				'preprocscript'	: os.path.basename(preProcFile),
				'tpxupload'		: FTP_URL + resultsOutputDir }

		csf.write(condor_submit_entry)
		csf.close()

		return csfPath

	def checkForQFITSData(self, request, imgList = None):
		"""
		Check if every image in this selection has been successfully processed with QFits-in.
		Policy: only the lastest successful qfits-in of current logged-in user is looked for.

		@return Dictionnary {'missingQFITS' : list of images names without QFTSin data, 'tasksIds' : list of matching tasks}
		"""

		post = request.POST
		if imgList:
			idList = imgList
		else:
			try:
				idList = request.POST['IdList'].split(',')
			except Exception, e:
				raise PluginError, "POST argument error. Unable to process data."

		tasksIds = []
		missing = []
		imgList = Image.objects.filter(id__in = idList)
		curTask = None

		for img in imgList:
			rels = Rel_it.objects.filter(image = img)
			if not rels:
				missing.extend([str(os.path.join(img.path, img.name + '.fits'))])
				continue

			relTaskIds = [rel.task.id for rel in rels]

			# Valid task is only the lastest successful qfits-in of current logged-in user
			tasks = Processing_task.objects.filter(	id__in = relTaskIds, 
													kind__name__exact = 'fitsin',
													success = True).order_by('-end_date')

			if not tasks:
				missing.append(str(os.path.join(img.path, img.name + '.fits')))
				continue

			tasksIds.append(int(tasks[0].id))

		return {'missingQFITS' : missing, 'tasksIds' : tasksIds}

	def checkForScampData(self, request, imgList = None):
		"""
		Check if the image selection matches a successful Scamp involving the same image selection.
		@return List of Scamp processings, if any
		"""

		post = request.POST
		if imgList:
			idList = imgList
		else:
			try:
				idList = request.POST['IdList'].split(',')
			except Exception, e:
				raise PluginError, "POST argument error. Unable to process data."

		from django.db import connection
		cur = connection.cursor()

		idList = string.join(idList, ',')
		mTasks = []
		cur.execute("""
		SELECT r.task_id, COUNT(r.image_id) FROM youpi_rel_it AS r, youpi_processing_task AS t, youpi_processing_kind AS k 
		WHERE r.task_id=t.id 
		AND t.kind_id=k.id
		AND k.name='scamp'
		AND r.image_id IN (%s)
		GROUP BY r.task_id 
		ORDER BY t.start_date desc
		""" % idList)
		res = cur.fetchall()

		if res:
			for r in res:
				mTasks.append(Processing_task.objects.filter(id = r[0])[0])
		else:
			return {'Warning': 'no scamp processing found matching that image selection. Will not use .head files for that selection.'}

		return {'Tasks' : [[str(t.id), str(t.start_date), str(t.end_date), str(t.hostname), str(t.results_output_dir)] for t in mTasks]}

	def getWeightPathsFromImageSelection(self, request, imgList = None):
		"""
		Compute data path of weight images for a given image selection
		@return List of paths to WEIGHT files
		"""

		post = request.POST
		try:
			idList = request.POST['IdList'].split(',')
			checks = self.checkForQFITSData(request)
		except Exception, e:
			if imgList:
				idList = imgList
				checks = self.checkForQFITSData(request, idList)
			else:
				raise PluginError, "POST argument error. Unable to process data."

		weight_files = []
		tasks = Processing_task.objects.filter(id__in = checks['tasksIds'])

		for task in tasks:
			img = Rel_it.objects.filter(task = task)[0].image
			weight_files.append([int(img.id), str(os.path.join(task.results_output_dir, img.name, 'qualityFITS', img.name + 
				'_weight.fits.fz'))])

		return weight_files

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
		data = Plugin_swarp.objects.filter(task__id = taskid)[0]

		# Error log content
		if task.error_log:
			err_log = str(zlib.decompress(base64.decodestring(task.error_log)))
		else:
			err_log = ''

		if data.log:
			swarplog = str(zlib.decompress(base64.decodestring(data.log)))
		else:
			swarplog = ''

		# Get related images
		rels = Rel_it.objects.filter(task__id = taskid)
		imgs = [r.image for r in rels]

		# Computes total exposure time
		totalExpTime = 0
		for img in imgs:
			totalExpTime += img.exptime

		# Looks for groups of swarp
		swarpHistory = Rel_it.objects.filter(image__in = imgs, task__kind__name = self.id).order_by('task')
		# Finds distinct tasks
		tasksRelated = []
		for sh in swarpHistory:
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

		thumbs = ['swarp.png']
		if data.thumbnails:
			thumbs = ['tn_' + thumb for thumb in thumbs]

		config = zlib.decompress(base64.decodestring(data.config))

		return {	'TaskId'			: str(taskid),
					'Title' 			: str("%s" % task.title),
					'User' 				: str(task.user.username),
					'Success' 			: task.success,
					'Start' 			: str(task.start_date),
					'End' 				: str(task.end_date),
					'TotalExposureTime'	: str(round(totalExpTime, 2)),
					'Duration' 			: str(task.end_date-task.start_date),
					'WWW' 				: str(data.www),
					'Index' 			: str(self.getConfigValue(config.split('\n'), 'XML_NAME')),
					'ResultsOutputDir' 	: str(task.results_output_dir),
					'ResultsLog'		: swarplog,
					'Config' 			: str(config),
					'Previews'			: thumbs,
					'ClusterId'			: str(task.clusterId),
					'HasThumbnails'		: data.thumbnails,
					'FITSImages'		: [str(os.path.join(img.path, img.name + '.fits')) for img in imgs],
					'History'			: history,
					'Log' 				: err_log,
					'WeightPath'		: str(data.weightPath),
					'UseQFITSWeights'	: int(data.useQFITSWeights),
					'HeadPath'			: str(data.headPath),
					'UseHeadFiles'		: int(data.useHeadFiles),
		}

	def getReprocessingParams(self, request):
		"""
		Returns all information for reprocessing a stack (so that it can be added to the shopping cart).
		"""

		try:
			taskId = request.POST['TaskId']
		except KeyError, e:
			raise PluginError, 'Bad parameters'

		data = Plugin_swarp.objects.filter(task__id = int(taskId))[0]
		rels = Rel_it.objects.filter(task__id = int(taskId))
		# Must be a list of list
		idList = [[int(r.image.id) for r in rels]]

		return {
				'resultsOutputDir' 	: str(self.getUserResultsOutputDir(request, data.task.results_output_dir, data.task.user.username)),
				'useQFITSWeights'	: str(data.useQFITSWeights),
				'idList'			: str(idList), 
				'weightPath'		: str(data.weightPath), 
				'headDataPaths'		: str(data.headPath),
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
		Save cart item custom data to DB
		"""

		post = request.POST
		try:
			idList = eval(post['IdList'])
			itemID = str(post['ItemId'])
			weightPath = post['WeightPath']
			config = post['Config']
			taskId = post.get('TaskId', '')
			resultsOutputDir = post['ResultsOutputDir']
			useQFITSWeights = int(post['UseQFITSWeights'])
			headDataPaths = post['HeadDataPaths'].split(',')
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data: %s" % e

		items = CartItem.objects.filter(kind__name__exact = self.id).order_by('-name')
		if items:
			itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
		else:
			itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' 			: idList, 
				 'weightPath' 		: weightPath, 
				 'resultsOutputDir' : resultsOutputDir, 
				 'useQFITSWeights' 	: useQFITSWeights,
				 'headDataPaths' 	: headDataPaths,
				 'taskId'			: taskId,
				 'config' 			: config }

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
		Returns a user's saved items for this plugin 
		"""
		# per-user items
		items, filtered = read_proxy(request, CartItem.objects.filter(kind__name__exact = self.id).order_by('-date'))
		res = []
		for it in items:
			data = marshal.loads(base64.decodestring(str(it.data)))
			res.append({'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username'			: str(it.user.username),
						'idList' 			: str(data['idList']), 
						'taskId' 			: str(data['taskId']), 
						'itemId' 			: str(it.id), 
						'weightPath' 		: str(data['weightPath']), 
						'resultsOutputDir' 	: str(self.getUserResultsOutputDir(request, data['resultsOutputDir'], it.user.username)),
				 		'useQFITSWeights' 	: str(data['useQFITSWeights']),
						'name' 				: str(it.name),
						'headDataPaths'		: string.join([str(p) for p in data['headDataPaths']], ','),
						'config' 			: str(data['config'])})

		return res

	def reports(self):
		"""
		Adds reporting capabilities to Swarp plugin
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
