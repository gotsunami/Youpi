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

import unittest
from django.test.client import Client
from terapix.exceptions import *

def showPart(title):
	"""
	Display title to stdout
	"""
	print "%s %s %s" % ('-' * 11, title, '-' * 10)

#class FakePlugin(ProcessingPlugin):
#	def __init__(self):
#		ProcessingPlugin.__init__(self)
#
#	def main(self):
#		return 'my result'

class Test_processing_plugin(unittest.TestCase):
	def setUp(self):
		self.client = Client()

	def testBadInputKeys(self):
		# No POST data
		self.assertRaises(PostDataError, self.client.post, '/youpi/process/plugin/', {})
		self.assertRaises(PostDataError, self.client.post, '/youpi/process/plugin/', {'Plugi': 'name'})

	def testBadPluginName(self):
		#self.assertRaises(PluginManagerError, self.client.post, '/youpi/process/plugin/', {'Plugin': '_bad_name_', 'Method': 'process'})
		pass

	def testBadMethodCall(self):
		#self.assertRaises(PluginEvalError, self.client.post, '/youpi/process/plugin/', {'Plugin': 'skel', 'Method': 'badmethodcall'})
		pass

#	def testReturnData(self):
#		# return HttpResponse(str({'result' : res}), mimetype = 'text/plain')
#		self.assertRaises(PluginEvalError, self.client.post, '/youpi/process/plugin/', {'Plugin': 'skel', 'Method': 'badmethodcall'})

if __name__ == '__main__':
	unittest.main()

