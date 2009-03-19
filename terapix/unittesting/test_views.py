import unittest
from django.test.client import Client
from terapix.exceptions import *

def showPart(title):
	"""
	Display title to stdout
	"""
	print "%s %s %s" % ('-' * 11, title, '-' * 10)

class Test_processing_plugin(unittest.TestCase):
	def setUp(self):
		self.client = Client()

	def testBadInputKeys(self):
		# No POST data
		self.assertRaises(PostDataError, self.client.post, '/youpi/process/plugin/', {})
		self.assertRaises(PostDataError, self.client.post, '/youpi/process/plugin/', {'Plugi': 'name'})

	def testBadPluginName(self):
		self.assertRaises(PluginManagerError, self.client.post, '/youpi/process/plugin/', {'Plugin': '_bad_name_', 'Method': 'process'})

	def testBadMethodCall(self):
		self.assertRaises(PluginEvalError, self.client.post, '/youpi/process/plugin/', {'Plugin': 'skel', 'Method': 'badmethodcall'})


if __name__ == '__main__':
	unittest.main()
