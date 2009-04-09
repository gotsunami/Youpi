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
	prevrelgrades = Plugin_fitsin.objects.exclude(prevrelgrade = None).filter(task__success = True).count()

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
	#fitsinIds = FirstQEval.objects.values('fitsin').distinct()
	#fitsins = Plugin_fitsin.objects.filter(id__in = [f['fitsin'] for f in fitsinIds])
	fitsins = Plugin_fitsin.objects.filter(task__success = True)
	tmp = {}
	for f in fitsins:
		grades = FirstQEval.objects.filter(fitsin = f).order_by('-date')
		imgName = Rel_it.objects.filter(task = f.task)[0].image.name

		# Looks for user-defined grades
		if grades:
			if not tmp.has_key(imgName):
				tmp[imgName] = []
			tmp[imgName].append((grades[0].grade, grades[0].date, grades[0].comment.comment))

		# Now looks for a previous release grade
		if f.prevrelgrade:
			if not tmp.has_key(imgName):
				tmp[imgName] = []
			# Add a fake datetime object to make sure this grade is the older one
			tmp[imgName].append([f.prevrelgrade, datetime.datetime(datetime.MINYEAR, 1, 1), f.prevrelcomment])

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

	return res 

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
				if not simulate:
					rels = Rel_it.objects.filter(task__kind__name = 'fitsin', image = img[0])
					fitsins = Plugin_fitsin.objects.filter(task__in = [r.task for r in rels])
					for proc in fitsins:
						proc.prevrelgrade, proc.prevrelcomment = grade, comment
						proc.save()
						writes += 1
					
				found += 1
			if not verbose:
				sys.stdout.write(term.BOL + "Found: %5d, Not Found: %5d, DB Writes: %5d, Line %5d" % (found, notfound, writes, pos))
			pos += 1
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
	parser.add_option('-i', '--ingest', dest = 'filename', help = 'Sets the CSV file to use for grade ingestion')
	parser.add_option('-l', '--list-only', action = 'store_true', help = 'List available grades in DB')
	parser.add_option('-t', '--stats', action = 'store_true', help = 'Display statistics')
	parser.add_option('-v', '--verbose', action = 'store_true', default = False, help = 'Increase verbosity')
	parser.add_option('-s', '--simulate', action = 'store_true', default = False, help = 'Simulate action (do nothing)')
	(options, args) = parser.parse_args()

	if len(args):
		parser.error('takes no argument at all')

	if options.list_only and options.filename:
		parser.error('options -l and -i are mutually exclusive')
	if options.stats and options.list_only:
		parser.error('options -t and -l are mutually exclusive')

	try:
		if options.stats:
			from terapix.reporting.plain import PlainTextReport
			print PlainTextReport(data = get_stats())
		elif options.list_only:
			from terapix.reporting.csv import CSVReport
			print CSVReport(data = get_grades())
		elif options.filename:
			print options.verbose
			ingest_grades(options.filename, options.simulate, verbose = options.verbose)
	except KeyboardInterrupt:
		print "Catched interrupt. Exiting..."
		sys.exit(2)

if __name__ == '__main__':
	main()
