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

	fixtures = ['test_user', 'test_ingestion', 'test_instrument', 'test_channel', 'test_image', 'test_tag']

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

	def test_get_images_from_tags(self):
		self.client.login(username='user1', password='youpi')
		response = self.client.post(reverse('terapix.youpi.cviews.tags.get_images_from_tags'), {'Tags': '[\'tag1\']'})
		tagList = json.decode(response.content)
		self.assertEquals(type(tagList),types.DictType)
		for t in ['fields', 'data', 'hidden']:
			self.assertTrue(tagList.has_key(t))
			self.assertEquals(type(tagList[t]),types.ListType)

	def test_save_tag(self):
		self.client.login(username='user1', password='youpi')
		response = self.client.post(reverse('terapix.youpi.cviews.tags.save_tag'), {
		'Name': 'tag5',
		'Comment': '',
		'Style': 'background-color: rgb(64, 150, 238); color:white; border:medium none -moz-use-text-color;'
		})

		save = json.decode(response.content)
		self.assertEquals(type(save), types.DictType)
		self.assertTrue(save.has_key('saved'))
		self.assertEquals(type(save['saved']), types.StringType)

		response = self.client.post(reverse('terapix.youpi.cviews.tags.save_tag'), {
		'Name': 'tag1',
		'Comment': '',
		'Style': 'background-color: rgb(64, 150, 238); color:white; border:medium none -moz-use-text-color;'
		})

		error = json.decode(response.content)
		self.assertEquals(type(error), types.DictType)
		self.assertTrue(error.has_key('Error'))
		self.assertEquals(type(error['Error']), types.StringType)

		#FIXME function needs one more test to be done for a user with no add_tag permissions, need new fixtures for this

	def test_update_tag(self):
		self.client.login(username='user1', password='youpi')
		response = self.client.post(reverse('terapix.youpi.cviews.tags.update_tag'), {
		'Name': 'tag-toto', 
		'NameOrig': 'tag1', 
		'Comment': '', 
		'Style': 'background-color: rgb(64, 150, 238); color:white; border:medium none -moz-use-text-color;'
		})
		update = json.decode(response.content)
		self.assertEquals(type(update),types.DictType)
		for i in ['updated', 'oldname']:
			self.assertTrue(update.has_key(i))
			self.assertEquals(type(update[i]), types.StringType)
		
		self.assertTrue(update.has_key('success'))
		self.assertEquals(type(update['success']), types.BooleanType)

	def test_delete_tag(self):
		self.client.login(username='user1', password='youpi')
		response = self.client.post(reverse('terapix.youpi.cviews.tags.delete_tag'), {'Name': 'tag1'})
		dtags = json.decode(response.content)
		self.assertTrue(type(dtags), types.DictType)
		for k in ['success', 'deleted']:
			self.assertTrue(dtags.has_key(k))
			self.assertEquals(type(dtags['deleted']),types.StringType)
			self.assertEquals(type(dtags['success']),types.BooleanType)

		response = self.client.post(reverse('terapix.youpi.cviews.tags.delete_tag'), {'Name': 'toto'})
		dtags = response.content
		self.assertEquals(type(dtags), types.StringType)

	def test_tag_mark_images(self):
		self.client.login(username='user1', password='youpi')
		response = self.client.post(reverse('terapix.youpi.cviews.tags.tag_mark_images'),{
		'Tags': '[\'toto\']',
		'IdList': '[\'1\',\'2\',\'3\']'
		})
		
		self.assertEquals(type(response.content), types.StringType)

	def test_tag_unmark_images(self):
		self.client.login(username='user1', password='youpi')
		response = self.client.post(reverse('terapix.youpi.cviews.tags.tag_unmark_images'),{
		'Tags': '[\'tag1\']',
		'IdList': '[\'1\',\'2\']'
		})
		self.assertEquals(type(response.content), types.StringType) 

if __name__ == '__main__':
	unittest.main()
	if len(sys.argv) == 2:
		try: unittest.main(defaultTest = sys.argv[1])
		except AttributeError:
			print "Error. No test with that name: %s" % sys.argv[1]
	else:
		unittest.main()
