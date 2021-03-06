"""
Tests for the built-in Condor library
"""

import unittest, types, time
import base64, marshal, sys
from mock import Mock
#
from terapix.lib.cluster import condor
from terapix.lib.cluster.condor import CondorClient, YoupiCondorClient
from terapix.youpi.models import CondorNodeSel
from terapix.exceptions import *
#
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.http import QueryDict
from django.test import TestCase
from django.conf import settings

class CondorCSFTest(unittest.TestCase):
    """
    Tests the CondorCSF class
    """
    def setUp(self):
        self.csf = condor.CondorCSF()

    def test_getSubmitFilePath(self):
        for k in (lambda x: x, 3, object()):
            self.assertRaises(TypeError, self.csf.getSubmitFilePath, k)
        self.assertRaises(TypeError, self.csf.getSubmitFilePath, 'scamp', username=1, plugin_id='scamp')
        self.assertTrue(type(self.csf.getSubmitFilePath('mat')) == types.StringType)
        self.assertTrue(self.csf.getSubmitFilePath('mat').startswith(settings.BASE_TEMP_DIR))

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
        for k in ({'k': 0}, 'a', lambda x: x, 1, object()):
            self.assertRaises(TypeError, self.csf.setTransferInputFiles, k)
        self.assertRaises(TypeError, self.csf.setTransferInputFiles, [1, 'a'])


class YoupiCondorCSFTest(TestCase):
    """
    Tests the YoupiCondorCSF class
    """
    fixtures = ['test_user']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = User.objects.all()[0]
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
        self.assertTrue(type(content) in types.StringTypes)
        # Those keys must have non-empty values
        for k in ('more', 'requirements'):
            self.assertTrue(type(self.csf.data[k]) == types.StringType)
            self.assertTrue(len(self.csf.data[k]) > 0)

    def test_setTransferInputFiles(self):
        for k in ({'k': 0}, 'a', lambda x: x, 1, object()):
            self.assertRaises(TypeError, self.csf.setTransferInputFiles, k)

    def test_getRequirementString(self):
        """
        Fake test for the moment
        """
        self.assertTrue(type(self.csf.getRequirementString()) in types.StringTypes)

class CondorMiscFunctionTest(TestCase):
    """
    Misc functions tests in this module
    """
    fixtures = ['test_user']

    def setUp(self):
        # Build a fake rule for some tests
        nodesel = [u'slot1@mix18.clic.iap.fr', u'slot2@mix18.clic.iap.fr']
        sel = CondorNodeSel.objects.create(
            user = User.objects.all()[0], 
            label = '12@mix18', 
            is_policy = False,
            nodeselection = base64.encodestring(marshal.dumps(nodesel))
        )
        sel.save()

    def test_get_requirement_string(self):
        for k in ({'k': 0}, lambda x: x, 1, object()):
            self.assertRaises(TypeError, condor.get_requirement_string, k, [])
        for k in ('', {'k': 0}, lambda x: x, 1, object()):
            self.assertRaises(TypeError, condor.get_requirement_string, '', k)

        self.assertRaises(ValueError, condor.get_requirement_string, 'MEM,G,1;G', [])       # Wrong ';'
        self.assertRaises(ValueError, condor.get_requirement_string, 'BADKEY,G,1,G', [])    # Wrong 'BADKEY'
        self.assertRaises(KeyError, condor.get_requirement_string, 'MEM,g,1,G', [])     # Wrong 'g'
        self.assertRaises(ValueError, condor.get_requirement_string, 'MEM,G,1,t', [])       # Wrong 't'

        # vms must be a list of lists
        self.assertRaises(TypeError, condor.get_requirement_string, 'MEM,G,1,T', ['node1', 'Idle'])
        self.assertRaises(TypeError, condor.get_requirement_string, 'MEM,G,1,T', [[1, 'Idle']])
        condor.get_requirement_string('SLT,B,12@mix18', [])

        # Output
        req = condor.get_requirement_string('MEM,G,1,G', [])
        self.assertTrue(type(req) == types.StringType)
        self.assertTrue(req.startswith('Requirements = ('))
        self.assertTrue(req.endswith(')'))

    def test_get_requirement_string_from_selection(self):
        for k in ({'k': 0}, lambda x: x, 1, object()):
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

class CondorQueueTest(unittest.TestCase):
    """
    Tests the CondorQueue class
    """
    def setUp(self):
        pass

    def test_init(self):
        for k in ({'k': 0}, lambda x: x, 1, object()):
            self.assertRaises(TypeError, condor.CondorQueue, envPath = k)
        for k in ('a', {'k': 0}, lambda x: x, 1, object()):
            self.assertRaises(TypeError, condor.CondorQueue, globalPool = k)

    def test_getJobs(self):
        jobs = condor.CondorQueue().getJobs()
        self.assertTrue(type(jobs) == types.TupleType)
        self.assertTrue(len(jobs) == 2)
        self.assertTrue(type(jobs[0]) == types.TupleType)
        self.assertTrue(type(jobs[1]) == types.IntType)

    def test_removeJobs(self):
        for k in ({'k': 0}, lambda x: x, 1, object()):
            self.assertRaises(TypeError, condor.CondorQueue().removeJob, k)

