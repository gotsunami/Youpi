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
Tests for the built-in Condor library
"""

import unittest, types, sys, os, re
#
from terapix.youpi import auth
from terapix.youpi.auth import Permissions, read_proxy, write_proxy
from terapix.youpi.models import Tag, Instrument
from terapix.exceptions import PermissionsError 
#
from django.contrib.auth.models import User
from django.db import models 
from django.http import HttpRequest
from django.test import TestCase

class PermissionsTest(unittest.TestCase):
	"""
	Tests the Permissions class
	"""
	def setUp(self):
		self.perm = Permissions('640')

	def test_init(self):
		for k in ({'k': 0}, lambda x: x, 1, object()):
			self.assertRaises(TypeError, Permissions, k)
		self.assertRaises(ValueError, Permissions, '124')
		self.assertRaises(ValueError, Permissions, '027')
		for k in ('user', 'group', 'others'):
			self.assertTrue(hasattr(Permissions('440'), k))

		p = Permissions('440')
		self.assertTrue(p.user.read == True)
		self.assertTrue(p.user.write == False)
		self.assertTrue(p.group.read == True)
		self.assertTrue(p.group.write == False)
		self.assertTrue(p.others.read == False)
		self.assertTrue(p.others.write == False)

		p = Permissions('644')
		self.assertTrue(p.user.write == True)
		self.assertTrue(p.others.read == True)

	def test_toJSON(self):
		json = self.perm.toJSON()
		self.assertTrue(type(json) == types.DictType)
		for k in ('user', 'group', 'others'):
			self.assertTrue(json.has_key(k))
			self.assertTrue(type(json[k]) == types.DictType)
			for m in ('read', 'write'):
				self.assertTrue(json[k].has_key(m))
				self.assertTrue(type(json[k][m]) == types.IntType)

	def test_toOctal(self):
		o = self.perm.toOctal()
		self.assertTrue(type(o) == types.StringType)
		self.assertTrue(len(o) == 3)
		self.assertTrue(re.match(r'^\d{3}$', o))
		bits = [int(b) for b in re.findall(r'\d', o)]
		for m in bits:
			self.assertTrue(m in auth.bits_range)

class AuthMiscFunctionTest(TestCase):
	"""
	Misc functions tests in auth module
	"""
	fixtures = ['test_user', 'test_tags']

	def setUp(self):
		# Build a suitable request for the *_proxy() functions
		self.request = HttpRequest()
		self.request.user = User.objects.all()[0]

	def test_read_proxy(self):
		tags = Tag.objects.all()
		inst = Instrument.objects.create(name = 'test')
		inst.save()

		for k in ({'k': 0}, lambda x: x, 1, object()):
			self.assertRaises(TypeError, read_proxy, k, 1)
			self.assertRaises(TypeError, read_proxy, self.request, k)

		# Instrument models don't support permissions
		self.assertRaises(PermissionsError, read_proxy, self.request, Instrument.objects.all())

		# Output
		# Tests 'user' perm bit with 'user1'
		data, filtered = read_proxy(self.request, tags)
		self.assertFalse(filtered)
		self.assertTrue(len(data) == tags.count())

		# Tests 'group' perm bit with 'user2'
		u = self.request.user
		self.request.user = User.objects.filter(username = 'user2')[0]
		data, filtered = read_proxy(self.request, tags)
		self.assertTrue(filtered)
		self.assertTrue(len(data) == 2) # tag4 matches (440) (group bit); tag3 matches (others bit)
		for i in range(2):
			self.assertTrue(data[i].name in ('tag3', 'tag4'))

		# Tests 'others' perm bit with 'user3'
		self.request.user = User.objects.filter(username = 'user3')[0]
		data, filtered = read_proxy(self.request, tags)
		self.assertTrue(filtered)
		self.assertTrue(len(data) == 1) # Only tag3 matches (444)
		self.assertTrue(data[0].name == 'tag3')
		self.request = u

if __name__ == '__main__':
	if len(sys.argv) == 2: 
		try: unittest.main(defaultTest = sys.argv[1])
		except AttributeError:
			print "Error. No test with that name: %s" % sys.argv[1]
	else: 
		unittest.main()

