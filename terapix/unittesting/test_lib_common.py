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

import unittest, types, sys, time
from terapix.lib.common import get_pixel_scale

class LibCommonTest(unittest.TestCase):
	"""
	Tests functions in the terapix.lib.common module
	"""
	def setUp(self):
		pass

	def test_get_pixel_scale(self):
		for k in ({'k': 0}, lambda x: x, 1, object()):
			self.assertRaises(TypeError, get_pixel_scale, k)
		self.assertRaises(IOError, get_pixel_scale, 'badimg')

if __name__ == '__main__':
	if len(sys.argv) == 2: 
		try: unittest.main(defaultTest = sys.argv[1])
		except AttributeError:
			print "Error. No test with that name: %s" % sys.argv[1]
	else: 
		unittest.main()
