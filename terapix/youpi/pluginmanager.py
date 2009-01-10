# vim: set ts=4

from django.contrib.sessions.models import Session
import glob, sys, types, re, os, string
import marshal, base64
from types import *
from settings import *
#
from terapix.youpi.models import *

PLUGIN_DIRS = os.path.join(HOME, 'youpi', 'terapix', 'youpi', 'plugins')
sys.path.insert(0, PLUGIN_DIRS)
sys.path.insert(0, PLUGIN_DIRS[:-len('/plugins')])

class CondorSetupError(Exception): pass
class CondorSubmitError(Exception): pass
class PluginError(Exception): pass
class PluginManagerError(Exception): pass
class PluginAllDataAlreadyProcessed(Exception): pass

class ProcessingPlugin: 
	type = 'YOUPIPLUGIN'

	def __init__(self):
		self.enable = True
		self.shortName = 'My short name here'
		self.optionLabel = 'My option label'
		# Default HTML template
		self.template = 'plugin_default.html'
		# Default plugin version
		self.version = '0.1'

		# Plugin data (to be processed)
		self.__data = [] 
		# Used to generate rather unique item ID in shopping cart
		self.itemCounter = 0

	def getConfigFileNames(self, request):
		# Updates entry
		configs = ConfigFile.objects.filter(kind__name__exact = self.id)
		if not len(configs):
			self.__saveDefaultConfigFileToDB(request)
			configs = ConfigFile.objects.filter(kind__name__exact = self.id)

		res = []
		for config in configs:
			res.append(str(config.name))

		return { 'configs' : res }

	def __saveDefaultConfigFileToDB(self, request):
		"""
		Looks into DB (youpi_configfiles table) if an entry for a default configuration file. 
		If not creates one with the embedded default content.
		"""

		try:
			f = open(os.path.join('terapix', 'youpi', 'plugins', 'conf', self.id + '.conf.default'))
			config = string.join(f.readlines())
			f.close()
		except IOError, e:
			raise PluginError, "Default config file for %s: %s" % (self.id, e)

		k = Processing_kind.objects.filter(name__exact = self.id)[0]
		try:
			m = ConfigFile(kind = k, name = 'default', content = config, user = request.user)
			m.save()
		except:
			# Cannot save, already exits: do nothing
			pass

		return config

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

	def hasItemsInCart(self):
		"""
		Returns True if this plugin has items in shopping cart.
		"""
		return len(self.__data) > 0

	def setData(self, dataList):
		"""
		Sets data to be processed 
		"""
		self.__data = dataList

	def removeData(self):
		"""
		Removed plugin data
		"""
		self.__data = []

	def getData(self):
		return self.__data

	def getClusterId(self, submit_content):
		"""
		Returns a dictionnary with number of jobs submitted to related cluster on Condor
		submit_content is a list with 3 elements of content as returned by condor_submit command 
		(i.e. 3 lines of plain text)
		"""

		if type(submit_content) != ListType:
			raise TypeError, "submit_content must be a list !"

		# Only third line is of interest
		try:
			data = submit_content[2]	
			m = re.match(r'^(?P<count>\d+?) .*? (?P<cluster>\d+?).$', data[:-1])
			count = m.group('count')
			cid = m.group('cluster')
		except IndexError:
			count = -1
			cid = -1
		except AttributeError:
			# RE issue, could be a Condor error
			if submit_content[1].find('ERROR') == 0:
				raise CondorSubmitError, "Condor error:\n%s" % string.join(submit_content[1:], '')

		return { 'count' : count, 'clusterId' : cid, 'data' : [str(s) for s in submit_content] }

	def getCondorRequirementString(self, request):
		"""
		Realtime and powerful Condor requirement string generation
		"""

		from terapix.youpi.cviews.condreqstr import *

		post = request.POST
		try:
			condorSetup = post['CondorSetup']
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		vms = get_condor_status()

		if condorSetup == 'default':
			dflt_setup = marshal.loads(base64.decodestring(request.user.get_profile().dflt_condor_setup))
			# Check Behaviour: policy or selection
			if not dflt_setup.has_key(self.id):
				raise PluginError, "No default Condor setup found for '%s' plugin." % self.optionLabel

			db = dflt_setup[self.id]['DB']
			if db == 'policy':
				pol = CondorNodeSel.objects.filter(label = dflt_setup[self.id]['DP'], is_policy = True)[0]
				req = get_requirement_string(pol.nodeselection, vms)
			else:
				# Default behaviour is 'selection'
				req = get_requirement_string_from_selection(dflt_setup[self.id]['DS'])

		elif condorSetup == 'custom':
			try:
				c_policy = str(post['Policy'])
				c_selection = None
			except Exception, e:
				try:
					c_selection = str(post['Selection'])
					c_policy = None
				except Exception, e:
					raise PluginError, 'condorSetup POST argument error. Unable to process data'

			if c_policy:
				pol = CondorNodeSel.objects.filter(label = c_policy, is_policy = True)[0]
				req = get_requirement_string(pol.nodeselection, vms)
			else:
				req = get_requirement_string_from_selection(c_selection)

		return req

	def deleteCartItem(self, request):
		post = request.POST
		try:
			name = str(post['Name'])
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		try:
			item = CartItem.objects.filter(kind__name__exact = self.id, name = name)[0]
			item.delete()
		except Exception, e:
			raise PluginError, "No item named '%s' found." % name

		return "Item %s deleted" % name

	def getMiscDataPaths(self, request):
		"""
		Returns a JSON object with paths to flags and weights
		"""
		post = request.POST
		try:
			keys = post['Keys'].split(',')
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		paths = {}
		for k in keys:
			try:
				m = MiscData.objects.filter(key = k, user = request.user)[0]
				data = marshal.loads(base64.decodestring(str(m.data)))
				paths[str(k)] = data
				paths[str(k)].sort()
			except:
				paths[str(k)] = []

		return paths

	def saveMiscDataPath(self, request):
		"""
		Save a path of type key.
		"""
		post = request.POST
		try:
			path = post['Path']
			key = str(post['Key'])
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		pathList = []
		canSave = True
		try:
			# Updates entry
			m = MiscData.objects.filter(key = key, user = request.user)[0]
			data = marshal.loads(base64.decodestring(str(m.data)))
			# Checks if path already exists
			if str(path) not in data:
				data.append(str(path))
				sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')
				m.data = sdata
			else:
				canSave = False
			pathList = data
		except:
			# Inserts a new one
			pathList = [str(path)]
			sdata = base64.encodestring(marshal.dumps(pathList)).replace('\n', '')
			m = MiscData(key = key, data = sdata, user = request.user)

		if canSave:
			m.save()

		return { key + 's' : pathList }

	def deleteMiscDataPath(self, request):
		"""
		Deletes a path of type key.
		"""
		post = request.POST
		try:
			path = str(post['Path'])
			key = str(post['Key'])
		except Exception, e:
			raise PluginError, "POST argument error. Unable to process data."

		# Updates entry
		m = MiscData.objects.filter(key = key, user = request.user)[0]
		data = marshal.loads(base64.decodestring(str(m.data)))
		# Checks if path already exists
		idx = -1
		if path in data:
			for i in range(len(data)):
				if path == data[i]:
					idx = i

			if idx >= 0:
				del data[idx]
				sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')
				m.data = sdata
				m.save()

		return { key : path }

	def getResultEntryDescription(self, task):
		return "My description " + str(task.id)


