
class CondorSetupError(Exception): pass
class CondorSubmitError(Exception): pass
class PostDataError(Exception): pass
#
class PluginError(Exception): pass
class PluginAllDataAlreadyProcessed(PluginError): pass
class PluginEvalError(PluginError): pass
class PluginManagerError(PluginError): pass