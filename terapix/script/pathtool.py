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
Useful to display/upgrade important data paths.
Run this script with no arguments to get a list of Youpi's data paths.
"""

import sys, os, string, curses, os.path
import marshal, base64, types, re
import datetime, time
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
except ImportError:
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)

def search(pattern, replace = None, force = False, verbose = False):
	"""
	Search and replace 'pattern' with 'replace' in all important data paths locations
	Set force to True to commit changes in the database.
	If replace is None then only the provided pattern is search; a report is produced

	Important data paths locations are:

	Model              fields
	-----------------------------------------------------------------------------------------
	Image              path
	Ingestion          path
	Processing_task    results_output_dir
	CartItem           data (base64:resultsOutputDir)
	Plugin_fitsin      flat, mask, reg
	Plugin_scamp       aheadPath, base64:ldac_files
	Plugin_swarp       headPath, weightPath
	Plugin_sex         weightPath, flagPath, dualweightPath, dualImage, dualflagPath, psfPath
	"""

	from django.db import connection
	cur = connection.cursor()
	print "Data paths for entities: Image, Ingestion, CartItem, Processing_task, Plugin_fitsin, Plugin_scamp, Plugin_swarp, Plugin_sex"
	if pattern:
		if replace:
			print "Will replace '%s' with '%s' (case-sensitive match)" % (pattern, replace)
			if not force:
				print "SIMULATION ONLY. Nothing will be written to the database!"
			else:
				r = raw_input('Are you sure you want to continue? (y/n) ')
				if r not in ('y', 'Y'):
					print "Aborted."
					sys.exit(2)
		else:
			print "Searching for: '%s'" % pattern

	targets = {
		'Image': 			{'table': 'youpi_image', 'fields': ('path',)},
		'Ingestion': 		{'table': 'youpi_ingestion', 'fields': ('path',)},
		'Processing_task': 	{'table': 'youpi_processing_task', 'fields': ('results_output_dir',)},
		'Plugin_fitsin': 	{'table': 'youpi_plugin_fitsin', 'fields': ('flat', 'mask', 'reg')},
		'Plugin_scamp': 	{'table': 'youpi_plugin_scamp', 'fields': ('aheadPath', '_b64:ldac_files:')},
		'Plugin_swarp': 	{'table': 'youpi_plugin_swarp', 'fields': ('headPath', 'weightPath')},
		'Plugin_sex': 		{'table': 'youpi_plugin_sex', 'fields': ('weightPath', 'flagPath', 'dualweightPath', 'dualImage', 'dualflagPath', 'psfPath')},
		# Special field format: base64:fieldname:[dictionnary_key] to lookup
		'CartItem': 		{'table': 'youpi_cartitem', 'fields': ('_b64:data:resultsOutputDir',)},
	}

	for model, data in targets.iteritems():
		for f in data['fields']:
			enc = None
			if f.startswith('_b64:'):
				enc, f, key = f.split(':')
			print "\n%s[%s]:" % (model, f)
			if not enc:
				# Traditional, clear (unencrypted) data
				if not replace:
					q = "SELECT DISTINCT(%s), COUNT(%s) FROM %s GROUP BY 1" % (f, f, data['table'])
					cur.execute(q)
					res = cur.fetchall()
					for r in res:
						if pattern:
							if r[0] and re.search(pattern, r[0], re.I):
								print "  %6d '%s'" % (r[1], r[0])
						else:
							print "  %6d '%s'" % (r[1], r[0])
				else:
					# Substitute pattern with 'replace'
					q = "UPDATE %s SET %s = REPLACE(%s, '%s', '%s')" % (data['table'], f, f, pattern, replace)
					if force:
						# Issue SQL queries
						cur.execute(q)
					else:
						print q
					
			else:
				# Data is base64 encoded
				q = "SELECT id, %s FROM %s" % (f, data['table'])
				cur.execute(q)
				res = cur.fetchall()
				for r in res:
					clear = marshal.loads(base64.decodestring(r[1]))
					if type(clear) == types.ListType:
						if not replace:
							for e in clear:
								if pattern:
									if e and re.search(pattern, e, re.I):
											print "  %6d %s" % (1, e)
								else:
									print "  %6d %s" % (1, e)
						else:
							# Replacing all elements in the list at once
							after = []
							for e in clear:
								after.append(e.replace(pattern, replace))
							encAfter = base64.encodestring(marshal.dumps(after)).replace('\n', '')
							q = "UPDATE %s SET %s = '%s' WHERE id=%s" % (data['table'], f, encAfter, r[0])
							if force:
								# Issue SQL queries
								cur.execute(q)
							else:
								if verbose: print q
								print "base64 (%d strings, %d bytes)" % (len(clear), len(encAfter))
					else:
						if pattern:
							if clear[key] and re.search(pattern, clear[key], re.I):
								if not replace:
									print "  %6d %s" % (1, clear[key])
								else:
									# Replacing one element
									encAfter = base64.encodestring(marshal.dumps(clear[key])).replace('\n', '')
									q = "UPDATE %s SET %s = '%s' WHERE id=%s" % (data['table'], f, encAfter, r[0])
									if force:
										# Issue SQL queries
										cur.execute(q)
									else:
										if verbose: print q
										print "base64 (%d bytes)" % (len(encAfter))
						else:
							print "  %6d %s" % (1, clear[key])
	
	if replace and force:
		print "Committing...",
		connection._commit()
		print "Done!"

def main():
	parser = OptionParser(description = 'Tool for listing/replacing data paths')
	parser.add_option('-f', '--force', 
			default = False, 
			action = 'store_true', 
			help = 'Force writing new paths to DB'
	)
	parser.add_option('-s', '--search', 
			default = None, 
			help = 'Search criteria'
	)
	parser.add_option('-r', '--replace', 
			default = False, 
			help = 'Replace search criteria with this string (case sensitive)'
	)
	parser.add_option('-v', '--verbose', 
			default = False, 
			action = 'store_true', 
			help = 'More verbosity'
	)

	(options, args) = parser.parse_args()
	if len(args): parser.error('takes no argument at all')

	try:
		start = time.time()
		search(options.search, options.replace, options.force, options.verbose)

		print "Took: %.2fs" % (time.time()-start)
	except KeyboardInterrupt:
		print "Exiting..."
		sys.exit(2)


if __name__ == '__main__':
	main()