class CondorJobTest(unittest.TestCase):
    """
    Tests the CondorJob class
    """
    def setUp(self):
        # Creates a dummy running job (jobstatus = 2)
        self.j = condor.CondorJob(a=1, b=2, JobStatus=2, JobStartDate=time.time())
        # Dummy not running job
        self.nj = condor.CondorJob(JobStatus=0, JobStartDate=time.time())

    def test_init_missing_ads(self):
        job = condor.CondorJob
        self.assertRaises(ValueError, job, a=1, b=2)

    def test_init_check_properties(self):
        self.assertTrue(self.j.a == 1)
        self.assertTrue(self.j.b == 2)
        self.assertTrue(self.j.JobStatus == 2)

    def test_isRunning_run(self):
        self.assertTrue(self.j.isRunning())

    def test_isRunning_pending(self):
        self.assertFalse(self.nj.isRunning())

    def test_getJobDuration_running_ret_type(self):
        self.assertFalse(self.nj.isRunning())

    def test_getJobDuration_repr_running(self):
        self.assertEqual(repr(self.j), '<CondorJob ??.?? is 2 on unknown>')

    def test_getJobDuration_repr_pending(self):
        self.assertEqual(repr(self.nj), '<CondorJob ??.?? is 0>')

    def test_getJobDuration_ret_format(self):
        import re
        self.assertTrue(re.match(r'^\d{2}:\d{2}:\d{2}$', self.j.getJobDuration()))

class YoupiCondorQueueTest(unittest.TestCase):
    """
    Tests the YoupiCondorQueue class
    """
    def setUp(self):
        pass
    
    def test_getJobs(self):
        jobs = condor.YoupiCondorQueue().getJobs()
        self.assertTrue(type(jobs) == types.TupleType)
        self.assertTrue(len(jobs) == 2)
        self.assertTrue(type(jobs[0]) == types.TupleType)
        self.assertTrue(type(jobs[1]) == types.IntType)
        jobs, count = jobs
        for j in jobs:
            self.assertTrue(hasattr(j, 'UserData'), 'Missing required userData attribute')

class CondorClientTest(unittest.TestCase):
    """
    Test the CondorClient class.
    """
    def setUp(self):
        self.c = CondorClient()

    def test_submit_param_file(self):
        self.assertRaises(TypeError, self.c.submit, 1)

    def test_submit_param_shell(self):
        self.assertRaises(TypeError, self.c.submit, 'toto', 1)

    def test_submit_bad_file(self):
        self.assertRaises(CondorSubmitError, self.c.submit, 'unknown')

    def test_submit_shell_call(self):
        cc = CondorClient()
        cc._shell_submit = Mock(return_value=('', '', '1 job, cluster 1024.'))
        cc.submit('file')
        self.assertTrue(cc._shell_submit.called, 'shell_submit() not called')

    def test_submit_ret_type(self):
        # condor_submit format: (3 lines)
        # Submitting job(s).
        # Logging submit event(s).
        # 1 job(s) submitted to cluster 1024.
        cc = CondorClient()
        cc._shell_submit = Mock(return_value=('', '', '1 job(s) submitted to cluster 1024.'))
        self.assertEqual(cc.submit('file'), ('1', '1024'))

    def test_getStatus_ret_type(self):
        stat = self.c.getStatus()
        self.assertTrue(type(stat) == types.ListType)

    def test_getStatus_ret_type_unit(self):
        stat = self.c.getStatus()
        for vm in stat:
            self.assertTrue(len(vm) == 2)
            self.assertTrue(type(vm[0]) == types.StringType)
            self.assertTrue(type(vm[1]) == types.StringType)


class YoupiCondorClientTest(unittest.TestCase):
    """
    Test the YoupiCondorClient class.
    """
    def setUp(self):
        self.c = YoupiCondorClient()
        self.c._shell_submit = Mock(return_value=('', '', '1 job(s) submitted to cluster 1024.'))

    def test_submit_ret_type(self):
        self.assertEqual(type(self.c.submit('file')), types.DictType)

    def test_submit_ret_key_count(self):
        self.assertTrue(self.c.submit('file').has_key('count'))

    def test_submit_ret_key_clusterId(self):
        self.assertTrue(self.c.submit('file').has_key('clusterId'))


if __name__ == '__main__':
    if len(sys.argv) == 2: 
        try: unittest.main(defaultTest = sys.argv[1])
        except AttributeError:
            print "Error. No test with that name: %s" % sys.argv[1]
    else: 
        unittest.main()

