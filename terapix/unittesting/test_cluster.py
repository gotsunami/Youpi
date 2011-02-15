
import unittest, types, time
import base64, marshal, sys
#
from terapix.lib.cluster import ClusterClient, ClusterQueue

class ClusterClientTest(unittest.TestCase):
    """
    Test the ClusterClient class
    """
    def setUp(self):
        self.client = ClusterClient()

    def test_submit(self):
        self.assertRaises(NotImplementedError, self.client.submit, '')

    def test_queue(self):
        self.assertTrue(self.client.queue == None)

    def test_setQueue_type(self):
        self.assertRaises(TypeError, self.client.setQueue, 1)

    def test_setQueueVal(self):
        q = ClusterQueue()
        self.client.setQueue(q)
        self.assertTrue(self.client.queue == q)

if __name__ == '__main__':
    if len(sys.argv) == 2: 
        try: unittest.main(defaultTest = sys.argv[1])
        except AttributeError:
            print "Error. No test with that name: %s" % sys.argv[1]
    else: 
        unittest.main()

