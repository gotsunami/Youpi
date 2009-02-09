"""
A set of custom Youpi request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.

These are referenced from the setting TEMPLATE_CONTEXT_PROCESSORS and used by
RequestContext.
"""

def release(request):
	"""
	Returns context variables for Youpi's release system.
	"""

	return {
		'user_release': request.user.get_profile().release,
	}

def appmenu(request):
	"""
	Returns context variables for Youpi's release system (Application menu).
	"""

	from terapix.settings import AUP
	
	app_menu = {'normal' : ( 	
					{'title' : 'Home', 				'id' : 'home', 			'href' : AUP},
					{'title' : 'Pre-ingestion',		'id' : 'preingestion',	'href' : AUP + '/preIngestion/'},
					{'title' : 'Ingestion', 		'id' : 'ing', 			'href' : AUP + '/ingestion/'},
					{'title' : 'Release', 			'id' : 'release',		'href' : AUP + '/release/'},
					{'title' : 'Processing', 		'id' : 'processing', 	'href' : AUP + '/processing/'},
					{'title' : 'Processing Results','id' : 'results',	 	'href' : AUP + '/results/'},
					{'title' : 'Active Monitoring', 'id' : 'monitoring', 	'href' : AUP + '/monitoring/'},
				),
				'apart' : ( 	
					# Display order is inverted
					{'title' : 'Preferences', 		'id' : 'preferences', 	'href' : AUP + '/preferences/'},
					{'title' : 'Condor Setup', 		'id' : 'condorsetup', 	'href' : AUP + '/condor/setup/'},
					{'title' : 'Shopping cart',		'id' : 'shoppingcart', 	'href' : AUP + '/cart/'},
				)
	}

	return { 'menu': app_menu }
