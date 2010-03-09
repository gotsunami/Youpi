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

import sys, os.path, re, time, string, re
import xml.dom.minidom as dom
import marshal, base64, zlib
from types import *
from sets import Set
#
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *
from terapix.youpi.models import *
from django.conf import settings
from terapix.youpi.auth import read_proxy
import terapix.lib.cluster.condor as condor
#
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render_to_response 
from django.template import RequestContext

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
		self.description = 'QualityFits'
		# Item prefix in processing cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'QF'
		self.index = 0

		self.template = 'plugins/qualityfitsin.html' 						# Main template, rendered in the processing page
		self.itemCartTemplate = 'plugins/qualityfitsin_item_cart.html' 		# Template for custom rendering into the processing cart
		self.jsSource = 'plugins/qualityfitsin.js' 							# Custom javascript

	def saveCartItem(self, request):
		"""
		Serialize cart item into DB.
	
		@param request Django HTTP request object
		@return Name of saved item when successful
		"""
		post = request.POST
		try:
			idList = eval(post['IdList'])
			itemId = str(post['ItemId'])
			flatPath = post['FlatPath']
			maskPath = post['MaskPath']
			regPath = post['RegPath']
			config = post['Config']
			taskId = post.get('TaskId', '')
			resultsOutputDir = post['ResultsOutputDir']
			exitIfFlatMissing = post['ExitIfFlatMissing']
			flatNormMethod = post['FlatNormMethod']
		except Exception, e:
			raise PluginError, ("POST argument error. Unable to process data: %s" % e)

		items = CartItem.objects.filter(kind__name__exact = self.id).order_by('-date')
		if items:
			itemName = "%s-%d" % (itemId, int(re.search(r'.*-(\d+)$', items[0].name).group(1))+1)
		else:
			itemName = "%s-%d" % (itemId, len(items)+1)

		# Custom data
		data = { 'idList' 			: idList, 
				 'flatPath' 		: flatPath, 
				 'maskPath' 		: maskPath, 
				 'regPath' 			: regPath, 
				 'taskId'			: taskId,
				 'resultsOutputDir' : resultsOutputDir, 
				 'exitIfFlatMissing': exitIfFlatMissing, 
				 'flatNormMethod'   : flatNormMethod,
				 'config' 			: config 
		}
		sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')

		profile = request.user.get_profile()
		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		cItem = CartItem(kind = k, name = itemName, user = request.user, mode = profile.dflt_mode, group = profile.dflt_group)
		cItem.data = sdata
		cItem.save()

		return "Item %s saved" % itemName

	def getSavedItems(self, request):
		"""
		Returns a user's saved items. 
		"""

		# per-user items
		items, filtered = read_proxy(request, CartItem.objects.filter(kind__name__exact = self.id).order_by('-date'))
		res = []
		for it in items:
			data = marshal.loads(base64.decodestring(str(it.data)))
			if not data.has_key('exitIfFlatMissing'):
				data['exitIfFlatMissing'] = 0
			if not data.has_key('flatNormMethod'):
				data['flatNormMethod'] = ''
			res.append({'date' 				: "%s %s" % (it.date.date(), it.date.time()), 
						'username' 			: str(it.user.username),
						'idList' 			: str(data['idList']), 
						'flatPath' 			: str(data['flatPath']), 
						'taskId' 			: str(data['taskId']), 
						'itemId' 			: str(it.id), 
						'maskPath' 			: str(data['maskPath']), 
						'regPath' 			: str(data['regPath']), 
						'resultsOutputDir' 	: str(self.getUserResultsOutputDir(request, data['resultsOutputDir'], it.user.username)),
						'name' 				: str(it.name),
						'exitIfFlatMissing' : int(data['exitIfFlatMissing']),
						'flatNormMethod'    : str(data['flatNormMethod']),
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

	def filterProcessingHistoryTasks(self, request, tasksIds):
		"""
		Filters processing history input tasks
		"""
		try:
			gradingFilter = request.POST['GradingFilter']
		except KeyError, e:
			raise PluginError, e

		from django.db import connection
		cur = connection.cursor()
		q = """
		SELECT COUNT(g.id) FROM youpi_firstqeval AS g, youpi_plugin_fitsin AS f, youpi_processing_task AS t
		WHERE g.fitsin_id=f.id
		AND f.task_id=t.id
		AND t.id=%d
		"""

		if gradingFilter == 'all': return tasksIds
		keep = []
		for id in tasksIds:
			cur.execute(q % id)
			hasgrades = cur.fetchall()[0][0]
			if gradingFilter == 'graded' and hasgrades:
				keep.append(id)
			elif hasgrades == 0:
				keep.append(id)

		return keep

	def getProcessingHistoryExtraData(self, taskId):
		"""
		Returns latest grade (if any) for this processing task
		"""
		grades = FirstQEval.objects.filter(fitsin__task__id = taskId).order_by('date')

		ret = False
		if grades:
			try:
				ret =  "Graded <b>" + grades[0].grade + '</b>'
				if len(grades) > 1:
					ret += " (%d)" % len(grades)
				ret = str(ret)
			except:
				pass

		return ret

	def getProcessingHistoryExtraHeader(self, request, tasks):
		"""
		Returns extra custom header for qfitsin items.
		@params tasks tasks objects _after_ they have been filtered (critera)
		"""
		qfs = Plugin_fitsin.objects.filter(task__in = tasks, task__success = True)
		grades = FirstQEval.objects.filter(fitsin__in = qfs).values('fitsin').distinct()
		all = qfs.count()
		if all: percent = len(grades)*100./all
		else: percent = 0
		return """
			<table style="width: %s">
				<tr>
					<td>%d of %d QFits processings already graded</td>
					<td><div id="ph_agraded_div" style="color: black;"></div></td>
				</tr>
			</table>
			<script type="text/javascript">new ProgressBar('ph_agraded_div', %.2f, {borderColor: 'gray', color: 'lightblue'});</script>
		""" % ('100%', len(grades), all, percent)

	def getTaskInfo(self, request):
		"""
		Returns information about a finished processing task
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
				com = ev.custom_comment
				if not com:
					com = ev.comment.comment
				gradingList.append([str(ev.user.username), str(ev.grade), str(com)])
				
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
			history.append({'User' 				: str(h.task.user.username),
							'Success' 			: h.task.success,
							'Start' 			: str(h.task.start_date),
							'Duration' 			: str(h.task.end_date-h.task.start_date),
							'Hostname' 			: str(h.task.hostname),
							'GradingCount'		: h_gcount,
							'TaskId'			: str(h.task.id),
							'FitsinId'			: str(h_fits.id),
							'Flat' 				: str(h_fits.flat),
							'Mask' 				: str(h_fits.mask),
							'Reg' 				: str(h_fits.reg),
							'ExitIfFlatMissing'	: h_fits.exitIfFlatMissing,
							'FlatNormMethod'	: h_fits.flatNormMethod,
							})

		try:
			runName = Rel_ri.objects.filter(image = img)[0].run.name
		except:
			runName = None

		ImgInfo = [	('Object', img.object),
					('RunId', runName),
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
					'ClusterId'			: str(task.clusterId),
					'Success' 			: task.success,
					'Start' 			: str(task.start_date),
					'End' 				: str(task.end_date),
					'Duration' 			: str(task.end_date-task.start_date),
					'Flat' 				: str(data.flat),
					'Mask' 				: str(data.mask),
					'Reg' 				: str(data.reg),
					'ExitIfFlatMissing'	: data.exitIfFlatMissing,
					'FlatNormMethod'	: data.flatNormMethod,
					'Config' 			: str(zlib.decompress(base64.decodestring(data.qfconfig))),
					'WWW' 				: str(data.www),
					'ImgName' 			: str(img.name),
					'ImgFilename' 		: str(img.filename),
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
					'QFitsHistory' 		: history,
					'Tags'				: [[str(t.name), str(t.style)] for t in img.tags()],
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

		from terapix.script.genimgdothead import genImageDotHead
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
			exitIfFlatMissing = int(post['ExitIfFlatMissing'])
			flatNormMethod = post['FlatNormMethod']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

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

		# QualityFITS configuration file
		customrc = self.getConfigurationFilePath()
		qfrc = open(customrc, 'w')
		qfrc.write(content)
		qfrc.close()

		# Condor submission file
		csfPath = condor.CondorCSF.getSubmitFilePath(self.id)

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
					'ExitIfFlatMissing'	: exitIfFlatMissing,
					'FlatNormMethod'	: flatNormMethod,
					'Config' 			: str(post['Config'])} 

		step = 2 							# At least step seconds between two job start

		# Generate CSF
		cluster = condor.YoupiCondorCSF(request, self.id, desc = self.optionLabel)
		cluster.setTransferInputFiles([customrc, os.path.join(settings.TRUNK, 'terapix', 'script', 'genimgdothead.py')])

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

		# One image per job queue
		for img in process_images:
			# Stores real image name (as available on disk)
			userData['RealImageName'] = str(img.filename)
			path = os.path.join(img.path, userData['RealImageName'] + '.fits')

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
			# results (settings.PROCESSING_OUTPUT) back. Every job queued will be put to sleep StartupDelay 
			# seconds
			#
			userData['StartupDelay'] = step
			# Mandatory for WP
			userData['JobID'] = self.getUniqueCondorJobId()

			# Automatic normalized flat generation
			if flatNormMethod:
				fnfile = "%s_norm_%s.fits" % (img.flat, flatNormMethod.lower())
				userData['FlatNormFile'] = fnfile

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

			if flatNormMethod:
				image_args += " --flatnorm %s" % fnfile
			
			userData['Warnings'] = {}
			userData['Warnings'][str(img.name) + '.fits'] = []

			if imgFlat: image_args += " -F %s" % imgFlat
			else: userData['Warnings'][str(img.name) + '.fits'].append('No suitable flat data found')

			if imgMask: image_args += " -M %s" % imgMask
			else: userData['Warnings'][str(img.name) + '.fits'].append('No suitable mask data found')

			if imgReg: image_args += " -P %s" % imgReg
			else: userData['Warnings'][str(img.name) + '.fits'].append('No suitable reg file found')

			# Only add --ahead param if needed
			hdata, lenght, missing = genImageDotHead(int(img.id))
			if hdata:
				image_args += " --ahead %s" % userData['RealImageName'] + '.head'
			
			if not len(userData['Warnings'][str(img.name) + '.fits']):
				del userData['Warnings'][str(img.name) + '.fits']
			
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
				pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, 'condor_submit %s 2>&1' % csfPath)) 
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

	def getReprocessingParams(self, request):
		"""
		Returns all information for reprocessing an image (so that it can be added to the processing cart).
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
				'ResultsOutputDir' 	: str(self.getUserResultsOutputDir(request, data.task.results_output_dir, data.task.user.username)),
		}

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
		idList = [[int(img.image.id) for img in imgs]]
		fitsin = Plugin_fitsin.objects.filter(task__in = tasks)[0]

		processings = {	'ResultsOutputDir' 	: str(tasks[0].results_output_dir), 
						'TaskId'			: int(tasks[0].id), # Used to retrieve config file content
						'IdList' 			: str(idList),
						'Count'				: len(idList),
						'Flat' 				: str(fitsin.flat),
						'Mask' 				: str(fitsin.mask),
						'Reg' 				: str(fitsin.reg),
						'ExitIfFlatMissing'	: str(fitsin.exitIfFlatMissing),
						'FlatNormMethod'	: str(fitsin.flatNormMethod),
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

		pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_q -xml"))
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

		pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_rm %s.%s" % (cluster, proc)))
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

	def reports(self):
		"""
		Adds reporting capabilities to QFITSin plugin
		"""

		outdirs = Processing_task.objects.filter(kind__name = self.id).values('results_output_dir').order_by('results_output_dir').distinct()
		outdirs = [g['results_output_dir'] for g in outdirs]
		nongopts = """Select output directory: <select name="output_dir_select">%s</select>""" % \
				string.join(map(lambda x: """<option value="%s">%s</option>""" % (x, x), outdirs), '\n')

		oneopts = """Select a grade: <select name="grade_select">%s</select>""" % \
				string.join(map(lambda x: """<option value="%s">%s</option>""" % (x[0], x[0]), GRADE_SET), '\n')

		rdata = [
			{'id': 'allgrades',		'title': 'List of all QualityFITS-in grades'},
			{'id': 'gradestats', 	'title': 'Grading statistics'},
			{'id': 'nongraded', 	'title': 'List of all non graded images', 'options': nongopts},
			{'id': 'onegrade', 		'title': 'List of all images with a selected grade', 'options': oneopts},
			{'id': 'piegrades', 	'title': 'Pie Chart of grades'},
		]
		rdata.sort(cmp=lambda x,y: cmp(x['title'], y['title']))

		return rdata

	def __getReportName(self, reportId):
		"""
		Returns report name
		"""
		for r in self.reports():
			if r['id'] == reportId:
				return r['title']

	def getReport(self, request, reportId):
		"""
		Generates a report.
		@param reportId report Id as returned by the reports() function
		"""
		post = request.POST

		if reportId == 'allgrades':
			from terapix.script.grading import get_grades
			from terapix.reporting.csv import CSVReport
			res = get_grades()
			return HttpResponse(str(CSVReport(data = get_grades())), mimetype = 'text/plain')

		elif reportId == 'gradestats':
			from django.db import connection
			cur = connection.cursor()
			paths = Processing_task.objects.filter(success = True, kind__name = self.id).distinct().values_list('results_output_dir', flat = True).order_by('results_output_dir')
			trs = []
			k = 0
			totalgraded = totalnongraded = totalprocessings = 0
			for path in paths:
				k += 1
				fitsins = Plugin_fitsin.objects.filter(task__success = True, task__results_output_dir = path).values_list('id', flat = True)
				# Only one grade even for processings graded multiple times by different users 
				q = """SELECT COUNT(*) FROM youpi_firstqeval WHERE fitsin_id IN (%s) GROUP BY fitsin_id""" % string.join([str(f) for f in fitsins], ',')
				cur.execute(q)
				res = cur.fetchall()
				ugrades = len(res)

				graded = ugrades
				nongraded = len(fitsins) - graded
				total = graded + nongraded
				totalgraded += graded
				totalnongraded += nongraded
				totalprocessings += total

				style = 'text-align: right;'
				gstyle = trstyle = gradecls = ''
				if graded == 0: gstyle = 'color: red;'
				elif graded < total: gstyle = 'color: orange; font-weight: bold;'
				else: 
					gstyle = 'color: green;'
					trstyle = 'complete'
					gradecls = 'gradecomplete'

				trs.append(("""
<tr class="%(trstyle)s">
	<td>%(idx)s</td>
	<td class="file">%(path)s</td>
	<td class="%(gradecls)s" style="%(style)s%(gstyle)s">%(graded)d</td>
	<td style="%(style)s">%(nongraded)d</td>
	<td style="%(style)s">%(percent).2f</td>
	<td style="%(style)s">%(total)d</td>
</tr>""" % {
	'idx'		: k,
	'path' 		: path,
	'graded' 	: graded,
	'nongraded' : nongraded,
	'total' 	: total,
	'style' 	: style,
	'gstyle' 	: gstyle,
	'trstyle' 	: trstyle,
	'gradecls' 	: gradecls,
	'percent' 	: graded*100./total,
}))

			content = """
<table class="report_grading_stats">
	<tr>
		<th></th>
		<th>Results Output Directory</th>
		<th># Graded</th>
		<th># Non graded</th>
		<th>%%</th>
		<th>Total of Processings</th>
	</tr>
	<tr style="background-color: lightyellow">
		<th></th>
		<th style="text-align: right">Total</th>
		<th style="text-align: right">%(totalgraded)d</th>
		<th style="text-align: right">%(totalnongraded)d</th>
		<th style="text-align: right">%(totalpercent).2f</th>
		<th style="text-align: right">%(totalprocessings)d</th>
	</tr>
	%(rows)s
	<tr style="background-color: lightyellow">
		<th></th>
		<th style="text-align: right">Total</th>
		<th style="text-align: right">%(totalgraded)d</th>
		<th style="text-align: right">%(totalnongraded)d</th>
		<th style="text-align: right">%(totalpercent).2f</th>
		<th style="text-align: right">%(totalprocessings)d</th>
	</tr>
</table>
""" % {
	'rows'				: string.join(trs, '\n'),
	'totalgraded'		: totalgraded,
	'totalpercent'		: totalgraded*100./totalprocessings,
	'totalnongraded'	: totalnongraded,
	'totalprocessings'	: totalprocessings,
}
			return render_to_response('report.html', {	
								'report_title' 		: self.__getReportName(reportId),
								'report_content' 	: content, 
			}, context_instance = RequestContext(request))

		elif reportId == 'onegrade':
			from terapix.reporting.csv import CSVReport
			try:
				grade = post['grade_select']
			except Exception, e:
				return HttpResponseRedirect('/youpi/reporting/')

			usergrades = FirstQEval.objects.filter(grade = grade).order_by('-date')
			content = []
			for g in usergrades:
				rel = Rel_it.objects.filter(task = g.fitsin.task)[0]
				content.append((rel.image.name, g.grade, rel.image.path, rel.image.checksum, g.date, g.user, g.comment.comment, g.custom_comment))
			if not usergrades: return HttpResponse('No images are graded ' + grade, mimetype = 'text/plain')
			return HttpResponse(str(CSVReport(data = content)), mimetype = 'text/plain')

		elif reportId == 'nongraded':
			try:
				outdir = post['output_dir_select']
			except Exception, e:
				return HttpResponseRedirect('/youpi/reporting/')

			fitsins = Plugin_fitsin.objects.filter(task__results_output_dir = outdir, task__success = True).values('id')
			fitsinsIds = [g['id'] for g in fitsins]
			usergrades = FirstQEval.objects.filter(fitsin__in = fitsins).values('fitsin').distinct()
			usergrades = [g['fitsin'] for g in usergrades]
			# Keeps qfits for non graded images only
			for ug in usergrades:
				fitsinsIds.remove(ug)
			tasks = Plugin_fitsin.objects.filter(id__in = fitsinsIds).values('task')
			tasksIds = [g['task'] for g in tasks]

			# Check permissions
			tasks, filtered = read_proxy(request, Processing_task.objects.filter(id__in = tasksIds).order_by('-start_date'))

			trs = []
			trs.append("<tr><th>%s</th></tr>" % outdir)
			if filtered:
				trs.append("""<tr><td><div class="perm_not_granted">You don't have permission to view the full results set. Some results have been filtered</div></td></tr>""")
			for t in tasks[:50]:
				rel = Rel_it.objects.filter(task = t)[0]
				f = Plugin_fitsin.objects.filter(task = t)[0]
				trs.append(("""
<tr onclick="this.writeAttribute('style', 'background-color: lightgreen;');">
	<td><a target="_blank" href="/youpi/grading/fitsin/%s">%s</a></td>
	<td>%s</td>
	<td>%s</td>
	<td>%s</td>
</tr>""" % (f.id, rel.image.name, t.start_date, t.user.username, t.hostname)))

			if not tasks and not filtered:
				trs.append(("""<tr><td>All images in this directory have already been graded</td></tr>"""))

			content = """
<div style="margin-bottom: 10px">Not graded: %(remaining)d images</div>
<table>
	%(rows)s
</table>
""" % {
	'remaining': len(fitsinsIds),
	'rows': string.join(trs, '\n'),
}

			return render_to_response('report.html', {	
								'report_title' 		: self.__getReportName(reportId),
								'report_content' 	: content, 
			}, context_instance = RequestContext(request))

		elif reportId == 'piegrades':
			from terapix.script.grading import get_proportions
			data = get_proportions()
			sum = 0
			for d in data:
				sum += d[1]
			if not sum:
				js = "No grades at all."
			else:
				# Get grading statistics
				js = """
<div id="imgcontainer" style="width:600px;height:300px;"></div>
<script type="text/javascript">
function draw_pie() {
	// Fill series.
	var grade_a = [[0, %(ga)d]];
	var grade_b = [[0, %(gb)d]];
	var grade_c = [[0, %(gc)d]];
	var grade_d = [[0, %(gd)d]];

	//Draw the graph.
	var f = Flotr.draw($('imgcontainer'), [
			{data: grade_a, label: 'Graded A (%(ga)d)'}, 
			{data: grade_b, label: 'Graded B (%(gb)d)'}, 
			{data: grade_c, label: 'Graded C (%(gc)d)'},
			{data: grade_d, label: 'Graded D (%(gd)d)'}
		], {
			HtmlText: false, 
			grid: {
				verticalLines: false, 
				horizontalLines: false
			},
			xaxis: {showLabels: false},
			yaxis: {showLabels: false}, 
			pie: {
				show: true, 
				explode: 6
			},
			legend:{
				position: 'se',
				backgroundColor: '#D2E8FF'
			}
		}
	);
}
draw_pie();
</script>
""" % {
	'ga': data[0][1], 
	'gb': data[1][1], 
	'gc': data[2][1], 
	'gd': data[3][1], 
}
			return render_to_response('report.html', {	
								'report_title' 		: self.__getReportName(reportId),
								'report_content' 	: js, 
			}, context_instance = RequestContext(request))

		
		return HttpResponseNotFound('Report not found.')
