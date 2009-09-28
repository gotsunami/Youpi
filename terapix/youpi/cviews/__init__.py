
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group
from django.db import IntegrityError
#
from terapix.youpi.pluginmanager import PluginManager
from terapix.youpi.models import SiteProfile
#
import base64, marshal

manager = PluginManager()

NULLSTRING = ''
WHITESPACE = ' '

def pref_save_default_condor_config(user):
	"""
	Save default Condor config for user.
	Should look like:
	{'skel': {'DB': 'selection', 'DS': '', 'DP': 'MIX_ALL'}, 
	 'fitsin': {'DB': 'policy', 'DS': '', 'DP': 'MIX_ALL'}, 
	 'swarp': {'DB': 'selection', 'DS': '', 'DP': 'MIX_ALL'} ... }
	"""

	kinds = ('DB', 'DP', 'DS')
	condor_setup = {}
	for plugin in manager.plugins:
		condor_setup[plugin.id] = {}
		condor_setup[plugin.id]['DB'] = 'policy'
		condor_setup[plugin.id]['DS'] = ''
		condor_setup[plugin.id]['DP'] = 'ALL'

	p = user.get_profile()
	p.dflt_condor_setup = base64.encodestring(marshal.dumps(condor_setup)).replace('\n', '')
	p.save()

def profile(fn):
	"""
	Decorator used to check for existing user profile
	"""
	def new(*args):
		try:
			user = args[0].user
			prof = user.get_profile()
		except ObjectDoesNotExist:
			# Create a new profile
			groups = user.groups.all()
			if not groups:
				# No user groups; add default one
				grp = Group(name = user.username)
				try:
					grp.save()
				except IntegrityError:
					# Already exits
					grp = Group.objects.filter(name = user.username)[0]
				user.groups.add(grp)
			else:
				grp = groups[0]

			p = SiteProfile(user = user, dflt_group = grp, dflt_mode = '640')
			p.save()
			# Adds default Condor config for that profile
			pref_save_default_condor_config(user)

		return fn(*args)

	return new
