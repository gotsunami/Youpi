# vim: set ts=4

import sys, os.path, time, string
import xml.dom.minidom as dom
import marshal, base64, zlib
from types import *
from pluginmanager import ProcessingPlugin, PluginError, CondorSubmitError
from terapix.youpi.models import *
#
from terapix.settings import *

class Scamp(ProcessingPlugin):
	"""	
	Class: Scamp
	Plugin for Scamp.
	
	Astro-Photo Calibration.
	- Needs "ldac" catalogs from Sextractor
	- Computes astrometric/Photometric solution from FITS images sequence
	"""	
	def __init__(self):
		ProcessingPlugin.__init__(self)

		self.id = 'scamp'
		self.optionLabel = 'Astro-Photo calibration'
		self.description = 'Scamp'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SCAMP'
		self.index = 20

		# Main template, rendered in the processing page
		self.template = 'plugin_scamp.html'
		# Template for custom rendering into the shopping cart
		self.itemCartTemplate = 'plugin_scamp_item_cart.html'
		# Custom javascript
		self.jsSource = 'plugin_scamp.js'
		# Scamp's output XML filename
		self.XMLFile = 'scamp.xml'

		# Decomment to disable the plugin
		#self.enable = False

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
						#'idList' 			: [str(i) for i in data['idList']], 
						'idList' 			: str(data['idList']), 
						'resultsOutputDir' 	: str(data['resultsOutputDir']), 
						'name' 				: str(it.name),
						'config' 			: str(data['config'])})

		return res

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
			config = post['Config']
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, ("POST argument error. Unable to process data: %s" % e)

		items = CartItem.objects.filter(kind__name__exact = self.id)
		itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' : idList, 
				 'resultsOutputDir' : resultsOutputDir, 
				 'config' : config }
		sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		cItem = CartItem(kind = k, name = itemName, user = request.user)
		cItem.data = sdata
		cItem.save()

		return "Item %s saved" % itemName

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

	def __getCondorSubmissionFile(self, request, idList):
		"""
		Generates a suitable Condor submission for processing images on the cluster.

		Note that the scampId variable is used to bypass the config variable: it allows to get the 
		configuration file content for an already processed image rather by selecting content by config 
		file name.
		"""

		post = request.POST
		try:
			itemId = str(post['ItemId'])
			config = post['Config']
			scampId = post['ScampId']
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		# Builds realtime Condor requirements string
		req = self.getCondorRequirementString(request)

		#
		# Config file selection and storage.
		#
		# Rules: 	if scampId has a value, then the config file content is retreive
		# 			from the existing scamp processing. Otherwise, the config file content
		#			is fetched by name from the ConfigFile objects.
		#
		# 			Selected config file content is finally saved to a regular file.
		#
		try:
			if len(scampId):
				config = Plugin_scamp.objects.filter(id = int(scampId))[0]
				content = str(zlib.decompress(base64.decodestring(config.config)))
			else:
				config = ConfigFile.objects.filter(kind__name__exact = self.id, name = config)[0]
				content = config.content
		except Exception, e:
			raise PluginError, "Unable to use a suitable config file: %s" % e

		now = time.time()
		customrc = os.path.join('/tmp/', "scamp-%s.rc" % now)
		scamprc = open(customrc, 'w')
		scamprc.write(content)
		scamprc.close()

		# Condor submission file
		csfPath = "/tmp/scamp-condor-%s.txt" % now

		images = Image.objects.filter(id__in = idList)
		# Content of YOUPI_USER_DATA env variable passed to Condor
		userData = {'ItemID' 			: itemId, 
					'ScampId' 			: str(scampId),
					'Warnings' 			: {}, 
					'SubmissionFile'	: csfPath, 
					'ConfigFile' 		: customrc, 
					'Descr' 			: '',									# Mandatory for Active Monitoring Interface (AMI) - Will be filled later
					'Kind'	 			: self.id,								# Mandatory for AMI, Wrapper Processing (WP)
					'UserID' 			: str(request.user.id),					# Mandatory for AMI, WP
					'ResultsOutputDir'	: str(resultsOutputDir),				# Mandatory for WP
					'Config' 			: str(post['Config'])} 

		step = 0 							# At least step seconds between two job start

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
log                     = /tmp/SCAMP.log.$(Cluster).$(Process)
error                   = /tmp/SCAMP.err.$(Cluster).$(Process)
output                  = /tmp/SCAMP.out.$(Cluster).$(Process)
notification            = Error
notify_user             = monnerville@iap.fr
# Computed Req string
%s
""" % (	os.path.join(submit_file_path, 'script'),
		submit_file_path, 
		os.path.join(submit_file_path, 'script'),
		customrc,
		submit_file_path, 
		os.path.join(submit_file_path, 'script'),
		req )

		csf.write(condor_submit_file)

		ldac_files = self.getLDACPathsFromImageSelection(request, idList)
		# Keep data path only
		ldac_files = [dat[1] for dat in ldac_files]

		#
		# $(Cluster) and $(Process) variables are substituted by Condor at CSF generation time
		# They are later used by the wrapper script to get the name of error log file easily
		#
		userData['ImgID'] = idList
		userData['Descr'] = str("%s from %d SExtractor catalogs" % (self.optionLabel, len(images)))		# Mandatory for Active Monitoring Interface (AMI)
		userData['LDACFiles'] = ldac_files

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

		scamp_params = "-XSL_URL %s/scamp.xsl" % os.path.join(	WWW_SCAMP_PREFIX, 
																request.user.username, 
																userData['Kind'], 
																userData['ResultsOutputDir'][userData['ResultsOutputDir'].find(userData['Kind'])+len(userData['Kind'])+1:] )
		condor_submit_entry = """
