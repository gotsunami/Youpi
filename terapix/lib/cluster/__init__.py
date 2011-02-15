# vim: set ts=4

from terapix.lib.cluster.exceptions import *

class ClusterJob(object): 
    """
    .. versionadded:: 0.7.1

    Base abstract class for cluster jobs. Has no implementation right now.
    """
    def isRunning(self):
        """
        Returns ``True`` if the job is running.

        .. note:: Not implemented, will raise a :class:`NotImplementedError` exception.
        """
        raise NotImplementedError

    def getJobDuration(self):
        """
        Returns the job's runtime duration, formatted as a string matching HH:MM:SS 
        or ``None`` if the job has been submitted but is not running yet.

        .. note:: Not implemented, will raise a :class:`NotImplementedError` exception.
        """
        raise NotImplementedError

    def remove(self):
        """
        Remove the job from the current queue.

        .. note:: Not implemented, will raise a :class:`NotImplementedError` exception.
        """
        raise NotImplementedError

class ClusterQueue(object): 
    """
    .. versionadded:: 0.7.1

    Base abstract class for cluster jobs queue. Has no implementation right now.
    """
    def getJobs(self):
        """
        Returns a tuple of a list of current active jobs and the number of jobs is that list.

        .. note:: Not implemented, will raise a :class:`NotImplementedError` exception.
        """
        raise NotImplementedError

    def removeJob(self, job):
        """
        Remove a job from the cluster queue. Should raise a :class:`TypeError` exception 
        if *job* is not a :class:`ClusterJob` instance.

        .. note:: Not implemented, will raise a :class:`NotImplementedError` exception.
        """
        raise NotImplementedError

class ClusterClient(object):
    """
    .. versionadded:: 0.7.1

    Base cluster client abstract class definition. Cluster client related modules should 
    inherit this class. Youpi implements a :class:`~terapix.lib.cluster.condor.CondorClient` class 
    to submit jobs to the Condor cluster.
    """
    def __init__(self):
        self.__queue = None

    def submit(self, filepath, shell_submit=None):
        """
        Submit a job on the cluster. *filepath* is the absolute path to the Condor submission 
        file. The job is submitted using the ``condor_submit`` program. *shell_submit* is a 
        callable (function) to call that actually runs the shell command and return the raw data, 
        splitted into lines.

        .. note:: Not implemented, will raise a :class:`NotImplementedError` exception.
        """
        raise NotImplementedError

    @property
    def queue(self):
        """
        Job Queue in use. Defaults to ``None``.
        """
        return self.__queue

    def setQueue(self, queue):
        """
        Set the job *queue* implementation to use. Must be a :class:`ClusterQueue` 
        instance (like :class:`~terapix.lib.cluster.condor.CondorQueue` or :class:`~terapix.lib.cluster.condor.YoupiCondorQueue`) 
        or will raise a :class:`TypeError` exception.
        """
        if not isinstance(queue, ClusterQueue):
            raise TypeError, 'Must be a ClusterQueue instance'
        self.__queue = queue



