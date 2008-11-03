# vim: set ts=4

from django.contrib.sessions.models import Session
from terapix.spica2.models import *
import glob, sys, types, re, os
import marshal, base64
from settings import *
from types import *

PLUGIN_DIRS = os.path.join(HOME, 'spica2', 'terapix', 'spica2', 'plugins')
sys.path.insert(0, PLUGIN_DIRS)
sys.path.insert(0, PLUGIN_DIRS[:-len('/plugins')])

class PluginError(Exception): pass
class PluginManagerError(Exception): pass

class Spica2Plugin: 
	type = 'SPICA2PLUGIN'

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

		return { 'count' : count, 'clusterId' : cid, 'data' : [str(s) for s in submit_content] }

	def getCondorRequirementString(self, condorHosts):
		#
		# Handle requirements from condorHosts
		# Hosts and vms must be separated from this vm@host list
		# Will build packets of (Machine == "host" && (VirtualMachineID == 1 [|| ...])) [|| ...]
		#
		reqHosts = {}
		for host in condorHosts:
			m = re.match(r'^.*?(?P<vmid>\d+)@(?P<name>.*?)$', host)
			name = m.group('name')
			vmid = m.group('vmid')
			try:
				reqHosts[name].append(vmid)
			except KeyError:
				reqHosts[name] = []
				reqHosts[name].append(vmid)

		req = '('
		for host, vms in reqHosts.iteritems():
			req += """(Machine == "%s" && (""" % host
			for vmid in vms:
				req += """VirtualMachineID == %d || """ % int(vmid)
			req = req[:-4] + ')) || '
		req = req[:-4] + ')'

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
				# Find class derived from Spica2Plugin
				for var in dir(module):
					if type(eval('module.' + var)) == types.ClassType:
						if var != Spica2Plugin.__name__:
							obj = eval('module.' + var)()
							# Don't know why isinstance and issubclass not working as expected
							if hasattr(obj, 'type'):
								if obj.type == 'SPICA2PLUGIN' and obj.enable:
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
