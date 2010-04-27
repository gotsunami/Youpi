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

from django.test.client import Client
from terapix.exceptions import *
from django.test import TestCase
from terapix.youpi.cviews import tags as t
import unittest, types
import re
from django.http import HttpRequest,HttpResponse
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import cjson as json

class TagsTest(TestCase):
	"""
	Tests tag module
	"""

	fixtures = ['test_user', 'test_tags']

	def setUp(self):
		self.client = Client()
		self.request = HttpRequest()
		self.user = User.objects.all()[0]
		self.user.set_password('youpi')
		self.user.save()

	def test_fetch_tags(self):
		self.client.login(username='user1', password='youpi')
		response = self.client.post(reverse('terapix.youpi.cviews.tags.fetch_tags'))
		ftags = json.decode(response.content)
		self.assertTrue(type(ftags), types.DictType)
		for k in ['tags', 'filtered']:
			self.assertTrue(ftags.has_key(k))
			self.assertEquals(type(ftags['tags']),types.ListType)
			self.assertEquals(type(ftags['filtered']),types.BooleanType)

		if ftags['tags'][0]:
			self.assertEquals(type(ftags['tags'][0]), types.DictType)
			for i in ['name', 'style', 'comment', 'username', 'date']:
				self.assertTrue(ftags['tags'][0].has_key(i))
				self.assertEquals(type(ftags['tags'][0][i]), types.StringType)
	
	def test_get_tag_info(self):
		self.client.login(username='user1', password='youpi')
		response = self.client.post(reverse('terapix.youpi.cviews.tags.get_tag_info'), {'Name': 'tag1'})
 		ftags = json.decode(response.content)
 		self.assertEquals(type(ftags), types.DictType)
 		self.assertTrue(ftags.has_key('info'))
		self.assertEquals(type(ftags['info']), types.DictType)
		for i in ['name', 'style', 'comment', 'username', 'date']:
			self.assertTrue(ftags['info'].has_key(i))
			self.assertEquals(type(ftags['info'][i]), types.StringType)
		
		response = self.client.post(reverse('terapix.youpi.cviews.tags.get_tag_info'), {'Name': 'toto'})
 		ftags = json.decode(response.content)
 		self.assertEquals(type(ftags), types.DictType)
 		self.assertTrue(ftags.has_key('info'))
		self.assertEquals(len(ftags['info']), 0)


if __name__ == '__main__':
	unittest.main()
	if len(sys.argv) == 2:
		try: unittest.main(defaultTest = sys.argv[1])
		except AttributeError:
			print "Error. No test with that name: %s" % sys.argv[1]
	else:
		unittest.main()
