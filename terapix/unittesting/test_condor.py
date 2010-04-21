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

import unittest, types
import base64, marshal
#
from terapix.lib.cluster import condor
from terapix.youpi.models import CondorNodeSel
#
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.http import QueryDict
from django.test import TestCase

class CondorCSFTest(unittest.TestCase):
	"""
	Tests the CondorCSF class
	"""
	def setUp(self):
		self.csf = condor.CondorCSF()

	def test_getSubmitFilePath(self):
		for k in (lambda x: x, 3, object()):
			self.assertRaises(TypeError, self.csf.getSubmitFilePath, k)
		# Output
		self.assertTrue(type(self.csf.getSubmitFilePath('mat')) == types.StringType)

	def test_getLogFilenames(self):
		for k in (lambda x: x, 3, object()):
			self.assertRaises(TypeError, self.csf.getLogFilenames, k)
		# Output
		logs = self.csf.getLogFilenames('jobs')
		self.assertTrue(type(logs) == types.DictType)
		for name in ('out', 'log', 'error'):
			self.assertTrue(name in logs.keys())

	def test_init(self):
		self.assertRaises(TypeError, condor.CondorCSF, 3)

	def test_updateData(self):
		csf = condor.CondorCSF()
		csf.updateData()
		for name in ('description', 'exec', 'transfer', 'more', 'requirements', 'queues', 'out', 'log', 'error'):
			self.assertTrue(name in csf.data.keys(), "Missing '%s' key in returned dictionary" % name )
			self.assertTrue(type(csf.data[name]) == types.StringType, "'%s' must be a string" % name)

	def test_addQueue(self):
		for k in (lambda x: x, 1, object()):
			self.assertRaises(TypeError, self.csf.addQueue, queue_args = k)
		for k in ('a', lambda x: x, 1, object()):
			self.assertRaises(TypeError, self.csf.addQueue, queue_env = k)
		self.assertRaises(TypeError, self.csf.addQueue, queue_env = {'key': 2})
		self.assertRaises(TypeError, self.csf.addQueue, queue_env = {2: 'val'})

		# Output
		# With arguments only
		q = self.csf.addQueue(queue_args = "arg1 arg2")
		self.assertTrue(type(q) == types.DictType)
		self.assertTrue(q.has_key('args'))

		# With env only
		q = self.csf.addQueue(queue_env = {'path': 'toto'})
		self.assertTrue(type(q) == types.DictType)
		self.assertTrue(q.has_key('env'))

	def test_removeQueue(self):
		# New instance to force zeroing the queue
		csf = condor.CondorCSF()
		for k in (lambda x: x, 'a', object()):
			self.assertRaises(TypeError, self.csf.removeQueue, k)
		# Should break: empty queue
		self.assertRaises(IndexError, self.csf.removeQueue, 10)

	def test_write(self):
		self.assertRaises(TypeError, self.csf.write, 1)

	def test_getSubmissionFileContent(self):
		content = self.csf.getSubmissionFileContent()
		self.assertTrue(type(content) == types.StringType)

	def test_setExecutable(self):
		for k in (lambda x: x, 1, object()):
			self.assertRaises(TypeError, self.csf.setExecutable, k)

	def test_setTransferInputFiles(self):
		for k in ({}, 'a', lambda x: x, 1, object()):
			self.assertRaises(TypeError, self.csf.setTransferInputFiles, k)
		self.assertRaises(TypeError, self.csf.setTransferInputFiles, [1, 'a'])


