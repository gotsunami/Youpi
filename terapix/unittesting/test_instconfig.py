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

import unittest, types, sys, os
#
from terapix.lib.itt.instconfig import InstrumentConfig

def makeTempFile(content):
	import tempfile
	fd, path = tempfile.mkstemp()
	os.write(fd, content)
	os.close(fd)
	return path

class InstrumentConfigTest(unittest.TestCase):
	"""
	Tests the InstrumentConfig class
	"""
	def setUp(self):
		pass

	def test_init(self):
		for k in ({'k': 0}, lambda x: x, 1, object()):
			self.assertRaises(TypeError, InstrumentConfig, k)
		self.assertTrue(InstrumentConfig('file').filename == 'file')

	def test_parse(self):
		bad_input = [
			'YRUN\n', 							# Missing ^+
			'+YRUN\n YRUN,', 					# Wrong separator
			'YRUN; TOTO; TATA; TITI\n', 		# Wrong field count
			'BADKW; TOTO; TATA\n', 				# Wrong kyeword name
		]
		for content in bad_input:
			path = makeTempFile(content)
			ic = InstrumentConfig(path)
			self.assertRaises(ValueError, ic.parse)
			os.unlink(path)

		# Feeds in a valid entry to check output
		path = makeTempFile('YRUN; HIERARCH ESO OBS PROG ID; RUNID')
		ic = InstrumentConfig(path)
		map = ic.parse()
		self.assertTrue(map.has_key('YRUN'))
		self.assertTrue(map.has_key('+COPY'))
		self.assertTrue(len(map['+COPY']) == 0)
		for k in ('SRC', 'MAP'):
			self.assertTrue(map['YRUN'].has_key(k))
		os.unlink(path)

		path = makeTempFile('YRUN; HIERARCH ESO OBS PROG ID')
		ic = InstrumentConfig(path)
		map = ic.parse()
		self.assertFalse(len(map['+COPY']) > 0)
		self.assertFalse(map['YRUN'].has_key('MAP'))
		os.unlink(path)


if __name__ == '__main__':
	if len(sys.argv) == 2: 
		try: unittest.main(defaultTest = sys.argv[1])
		except AttributeError:
			print "Error. No test with that name: %s" % sys.argv[1]
	else: 
		unittest.main()

