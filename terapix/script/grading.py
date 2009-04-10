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
Grades all Qualityfits-in processings. Can output a list of all grades in the 
database.
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
	#
	from terapix.settings import *
	from terapix.youpi.models import *
except ImportError:
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)

def get_stats():
	total = Plugin_fitsin.objects.filter(task__success = True).count()
	usergrades = FirstQEval.objects.all().values('fitsin').distinct()
	prevrelgrades = Plugin_fitsin.objects.exclude(prevrelgrade = '').filter(task__success = True).count()

	stats = (
		('User-defined grades', len(usergrades)),
		('Previous release grades', prevrelgrades),
		('Total of successful QualityFITS processings', total),
	)

	return stats

def get_grades():
	"""
	Returns all images grades in the database. Only the latest grade, when available, is returned for 
	each image. Both user-defined and previous release grades are checked for grading information and 
	comment.

	@return a list of tuples [(image name, grade, comment), ...]
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

	tmp = {}
	for r in res:
		grades = FirstQEval.objects.filter(fitsin__id = r[0]).order_by('-date')
		imgName = r[3]

		# Looks for user-defined grades
		if grades:
			if not tmp.has_key(imgName):
				tmp[imgName] = []
			tmp[imgName].append((grades[0].grade, grades[0].date, grades[0].comment.comment))

		# Now looks for a previous release grade
		if r[1]:
			if not tmp.has_key(imgName):
				tmp[imgName] = []
			# Add a fake datetime object to make sure this grade is the older one
			tmp[imgName].append([r[1], datetime.datetime(datetime.MINYEAR, 1, 1), r[2]])

	# Now, only keep the latest grade for each image
	res = []
	for imgName, grades in tmp.iteritems():
		if len(grades) == 1:
			res.append((imgName, grades[0][0], grades[0][2]))
			continue
		latest = grades[0]
		for k in range(1, len(grades)):
			if grades[k][1] > latest[1]:
				latest = grades[k]
		res.append((imgName, latest[0], latest[2]))

	# Sort by image name
	res.sort(cmp = lambda x,y: cmp(x[0], y[0])) 
	return res

def delete_grades(simulate, verbose = False):
	total = Plugin_fitsin.objects.filter(task__success = True).exclude(prevrelgrade = '').count()
	print "Simulation:", simulate
	print "Computing how many grades to delete..."
	print "%d grades (and comments) to delete." % total

	if not simulate and total:
		r = raw_input('Continue? (y/n) ')
		if r not in ('y', 'Y'):
			print "Aborted."
			sys.exit(2)

		from django.db import connection
		cur = connection.cursor()
		cur.execute("UPDATE youpi_plugin_fitsin SET prevrelgrade = '', prevrelcomment = ''")
		connection._commit()
		print "Done"

def ingest_grades(filename, simulate, verbose = False, separator = ';'):
	try:
		f = open(filename)
	except IOError, e:
		print e
		sys.exit(1)

	print "Looking for fields separated by '%s'" % separator
	print "Each line should match: '%s'" % string.join(('Image name', 'Grade', 'Comment'), separator)
	print "Simulation:", simulate

	start = time.time()
	term = TerminalController()
	sys.stdout.write(term.HIDE_CURSOR)

	notfound = found = imgcount = writes = 0
	pos = 1
	from django.db import connection
	cur = connection.cursor()
	try:
		while True:
			line = f.readline()[:-1]
			if not line: break

			name, grade, comment = line.split(separator)
			img = Image.objects.filter(name = name)
			if not img:
				notfound += 1
				if verbose:
					print "Not Found:", name
					sys.stdout.flush()
			else:
				found += 1
				if not simulate:
					rels = Rel_it.objects.filter(task__kind__name = 'fitsin', image = img[0])
					fitsins = Plugin_fitsin.objects.filter(task__in = [r.task for r in rels], task__success = True).values('id')
					if fitsins:
						q = """
						UPDATE youpi_plugin_fitsin 
						SET prevrelgrade="%s", prevrelcomment="%s"
						WHERE id IN (%s)
						""" % (grade, comment, string.join([str(i['id']) for i in fitsins], ','))
						cur.execute(q)
						writes += len(fitsins)
					
			if not verbose:
				sys.stdout.write(term.BOL + "Found: %5d, Not Found: %5d, DB Writes: %5d, Line %5d" % (found, notfound, writes, pos))
			pos += 1

		connection._commit()
	except KeyboardInterrupt:
		sys.stdout.write(term.SHOW_CURSOR)
		raise

	f.close()
	sys.stdout.write(term.SHOW_CURSOR + '\n')

	if verbose:
		print "Found: %5d, Not Found: %5d, DB Writes: %5d, Line %5d" % (found, notfound, writes, pos-1)
	print "Time elapsed: %.2f sec" % (time.time() - start)


def main():
	parser = OptionParser(description = 'My prog')
	parser.add_option('-d', '--delete', 
			default = False, 
			action = 'store_true', 
			help = 'Delete available grades in DB (previous release only, not user-defined ones)'
	)
	parser.add_option('-i', '--ingest', 
			default = False, 
			dest = 'filename', 
			help = 'Sets the CSV file to use for grade ingestion'
	)
	parser.add_option('-l', '--list-only', 
			default = False, 
			action = 'store_true', 
			help = 'List available grades in DB'
	)
	parser.add_option('-t', '--stats', 
			default = False, 
			action = 'store_true', 
			help = 'Display statistics'
	)
	parser.add_option('-v', '--verbose', 
			action = 'store_true', 
			default = False, 
			help = 'Increase verbosity'
	)
	parser.add_option('-s', '--simulate', 
			action = 'store_true', 
			default = False, 
			help = 'Simulate action (do nothing)'
	)

	try: opts = sys.argv[1]
	except IndexError: parser.print_help()

	(options, args) = parser.parse_args()
	if len(args): parser.error('takes no argument at all')

	if options.list_only and options.filename:
		parser.error('options -l and -i are mutually exclusive')
	if options.stats and options.list_only:
		parser.error('options -t and -l are mutually exclusive')
	if options.delete and options.filename:
		parser.error('options -d and -i are mutually exclusive')
	if options.delete and options.stats:
		parser.error('options -d and -t are mutually exclusive')
	if options.filename and options.stats:
		parser.error('options -i and -t are mutually exclusive')
	if options.delete and options.list_only:
		parser.error('options -d and -l are mutually exclusive')

	try:
		if options.stats:
			from terapix.reporting.plain import PlainTextReport
			print PlainTextReport(data = get_stats())
		elif options.list_only:
			from terapix.reporting.csv import CSVReport
			print CSVReport(data = get_grades())
		elif options.filename:
			ingest_grades(options.filename, options.simulate, verbose = options.verbose)
		elif options.delete:
			delete_grades(options.simulate, verbose = options.verbose)
	except KeyboardInterrupt:
		print "Catched interrupt. Exiting..."
		sys.exit(2)


if __name__ == '__main__':
	main()
