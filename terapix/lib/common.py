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

import os.path

def get_title_from_menu_id(menuId):
	from youpi.context_processors import appmenu
	parts = appmenu(None)['menu'].values()
	for p in parts:
		for m in p:
			if m['id'] == menuId:
				return m['title']

	return None
