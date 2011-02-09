# vim: set ts=4

import os, sys, os.path, re, time, string
import marshal, base64, zlib
from stat import *
import cjson as json
#
import terapix.lib.cluster.condor as condor
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

class Swarp(ProcessingPlugin):
	"""
	Plugin for Swarp
	"""
	def __init__(self):
		ProcessingPlugin.__init__(self)

		self.id = 'swarp'
		self.optionLabel = 'Swarp'
		self.description = 'Image stacking'
		# Item prefix in processing cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SWARP'
		self.index = 50

		self.template = 'plugins/swarp.html' 						# Main template, rendered in the processing page
		self.itemCartTemplate = 'plugins/swarp_item_cart.html' 		# Template for custom rendering into the processing cart
		self.jsSource = 'plugins/swarp.js' 							# Custom javascript
		self.isAstromatic = True									# Part of the www.astromatic.net software suite (Scamp, Swarp, Sextractor...)

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
		error = condorError = info = '' 

		try:
			for imgList in idList:
				if not len(imgList):
					continue
				csfPath = self.__getCondorSubmissionFile(request, imgList, headDataPaths[k])
				pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_submit %s 2>&1" % csfPath)) 
				data = pipe.readlines()
				pipe.close()
				cluster_ids.append(self.getClusterId(data))
				k += 1
		except CondorSubmitError, e:
				condorError = str(e)
		except PluginAllDataAlreadyProcessed:
				info = 'This item has already been fully processed. Nothing to do.'
		except Exception, e:
				error = "Error while processing list #%d: %s" % (k+1, e)

		return {'ClusterIds': cluster_ids, 'NoData': info, 'Error': error, 'CondorError': condorError}

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
			headPath = post['HeadPath']
			config = post['Config']
			taskId = post.get('TaskId', '')
			resultsOutputDir = post['ResultsOutputDir']
			reprocessValid = int(post['ReprocessValid'])
			useAutoQFITSWeights = int(post['UseAutoQFITSWeights'])
			useAutoScampHeads = int(post['UseAutoScampHeads'])
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data: %s" % e

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

		images = Image.objects.filter(id__in = idList)
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
					swarp = Plugin_swarp.objects.get(task = task)
					conf = str(zlib.decompress(base64.decodestring(swarp.config)))
					if  conf == content and headPath == swarp.headPath and weightPath == swarp.weightPath:
						skip_processing = True
						break

			if skip_processing:
				raise PluginAllDataAlreadyProcessed

		# At least step seconds between two job start
		step = 0 							

		# Condor submission file
		cluster = condor.YoupiCondorCSF(request, self.id, desc = self.optionLabel)
		csfPath = cluster.getSubmitFilePath()
		tmpDir = os.path.dirname(csfPath)

		# Swarp config file
		customrc = cluster.getConfigFilePath()
		swrc = open(customrc, 'w')
		swrc.write(content)
		swrc.close()

		# Swarp file containing a list of images to process (one per line)
		swarpImgsFile = os.path.join(tmpDir, "swarp-imglist-%s.rc" % time.time())
		imgPaths = [img.filename + '.fits' for img in images]
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
					'HeadPath'			: str(headPath),
					'UseAutoQFITSWeights'	: int(useAutoQFITSWeights),
					'UseAutoScampHeads'		: int(useAutoScampHeads),
					'Descr'				: "%s of %d FITS images, %s" % (self.optionLabel, len(images), str(xmlRootName)),	# Mandatory for AMI
					'JobID' 			: self.getUniqueCondorJobId(),
					'StartupDelay'		: step,
		} 

		# Set up default files to delete after processing
		self.setDefaultCleanupFiles(userData)

		#
		# Write userdata.conf which olds the remaining information needed by the wrapper processing script
		# This file must only holds a serialized Python dictionary which will be merged by the WP script with 
		# the userData dictionary passed as its first argument
		#
		bigUserData = {'ImgID': idList}
		userdataFile = "%s-userdata-%s.conf" % (self.id, time.time())
		userData['BigUserData'] = userdataFile # Pass the name to the WP script
		udf = open(os.path.join(tmpDir, userdataFile), 'w')
		udf.write(base64.encodestring(marshal.dumps(bigUserData)).replace('\n', ''))
		udf.close()

		submit_file_path = os.path.join(settings.TRUNK, 'terapix')

		# Weight maps support
		if useAutoQFITSWeights:
			weight_files = self.getWeightPathsFromImageSelection(request, idList)
			weight_files = string.join([dat[1] for dat in weight_files], ', ')
		else:
			weight_files = string.join([os.path.join(weightPath, img.filename + '_weight.fits') for img in images], ', ')

		# .head files support
		head_files = os.path.join(submit_file_path, 'NOP')
		if useAutoScampHeads:
			if len(headDataPath):
				head_files = string.join([os.path.join(headDataPath, img.filename + '.head') for img in images], ', ')
				userData['HeadPath'] =  str(headDataPath)
		else:
			# Custom path to Scamp head files provided
			head_files = string.join([os.path.join(headPath, img.filename + '.head') for img in images], ', ')
			userData['HeadPath'] =  str(headPath)

		# List of all input files to be transferred (for -l option of condor_transfer.pl)
		transferFile = "swarp-transfer-%s.rc" % time.time()
		tf = open(os.path.join(tmpDir, transferFile), 'w')
		tf.write('\n' + head_files.replace(', ', '\n'))		# Heads
		tf.write('\n' + string.join([os.path.join(img.path, img.filename + '.fits') for img in images], '\n')) # Images
		tf.close()

		#
		# Pre-processing script runned by condor_transfer.pl
		# This is mandatory in order to be able to uncompress the weight maps
		# preProcFile is filled later
		#
		preProcFile = os.path.join(tmpDir, "swarp-preprocessing-%s.py" % time.time())

		# Base64 encoding + marshal serialization
		# Will be passed as argument 1 to the wrapper script
		try:
			encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
		except ValueError:
			raise ValueError, userData

		swarp_params = ''
		try:
			url = self.getConfigValue(content.split('\n'), 'XSL_URL')
			xslPath = re.search(r'file://(.*)$', url)
			if xslPath:
				# This is a local (or NFS) path, Youpi will serve it
				swarp_params = "-XSL_URL %s" % os.path.join(
					get_static_url(userData['ResultsOutputDir']),
					request.user.username, 
					userData['Kind'], 
					userData['ResultsOutputDir'][userData['ResultsOutputDir'].find(userData['Kind'])+len(userData['Kind'])+1:],
					os.path.basename(xslPath.group(1))
				)
			else:
				# Copy attribute as is
				if url: swarp_params = "-XSL_URL " + url
		except TypeError, e:
			pass
		except AttributeError, e:
			pass

		# Now generates the preprocessing Python script needed to be able 
		# to uncompress all fz/gzip weight maps
		pf = open(preProcFile, 'w')
		tmplf = open(os.path.join(settings.TRUNK, 'terapix', 'youpi', 'plugins', 'swarp-preprocessing.tmpl'))
		tmpl = string.Template(''.join(tmplf.readlines()))
		tmplf.close()
		pf.write(tmpl.substitute({
			'swarp'			: settings.CMD_SWARP,
			'params'		: swarp_params,
			'imgsfile'		: os.path.basename(swarpImgsFile),
			'config'		: os.path.basename(customrc),
			'weight_files'	: weight_files.split(', '),
		}))
		pf.close()
		RWX_ALL = S_IRWXU | S_IRWXG | S_IRWXO 
		os.chmod(preProcFile, RWX_ALL)

		#
		# Generate CSF
		#
		cluster.setTransferInputFiles([
			os.path.join(submit_file_path, 'script', 'stack_ingestion.py'),
			customrc,
			os.path.join(tmpDir, userdataFile),
			swarpImgsFile,
			os.path.join(tmpDir, transferFile),
			preProcFile,
		])
		cluster.addQueue(
			queue_args = str("%(encuserdata)s %(condor_transfer)s -l %(transferfile)s -- ./%(preprocscript)s" % {
				'encuserdata' 		: encUserData, 
				'condor_transfer'	: "%s %s" % (settings.CMD_CONDOR_TRANSFER, settings.CONDOR_TRANSFER_OPTIONS),
				'transferfile'  	: transferFile,
				'preprocscript'		: os.path.basename(preProcFile),
			}),
			queue_env = {
				'USERNAME'				: request.user.username,
				'TPX_CONDOR_UPLOAD_URL'	: get_tpx_condor_upload_url(resultsOutputDir), 
				'YOUPI_USER_DATA'		: encUserData,
			}
		)
		cluster.write(csfPath)

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
				missing.extend([str(os.path.join(img.path, img.filename + '.fits'))])
				continue

			relTaskIds = [rel.task.id for rel in rels]

			# Valid task is only the latest successful qfits-in of current logged-in user
			tasks = Processing_task.objects.filter(	id__in = relTaskIds, 
													kind__name__exact = 'fitsin',
													success = True).order_by('-end_date')

			if not tasks:
				missing.append(str(os.path.join(img.path, img.filename + '.fits')))
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

		try:
			idList = string.join(idList, ',')
		except TypeError:
			idList = ','.join([str(id) for id in idList])
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
	
			# Same as qualityfits.py img.name image database name is used, to distinguish 
			# multiple instance of the same image in database, but we use the real image filename
			# to get real weight filename on disks
			weight_files.append([int(img.id), str(os.path.join(task.results_output_dir, img.name, 'qualityFITS', img.filename + 
				'_weight.fits'))])

		return weight_files

	def autoProcessSelection(self, request):
		"""
		Looks for mandatory data for being able to process an image selection with Swarp 
		automatically. Checks are performed in the following order:
		1. Gets the list of images for that selection
		2. Looks for a config file with the name of this selections and use it if found. If not, uses 
		   the default config file for the job. Emits a warning.
		3. Handles WeightPath variable:
		    AUTO: checks for QFits data (looks for weight maps for every image). Emits a warning for 
			      missing weight maps
			CUSTOM PATH: don't check for weight maps at all
		4. Handles HeadPath variable:
		    AUTO: checks for Scamp data. If there are more that 1 scamp for that selection of images, takes
			      the latest one (emits a warning).
			CUSTOM PATH: don't check for Scamp .head files at all
		@return a dictionary
		"""

		post = request.POST
		try:
			selName = request.POST['SelName']
			weightPath = request.POST['WeightPath']
			headPath = request.POST['HeadPath']
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

		# 3. Handles weight path
		if weightPath == 'AUTO':
			useAutoQFITSWeights = 1
			qfdata = self.checkForQFITSData(request, idList)
		else:
			useAutoQFITSWeights = 0
			qfdata = None

		# 4. Handles head path
		if headPath == 'AUTO':
			useAutoScampHeads = 1
			scampdata = self.checkForScampData(request, idList)
			if scampdata.has_key('Tasks'):
				# Keep the latest Scamp only
				scampdata = {'Tasks': scampdata['Tasks'][0]}
				headDataPath = scampdata['Tasks'][4]
			else:
				# Has warnings
				warnings.append(scampdata['Warning'])
				del scampdata['Warning']
				headDataPath = '' # Empty data path
		else:
			scampdata = None
			useAutoScampHeads = 0
			headDataPath = headPath

		# The following result set will be used on the client side to add an item in 
		# the processing cart
		res = {
			'selName'				: selName,
			'weightPath'			: weightPath,
			'headPath'				: headPath,
			'idList'				: str([[int(id) for id in idList]]), # Must be a list of one list of integers (not long)
			'config'				: config,
			'warning'				: warnings,
			'qfitsdata'				: qfdata,
			'scampdata'				: scampdata,
			'useAutoQFITSWeights'	: useAutoQFITSWeights,
			'useAutoScampHeads'		: useAutoScampHeads,
			'headDataPaths'			: headDataPath, 
			'imgCount'				: len(idList),
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
					'Hostname'			: str(task.hostname),
					'Success' 			: task.success,
					'Start' 			: str(task.start_date),
					'End' 				: str(task.end_date),
					'TotalExposureTime'	: str(round(totalExpTime, 2)),
					'Duration' 			: str(task.end_date-task.start_date),
					'WWW' 				: str(data.www),
					'Index' 			: str(self.getConfigValue(config.split('\n'), 'XML_NAME')),
					'StackName'			: str(self.getConfigValue(config.split('\n'), 'IMAGEOUT_NAME')),
					'ResultsOutputDir' 	: str(task.results_output_dir),
					'ResultsLog'		: swarplog,
					'Config' 			: str(config),
					'Previews'			: thumbs,
					'ClusterId'			: str(task.clusterId),
					'HasThumbnails'		: data.thumbnails,
					'FITSImages'		: [str(os.path.join(img.path, img.filename + '.fits')) for img in imgs],
					'History'			: history,
					'Log' 				: err_log,
					'WeightPath'		: str(data.weightPath),
					'HeadPath'			: str(data.headPath),
					'UseAutoQFITSWeights'	: data.useAutoQFITSWeights,
					'UseAutoScampHeads'		: data.useAutoScampHeads,
					'HeadPath'			: str(data.headPath),
		}

	def getReprocessingParams(self, request):
		"""
		Returns all information for reprocessing a stack (so that it can be added to the processing cart).
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
				'useAutoQFITSWeights'	: str(data.useAutoQFITSWeights),
				'useAutoScampHeads'		: str(data.useAutoScampHeads),
				'idList'			: str(idList), 
				'weightPath'		: str(data.weightPath), 
				'headPath'			: str(data.headPath), 
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
			headPath = post['HeadPath']
			config = post['Config']
			taskId = post.get('TaskId', '')
			resultsOutputDir = post['ResultsOutputDir']
			useAutoQFITSWeights = int(post['UseAutoQFITSWeights'])
			useAutoScampHeads = int(post['UseAutoScampHeads'])
			headDataPaths = post['HeadDataPaths'].split(',')
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data: %s" % e

		items = CartItem.objects.filter(kind__name__exact = self.id).order_by('-date')
		if items:
			itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
		else:
			itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' 			: idList, 
				 'weightPath' 		: weightPath, 
				 'headPath' 		: headPath, 
				 'resultsOutputDir' : resultsOutputDir, 
				 'useAutoQFITSWeights' 	: useAutoQFITSWeights,
				 'useAutoScampHeads' 	: useAutoScampHeads,
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
			# Set default values for items without this information
			if not data.has_key('headPath'):
				data['headPath'] = 'AUTO'
			if not data.has_key('useAutoScampHeads'):
				data['useAutoScampHeads'] = 1
			if not data.has_key('useAutoQFITSWeights'):
				data['useAutoQFITSWeights'] = 1
			res.append({'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username'			: str(it.user.username),
						'idList' 			: str(data['idList']), 
						'taskId' 			: str(data['taskId']), 
						'itemId' 			: str(it.id), 
						'weightPath' 		: str(data['weightPath']), 
						'headPath' 			: str(data['headPath']), 
						'resultsOutputDir' 	: str(self.getUserResultsOutputDir(request, data['resultsOutputDir'], it.user.username)),
				 		'useAutoQFITSWeights' 	: str(data['useAutoQFITSWeights']),
				 		'useAutoScampHeads' 	: str(data['useAutoScampHeads']),
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
