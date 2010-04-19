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
from terapix.lib.cluster import condor

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
		#selbf.csf = condor.YoupiCondorCSF()
		pass

	def test_init(self):
		pass

if __name__ == '__main__':
	unittest.main()
