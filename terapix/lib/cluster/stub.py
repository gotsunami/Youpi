"""
:mod:`stub` --- Stub classes for unit testing
=============================================

This library provides convenient stub classes, suitable for using with unit tests.
"""

# vim: set ts=4

import types, time, os.path
import os, string, re
import xml.dom.minidom as dom
import base64, marshal
#
from terapix.lib.cluster import ClusterClient
from terapix.lib.cluster.condor import CondorJob, CondorQueue

class StubCondorQueue(CondorQueue):
    """
    .. versionadded:: 0.7.1

    Fake Handler of a Condor processing queue. Used as default queue by the
    :class:`~terapix.lib.cluster.stub.StubCondorClient` class.

    Constructor pamareters have no effects.
    """
    def __init__(self, envPath = None, globalPool = False):
        CondorQueue.__init__(self, envPath, globalPool)

    def getJobs(self):
        """
        Override CondorQueue.getJobs() in order to keep only Youpi-related jobs.
        """
        youpiJobs = [
            CondorJob(RemoteHost='host1', JobStatus=2, ClusterId=1024, ProcId=0), 
            CondorJob(RemoteHost='host2', JobStatus=0, ClusterId=1024, ProcId=1)
        ]
        return tuple(youpiJobs), len(youpiJobs)

class StubCondorClient(ClusterClient):
    """
    .. versionadded:: 0.7.1

    Fake implementation (stub) of a Condor client inheriting the :class:`~terapix.lib.cluster.ClusterClient` class, 
    suitable for unit tests. This class uses a :class:`~terapix.lib.cluster.stub.StubCondorQueue` 
    object for its default queue::

        manager = ApplicationManager()
        manager.setClusterClient(StubCondorClient()) 
        jobs, jobCount = manager.cluster.queue.getJobs()
    """
    def __init__(self):
        CondorClient.__init__(self)
        self.setQueue(StubCondorQueue())

    def submit(self, filepath, shell_submit=None):
        """
        Submit a job on the cluster. *filepath* and *shell_submit* are ignored. Raises no 
        exception at all.

        Always return a tuple ``("1", "1024")`` to state that 1 job has been 
        successfully submitted with a cluster Id of 1024.
        """
        return ("1", "1024")

    def getStatus(self):
        """
        Returns a list of all available Condor nodes and status. Always returns
        the following value:: 
        
            [["node 1", "Idle"], ["node 2", "Running"]].
        """
        return [["node 1", "Idle"], ["node 2", "Running"]]

