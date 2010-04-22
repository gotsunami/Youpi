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
Tests for coordinates converting functions
"""

import unittest, types
from terapix.lib import coordconvert as cv
import re

class AlphaTest(unittest.TestCase):
	"""
	Tests the Alpha class
	"""
	def setUp(self):
		pass

	def test_deg_to_sex(self):
		self.assertRaises(TypeError, cv.Alpha.deg_to_sex, 'x')
		self.assertRaises(TypeError, cv.Alpha.deg_to_sex, ['a','b'])
		self.assertRaises(ValueError, cv.Alpha.deg_to_sex, 400)
		self.assertRaises(ValueError, cv.Alpha.deg_to_sex, -2.)

		# Output
		g = cv.Alpha.deg_to_sex(245.34)
		k = re.match(r'^(\d{2})\:(\d{2})\:(\d{2}\.\d{2})$',g)
		self.assertTrue(type(k.group()), types.StringType)
		self.assertTrue(int(k.group(1)),types.IntType)
		self.assertTrue(int(k.group(2)),types.IntType)
		self.assertTrue(float(k.group(3)),types.FloatType)

	def test_sex_to_deg(self):
		for k in (lambda x: x, 3, object()):
			self.assertRaises(TypeError, cv.Alpha.sex_to_deg, k)

		for l in (lambda x: x, 3, object()):
			self.assertRaises(TypeError, cv.Alpha.sex_to_deg, 'toto',l)
	
		self.assertRaises(ValueError, cv.Alpha.sex_to_deg, 'x')
		self.assertRaises(ValueError, cv.Alpha.sex_to_deg, '')
		self.assertRaises(ValueError, cv.Alpha.sex_to_deg, '13/24/31.32',':')
		self.assertRaises(ValueError, cv.Alpha.sex_to_deg, '13:24:31.32','/')
		self.assertRaises(ValueError, cv.Alpha.sex_to_deg, '42:24:31.32')
		self.assertRaises(ValueError, cv.Alpha.sex_to_deg, '13:61:31.32')
		self.assertRaises(ValueError, cv.Alpha.sex_to_deg, '13:24:1.2')
		self.assertRaises(ValueError, cv.Alpha.sex_to_deg, '13:24:31.34322')

		# Output
		g = cv.Alpha.sex_to_deg('13:20:00.00')
		self.assertTrue(g, types.FloatType)

class DeltaTest(unittest.TestCase):
	"""
	Tests the Delta class
	"""
	def setUp(self):
		pass

	def test_deg_to_sex(self):
		self.assertRaises(TypeError,cv.Delta.deg_to_sex, 'x')
		self.assertRaises(TypeError, cv.Delta.deg_to_sex, ['a','b'])
		self.assertRaises(ValueError, cv.Delta.deg_to_sex, 100)
		self.assertRaises(ValueError, cv.Delta.deg_to_sex, -91.)

		# Output
		g = cv.Delta.deg_to_sex(45.234)
		k = re.match(r'^[\+|\-](\d{2})\:(\d{2})\:(\d{2}\.\d)$',g)
		self.assertTrue(type(k.group()), types.StringType)
		self.assertTrue(int(k.group(1)),types.IntType)
		self.assertTrue(int(k.group(2)),types.IntType)
		self.assertTrue(float(k.group(3)),types.FloatType)

	def test_sex_to_deg(self):
		for k in (lambda x: x, 3, object()):
			self.assertRaises(TypeError, cv.Delta.sex_to_deg, k)

		for l in (lambda x: x, 3, object()):
			self.assertRaises(TypeError, cv.Delta.sex_to_deg, 'toto',l)
	
		self.assertRaises(ValueError, cv.Delta.sex_to_deg, 'x')
		self.assertRaises(ValueError, cv.Delta.sex_to_deg, '')
		self.assertRaises(ValueError, cv.Delta.sex_to_deg, '13/24/31.32',':')
		self.assertRaises(ValueError, cv.Delta.sex_to_deg, '13:24:31.32','/')
		self.assertRaises(ValueError, cv.Delta.sex_to_deg, '42:24:31.32')
		self.assertRaises(ValueError, cv.Delta.sex_to_deg, '13:61:31.32')
		self.assertRaises(ValueError, cv.Delta.sex_to_deg, '13:24:1.2')
		self.assertRaises(ValueError, cv.Delta.sex_to_deg, '13:24:31.34322')

		# Output
		g = cv.Delta.sex_to_deg('-13:20:00.0')
		self.assertTrue(g, types.FloatType)


if __name__ == '__main__':
	unittest.main()
	if len(sys.argv) == 2:
		try: unittest.main(defaultTest = sys.argv[1])
		except AttributeError:
			print "Error. No test with that name: %s" % sys.argv[1]
	else:
		unittest.main()
