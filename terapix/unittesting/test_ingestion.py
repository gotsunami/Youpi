import unittest
from terapix.script.ingestion import *

class TestIngestion(unittest.TestCase):
	def setUp(self):
		clog = StringBuffer()
		pass

	def testdebug(self):
		try:
			self.assertRaises(TypeError, debug, 'msg', INFOS)
		except NameError:
			# global clog not found
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