arguments               = %s /usr/local/bin/condor_transfert.pl /usr/local/bin/scamp %s %s -c %s 2>/dev/null
# YOUPI_USER_DATA = %s
environment             = USERNAME=%s; TPX_CONDOR_UPLOAD_URL=%s; PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin; YOUPI_USER_DATA=%s
queue""" %  (	encUserData, 
				scamp_params,
				string.join(ldac_files), 
				os.path.basename(customrc),
				userData, 
				request.user.username,
				FTP_URL + resultsOutputDir,
				base64.encodestring(marshal.dumps(userData)).replace('\n', '') )

		csf.write(condor_submit_entry)
		csf.close()

		return csfPath

	def checkForSelectionLDACData(self, request, imgList = None):
		"""
		Check if every image in this selection has associated LDAC data.
		Policy: only the lastest successful qfits-in of current logged-in user is looked for.

		@return Dictionnary {'missingLDAC' : list of images names without LDAC data, 'tasksIds' : list of matching tasks}
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
				missing.extend([str(img.name)])
				continue

			relTaskIds = [rel.task.id for rel in rels]

			# Valid task is only the lastest successful qfits-in of current logged-in user
			tasks = Processing_task.objects.filter(	id__in = relTaskIds, 
													user = request.user, 
													kind__name__exact = 'fitsin',
													success = True).order_by('-end_date')

			if not tasks:
				missing.append(str(img.name))
				continue

			tasksIds.append(int(tasks[0].id))

		return {'missingLDACImages' : missing, 'tasksIds' : tasksIds}

	def getLDACPathsFromImageSelection(self, request, imgList = None):
		"""
		Compute LDAC data path for a given image selection

		@return List of paths to LDAC files
		"""

		post = request.POST
		try:
			idList = request.POST['IdList'].split(',')
			checks = self.checkForSelectionLDACData(request)
		except Exception, e:
			if imgList:
				idList = imgList
				checks = self.checkForSelectionLDACData(request, idList)
			else:
				raise PluginError, "POST argument error. Unable to process data."

		ldac_files = []
		tasks = Processing_task.objects.filter(id__in = checks['tasksIds'])

		for task in tasks:
			img = Rel_it.objects.filter(task = task)[0].image
			ldac_files.append([int(img.id), str(os.path.join(task.results_output_dir, img.name, 'qualityFITS', img.name + '.ldac'))])

		return ldac_files

	def getResultEntryDescription(self, task):
		"""
		Returns custom result entry description for a task.
		task: django object

		returned value: HTML tags allowed
		"""

		rels = Rel_it.objects.filter(task = task)
		return "%s of <b>%d LDAC files</b>" % (self.optionLabel, len(rels))

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
		data = Plugin_scamp.objects.filter(task__id = taskid)[0]

		if task.error_log:
			log = str(zlib.decompress(base64.decodestring(task.error_log)))
		else:
			log = ''

		if data.log:
			scamplog = str(zlib.decompress(base64.decodestring(data.log)))
		else:
			scamplog = ''

		# Get related images
		rels = Rel_it.objects.filter(task__id = taskid)
		imgs = []
		for r in rels:
			imgs.append(r.image)

		# Looks for groups of scamps
		scampHistory = Rel_it.objects.filter(image__in = imgs, task__kind__name = self.id).order_by('task')
		old_task = scampHistory[0].task
		gtasks= [old_task]
		for h in scampHistory:
			task = h.task
			if old_task != task:
				# Other scamp
				gtasks.append(task)
				old_task = task

		history = []
		for st in gtasks:
			history.append({'User' 			: str(st.user.username),
							'Success' 		: st.success,
							'Start' 		: str(st.start_date),
							'Duration' 		: str(st.end_date-st.start_date),
							'Hostname' 		: str(st.hostname),
							'TaskId'		: str(st.id),
							})

		thumbs = [	'astr_chi2_1.png', 'astr_interror1d_1.png', 'astr_interror2d_1.png', 'astr_referror1d_1.png', 'astr_referror2d_1.png',
					'distort_1.png', 'fgroups_1.png', 'psphot_error_1.png' ];
		if data.thumbnails:
			thumbs = ['tn_' + thumb for thumb in thumbs]

		return {	'TaskId'			: str(taskid),
					'Title' 			: str("%s processing" % self.description),
					'User' 				: str(task.user.username),
					'Hostname'			: str(task.hostname),
					'Success' 			: task.success,
					'Start' 			: str(task.start_date),
					'End' 				: str(task.end_date),
					'WWW' 				: str(data.www),
					'LDACFiles'			: marshal.loads(base64.decodestring(data.ldac_files)),
					'Duration' 			: str(task.end_date-task.start_date),
					'ResultsOutputDir' 	: str(task.results_output_dir),
					'Log' 				: log,
					'ResultsLog'		: scamplog,
					'Config' 			: str(zlib.decompress(base64.decodestring(data.config))),
					'Previews'			: thumbs,
					'HasThumbnails'		: data.thumbnails,
					'History'			: history,
			}

	def checkIfXMLExists(self, request):
		"""
		Locates scamp.xml file path on cluster

		@return Dictionary with filename or -1 if not found
		"""

		post = request.POST
		try:
			taskId = request.POST['TaskId']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		task = Processing_task.objects.filter(id = taskId)[0]

		# FIXME: may not be self.XMLFile with custom conf file
		filePath = str(os.path.join(task.results_output_dir, self.XMLFile))

		if not os.path.exists(filePath):
			filePath = -1

		return { 'FilePath' : filePath }

	def parseScampXML(self, request):
		"""
		"""

		post = request.POST
		try:
			taskId = request.POST['TaskId']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		task = Processing_task.objects.filter(id = taskId)[0]
		file = str(os.path.join(task.results_output_dir, self.XMLFile))

		doc = dom.parse(file)
		fields = []
		ldac_list = []
		td = []
	
		data = doc.getElementsByTagName('TABLE')[0]
		fieldNodes = data.getElementsByTagName('FIELD')
	
		for node in fieldNodes:
			fields.append([str(node.getAttribute('name')), str(node.getAttribute('datatype'))])
	
		return { 'Fields' : fields }

	def processQueryOnXML(self, request):
		post = request.POST
		try:
			query = request.POST['Query']
			taskId = request.POST['TaskId']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		ldac_files = []

		tmp = query.split(',')
		query = []
		for i in range(0, len(tmp), 3):
			query.append(tmp[i:i+3])

		fields = self.parseScampXML(request)['Fields']

		task = Processing_task.objects.filter(id = taskId)[0]
		data = Plugin_scamp.objects.filter(task__id = taskId)[0]
		file = str(os.path.join(task.results_output_dir, self.XMLFile))

		doc = dom.parse(file)
		tabledata = doc.getElementsByTagName('TABLEDATA')[0]
		trNodes = tabledata.getElementsByTagName('TR')

		for trNode in trNodes:
			match = True
			tdNodes = trNode.getElementsByTagName('TD')
			for param in query:
				param = [int(param[0]), int(param[1]), param[2]]
				paramValue = tdNodes[param[0]].firstChild.nodeValue
				# Look for field type
				paramType = fields[param[0]][1]

				# Find LDAC files
				if paramType == 'char':
					conds =  ['matches', 'is different from']
					cond = conds[param[1]]
					if cond == conds[0] and paramValue.find(param[2]) == -1:
						match = False
					elif cond == conds[1] and paramValue.find(param[2]) != -1:
						match = False
				elif paramType == 'int' or paramType == 'float' or paramType == 'double':
					conds = ['=', '<', '>', '<>']
					cond = conds[param[1]]
					if cond == conds[0] and float(paramValue) != float(param[2]):
						match = False
				elif paramType == 'boolean':
					conds = ['T', 'F']
					cond = conds[param[1]]
					if cond != paramValue:
						match = False

			if match:
				ldac = str(tdNodes[0].firstChild.nodeValue)
				if ldac not in ldac_files:
					ldac_files.append(ldac)

		qfits_ldac_files = marshal.loads(base64.decodestring(data.ldac_files))

		return {'LDACFiles' : ldac_files, 
				'TaskId'	: int(task.id),
				'DataPath' : str(os.path.dirname(qfits_ldac_files[0])) }


	def getImgIdListFromLDACFiles(self, request):
		post = request.POST
		try:
			ldac_files = request.POST['LDACFiles'].split(',')
			taskId = request.POST['TaskId']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		imgFiles = [f[:f.find('.ldac')] for f in ldac_files]

		rels = Rel_it.objects.filter(task__id = taskId)
		task = Processing_task.objects.filter(id = taskId)[0]
		data = Plugin_scamp.objects.filter(task__id = taskId)[0]

		relsImgs = [(r.image.name, r.image.id) for r in rels]

		idList = []
		for img in relsImgs:
			if img[0] in imgFiles:
				idList.append(int(img[1]))

		return {'IdList' : idList,
				'ScampId' : int(data.id),
				'ResultsOutputDir' : os.path.join(str(task.results_output_dir), 'subprocess/' )}
