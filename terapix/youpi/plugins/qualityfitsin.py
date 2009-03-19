# vim: set ts=4

import sys, os.path, re, time, string, re
import xml.dom.minidom as dom
import marshal, base64, zlib
from types import *
from sets import Set
#
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *
from terapix.youpi.models import *
from terapix.settings import *

class QualityFitsIn(ProcessingPlugin):
	"""
	Plugin for QualityFitsIn.
	
	- First Quality Evaluation.
	- Need FITS images
	- Need FITS Flat
	- Need FITS Mask
	- Need REG File 
	- Produce FITS Weightmap image
	"""

	def __init__(self):
		ProcessingPlugin.__init__(self)

		#
		# REQUIRED members (see doc/writing_plugins/writing_plugins.pdf)
		#
		self.id = 'fitsin'
		self.optionLabel = 'First Quality Evaluation'
		self.description = 'QualityFits-In processing'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'QF'
		self.index = 0

		self.template = 'plugins/qualityfitsin.html' 						# Main template, rendered in the processing page
		self.itemCartTemplate = 'plugins/qualityfitsin_item_cart.html' 		# Template for custom rendering into the shopping cart
		self.jsSource = 'plugins/qualityfitsin.js' 							# Custom javascript

		# Decomment to disable the plugin
		#self.enable = False

	def saveCartItem(self, request):
		"""
		Serialize cart item into DB.
	
		@param request Django HTTP request object
		@return Name of saved item when successful
		"""
		post = request.POST
		try:
			idList = eval(post['IdList'])
			itemID = str(post['ItemID'])
			flatPath = post['FlatPath']
			maskPath = post['MaskPath']
			regPath = post['RegPath']
			config = post['Config']
			taskId = post.get('TaskId', '')
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, ("POST argument error. Unable to process data: %s" % e)

		items = CartItem.objects.filter(kind__name__exact = self.id)
		if items:
			itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
		else:
			itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' : idList, 
				 'flatPath' : flatPath, 
				 'maskPath' : maskPath, 
				 'regPath' : regPath, 
				 'taskId'			: taskId,
				 'resultsOutputDir' : resultsOutputDir, 
				 'config' : config }
		sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		cItem = CartItem(kind = k, name = itemName, user = request.user)
		cItem.data = sdata
		cItem.save()

		return "Item %s saved" % itemName

	def getSavedItems(self, request):
		"""
		Returns a user's saved items. 
		"""

		# per-user items
		items = CartItem.objects.filter(kind__name__exact = self.id, user = request.user).order_by('-date')
		res = []
		for it in items:
			data = marshal.loads(base64.decodestring(str(it.data)))
			res.append({'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username' 			: str(it.user.username),
						'idList' 			: str(data['idList']), 
						'flatPath' 			: str(data['flatPath']), 
						'taskId' 			: str(data['taskId']), 
						'maskPath' 			: str(data['maskPath']), 
						'regPath' 			: str(data['regPath']), 
						'resultsOutputDir' 	: str(data['resultsOutputDir']), 
						'name' 				: str(it.name),
						'config' 			: str(data['config'])})

		return res

	def hasSavedItems(self):
		sItems = CartItem.object.filter(kind__name__exact = self.id)
		return 'mat1!'

	def format(self, data, format):
		try:
			if data:
				return format % data
			else:
				return None
		except TypeError:
			return None

	def getTaskInfo(self, request):
		"""
		Returns information about a finished processing task
		"""
		post = request.POST
		try:
			taskid = post['TaskId']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		task = Processing_task.objects.filter(id = taskid)[0]
		img = Rel_it.objects.filter(task__id = taskid)[0].image
		data = Plugin_fitsin.objects.filter(task__id = taskid)[0]
		# QFits processing history for that image
		qfhistory = Rel_it.objects.filter(image__id = img.id, task__kind__name = self.id).order_by('-id')
		evals = FirstQEval.objects.filter(fitsin__task__id = taskid).order_by('-date')
		gradingCounts = 0
		gradingList = []

		if evals:
			gradingCounts = len(evals)
			for ev in evals:
				gradingList.append([str(ev.user.username), str(ev.grade)])
				
		if task.error_log:
			log = str(zlib.decompress(base64.decodestring(task.error_log)))
		else:
			log = ''

		if data.qflog:
			qflog = str(zlib.decompress(base64.decodestring(data.qflog)))
		else:
			qflog = ''

		history = []
		for h in qfhistory:
			h_fits = Plugin_fitsin.objects.filter(task__id = h.task.id)[0]
			h_evals = FirstQEval.objects.filter(fitsin__task__id = h.task.id).order_by('-date')
			h_gcount = 0
			if h_evals:
				h_gcount = len(h_evals)
			history.append({'User' 			: str(h.task.user.username),
							'Success' 		: h.task.success,
							'Start' 		: str(h.task.start_date),
							'Duration' 		: str(h.task.end_date-h.task.start_date),
							'Hostname' 		: str(h.task.hostname),
							'GradingCount'	: h_gcount,
							'TaskId'		: str(h.task.id),
							'FitsinId'		: str(h_fits.id),
							'Flat' 			: str(h_fits.flat),
							'Mask' 			: str(h_fits.mask),
							'Reg' 			: str(h_fits.reg)
							})

		ImgInfo = [	('Object', img.object),
					('RunId', img.run.name),
					('Filter', img.channel.name),
					('ExpTime', self.format(img.exptime, "%.1f")),
					('Ingestion Date', img.ingestion_date),
					('Air Mass', self.format(img.airmass, "%.3f")),
					('Phot_c (header)', img.photc_header),
					('Phot_c (custom)', img.photc_custom),
					('RA', img.alpha),
					('Dec', img.delta),
					('UTC obs', img.dateobs),
					('Telescope', img.instrument.telescope),
					('Instrument', img.instrument.name)
				]

		
		QFitsInfo = [	('RA offset', data.astoffra, 'arcsec'),
						('Dec offset', data.astoffde, 'arcsec'),
						('RA std dev', data.aststdevra, 'arcsec'),
						('Dec std dev', data.aststdevde, 'arcsec'),
						('Saturation level', self.format(data.satlev, "%9.4f"), 'ADU'),
						('Median background', None, 'ADU'),
						('Min PSF FWHM', self.format(data.psffwhmmin, "%8.3f"), 'arcsec'),
						('Avg PSF FWHM', self.format(data.psffwhm, "%8.3f"), 'arcsec'),
						('Max PSF FWHM', self.format(data.psffwhmmax, "%8.3f"), 'arcsec'),
						('Min PSF half-light diameter', self.format(data.psfhldmin, "8.3f"), 'arcsec'),
						('Avg PSF half-light diameter', self.format(data.psfhld, "8.3f"), 'arcsec'),
						('Max PSF half-light diameter', self.format(data.psfhldmax, "8.3f"), 'arcsec'),
						('Min PSF elongation', self.format(data.psfelmin, "%5.2f"), ''),
						('Avg PSF elongation', self.format(data.psfel, "%5.2f"), ''),
						('Max PSF elongation', self.format(data.psfelmax, "%5.2f"), ''),
						('Min PSF chi2/d.o.f', self.format(data.psfchi2min, "%7.2f"), ''),
						('Avg PSF chi2/d.o.f', self.format(data.psfchi2, "%7.2f"), ''),
						('Max PSF chi2/d.o.f', self.format(data.psfchi2max, "%7.2f"), ''),
						('Min PSF residuals', self.format(data.psfresimin, "%7.2f"), ''),
						('Avg PSF residuals', self.format(data.psfresi, "%7.2f"), ''),
						('Max PSF residuals', self.format(data.psfresimax, "%7.2f"), ''),
						('Min PSF asymmetry', self.format(data.psfasymmin, "%7.2f"), ''),
						('Avg PSF asymmetry', self.format(data.psfasym, "%7.2f"), ''),
						('Max PSF asymmetry', self.format(data.psfasymmax, "%7.2f"), ''),
						('Min number of PSF stars', self.format(data.nstarsmin, "%d"), ''),
						('Avg number of PSF stars', self.format(data.nstars, "%d"), ''),
						('Max number of PSF stars', self.format(data.nstarsmax, "%d"), ''),
						('Previous Release Qfits-in Grade', self.format(data.prevrelgrade, "%s"), ''),
						('Previous Release Qfits-in Comment', self.format(data.prevrelcomment, "%s"), '')
				]

		return {	'TaskId'			: str(taskid),
					'Title' 			: str("%s - %s.fits" % (self.description, img.name)),
					'User' 				: str(task.user.username),
					'Hostname'			: str(task.hostname),
					'Success' 			: task.success,
					'Start' 			: str(task.start_date),
					'End' 				: str(task.end_date),
					'Duration' 			: str(task.end_date-task.start_date),
					'Flat' 				: str(data.flat),
					'Mask' 				: str(data.mask),
					'Reg' 				: str(data.reg),
					'Config' 			: str(zlib.decompress(base64.decodestring(data.qfconfig))),
					'WWW' 				: str(data.www),
					'ImgName' 			: str(img.name),
					'ImgId'				: str(img.id),
					'Log' 				: log,
					'GradingCount' 		: gradingCounts,
					'Grades' 			: gradingList,
					'ImgPath' 			: str(img.path),
					'FitsinId' 			: str(data.id),
					'ImgInfo'			: [[i[0], str(i[1])] for i in ImgInfo],
					'QFitsInfo'			: [[i[0], str(i[1]), str(i[2])] for i in QFitsInfo],
					'ResultsLog'		: qflog,
					'ResultsOutputDir' 	: str(task.results_output_dir),
					'QFitsHistory' 		: history
				}

	
	def getUrlToGradingData(self, request, fitsId):
		data = Plugin_fitsin.objects.filter(id = fitsId)[0]
		return data.www

	def grade(self, request):
		"""
		Saves image's grade into DB
		"""

		post = request.POST
		try:
			grade = post['Grade']
			fitsinId = post['FitsId']
			prCommentId = post['PredefinedCommentId']
			customComment = post['CustomComment']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		f = Plugin_fitsin.objects.filter(id = int(fitsinId))[0]
		c = FirstQComment.objects.filter(id = int(prCommentId))[0]

		try:
			m = FirstQEval(grade = grade, user = request.user, fitsin = f, comment = c, custom_comment = customComment)
			m.save()
		except Exception, e:
			# Updates existing value
			m = FirstQEval.objects.filter(user = request.user, fitsin = f)[0]
			m.grade = grade
			m.comment = c
			m.custom_comment = customComment
			m.date = "%4d-%02d-%02d %02d:%02d:%02d" % time.localtime()[:6]
			m.save()

		return str(grade)

	def __getCondorSubmissionFile(self, request, idList):
		"""
		Generates a suitable Condor submission for processing images on the cluster.

		Note that the fitsinId variable is used to bypass the config variable: it allows to get the 
		configuration file content for an already processed image rather by selecting content by config 
		file name.
		"""

		post = request.POST
		try:
			itemId = str(post['ItemId'])
			flatPath = post['FlatPath']
			maskPath = post['MaskPath']
			taskId = post.get('TaskId', '')
			regPath = post['RegPath']
			config = post['Config']
			resultsOutputDir = post['ResultsOutputDir']
			reprocessValid = int(post['ReprocessValid'])
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		# Builds realtime Condor requirements string
		req = self.getCondorRequirementString(request)

		#
		# Config file selection and storage.
		#
		# Rules: 	if taskId has a value, then the config file content is retreive
		# 			from the existing qfitsin processing. Otherwise, the config file content
		#			is fetched by name from the ConfigFile objects.
		#
		# 			Selected config file content is finally saved to a regular file.
		#
		try:
			if len(taskId):
				config = Plugin_fitsin.objects.filter(task__id = int(taskId))[0]
				content = str(zlib.decompress(base64.decodestring(config.qfconfig)))
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
		customrc = os.path.join('/tmp/', "qf-%s.rc" % now)
		qfrc = open(customrc, 'w')
		qfrc.write(content)
		qfrc.close()

		# Condor submission file
		csfPath = "/tmp/qcondor-%s.txt" % now

		images = Image.objects.filter(id__in = idList)
		# Content of YOUPI_USER_DATA env variable passed to Condor
		userData = {'ItemID' 			: itemId, 
#					'FitsinId' 			: str(fitsinId),
					'Warnings' 			: {}, 
					'SubmissionFile'	: csfPath, 
					'ConfigFile' 		: customrc, 
					'Descr' 			: '',									# Mandatory for Active Monitoring Interface (AMI)
					'Kind'	 			: self.id,								# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 			: str(request.user.id),					# Mandatory for AMI, WP
					'ResultsOutputDir'	: str(resultsOutputDir),				# Mandatory for WP
					'Flat' 				: str(flatPath), 
					'Mask' 				: str(maskPath), 
					'Reg' 				: str(regPath), 
					'Config' 			: str(post['Config'])} 

		step = 2 							# At least step seconds between two job start

		csf = open(csfPath, 'w')

		submit_file_path = os.path.join(TRUNK, 'terapix')

	 	# Generates CSF
		condor_submit_file = """
#
# Condor submission file
# Please not that this file has been generated automatically by Youpi
# http://clix.iap.fr/youpi/
#
executable              = %s/wrapper_processing.py
universe                = vanilla
transfer_executable     = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_input_files    = %s/settings.py, %s/DBGeneric.py, %s, %s/NOP
initialdir				= %s
transfer_output_files   = NOP
log                     = /tmp/QF.log.$(Cluster).$(Process)
error                   = /tmp/QF.err.$(Cluster).$(Process)
output                  = /tmp/QF.out.$(Cluster).$(Process)
notification            = Error
notify_user             = monnerville@iap.fr
# Computed Req string
%s""" % (	os.path.join(submit_file_path, 'script'),
			submit_file_path, 
			os.path.join(submit_file_path, 'script'),
			customrc,
			submit_file_path, 
			os.path.join(submit_file_path, 'script'),
			req )

		csf.write(condor_submit_file)

		# Check if already successful processings
		process_images = []
		for img in images:
			rels = Rel_it.objects.filter(image = img)
			if rels:
				reprocess_image = True
				for r in rels:
					if r.task.success and r.task.kind.name == self.id:
						# Check if same run parameters
						fitsin = Plugin_fitsin.objects.filter(task = r.task)[0]
						conf = str(zlib.decompress(base64.decodestring(fitsin.qfconfig)))
						if 	conf == content or flatPath == fitsin.flat or maskPath == fitsin.mask or \
							regPath == fitsin.reg or resultsOutputDir == r.task.results_output_dir:
							reprocess_image = False

				if reprocess_image or reprocessValid:
					process_images.append(img)
			else:
				process_images.append(img)

		if not process_images:
			raise PluginAllDataAlreadyProcessed

		# One image per job
		for img in process_images:
			path = os.path.join(img.path, img.name + '.fits')
			# FLAT checks
			if os.path.isdir(flatPath):
				if img.flat:
					imgFlat = os.path.join(flatPath, img.flat)
				else:
					imgFlat = None
			elif os.path.isfile(flatPath):
				imgFlat = flatPath
			else:
				# No suitable flat data found
				imgFlat = None

			# MASK checks
			if os.path.isdir(maskPath):
				if img.mask:
					imgMask = os.path.join(maskPath, img.mask)
				else:
					imgMask = None
			elif os.path.isfile(maskPath):
				imgMask = maskPath
			else:
				# No suitable mask data found
				imgMask = None

			# REG file checks
			if os.path.isdir(regPath):
				if img.reg:
					imgReg = os.path.join(regPath, img.reg)
				else:
					imgReg = None
			elif os.path.isfile(regPath):
					imgReg = regPath
			else:
				# No suitable reg file found
				imgReg = None

			#
			# $(Cluster) and $(Process) variables are substituted by Condor at CSF generation time
			# They are later used by the wrapper script to get the name of error log file easily
			#
			userData['ImgID'] = str(img.id)
			userData['Descr'] = str("%s of %s" % (self.optionLabel, img.name))		# Mandatory for Active Monitoring Interface (AMI)
			#
			# Delaying job startup will prevent "Too many connections" MySQL errors
			# and will decrease the load of the node that will receive all qualityFITS data
			# results (PROCESSING_OUTPUT) back. Every job queued will be put to sleep StartupDelay 
			# seconds
			#
			userData['StartupDelay'] = step

			# Base64 encoding + marshal serialization
			# Will be passed as argument 1 to the wrapper script
			try:
				encUserData = base64.encodestring(marshal.dumps(userData)).replace('\n', '')
			except ValueError:
				raise ValueError, userData

			condor_submit_img_entries = """
arguments                = %s /usr/local/bin/condor_transfert.pl /usr/local/bin/qualityFITS -vv""" % encUserData

			userData['Warnings'] = {}
			userData['Warnings'][str(img.name) + '.fits'] = []
			if imgFlat:
				condor_submit_img_entries += " -F %s" % imgFlat
			else:
				userData['Warnings'][str(img.name) + '.fits'].append('No suitable flat data found')

			if imgMask:
				condor_submit_img_entries += " -M %s" % imgMask
			else:
				userData['Warnings'][str(img.name) + '.fits'].append('No suitable mask data found')

			if imgReg:
				condor_submit_img_entries += " -P %s" % imgReg
			else:
				userData['Warnings'][str(img.name) + '.fits'].append('No suitable reg file found')

			if not len(userData['Warnings'][str(img.name) + '.fits']):
				del userData['Warnings'][str(img.name) + '.fits']

			condor_submit_img_entries += """ -c %s %s""" % (os.path.basename(customrc), path)

			# Add per-job custom environment variable
			condor_submit_img_entries += """
# YOUPI_USER_DATA = %s
environment             = TPX_CONDOR_UPLOAD_URL=%s; PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin; YOUPI_USER_DATA=%s""" %  (	userData, 
																															FTP_URL + resultsOutputDir,
																															base64.encodestring(marshal.dumps(userData)).replace('\n', '') ) 

			condor_submit_img_entries += "\nqueue"
			csf.write(condor_submit_img_entries)


		csf.close()

		return csfPath

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
		k = 1
		error = condorError = info = '' 

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
		except PluginAllDataAlreadyProcessed:
				info = 'This item has already been fully processed. Nothing to do.'
		except Exception, e:
				error = "Error while processing list #%d: %s" % (k, e)

		return {'ClusterIds': cluster_ids, 'NoData': info, 'Error': error, 'CondorError': condorError}

	def getRuns(self, request):
		# Return a list of lists [run name, image count]
		return [[str(r.name), int(Image.objects.filter(run__name = r.name).count())] for r in Run.objects.all()]

	def getReprocessingParams(self, request):
		"""
		Returns all information for reprocessing an image (so that it can be added to the shopping cart).
		Information needed: related image ID, flat, mask and reg data path, resultsOutputDir
		"""

		try:
			taskId = request.POST['TaskId']
		except KeyError, e:
			raise PluginError, 'Bad parameters'

		data = Plugin_fitsin.objects.filter(task__id = int(taskId))[0]
		img = Rel_it.objects.filter(task = data.task)[0].image

		return {'ImageId' 			: int(img.id), 
				'Flat' 				: str(data.flat),
				'Mask' 				: str(data.mask),
				'Reg' 				: str(data.reg),
				'ResultsOutputDir' 	: str(data.task.results_output_dir) }

	def getTaskLog(self, request):
		"""
		Returns task error log.
		"""

		try:
			taskId = request.POST['TaskId']
		except KeyError, e:
			raise PluginError, 'Bad parameters'

		task = Processing_task.objects.filter(id = int(taskId))[0]
		img = Rel_it.objects.filter(task = task)[0].image.name

		return {'ImgName' : str(img), 'Log' : str(zlib.decompress(base64.decodestring(task.error_log)))}

	def getOutputDirStats(self, outputDir):
		"""
		Return some qftsin-related statistics about processings from outputDir.
		"""

		headers = ['Different images processed', 'Image success', 'Image failures', 'Task success', 'Task failures', 'Total processings']
		cols = []
		tasks = Processing_task.objects.filter(results_output_dir = outputDir)
		tasks_success = tasks_failure = 0
		for t in tasks:
			if t.success == 1:
				tasks_success += 1
			else:
				tasks_failure += 1

		rels = Rel_it.objects.filter(task__in = tasks)
		distinct_imgs = [r.image for r in rels]
		distinct_imgs = list(Set(distinct_imgs))

		success_imgs = []
		failure_imgs = []
		for img in distinct_imgs:
			img_rels = Rel_it.objects.filter(image = img)
			for r in img_rels:
				if r.task.success == 1:
					success_imgs.append(img)
				else:
					failure_imgs.append(img)

		success_imgs = list(Set(success_imgs))
		failure_imgs = list(Set(failure_imgs))
		# now remove successes from failures
		ff = []
		i = 0
		for f in failure_imgs:
			if f not in success_imgs:
				ff.append(f)
			i += 1

		failure_imgs = ff
		img_rels = Rel_it.objects.filter(image__in = failure_imgs)
		taskList = []
		z = []
		# Only take first task
		for r in img_rels:
			if r.task.results_output_dir == outputDir and r.image.id not in z:
				z.append(r.image.id)
				taskList.append([int(r.task.id), str(r.image.name)])

		stats = {	'Distinct' 			: len(distinct_imgs),
					'ImageSuccessCount'	: [len(success_imgs), "%.2f" % (float(len(success_imgs))/len(distinct_imgs)*100)],
					'ImageFailureCount'	: [len(failure_imgs), "%.2f" % (float(len(failure_imgs))/len(distinct_imgs)*100)],
					'TaskSuccessCount' 	: [tasks_success, "%.2f" % (float(tasks_success)/len(tasks)*100)],
					'TaskFailureCount' 	: [tasks_failure, "%.2f" % (float(tasks_failure)/len(tasks)*100)],
					'ReprocessTaskList' : [t[0] for t in taskList],
					'ImagesTasks'		: taskList,
					'Total' 			: len(tasks) }

		return stats

	def reprocessAllFailedProcessings(self, request):
		"""
		Returns parameters to allow reprocessing of failed processings
		"""

		try:
			# taskList is already a list of failed processings
			tasksList = request.POST['TasksList'].split(',')
		except KeyError, e:
			raise PluginError, 'Bad parameters'

		tasks = Processing_task.objects.filter(id__in = tasksList)
		imgs = Rel_it.objects.filter(task__in = tasks)
		imgList = [[int(img.image.id) for img in imgs]]
		fitsin = Plugin_fitsin.objects.filter(task__in = tasks)[0]

		processings = {	'ResultsOutputDir' 	: str(tasks[0].results_output_dir), 
						'ImgList' 			: str(imgList),
						'Count'				: len(imgList),
						'Flat' 				: str(fitsin.flat),
						'Mask' 				: str(fitsin.mask),
						'Reg' 				: str(fitsin.reg),
						'FitsinId' 			: int(fitsin.id) }

		return { 'Processings' : [processings] }

	def jobStatus(self, request):
		"""
		Parses XML output from Condor and returns a JSON object.
		Only Youpi's related job are monitored. A Youpi job must have 
		an environment variable named YOUPI_USER_DATA which can contain
		serialized base64-encoded data to be parsed.

		nextPage: id of the page of 'limit' results to display
		"""

		try:
			nextPage = int(request.POST['NextPage'])
		except KeyError, e:
			raise PluginError, 'Bad parameters'

		pipe = os.popen("/opt/condor/bin/condor_q -xml")
		data = pipe.readlines()
		pipe.close()

		res = []
		# Max jobs per page
		limit = 10

		# Removes first 3 lines (not XML)
		doc = dom.parseString(string.join(data[3:]))
		jNode = doc.getElementsByTagName('c')

		# Youpi Condor job count
		jobCount = 0

		for job in jNode:
			jobData = {}
			data = job.getElementsByTagName('a')

			for a in data:
				if a.getAttribute('n') == 'ClusterId':
					jobData['ClusterId'] = str(a.firstChild.firstChild.nodeValue)

				elif a.getAttribute('n') == 'ProcId':
					jobData['ProcId'] = str(a.firstChild.firstChild.nodeValue)

				elif a.getAttribute('n') == 'JobStatus':
					# 2: running, 1: pending
					jobData['JobStatus'] = str(a.firstChild.firstChild.nodeValue)

				elif a.getAttribute('n') == 'RemoteHost':
					jobData['RemoteHost'] = str(a.firstChild.firstChild.nodeValue)

				elif a.getAttribute('n') == 'Args':
					fitsFile = str(a.firstChild.firstChild.nodeValue)
					jobData['FitsFile'] = fitsFile.split('/')[-1]
				
				elif a.getAttribute('n') == 'JobStartDate':
					secs = (time.time() - int(a.firstChild.firstChild.nodeValue))
					h = m = 0
					s = int(secs)
					if s > 60:
						m = s/60
						s = s%60
						if m > 60:
							h = m/60
							m = m%60
	
					jobData['JobDuration'] = "%02d:%02d:%02d" % (h, m, s)

				elif a.getAttribute('n') == 'Env':
					# Try to look for YOUPI_USER_DATA environment variable
					# If this is variable is found then this is a Youpi's job so we can keep it
					env = str(a.firstChild.firstChild.nodeValue)
					if env.find('YOUPI_USER_DATA') >= 0:
						m = re.search('YOUPI_USER_DATA=(.*?)$', env)
						userData = m.groups(0)[0]	
						c = userData.find(';')
						if c > 0:
							userData = userData[:c]
						jobData['UserData'] = marshal.loads(base64.decodestring(str(userData)))

						if jobData['UserData'].has_key('Kind'):
							if jobData['UserData']['Kind'] == self.id:
								res.append(jobData)
								jobCount += 1

		# Computes total pages
		pageCount = 1
		if jobCount  > limit:
			pageCount = jobCount / limit
			if jobCount % limit > 0:
				pageCount += 1
	
		# Selects res subset according to NextPage and limit
		if nextPage > pageCount:
			nextPage = pageCount
		res = res[(nextPage-1)*limit:limit*nextPage]

		return [res, jobCount, pageCount, nextPage]

	def cancelJob(self, request):
		"""
		Cancel a Job. POST arg used are clusterId and procId
		"""

		post = request.POST
		cluster = str(post['ClusterId'])
		proc = str(post['ProcId'])

		pipe = os.popen("/opt/condor/bin/condor_rm %s.%s" % (cluster, proc))
		data = pipe.readlines()
		pipe.close()

		return 'Job cancelled'

#	def getResultEntryDescription(self, task):
#		"""
#		Returns custom result entry description for a task.
#		task: django object
#
#		returned value: HTML tags allowed
#		"""
#
#		img = Rel_it.objects.filter(task = task)[0].image
#		return "%s of image <b>%s</b>" % (self.optionLabel, img.name)

	def getResultEntryDescription(self, data):
		"""
		returned value: HTML tags allowed
		"""

		return "%s of image <b>%s</b>" % (self.optionLabel, data['imgName'])
