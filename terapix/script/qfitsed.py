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
Outputs a list of all QFITSed images + grade(if any) + who + date
"""

import sys, os, string, curses
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

def get_images():
	"""
	Get successfull Qfitsed images by user

	@return a list of tuple
	"""
	from django.db import connection
	cur = connection.cursor()
	cur.execute("""
		SELECT i.name, t.start_date, u.username
		FROM youpi_image AS i, youpi_processing_task AS t, youpi_rel_it AS r, auth_user as u, youpi_processing_kind as k
		WHERE t.id=r.task_id
		AND t.user_id=u.id
		AND i.id=r.image_id
		AND t.success=1
		AND t.kind_id=k.id
		AND k.name='fitsin'
		ORDER BY 1
	""")
	res = cur.fetchall()
	return res

def get_grades():
	"""
	Get all grades from a specific successfull QFits

	@return a list of tuple
	"""
	from django.db import connection
	cur = connection.cursor()
	cur.execute("""
		SELECT f.id, f.prevrelgrade, f.prevrelcomment, i.name 
		FROM youpi_plugin_fitsin AS f, youpi_processing_task AS t, youpi_rel_it AS r, youpi_image AS i
		WHERE f.task_id=t.id 
		AND r.task_id=f.task_id
		AND r.image_id = i.id
		AND t.success=1""")
	res = cur.fetchall()

def main():
	parser = OptionParser(description = 'Lists all Qualityfited images')
	parser.add_option('-l', '--list-only', 
			default = False, 
			action = 'store_true', 
			help = 'List available grades in DB'
	)
	parser.add_option('-v', '--verbose', 
			action = 'store_true', 
			default = False, 
			help = 'Increase verbosity'
	)

	try: opts = sys.argv[1]
	except IndexError: parser.print_help()

	(options, args) = parser.parse_args()
	if len(args): parser.error('takes no argument at all')

	try:
		if options.list_only:
			from terapix.reporting.csv import CSVReport
			print CSVReport(data = get_images())
	except KeyboardInterrupt:
		print "Exiting..."
		sys.exit(2)


if __name__ == '__main__':
	main()
