# vim: set ts=4

import sys, os.path, re, time, string
import marshal, base64, zlib
from pluginmanager import ProcessingPlugin, PluginError, CondorSubmitError
from terapix.youpi.models import *
#
from terapix.settings import *

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

		# Decomment to disable the plugin
		#self.enable = False

	def process(self, request):
		"""
		Do the job.
		1. Generates a condor submission file
		2. Executes condor_submit on that file
		3. Returns info related to ClusterId and number of jobs submitted
		"""

		# FIXME
		#return {'Error': 'Plugin not yet implemented.'}

		try:
			idList = eval(request.POST['IdList'])	# List of lists
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		cluster_ids = []
		k = 1
		error = condorError = '' 

		try:
			for imgList in idList:
				if not len(imgList):
					continue
				csfPath = self.__getCondorSubmissionFile(request, imgList)
				pipe = os.popen("/opt/condor/bin/condor_submit %s 2>&1" % csfPath) 
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

	def __getCondorSubmissionFile(self, request, idList):
		"""
		Generates a suitable Condor submission for processing images on the cluster.

		Note that the swarpId variable is used to bypass the config variable: it allows to get the 
		configuration file content for an already processed image rather by selecting content by config 
		file name.
		"""

		post = request.POST
		try:
			itemId = str(post['ItemId'])
			weightPath = post['WeightPath']
			config = post['Config']
			swarpId = post['SwarpId']
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
		# Rules: 	if swarpId has a value, then the config file content is retreive
		# 			from the existing Swarp processing. Otherwise, the config file content
		#			is fetched by name from the ConfigFile objects.
		#
		# 			Selected config file content is finally saved to a regular file.
		#
		try:
			if len(swarpId):
				config = Plugin_swarp.objects.filter(id = int(swarpId))[0]
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
		customrc = os.path.join('/tmp/', "swarp-config-%s.rc" % now)
		swrc = open(customrc, 'w')
		swrc.write(content)
		swrc.close()

		# Condor submission file
		csfPath = "/tmp/swarp-condor-%s.txt" % now
		csf = open(csfPath, 'w')

		# Swarp file containing a list of images to process (one per line)
		images = Image.objects.filter(id__in = idList)
		swarpImgsFile = os.path.join('/tmp/', "swarp-imglist-%s.rc" % now)
		imgPaths = [img.name + '.fits' for img in images]
		swif = open(swarpImgsFile, 'w')
		swif.write(string.join(imgPaths, '\n'))
		swif.close()

		# Content of YOUPI_USER_DATA env variable passed to Condor
		userData = {'Kind'	 			: self.id,							# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 			: str(request.user.id),				# Mandatory for AMI, WP
					'ItemID' 			: itemId,
					'SubmissionFile'	: csfPath, 
					'ConfigFile' 		: customrc, 
					'Weight' 			: str(weightPath), 
					'Descr' 			: '',								# Mandatory for Active Monitoring Interface (AMI) - Will be filled later
					'ResultsOutputDir'	: str(resultsOutputDir)				# Mandatory for WP
		} 

		step = 0 							# At least step seconds between two job start

		submit_file_path = os.path.join(TRUNK, 'terapix')

		if useQFITSWeights:
			weight_files = self.getWeightPathsFromImageSelection(request, idList)
			weight_files = string.join([dat[1] for dat in weight_files], ', ')
		else:
			weight_files = string.join([os.path.join(weigthPath, img.name + '_weight.fits.fz') for img in images], ', ')

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
transfer_input_files    = %(weights)s, %(images)s, %(settings)s/settings.py, %(dbgeneric)s/DBGeneric.py, %(config)s, %(swarplist)s, %(nop)s/NOP
initialdir				= %(initdir)s
transfer_output_files   = NOP
log                     = /tmp/SWARP.log.$(Cluster).$(Process)
error                   = /tmp/SWARP.err.$(Cluster).$(Process)
output                  = /tmp/SWARP.out.$(Cluster).$(Process)
notification            = Error
notify_user             = monnerville@iap.fr
# Computed Req string
%(requirements)s
""" % {	'description'	: self.description,
		'wrapper' 		: os.path.join(submit_file_path, 'script'),
		'settings' 		: submit_file_path, 
		'dbgeneric' 	: os.path.join(submit_file_path, 'script'),
		'config' 		: customrc,
		'swarplist' 	: swarpImgsFile,
		'nop' 			: submit_file_path, 
		'weights'		: weight_files,
		'images'		: string.join([os.path.join(img.path, img.name + '.fits') for img in images], ', '),
		'initdir' 		: os.path.join(submit_file_path, 'script'),
		'requirements' 	: req }

		csf.write(condor_submit_file)

		userData['ImgID'] = idList
		userData['Descr'] = str("%s of %d FITS images" % (self.optionLabel, len(images)))		# Mandatory for Active Monitoring Interface (AMI)

		#
		# Delaying job startup will prevent "Too many connections" MySQL errors
		# and will decrease the load of the node that will receive all qualityFITS data
		# results (PROCESSING_OUTPUT) back. Every job queued will be put to sleep StartupDelay 
		# seconds
		#
		userData['StartupDelay'] = step
		userData['Warnings'] = {}

		# Base64 encoding + marshal serialization
		# Will be passed as argument 1 to the wrapper script
		try:
			encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
		except ValueError:
			raise ValueError, userData

		swarp_params = "-XSL_URL %sswarp.xsl" % os.path.join(	WWW_SWARP_PREFIX, 
																request.user.username, 
																userData['Kind'], 
																userData['ResultsOutputDir'][userData['ResultsOutputDir'].find(userData['Kind'])+len(userData['Kind'])+1:] )


		condor_submit_entry = """
