from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

class MaintenanceModeMiddleware(object):
	"""
	Custom Django middleware for maintenance mode. Just set the MAINTENANCE
	variable to True in your settings file in order to redirect all but staff 
	users to a maintenance page template.
	"""
	def process_request(self, request):
		if request.META['PATH_INFO'] == reverse('terapix.youpi.views.maintenance'):
			return None
		if hasattr(settings, 'MAINTENANCE'):
			if settings.MAINTENANCE and not request.user.is_staff:
				return HttpResponseRedirect(reverse('terapix.youpi.views.maintenance'))
		return None 
