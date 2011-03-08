"""
Tests for the Condor Stub library
"""

import unittest, types, time
import base64, marshal, sys
from mock import Mock
#
from terapix.lib.cluster import condor
from terapix.lib.cluster.stub import StubCondorQueue, StubCondorClient
from terapix.lib.cluster.condor import CondorJob
#

class StubCondorQueueTest(unittest.TestCase):
    """
    Tests the StubCondorQueue class
    """
    def setUp(self):
        self.jobs, self.count = StubCondorQueue().getJobs()

    def test_getJobs_length(self):
        self.assertTrue(len(self.jobs) == 2)

    def test_getJobs_count(self):
        self.assertTrue(self.count == 2)

    def test_getJobs_type(self):
        for j in self.jobs:
            self.assertTrue(isinstance(j, CondorJob))

class StubCondorClientTest(unittest.TestCase):
    """
    Tests the StubCondorClient class
    """
    def setUp(self):
        self.c = StubCondorClient()

    def test_submit_return_type(self):
        self.assertEqual(type(self.c.submit(1,2)), types.TupleType)

    def test_getStatus_return_type(self):
        self.assertEqual(type(self.c.getStatus()), types.ListType)

    def test_getStatus_return_members(self):
        s = self.c.getStatus()
        for node in s:
            self.assertEqual(type(node), types.ListType)
            self.assertTrue(len(node) == 2)

if __name__ == '__main__':
    if len(sys.argv) == 2: 
        try: unittest.main(defaultTest = sys.argv[1])
        except AttributeError:
            print "Error. No test with that name: %s" % sys.argv[1]
    else: 
        unittest.main()
