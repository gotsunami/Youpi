##############################################################################
#
# Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
#                    Mathias Monnerville <monnerville@iap.fr>
#                    Gregory Semah <semah@iap.fr>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
##############################################################################


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
class PermissionsConvertError(PermissionsError): pass
