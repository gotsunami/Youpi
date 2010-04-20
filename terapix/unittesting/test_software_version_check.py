##############################################################################
#
# copyright (c) 2008-2010 terapix youpi development team. all rights reserved.
#                    mathias monnerville <monnerville@iap.fr>
#                    gregory semah <semah@iap.fr>
#
# this program is free software; you can redistribute it and/or
# modify it under the terms of the gnu general public license
# as published by the free software foundation; either version 2
# of the license, or (at your option) any later version.
#
##############################################################################

import unittest, types, random
from django.test.client import Client
from terapix.exceptions import *
from terapix.script import soft_version_check as svc
from django.conf import settings

class testsvcscript(unittest.TestCase):
	def setup(self):
		self.client = Client()

	def test_getNowDateTime(self):
		g = svc.getNowDateTime()
		self.assertTrue(type(g) == types.StringType)

	def test_process(self):
		self.assertRaises(TypeError, svc.process, ['asdf','afa'])
		self.assertRaises(TypeError, svc.process, 'erwgw')

if __name__ == '__main__':
	unittest.main()

