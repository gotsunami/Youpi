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
Check all plugins description field.
Table: youpi_processing_task
Field: title
"""

import sys, os, string, curses, os.path
import datetime, time, zlib, base64
from optparse import OptionParser
from terminal import *
os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from django.db import IntegrityError
	from django.conf import settings
	#
	from terapix.youpi.models import *
	from terapix.youpi.pluginmanager import PluginManager
except ImportError:
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)

def check_descr(simulate):
	manager = PluginManager()
	for plugin in manager.plugins:
		updated = 0
		if not plugin.isAstromatic: continue
		print "Checking %s processings tasks" % plugin.id
		tasks = Processing_task.objects.filter(kind__name = plugin.id)
		for t in tasks:
			pdata = eval('Plugin_' + plugin.id + '.objects.filter(task = t)')[0]
			config = zlib.decompress(base64.decodestring(pdata.config))
			xmlName = plugin.getConfigValue(config.split('\n'), 'XML_NAME')
			xmlRootName = xmlName[:xmlName.rfind('.')]
			if not xmlRootName:
				print "W: XML_NAME not found in config file for task id %d" % t.id
			if t.title.find(xmlRootName) == -1:
				t.title += ", %s" % xmlRootName
				if not simulate: t.save()
				updated += 1
		
		print "Total: %d, Updated: %d\n" % (len(tasks), updated)

def main():
	parser = OptionParser(description = 'Check all plugins description field. Apply fixes when necessary.')
	parser.add_option('-s', '--simulate', 
			action = 'store_true', 
			default = False, 
			help = 'Simulate action (do nothing)'
	)

	(options, args) = parser.parse_args()

	try:
		start = time.time()
		check_descr(options.simulate)
		print "Took: %.2fs" % (time.time()-start)
	except KeyboardInterrupt:
		print "Exiting..."
		sys.exit(2)

if __name__ == '__main__':
	main()
