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

import sys, os, string
from optparse import OptionParser
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

def print_stats():
	total = Plugin_fitsin.objects.filter(task__success = True).count()
	usergrades = FirstQEval.objects.all().values('fitsin').distinct()
	prevrelgrades = Plugin_fitsin.objects.exclude(prevrelgrade = None).filter(task__success = True).count()

	print "Stats about image grading:"
	stats = (
		('User-defined grades', len(usergrades)),
		('Previous release grades', prevrelgrades),
		('Total of successful QualityFITS processings', total),
	)
	for s in stats:
		print "%-40s  %6d" % (s[0], s[1])

def print_grade_list(separator = ';'):
	fitsinIds = FirstQEval.objects.values('fitsin').distinct()
	fitsins = Plugin_fitsin.objects.filter(id__in = [f['fitsin'] for f in fitsinIds])
	k = 0
	print 'Image name,Grade,Predefined comment, Custom comment'
	res = {}
	for f in fitsins:
		grades = FirstQEval.objects.filter(fitsin = f).order_by('-date')
		if grades:
		#	print "%s%s%s%s%s%s%s" % (Rel_it.objects.filter(task = f.task)[0].image.name, separator, grades[0].grade, separator, grades[0].comment.comment, separator, grades[0].custom_comment)
			imgName = Rel_it.objects.filter(task = f.task)[0].image.name
			if not res.has_key(imgName):
				res[imgName] = []
			res[imgName].append(grades[0].grade)

		k += 1

	print res


def main():
	parser = OptionParser(description = 'My prog')
	parser.add_option('-c', '--csv', dest = 'filename', help = 'Sets the CSV file to use')
	parser.add_option('-s', '--simulate', action = 'store_true', help = 'Simulate action (do nothing)')
	parser.add_option('-t', '--stats', action = 'store_true', help = 'Display statistics')
	parser.add_option('-l', '--list-only', action = 'store_true', help = 'List available grades in DB')
	(options, args) = parser.parse_args()

	if len(args):
		parser.error('takes no argument at all')

	if options.list_only and options.filename:
		parser.error('options -l and -c are mutually exclusive')
	if options.stats and options.list_only:
		parser.error('options -t and -l are mutually exclusive')

	if options.stats:
		print_stats()
	elif options.list_only:
		print_grade_list()

if __name__ == '__main__':
	main()