class PluginManager:
	def __init__(self):
		self.plugins = []
		# Looks for plugins

		pyfiles = glob.glob(os.path.join(PLUGIN_DIRS, '*.py'))
		try:
			for file in pyfiles:
				module = __import__(os.path.basename(file)[:-3])
				# Find class derived from ProcessingPlugin
				for var in dir(module):
					if type(eval('module.' + var)) == types.ClassType:
						if var != ProcessingPlugin.__name__:
							obj = eval('module.' + var)()
							# Don't know why isinstance and issubclass not working as expected
							if hasattr(obj, 'type'):
								if obj.type == 'YOUPIPLUGIN' and obj.enable:
									self.plugins.append(obj)
							
							del obj

		except ImportError, e:
			raise PluginManagerError, "Error importing %s: %s" % (file, e)

		# Order plugins by index (useful to get a displaying order)
		self.__order()

	def __order(self):
		"""
		Order list of plugins, order by index property
		"""

		try:
			self.plugins.sort(lambda x,y: cmp(x.index, y.index))
		except AttributeError:
			raise PluginManagerError, "Unable to sort plugins by index. Missing index property."

	def getPluginByName(self, iname):
		"""
		Returns plugin object by internal name if found or None.
		"""
		for p in self.plugins:
			if p.id == iname:
				return p

		raise PluginManagerError, "No plugin with id '%s' found." % iname
