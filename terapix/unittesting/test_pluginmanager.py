
"""
Tests for the plugin manager
"""

import unittest, types, sys, time
#
from terapix.youpi.pluginmanager import ApplicationManager, ProcessingPlugin
from terapix.lib.cluster import ClusterClient
from django.http import HttpRequest

class ApplicationManagerTest(unittest.TestCase):
    """
    Tests the Permissions class
    """
    def setUp(self):
        self.pm = ApplicationManager()

    def test_init_plugins_available(self):
        self.assertTrue(len(self.pm._ApplicationManager__instances.keys()) > 0, 'No plugins available')

    def test_plugins_attr(self):
        self.assertTrue(hasattr(self.pm, 'plugins'))

    def test_plugins_ret_type(self):
        plugins = self.pm.plugins
        self.assertEquals(type(plugins), types.ListType)

    def test_plugins_ptype(self):
        plugins = self.pm.plugins
        for p in plugins:
            self.assertTrue(isinstance(p, ProcessingPlugin))

    def test_getPluginByName(self):
        self.assertRaises(TypeError, self.pm.getPluginByName, 0)

    def test_setClusterClient(self):
        self.assertRaises(TypeError, self.pm.setClusterClient, 1)

    def test_cluster_none(self):
        self.assertEqual(self.pm.cluster, None)

    def test_cluster_set(self):
        class MyCluster(ClusterClient): pass
        mc = MyCluster()
        self.pm.setClusterClient(mc)
        self.assertEqual(self.pm.cluster, mc)

class ProcessingPluginTest(unittest.TestCase):
    """
    Tests the ProcessingPlugin class
    """
    def setUp(self):
        self.plugin = ProcessingPlugin()

    def test_getUniqueCondorJobId(self):
        id = self.plugin.getUniqueCondorJobId()
        self.assertEquals(type(id), types.StringType)
        # Tests pseudo randomness
        self.assertNotEquals(id, self.plugin.getUniqueCondorJobId())

    def test_getConfigValue(self):
        for k in ({'k': 0}, lambda x: x, 1, object()):
            self.assertRaises(TypeError, self.plugin.getConfigValue, k, 'KEYWORD')
            self.assertRaises(TypeError, self.plugin.getConfigValue, [], k)

        content = ['nop nop nop', 'KEYWORD1 VALUE1']
        w = self.plugin.getConfigValue(content, 'wrongkey')
        v = self.plugin.getConfigValue(content, 'KEYWORD1')
        self.assertEquals(type(w), types.BooleanType)
        self.assertEquals(w, False)

        self.assertEquals(type(v), types.StringType)
        self.assertEquals(v, 'VALUE1')
        self.assertEquals(self.plugin.getConfigValue([], 'key'), False)

    def test_reports(self):
        self.assertEquals(type(self.plugin.reports()), types.ListType)

    def test_getUserResultsOutputDir_param_request(self):
        req = HttpRequest()
        self.assertRaises(TypeError, self.plugin.getUserResultsOutputDir, 0)        # request

    def test_getUserResultsOutputDir_param_oldpath(self):
        req = HttpRequest()
        req.user = type('User', (object,), {'username': 'user'})()
        self.assertRaises(TypeError, self.plugin.getUserResultsOutputDir, req, 1)   # oldPath

    def test_getUserResultsOutputDir_param_oldusername(self):
        req = HttpRequest()
        self.assertRaises(TypeError, self.plugin.getUserResultsOutputDir, req, 'path', 0)   # oldUserName

    def test_getUserResultsOutputDir_param_missing_oldusername(self):
        req = HttpRequest()
        self.assertRaises(TypeError, self.plugin.getUserResultsOutputDir, req, 'path')  # Missing oldUserName

    def test_getUserResultsOutputDir_ret_type(self):
        req = HttpRequest()
        req.user = type('User', (object,), {'username': 'user'})()
        res = self.plugin.getUserResultsOutputDir(req)
        self.assertEquals(type(res), types.StringType)

    def test_getUserResultsOutputDir_ret_value(self):
        req = HttpRequest()
        req.user = type('User', (object,), {'username': 'user'})()
        res = self.plugin.getUserResultsOutputDir(req, '/my/path/olduser/', 'olduser')
        self.assertEquals(res, '/my/path/user/')

    def test_setDefaultCleanupFiles(self):
        for k in ([1], lambda x: x, 1, object()):
            self.assertRaises(TypeError, self.plugin.setDefaultCleanupFiles, k)

        ud = self.plugin.setDefaultCleanupFiles({})
        self.assertEquals(type(ud), types.DictType)
        self.assertTrue(ud.has_key('RemoveFiles'))
        self.assertEquals(type(ud['RemoveFiles']), types.ListType)
        for pattern in ud['RemoveFiles']:
            self.assertEquals(type(pattern), types.StringType)

    def test_getConfigFileContent(self):
        pass


if __name__ == '__main__':
    if len(sys.argv) == 2: 
        try: unittest.main(defaultTest = sys.argv[1])
        except AttributeError:
            print "Error. No test with that name: %s" % sys.argv[1]
    else: 
        unittest.main()
