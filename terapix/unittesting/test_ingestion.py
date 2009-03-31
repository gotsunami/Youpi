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

import unittest
from terapix.script.ingestion import *

clog = StringBuffer()

def showPart(title):
	"""
	Display title to stdout
	"""
	print "%s %s %s" % ('-' * 11, title, '-' * 10)

class TestDB(unittest.TestCase):
	def __init__(self, methodName='runTest'):
		unittest.TestCase.__init__(self, methodName)
		showPart('MYSQL')

		db = DB(host = DATABASE_HOST,
				user = DATABASE_USER,
				passwd = DATABASE_PASSWORD,
				db = DATABASE_NAME)
		self.g = DBGeneric(db.con)

	def setUp(self):
		pass

	def testSetupDB(self):
		"Setting up test db"
		self.g.execute("drop database if exists test");
		self.g.execute("create database test");

class TestIngestion(unittest.TestCase):
	showPart('INGESTION')
	def setUp(self):
		pass

#	def testdebug(self):
#		try:
#		global clog
#		self.assertRaises(TypeError, debug, 'msg', INFO)
#		except NameError:
#			# global clog not found
#			pass

	def testb(self):
		pass

#	def testchoice(self):
#		"Test the choice"
#		element = random.choice(self.seq)
#		self.assert_(element in self.seq)
#
#	def testsample(self):
#		self.assertRaises(ValueError, random.sample, self.seq, 20)
#		for element in random.sample(self.seq, 5):
#			self.assert_(element in self.seq)

if __name__ == '__main__':
	unittest.main()
