##############################################################################
#
# Copyright (c) 2008-2010 Terapix Youpi development team. All Rights Reserved.
#                    Mathias Monnerville <monnerville@iap.fr>
#                    Gregory Semah <semah@iap.fr>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
##############################################################################

"""
Tests for the plugin manager
"""

import unittest, types, sys
#
from terapix.youpi.pluginmanager import PluginManager, ProcessingPlugin

class PluginManagerTest(unittest.TestCase):
	"""
	Tests the Permissions class
	"""
	def setUp(self):
		self.pm = PluginManager()

	def test_plugins(self):
		plugins = self.pm.plugins
		self.assertTrue(hasattr(self.pm, 'plugins'))
		self.assertEquals(type(plugins), types.ListType)
		for p in plugins:
			self.assertTrue(isinstance(p, ProcessingPlugin))

		#for k in ({'k': 0}, lambda x: x, 1, object()):
		#	self.assertRaises(TypeError, Permissions, k)

	def test_getPluginByName(self):
		for k in ({'k': 0}, lambda x: x, 1, object()):
			self.assertRaises(TypeError, self.pm.getPluginByName, k)


if __name__ == '__main__':
	if len(sys.argv) == 2: 
		try: unittest.main(defaultTest = sys.argv[1])
		except AttributeError:
			print "Error. No test with that name: %s" % sys.argv[1]
	else: 
		unittest.main()
