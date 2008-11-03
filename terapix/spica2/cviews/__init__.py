
from django.core.exceptions import ObjectDoesNotExist

from terapix.youpi.pluginmanager import PluginManager
from terapix.youpi.models import SiteProfile

manager = PluginManager()

NULLSTRING = ''
WHITESPACE = ' '
HOST_DOMAIN = '.clic.iap.fr'

def profile(fn):
	def new(*args):
		try:
			user = args[0].user
			prof = user.get_profile()
		except ObjectDoesNotExist:
			# Create a new profile
			p = SiteProfile(user = user)
			p.save()
		return fn(*args)

	return new
