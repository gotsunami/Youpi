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

"""
A set of custom Youpi request processors that return dictionaries to be merged into a
template context. Each function takes the request object as its only parameter
and returns a dictionary to add to the context.

These are referenced from the setting TEMPLATE_CONTEXT_PROCESSORS and used by
RequestContext.
"""

def appmenu(request):
	"""
	Returns context variables for Youpi's release system (Application menu).
	"""

	from terapix.settings import AUP
	
	app_menu = {'normal' : ( 	
					{'title' : 'Home', 				'id' : 'home', 			'href' : AUP},
					{'title' : 'Pre-ingestion',		'id' : 'preingestion',	'href' : AUP + '/preIngestion/'},
					{'title' : 'Ingestion', 		'id' : 'ing', 			'href' : AUP + '/ingestion/'},
					{'title' : 'Tags', 				'id' : 'tags',			'href' : AUP + '/tags/'},
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
