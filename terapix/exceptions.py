
class CondorSetupError(Exception): pass
class CondorSubmitError(Exception): pass
class PostDataError(Exception): pass
#
class PluginError(Exception): pass
class PluginAllDataAlreadyProcessed(PluginError): pass
class PluginEvalError(PluginError): pass
class PluginManagerError(PluginError): pass
#
# For debugging
class DebugError(Exception): pass
#
class PermissionsError(Exception): pass
#
class ReportIncompleteDefinitionError(Exception): pass
