
# vim: set ts=4

from django.conf import settings
from django.contrib.sessions.models import Session
from django.http import HttpRequest
#
import glob, sys, types, re, os, string, os.path
import marshal, base64, time
import magic
from types import *
#
from terapix.youpi.auth import *
from terapix.youpi.models import *
from terapix.exceptions import *
from terapix.lib.cluster import ClusterClient
from terapix.lib.cluster.condor import YoupiCondorClient

PLUGIN_DIRS = os.path.join(settings.TRUNK, 'terapix', 'youpi', 'plugins')
sys.path.insert(0, PLUGIN_DIRS)
sys.path.insert(0, PLUGIN_DIRS[:-len('/plugins')])

class ProcessingPlugin(object): 
    """
    Base processing plugin class.
    """
    def __init__(self):
        # id must be overwritten in sub classes
        self.id = 'processingplugin'
        self.shortName = 'My short name here'
        self.optionLabel = 'My option label'
        # Default HTML template
        self.template = 'plugin_default.html'
        # Default plugin version
        self.version = '0.1'
        self.isAstromatic = False   # Part of the www.astromatic.net software suite (Scamp, Swarp, Sextractor...)

        # Plugin data (to be processed)
        self.__data = [] 
        # Used to generate rather unique item ID in processing cart
        self.itemCounter = 0

    def setDefaultCleanupFiles(self, userData):
        """
        Adds a RemoveFiles key in the userData dictionary, which is a list of files 
        to be deleted at the end of processing.

        @param userData dictionary of input data passed to the 
        wrapper processing at runtime
        @returns userData
        """
        if type(userData) != types.DictType:
            raise TypeError, "userData must be a dictionary"

        userData['RemoveFiles'] = ['*.py', '*.conf', '*.rc', '*.pyc', '*.exe', 'NOP']
        return userData

    def getUniqueCondorJobId(self):
        """
        Builds a unique Condor job Id string. Can be passed to the wrapper_processing script on 
        the cluster so that it can retreive all job information from Condor.
        @return Condor Id string
        """
        import random
        random.seed()
        return "%s:%f-%d" % (self.id, time.time(), random.randint(1, 1000000))

    def getConfigValue(self, content, keyword):
        """
        Parses all lines of content looking for a keyword.
        Content must be a list of strings.
        Blank lines are skipped. Comments starting by # are ignored
        Keyword search is case-sensitive.
        @param content list of strings
        @param keyword word search in content
        @returns keyword's value or False
        """
        if type(content) != types.ListType:
            raise TypeError, "content must be a list of strings"
        if type(keyword) != types.StringType:
            raise TypeError, "keyword must be a string"

        for line in content:
            if line.find(keyword) != -1:
                if line[-1] == '\n': line = line[:-1]
                line = re.sub(r'#.*$', '', line)
                res = [k for k in re.split(r'[ \t]', line) if len(k)]
                try: return res[1]
                except: return False

        return False

    def reports(self):
        """
        Reporting capabilities
        """

        return []

    def getUserResultsOutputDir(self, request, oldPath = None, oldUserName = None):
        """
        Builds a default output path for the user if oldPath is None.
        If oldPath (a path to a previously processed item) is a string, then attempts to 
        replace the old login name with the name of the current request owner.

        When called only with request as first parameter, returns the concatenation of 
        the first entry in the PROCESSING_OUTPUT list with the username and current plugin id.

        @param oldPath Old output path used for processing an item
        @param oldUserName Old owner of the processing
        @return The full output directory path
        """
        if not isinstance(request, HttpRequest):
            raise TypeError, "request must be an HttpRequest Django instance"
        if oldPath and (type(oldPath) != types.StringType and type(oldPath) != types.UnicodeType):
            raise TypeError, "oldPath must be a string"
        if oldUserName and (type(oldUserName) != types.StringType and type(oldUserName) != types.UnicodeType):
            raise TypeError, "oldUserName must be a string"
        if oldPath and not oldUserName:
            raise TypeError, "oldUserName must be supplied along with oldPath"

        if oldPath: return oldPath.replace(oldUserName, request.user.username)
        return os.path.join(settings.PROCESSING_OUTPUT[0], request.user.username, self.id)

    def getConfigFileContent(self, request):
        post = request.POST
        try:
            name = str(post['Name'])
            type = str(post['Type'])
        except:
            raise PluginError, "invalid post parameters %s" % post

        # updates entry
        try:
            config = ConfigFile.objects.filter(kind__name__exact = self.id, name = name, type__name = type)[0]
        except:
            raise PluginError, "no config file with that name: %s" % name

        return {'id': str(config.id), 'data': str(config.content)}


    def getConfigFileNames(self, request):
        post = request.POST
        try:
            type = str(post['Type'])
        except:
            raise PluginError, "invalid post parameters %s" % post

        # Updates entry
        dfltconfig = ConfigFile.objects.filter(kind__name__exact = self.id, name = 'default', type__name = type)
        if not dfltconfig:
            self.__saveDefaultConfigFileToDB(request)

        configs = ConfigFile.objects.filter(kind__name__exact = self.id, type__name = type)
        res = [str(config.name) for config in configs if config.name != 'default']
        # Always append 'default' config file
        res.insert(0, 'default')

        return {'configs': res}

    def getXSLParam(self):
        """
        Returns the -XSL_PARAM parameter for the command line. Note: the fistin 
        plugin does not support such a parameter.
        """
        if self.id == 'fitsin': 
            raise ValueError, "QualityFITS does not support XSL files. Bad plugin id."

        return "-XSL_URL %s.xsl" % self.id

    def importConfigFiles(self, request):
        """
        Import all configuration files in a directory. File names are matched against 
        a pattern.
        """

        post = request.POST
        try:
            path = post['Path']
            patterns = post['Patterns'].split(';')
            type = post['Type']
        except:
            raise PluginError, "invalid post parameters %s" % post

        res = {}
        MAX_FILE_SIZE = 1024 # In Kb
        STEP = 10

        files = []
        try:
            for pat in patterns:
                pfiles = glob.glob(os.path.join(path, pat))
                files.extend(pfiles)
        except:
            res['error'] = 'An error occured when looking for files in the provided path. Please check your path and try again'

        try: 
            pos = int(post['Pos'])
            total = int(post['Total'])
            skipped = int(post.get('Skipped', 0))
        except:
            # First call to this function
            # Compute total
            total = len(files);
            skipped = 0
            pos = 0

        mag = magic.open(magic.MAGIC_NONE)
        mag.load()

        res['skipped'] = skipped
        profile = request.user.get_profile()
        ctype = ConfigType.objects.filter(name = type)[0]
        kind = Processing_kind.objects.filter(name__exact = self.id)[0]
        frame = range(len(files))[pos:]
        z = 0
        for k in frame:
            if pos == total: break
            pos += 1
            z += 1
            try:
                # Check magic number. Must be equal to 'ASCII text'
                if mag.file(files[k]).find('ASCII') == -1:
                    res['skipped'] += 1
                    continue
                f = open(files[k])
                content = string.join(f.readlines(), '\n')
                base = os.path.basename(files[k])
                name = base[:base.rfind('.')]
                res['config'] = str(name)
                f.close()
            except Exception, e:
                res['error'] = str(e)
                break

            try:
                # Updates entry
                m = ConfigFile.objects.filter(kind = kind, name = name, type = ctype)[0]
                m.content = content
            except:
                # ... or inserts a new one
                m = ConfigFile(kind = kind, name = name, content = content, user = request.user, type = ctype, mode = profile.dflt_mode, group = profile.dflt_group)

            success = write_proxy(request, m)
            if z > STEP: break

        res['total'] = total
        res['pos'] = pos 
        if total == 0: res['percent'] = 0
        else: res['percent'] = pos*100./total
        return res

    def setDefaultConfigFiles(self, defaultCF):
        """
        Used by plugins to alter the default config files list.
        The base class does nothing and returns defautlCF.
        """

        # Do nothing in base class
        return defaultCF

    def getDefaultConfigFiles(self):
        """
        Returns the default config files list to use with the ConfigFileWidget JS class.
        """

        # Default config files to use
        return [
            {'path': os.path.join(settings.PLUGINS_CONF_DIR, self.id + '.conf.default'), 'type': 'config'},
        ]

    def __saveDefaultConfigFileToDB(self, request):
        """
        Looks into DB (youpi_configfiles table) if an entry for a default configuration file. 
        If not creates one with the embedded default content.
        """
        post = request.POST
        try:
            type = str(post['Type'])
        except:
            raise PluginError, "invalid post parameters %s" % post

        # Should be used by plugins to alter the default content of the list
        defaultConfigFiles = self.setDefaultConfigFiles(self.getDefaultConfigFiles())

        for cf in defaultConfigFiles:
            if cf['type'] != type: continue
            try:
                f = open(cf['path'])
                config = string.join(f.readlines())
                f.close()
            except IOError, e:
                raise PluginError, "Default config file for %s: %s" % (self.id, e)
        
            k = Processing_kind.objects.filter(name__exact = self.id)[0]
            t = ConfigType.objects.filter(name = type)[0]
            try:
                m = ConfigFile(kind = k, name = 'default', content = config, user = request.user, type = t)
                m.save()
            except:
                # Cannot save, already exits: do nothing
                pass

    def saveConfigFile(self, request):
        """
        Save configuration file to DB
        """
        post = request.POST
        try:
            name = str(post['Name'])
            type = str(post['Type'])
            config = str(post['Content'])
        except Exception, e:
            raise PluginError, "Unable to save config file: no name given"

        profile = request.user.get_profile()
        t = ConfigType.objects.filter(name = type)[0]
        try:
            # Updates entry
            m = ConfigFile.objects.filter(kind__name__exact = self.id, name = name, type = t)[0]
            m.content = config
        except:
            # ... or inserts a new one
            k = Processing_kind.objects.filter(name__exact = self.id)[0]
            m = ConfigFile(kind = k, name = name, content = config, user = request.user, type = t, mode = profile.dflt_mode, group = profile.dflt_group)

        success = write_proxy(request, m)

        return {'name': name, 'success': int(success)}

    def deleteConfigFile(self, request):
        """
        Deletes configuration file to DB
        """
        post = request.POST
        try:
            name = str(post['Name'])
            type = str(post['Type'])
        except Exception, e:
            raise PluginError, "Unable to delete config file: no name given"

        try:
            config = ConfigFile.objects.filter(kind__name__exact = self.id, name = name, type__name = type)[0]
        except:
            raise PluginError, "No config file with that name: %s" % name

        #config.delete()
        success = write_proxy(request, config, delete = True)

        return {'name': name, 'success': int(success)}

    def getOutputDirStats(self, outputDir):
        """
        Return some related statistics about processings from outputDir.
        """

        headers = ['Task success', 'Task failures', 'Total processings']
        cols = []
        tasks = Processing_task.objects.filter(results_output_dir = outputDir)
        tasks_success = tasks_failure = 0
        for t in tasks:
            if t.success == 1:
                tasks_success += 1
            else:
                tasks_failure += 1

        stats = {   'TaskSuccessCount'  : [tasks_success, "%.2f" % (float(tasks_success)/len(tasks)*100)],
                    'TaskFailureCount'  : [tasks_failure, "%.2f" % (float(tasks_failure)/len(tasks)*100)],
                    'Total'             : len(tasks) }

        return stats

    def hasItemsInCart(self):
        """
        Returns True if this plugin has items in processing cart.
        """
        return len(self.__data) > 0

    def setData(self, dataList):
        """
        Sets data to be processed 
        """
        self.__data = dataList

    def removeData(self):
        """
        Removed plugin data
        """
        self.__data = []

    def getData(self):
        return self.__data

    def deleteCartItem(self, request):
        post = request.POST
        try:
            name = str(post['Name'])
        except Exception, e:
            raise PluginError, "POST argument error. Unable to process data."

        try:
            item = CartItem.objects.filter(kind__name__exact = self.id, name = name)[0]
            success = write_proxy(request, item, delete = True)
        except Exception, e:
            raise PluginError, "No item named '%s' found." % name

        return {'name': name, 'success': int(success)}

    def getMiscDataPaths(self, request):
        """
        Returns a JSON object with paths to flags and weights
        """
        post = request.POST
        try:
            keys = post['Keys'].split(',')
        except Exception, e:
            raise PluginError, "POST argument error. Unable to process data."

        paths = {}
        for k in keys:
            try:
                m = MiscData.objects.filter(key = k, user = request.user)[0]
                data = marshal.loads(base64.decodestring(str(m.data)))
                paths[str(k)] = data
                paths[str(k)].sort()
            except:
                paths[str(k)] = []

        return paths

    def saveMiscDataPath(self, request):
        """
        Save a path of type key.
        """
        post = request.POST
        try:
            path = post['Path']
            key = str(post['Key'])
        except Exception, e:
            raise PluginError, "POST argument error. Unable to process data."

        pathList = []
        canSave = True
        try:
            # Updates entry
            m = MiscData.objects.filter(key = key, user = request.user)[0]
            data = marshal.loads(base64.decodestring(str(m.data)))
            # Checks if path already exists
            if str(path) not in data:
                data.append(str(path))
                sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')
                m.data = sdata
            else:
                canSave = False
            pathList = data
        except:
            # Inserts a new one
            pathList = [str(path)]
            sdata = base64.encodestring(marshal.dumps(pathList)).replace('\n', '')
            profile = request.user.get_profile()
            m = MiscData(key = key, data = sdata, user = request.user, mode = profile.dflt_mode, group = profile.dflt_group)

        if canSave:
            m.save()

        return { key + 's' : pathList }

    def deleteMiscDataPath(self, request):
        """
        Deletes a path of type key.
        """
        post = request.POST
        try:
            path = str(post['Path'])
            key = str(post['Key'])
        except Exception, e:
            raise PluginError, "POST argument error. Unable to process data."

        # Updates entry
        m = MiscData.objects.filter(key = key, user = request.user)[0]
        data = marshal.loads(base64.decodestring(str(m.data)))
        # Checks if path already exists
        idx = -1
        if path in data:
            for i in range(len(data)):
                if path == data[i]:
                    idx = i

            if idx >= 0:
                del data[idx]
                sdata = base64.encodestring(marshal.dumps(data)).replace('\n', '')
                m.data = sdata
                m.save()

        return { key : path }

    def getResultEntryDescription(self, task):
        return "My description " + str(task.id)