arguments               = %(encuserdata)s /usr/local/bin/condor_transfert.pl /usr/bin/swarp %(params)s @%(imgsfile)s -c %(config)s 2>/dev/null
# YOUPI_USER_DATA = %(userdata)s
environment             = USERNAME=%(user)s; TPX_CONDOR_UPLOAD_URL=%(tpxupload)s; PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin; YOUPI_USER_DATA=%(encuserdata)s
queue""" %  {	'encuserdata' 	: encUserData, 
				'params'		: swarp_params,
				'config'		: os.path.basename(customrc),
				'userdata'		: userData, 
				'user'			: request.user.username,
				'imgsfile'		: os.path.basename(swarpImgsFile),
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
													user = request.user, 
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

		tasksIds = []
		missing = []
		imgList = Image.objects.filter(id__in = idList)

		tasks = Processing_task.objects.filter(	user = request.user, 
												kind__name__exact = 'scamp',
												success = True).order_by('-end_date')
		mTasks = []
		for t in tasks:
			rels = Rel_it.objects.filter(task = t, image__in = imgList)
			if not rels or len(rels) != len(imgList):
				return {'Warning': 'no scamp processing found matching that image selection. Will not use .head files for that selection.'}
			else:
				mTasks.append(t)

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

		return {	'TaskId'			: str(taskid),
					'Title' 			: str("%s" % self.description),
					'User' 				: str(task.user.username),
					'Success' 			: task.success,
					'Start' 			: str(task.start_date),
					'End' 				: str(task.end_date),
					'TotalExposureTime'	: str(round(totalExpTime, 2)),
					'Duration' 			: str(task.end_date-task.start_date),
					'WWW' 				: str(data.www),
					'ResultsOutputDir' 	: str(task.results_output_dir),
					'ResultsLog'		: swarplog,
					'Config' 			: str(zlib.decompress(base64.decodestring(data.config))),
					'Previews'			: thumbs,
					'HasThumbnails'		: data.thumbnails,
					'FITSImages'		: [str(os.path.join(img.path, img.name + '.fits')) for img in imgs],
					'History'			: history,
					'Log' 				: err_log,
					'Weight'			: str(data.weight),
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
			itemID = str(post['ItemID'])
			weightPath = post['WeightPath']
			config = post['Config']
			resultsOutputDir = post['ResultsOutputDir']
			useQFITSWeights = int(post['UseQFITSWeights'])
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data: %s" % e

		items = CartItem.objects.filter(kind__name__exact = self.id)
		itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' : idList, 
				 'weightPath' : weightPath, 
				 'resultsOutputDir' : resultsOutputDir, 
				 'useQFITSWeights' : useQFITSWeights,
				 'config' : config }

		sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		cItem = CartItem(kind = k, name = itemName, user = request.user)
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
		items = CartItem.objects.filter(kind__name__exact = self.id, user = request.user).order_by('-date')
		res = []
		for it in items:
			data = marshal.loads(base64.decodestring(str(it.data)))
			res.append({'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username'			: str(it.user.username),
						'idList' 			: str(data['idList']), 
						'weightPath' 		: str(data['weightPath']), 
						'resultsOutputDir' 	: str(data['resultsOutputDir']), 
				 		'useQFITSWeights' 	: str(data['useQFITSWeights']),
						'name' 				: str(it.name),
						'config' 			: str(data['config'])})

		return res
