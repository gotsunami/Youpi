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

import unittest, types, random
from django.test.client import Client
from terapix.exceptions import *
from terapix.script import grading
from django.conf import settings

class TestGradingScript(unittest.TestCase):
	def setUp(self):
		self.client = Client()
		self.res_output_dir = settings.PROCESSING_OUTPUT + 'fitsin/'

	def test_get_stats(self):
		g = grading.get_stats()
		self.assertTrue(type(g) == types.TupleType)
		for gi in g:
			self.assertTrue(type(gi) == types.TupleType)

	def test_get_grades(self):
	
		self.minilist = [random.randint(1, 15000)]
		self.maxilist = []
		for k in range(0,10):
			self.maxilist.append(random.randint(1, 15000))
	
		empty = grading.get_grades(None, None)
		self.assertTrue(type(empty) == types.ListType)
		for e in empty:
			self.assertTrue(type(e) == types.TupleType)
		
		full = grading.get_grades(self.res_output_dir, self.maxilist)
		self.assertTrue(type(full) == types.ListType)
		for f in full:
			self.assertTrue(type(f) == types.TupleType)

		self.assertRaises(TypeError, grading.get_grades, 2.34)
		self.assertRaises(TypeError, grading.get_grades, 2.34, None)
		self.assertRaises(TypeError, grading.get_grades, None, 2.34)

	def test_get_proportions(self):
		g = grading.get_proportions()
		self.assertTrue(type(g) == types.ListType)
		for gi in g:
			self.assertTrue(type(gi) == types.TupleType)



if __name__ == '__main__':
	unittest.main()