class ApplicationManagerError(PluginError): pass

class ApplicationManager(object):
    """
    Application manager responsible for loading custom processing plugins. No :class:`ClusterClient` 
    is set by default.
    """
    __instances = {}

    def __init__(self):
        # Looks for plugins
        self.__loadPlugins()
        self.__cluster = None

    def __loadPlugins(self):
        """
        Dynamically loads plugins from the settings.PLUGIN_DIRS directory.
        Ensure that each plugin has an id attribute and is unique accross all
        registered plugins.
        """
        for name in settings.YOUPI_ACTIVE_PLUGINS:
            if name.endswith('.py'): name = name[:-3]
            try: __import__(name)
            except ImportError, e:
                raise ApplicationManagerError, "Unable to load plugin '%s.py': %s" % (name, e)

        for obj in ProcessingPlugin.__subclasses__():
            if obj not in self.__instances:
                self.__instances[obj] = obj()
                if not hasattr(self.__instances[obj], 'id'):
                    raise ApplicationManagerError, "Plugin %s does not have an id attribute which is mandatory" % obj

        # Ensure plugin id is unique
        ids = {}
        for plug in self.__instances.values():
            if not ids.has_key(plug.id): ids[plug.id] = []
            ids[plug.id].append(plug)
        for id, plugs in ids.iteritems():
            if len(plugs) > 1:
                raise ApplicationManagerError, "The %s plugins can't have the same id attribute '%s'" % (plugs, id)

    def reload(self):
        """
        Force reloading all plugins specified in settings.YOUPI_ACTIVE_PLUGINS
        """
        self.__instances = {}
        self.__loadPlugins()

    @property
    def plugins(self):
        """
        @return List of currently activated plugins, sorted by their index property
        """
        active_plugins = self.__instances.values()
        # Sort by index property
        try:
            active_plugins.sort(lambda x,y: cmp(x.index, y.index))
        except AttributeError:
            raise ApplicationManagerError, "Unable to sort plugins by index. Missing index property."
        return active_plugins

    def getPluginByName(self, iname):
        """
        Returns plugin object by internal name if found or None.
        """
        if type(iname) != types.StringType and type(iname) != types.UnicodeType:
            raise TypeError, "iname must be a string"

        for p in self.plugins:
            if p.id == iname:
                return p

        raise ApplicationManagerError, "No plugin with id '%s' found." % iname

    def setClusterClient(self, client):
        """
        Set the cluster client implementation to use. *client* must be a :class:`~terapix.lib.cluster.ClusterClient` instance.
        """
        if not isinstance(client, ClusterClient):
            raise TypeError, "cluster must be a ClusterClient object"
        self.__cluster = client

    @property
    def cluster(self):
        """
        :class:`ClusterClient` instance in use.
        """
        return self.__cluster

# Global plugin manager
manager = ApplicationManager()
manager.setClusterClient(YoupiCondorClient())