class YoupiCondorCSFTest(unittest.TestCase):
	"""
	Tests the YoupiCondorCSF class
	"""
	def setUp(self):
		self.request = HttpRequest()
		# TODO: fix this. getRequirementString() is complex and needs info in DB
		# This hack is used to test the getSubmissionFileContent function
		class LightYoupiCondorCSF(condor.YoupiCondorCSF):
			def getRequirementString(self):
				return 'req'
		self.csf = LightYoupiCondorCSF(self.request, 'id')

	def test_init(self):
		self.assertRaises(TypeError, condor.YoupiCondorCSF, 'a', 'id')
		self.assertRaises(TypeError, condor.YoupiCondorCSF, self.request, 1)
		self.assertTrue(self.csf.id == 'id')
		self.assertTrue(self.csf.request == self.request)
	
	def test_getSubmissionFileContent(self):
		content = self.csf.getSubmissionFileContent()
		self.assertTrue(type(content) == types.StringType)
		# Those keys must have non-empty values
		for k in ('more', 'requirements'):
			self.assertTrue(type(self.csf.data[k]) == types.StringType)
			self.assertTrue(len(self.csf.data[k]) > 0)

	def test_setTransferInputFiles(self):
		for k in ({}, 'a', lambda x: x, 1, object()):
			self.assertRaises(TypeError, self.csf.setTransferInputFiles, k)

	def test_getRequirementString(self):
		"""
		Fake test for the moment
		"""
		self.assertTrue(type(self.csf.getRequirementString()) == types.StringType)

class CondorMiscFunctionTest(TestCase):
	"""
	Misc functions tests in this module
	"""
	fixtures = ['test_user']

	def setUp(self):
		pass

	def test_get_condor_status(self):
		stat = condor.get_condor_status()
		self.assertTrue(type(stat) == types.ListType)
		for vm in stat:
			self.assertTrue(len(vm) == 2)
			self.assertTrue(type(vm[0]) == types.StringType)
			self.assertTrue(type(vm[1]) == types.StringType)

	def test_get_requirement_string(self):
		for k in ({}, lambda x: x, 1, object()):
			self.assertRaises(TypeError, condor.get_requirement_string, k, [])
		for k in ('', {}, lambda x: x, 1, object()):
			self.assertRaises(TypeError, condor.get_requirement_string, '', k)

		self.assertRaises(ValueError, condor.get_requirement_string, 'MEM,G,1;G', [])		# Wrong ';'
		self.assertRaises(ValueError, condor.get_requirement_string, 'BADKEY,G,1,G', [])	# Wrong 'BADKEY'
		self.assertRaises(ValueError, condor.get_requirement_string, 'MEM,g,1,G', [])		# Wrong 'g'
		self.assertRaises(ValueError, condor.get_requirement_string, 'MEM,G,1,t', [])		# Wrong 't'

		# vms must be a list of lists
		self.assertRaises(TypeError, condor.get_requirement_string, 'MEM,G,1,T', ['node1', 'Idle'])
		self.assertRaises(TypeError, condor.get_requirement_string, 'MEM,G,1,T', [[1, 'Idle']])

		# Output
		req = condor.get_requirement_string('MEM,G,1,G', [])
		self.assertTrue(type(req) == types.StringType)
		self.assertTrue(req.startswith('Requirements = ('))
		self.assertTrue(req.endswith(')'))

	def test_get_requirement_string_from_selection(self):
		for k in ({}, lambda x: x, 1, object()):
			self.assertRaises(TypeError, condor.get_requirement_string_from_selection, k)
		self.assertRaises(condor.CondorError, condor.get_requirement_string_from_selection, '__nofound__')

		sel = CondorNodeSel.objects.create(user = User.objects.all()[0], label = 'test', is_policy = False)
		sel.nodeselection = base64.encodestring(marshal.dumps(['slot1@node1', 'slot2@node1'])).replace('\n', '')
		sel.save()
		req = condor.get_requirement_string_from_selection('test')
		self.assertTrue(type(req) == types.StringType)
		self.assertTrue(req.startswith('Requirements = (('))
		self.assertTrue(req.endswith('))'))
		self.assertTrue(req == 'Requirements = ((Name == "slot1@node1" || Name == "slot2@node1"))')


if __name__ == '__main__':
	unittest.main()
