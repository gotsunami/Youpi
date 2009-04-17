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

import sys, os.path, time, string, re
import xml.dom.minidom as dom
import marshal, base64, zlib
from types import *
#
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *
from terapix.youpi.models import *
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

		self.template = 'plugins/scamp.html' 						# Main template, rendered in the processing page
		self.itemCartTemplate = 'plugins/scamp_item_cart.html' 		# Template for custom rendering into the shopping cart
		self.jsSource = 'plugins/scamp.js' 							# Custom javascript

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
						'idList' 			: str(data['idList']), 
						'resultsOutputDir' 	: str(data['resultsOutputDir']), 
				 		'aheadPath'			: str(data['aheadPath']),
						'name' 				: str(it.name),
						'taskId' 			: str(data['taskId']), 
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
			itemID = str(post['ItemId'])
			config = post['Config']
			taskId = post.get('TaskId', '')
			aheadPath = post['AheadPath']
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, ("POST argument error. Unable to process data: %s" % e)

		items = CartItem.objects.filter(kind__name__exact = self.id)
		if items:
			itemName = "%s-%d" % (itemID, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
		else:
			itemName = "%s-%d" % (itemID, len(items)+1)

		# Custom data
		data = { 'idList' 			: idList, 
				 'resultsOutputDir' : resultsOutputDir, 
				 'taskId'			: taskId,
				 'aheadPath'		: aheadPath,
				 'config' 			: config,
		}
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

		Note that the taskId variable is used to bypass the config variable: it allows to get the 
		configuration file content for an already processed image rather by selecting content by config 
		file name.
		"""

		post = request.POST
		try:
			itemId = str(post['ItemId'])
			config = post['Config']
			taskId = post.get('TaskId', '')
			resultsOutputDir = post['ResultsOutputDir']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		# Builds realtime Condor requirements string
		req = self.getCondorRequirementString(request)

		#
		# Config file selection and storage.
		#
		# Rules: 	if taskId has a value, then the config file content is retreive
		# 			from the existing scamp processing. Otherwise, the config file content
		#			is fetched by name from the ConfigFile objects.
		#
		# 			Selected config file content is finally saved to a regular file.
		#
		try:
			if len(taskId):
				config = Plugin_scamp.objects.filter(task__id = int(taskId))[0]
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

		# Scamp configuration file
		customrc = self.getConfigurationFilePath()
		scamprc = open(customrc, 'w')
		scamprc.write(content)
		scamprc.close()

		# Condor submission file
		csfPath = self.getCondorSubmitFilePath()

		# Get filenames for Condor log files (log, error, out)
		logs = self.getCondorLogFilenames()

		images = Image.objects.filter(id__in = idList)
		# Content of YOUPI_USER_DATA env variable passed to Condor
		userData = {'ItemID' 			: itemId, 
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
executable              = %(wrapperpath)s/wrapper_processing.py
universe                = vanilla
transfer_executable     = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_input_files    = %(settingspath)s/settings.py, %(scriptpath)s/DBGeneric.py, %(conf)s, %(settingspath)s/NOP
initialdir				= %(initdir)s
transfer_output_files   = NOP
log                     = %(log)s
error                   = %(errlog)s
output                  = %(outlog)s
notification            = Error
notify_user             = monnerville@iap.fr
# Computed Req string
%(requirements)s""" % { 
	'wrapperpath'	: os.path.join(submit_file_path, 'script'),
	'settingspath'	: submit_file_path, 
	'scriptpath'	: os.path.join(submit_file_path, 'script'),
	'conf'			: customrc,
	'initdir'		: os.path.join(submit_file_path, 'script'),
	'requirements'	: req ,
	'log'			: logs['log'],
	'errlog'		: logs['error'],
	'outlog'		: logs['out'],
}


		csf.write(condor_submit_file)

		ldac_files = self.getLDACPathsFromImageSelection(request, idList)
		# Keep data path only
		ldac_files = [dat[1] for dat in ldac_files]

		userData['ImgID'] = idList
		userData['Descr'] = str("%s from %d SExtractor catalogs" % (self.optionLabel, len(images)))		# Mandatory for Active Monitoring Interface (AMI)
		userData['LDACFiles'] = ldac_files
		# Mandatory for WP
		userData['JobID'] = self.getUniqueCondorJobId()

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

	def checkForSelectionLdacAheadData(self, request, imgList = None):
		"""
		Check if every image in this selection has associated LDAC/AHEAD data.
		Policy: only the lastest successful qfits-in of current logged-in user is looked for.

		#@return Dictionnary {'missing' : list of images names without LDAC/AHEAD data, 'tasksIds' : list of matching tasks}
		@return Dictionnary {'missing' : [[img1, ['img1.ldac', 'img1.ahead']], [img2, ...], ...], 'tasksIds' : list of matching tasks}
		"""

		post = request.POST
		try:
			aheadPath = post['AheadPath']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data MATMAT."

		if imgList:
			idList = imgList
		else:
			try:
				idList = request.POST['IdList'].split(',')
			except Exception, e:
				raise PluginError, "POST argument error. Unable to process data."

		tasksIds = []
		missing = []
		imgList = Image.objects.filter(id__in = idList).order_by('name')
		curTask = None

		for img in imgList:
			ldacMissing = aheadMissing = False
			rels = Rel_it.objects.filter(image = img)
			if not rels:
				#missing.extend([str(img.name)])
				ldacMissing = True

			relTaskIds = [rel.task.id for rel in rels]

			# Valid task is only the lastest successful qfits-in of current logged-in user
			tasks = Processing_task.objects.filter(	id__in = relTaskIds, 
													user = request.user, 
													kind__name__exact = 'fitsin',
													success = True).order_by('-end_date')

			if not tasks:
				#missing.append(str(img.name))
				ldacMissing = True

			if not os.path.exists(os.path.join(aheadPath, img.name + '.ahead')):
				aheadMissing = True

			if ldacMissing or aheadMissing:
				info = [str(img.name)]
				miss = []
				if ldacMissing: miss.append(str(img.name) + '.ldac')
				if aheadMissing: miss.append(str(img.name) + '.ahead')
				info.append(miss)
				missing.append(info)


			if not ldacMissing and not aheadMissing:
				tasksIds.append(int(tasks[0].id))

		return {'missing' : missing, 'total': int(len(imgList)), 'totalms': int(len(missing)), 'tasksIds' : tasksIds}

	def getLDACPathsFromImageSelection(self, request, imgList = None):
		"""
		Compute LDAC data path for a given image selection

		@return List of paths to LDAC files
		"""

		post = request.POST
		try:
			idList = request.POST['IdList'].split(',')
			checks = self.checkForSelectionLdacAheadData(request)
		except Exception, e:
			if imgList:
				idList = imgList
				checks = self.checkForSelectionLDACData(request, idList)
			else:
				raise PluginError, "POST argument error. Unable to process data KKKK."

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
					'ClusterId'			: str(task.clusterId),
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
				'TaskId' : int(task.id),
				'ResultsOutputDir' : os.path.join(str(task.results_output_dir), 'subprocess/' )}

	def getReprocessingParams(self, request):
		"""
		Returns all information for reprocessing a calibration (so that it can be added to the shopping cart).
		"""

		try:
			taskId = request.POST['TaskId']
		except KeyError, e:
			raise PluginError, 'Bad parameters'

		data = Plugin_scamp.objects.filter(task__id = int(taskId))[0]
		rels = Rel_it.objects.filter(task__id = int(taskId))
		# Must be a list of list
		idList = [[int(r.image.id) for r in rels]]

		return {'resultsOutputDir' 	: str(data.task.results_output_dir),
				'idList'			: str(idList), 
		}
