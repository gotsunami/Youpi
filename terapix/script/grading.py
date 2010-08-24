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

import sys, os, string, curses, os.path, types
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

def get_stats():
	"""
	Returns statistics information of QFITS processing status from user's defined output directory	

	@return a list of tuples 
	"""

	total = Plugin_fitsin.objects.filter(task__success = True).count()
	usergrades = FirstQEval.objects.all().values('fitsin').distinct()
	prevrelgrades = Plugin_fitsin.objects.exclude(prevrelgrade = '').filter(task__success = True).count()

	stats = (
		('User-defined grades', len(usergrades)),
		('Previous release grades', prevrelgrades),
		('Total of successful QualityFITS processings', total),
	)

	return stats

def get_grades_with_tag(tag):
	from django.db import connection
	cur = connection.cursor()
	q = """SELECT image_id FROM youpi_rel_tagi AS tagi, youpi_tag AS t WHERE tagi.tag_id=t.id AND t.name='%s'""" % tag
	cur.execute(q)
	res = cur.fetchall()
	imgList = [r[0] for r in res]
	return get_grades(idList = imgList)

def get_grades(res_output_dir = None, idList = None):
	"""
	Returns all images grades in the database. Only the latest grade, when available, is returned for 
	each image. Both user-defined and previous release grades are checked for grading information and 
	comment.

	@return a list of tuples [(image name, grade, comment), ...]
	"""
	
	if res_output_dir and type(res_output_dir) != types.StringType and type(res_output_dir) != types.UnicodeType:
		raise TypeError, "res_output_dir must be a string"

	if idList and type(idList) != types.ListType:
		raise TypeError, "idList must be a list of id [id1, id2,...]"

	from django.db import connection
	cur = connection.cursor()
	q = """
		SELECT f.id, f.prevrelgrade, f.prevrelcomment, i.name, i.id 
		FROM youpi_plugin_fitsin AS f, youpi_processing_task AS t, youpi_rel_it AS r, youpi_image AS i
		WHERE f.task_id=t.id 
		AND r.task_id=f.task_id
		AND r.image_id = i.id
		AND t.success=1"""
	if idList:
		q += """ AND i.id IN (%s)""" % ','.join([str(r) for r in idList])
	if res_output_dir:
		q += """ AND t.results_output_dir="%s";""" % res_output_dir
	if q.find(';') == -1: q += ';'
	cur.execute(q)
	res = cur.fetchall()

	tmp = {}
	for r in res:
		# Latest grade
		grades = FirstQEval.objects.filter(fitsin__id = r[0]).order_by('-date')
		imgName = r[3]

		# Looks for user-defined grades
		if grades:
			if not tmp.has_key(imgName):
				tmp[imgName] = []
			# Keep custom comment in priority, if any
			if grades[0].custom_comment:
				tmp[imgName].append((grades[0].grade, grades[0].date, grades[0].custom_comment, grades[0].fitsin.id, r[4]))
			else:
				# Keep predefined comment
				tmp[imgName].append((grades[0].grade, grades[0].date, grades[0].comment.comment, grades[0].fitsin.id, r[4]))

		# Now looks for a previous release grade
		if r[1]:
			if not tmp.has_key(imgName):
				tmp[imgName] = []
			# Add a fake datetime object to make sure this grade is the older one
			tmp[imgName].append([r[1], datetime.datetime(datetime.MINYEAR, 1, 1), r[2], r[0], r[4]])

	# Now, only keep the latest grade for each image
	res = []
	for imgName, grades in tmp.iteritems():
		if len(grades) == 1:
			res.append((imgName, grades[0][0], grades[0][2], grades[0][3], grades[0][4]))
			continue
		latest = grades[0]
		for k in range(1, len(grades)):
			if grades[k][1] > latest[1]:
				latest = grades[k]
		res.append((imgName, latest[0], latest[2], latest[3], latest[4]))

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
		cur.execute("UPDATE youpi_plugin_fitsin SET prevrelgrade = NULL, prevrelcomment = ''")
		connection._commit()
		print "Done"

def get_proportions():
	"""
	Get the proportion of each grade for all images ingested and graded in Youpi

	@return a list of tuple
	"""
	from django.db import connection
	cur = connection.cursor()
	q1 = "select grade, count(grade) from youpi_firstqeval group by grade"

	grades = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
	for q in (q1,):
		cur.execute(q)
		res = cur.fetchall()
		for g in res:
			if g[0] in ('A','B','C','D'):
				grades[g[0]] += int(g[1])

	grades = [(k,v) for k,v in grades.iteritems()]
	grades.sort(cmp = lambda x,y: cmp(x[0], y[0]))
	return grades

def copy_grades(simulate, user, verbose):
	print "Will copy prevrel grades into the the youpi_firstqeval table, graded by user %s" % user
	print "This copy is non-destructive. You can run this command multiple times."
	try:
		user = User.objects.filter(username__exact = user)[0]
	except:
		# User not found; exiting
		print "Abort: user '%s' not found in database." % user
		sys.exit(1)

	term = TerminalController()
	sys.stdout.write(term.HIDE_CURSOR)

	fitsins = Plugin_fitsin.objects.exclude(prevrelgrade = None).filter(task__success = True)
	com = FirstQComment.objects.all()[0]
	writes = k = matches = 0
	print "Preparing data..."

	try:
		for f in fitsins:
			k += 1
			mg = FirstQEval.objects.filter(user = user, fitsin = f)
			if not mg:
				matches += 1
				if not f.prevrelgrade: print "WARNING: No grade('%s')" % f.prevrelgrade
				if not simulate:
					e = FirstQEval(user = user, fitsin = f)
					e.grade = f.prevrelgrade
					e.comment = com
					if f.prevrelcomment: e.custom_comment = f.prevrelcomment
					else: e.custom_comment = ''
					e.save()
					writes += 1
			sys.stdout.write(term.BOL + "QFits-in: %5d, Matches: %5d, User grades added: %5d" % (k, matches, writes))
	except:
		sys.stdout.write(term.SHOW_CURSOR)
		raise

	sys.stdout.write(term.SHOW_CURSOR + '\n')
	print "New grades added: %d" % writes

def export_grades(output_dir, verbose):
	"""
	Export all grades from the DB. Generated 2 CSV files: one containing all user-defined grades, the other containing 
	all previous release grades.
	"""
	prgname = 'previous-release-grades.csv'
	if output_dir: prgname = os.path.join(output_dir, prgname)
	try:
		prgfile = open(prgname, 'w')
	except Exception, e:
		print "Error: %s" %e
		sys.exit(1)

	from django.db import connection
	cur = connection.cursor()

	# Previous release grades
	q = """
	SELECT i.name, f.prevrelgrade, f.prevrelcomment
	FROM youpi_image AS i, youpi_plugin_fitsin AS f, youpi_rel_it AS r, youpi_processing_task AS t
	WHERE f.prevrelgrade is not NULL
	AND r.image_id = i.id
	AND r.task_id = t.id
	AND f.task_id = t.id
	ORDER BY 1
	"""
	cur.execute(q)
	res = cur.fetchall()
	prgcount = 0
	for r in res:
		prgfile.write(string.join(r, ';') + '\n')
		prgcount += 1
	prgfile.close()
	print "%-10s %-50s %10d" % ('PRELGRADE', prgname, prgcount)

	# User-defined grades
	q = """
	SELECT count(e.grade), u.username, u.id
	FROM youpi_firstqeval AS e, auth_user AS u
	WHERE e.user_id = u.id
	GROUP BY 2
	ORDER BY 2
	"""
	cur.execute(q)
	res = cur.fetchall()
	for u in res:
		ugname = "%s-user-grades.csv" % u[1]
		if output_dir: ugname = os.path.join(output_dir, ugname)
		try:
			ugfile = open(ugname, 'w')
		except Exception, e:
			print "Error: %s" %e
			sys.exit(1)
		q = """
		SELECT i.name, e.grade, c.comment, e.custom_comment
		FROM youpi_image AS i, youpi_firstqeval AS e, youpi_firstqcomment AS c, youpi_plugin_fitsin AS f, youpi_rel_it AS r, youpi_processing_task AS t
		WHERE e.fitsin_id = f.id
		AND f.task_id = t.id
		AND r.task_id = t.id
		AND r.image_id = i.id
		AND e.comment_id = c.id
		AND e.user_id = %d
		ORDER BY 1
		""" % u[2]
		cur.execute(q)
		data = cur.fetchall()
		ugcount = 0
		for r in data:
			ugfile.write(string.join(r, ';') + '\n')
			ugcount += 1
		ugfile.close()
		print "%-10s %-50s %10d %-10s" % ('USERGRADES', ugname, ugcount, u[1])

def ingest_grades(filename, simulate, user, verbose = False, separator = ';'):
	try:
		f = open(filename)
	except IOError, e:
		print e
		sys.exit(1)

	print "Looking for fields separated by '%s'" % separator
	print "Each line should match: '%s'" % string.join(('Image name', 'Grade', 'Comment'), separator)
	print "(Also accepted: '%s' with the -u option)" % string.join(('Image name', 'Grade', 'Custom comment', 'Comment'), separator)

	if user:
		print "Will ingest grades in the youpi_firstqeval table"
		try:
			user = User.objects.filter(username__exact = user)[0]
		except:
			# User not found; exiting
			print "Abort: user '%s' not found in database." % user
			sys.exit(1)

	else:
		print "Will ingest grades in the youpi_plugin_fitsin table"
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

			try: 
				name, grade, comment = line.split(separator)
				custom_comment = comment
			except ValueError, e:
				try:
					name, grade, custom_comment, comment = line.split(separator)
				except ValueError, e:
					print "\n[Parsing Error] in CSV file at line %d: %s" % (pos, e)
					raise KeyboardInterrupt

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
					if not rels: continue
					fitsins = Plugin_fitsin.objects.filter(task__in = [r.task for r in rels], task__success = True)
					if not user:
						q = """
						UPDATE youpi_plugin_fitsin 
						SET prevrelgrade="%s", prevrelcomment="%s"
						WHERE id IN (%s)
						""" % (grade, comment, string.join([str(i.id) for i in fitsins], ','))
						cur.execute(q)
						writes += len(fitsins)
					else:
						# Check for existing grade for this processing by this user
						matchg = FirstQEval.objects.filter(user = user, fitsin__in = fitsins).order_by('-date')
						if matchg:
							# Update the grade for the latest evaluation only
							m = matchg[0]
							m.grade = grade
							m.custom_comment = custom_comment
							m.save()
							writes += 1
						else:
							# No user-grade for this image, create a new one
							try:
								com = FirstQComment.objects.filter(comment = custom_comment)[0]
							except:
								com = FirstQComment.objects.all()[0]
							for fit in fitsins:
								m = FirstQEval(user = user, fitsin = fit)
								m.grade = grade
								m.comment = com
								m.custom_comment = custom_comment
								m.save()
							writes += len(fitsins)
					
			if not verbose:
				sys.stdout.write(term.BOL + "Found: %5d, Not Found: %5d, DB Writes: %5d, Line %5d" % (found, notfound, writes, pos))
			pos += 1

		connection._commit()
	except:
		sys.stdout.write(term.SHOW_CURSOR)
		raise

	f.close()
	sys.stdout.write(term.SHOW_CURSOR + '\n')

	if verbose:
		print "Found: %5d, Not Found: %5d, DB Writes: %5d, Line %5d" % (found, notfound, writes, pos-1)
	print "Time elapsed: %.2f sec" % (time.time() - start)


def main():
	parser = OptionParser(description = 'Tool for grading all Qualityfits-in processings')
	parser.add_option('-c', '--copy', 
			action = 'store_true', 
			default = False, 
			help = 'Copy a prevrelgrade to a user grade if no user grade available. Must be used with option -u'
	)
	parser.add_option('-d', '--delete', 
			default = False, 
			action = 'store_true', 
			help = 'Delete available grades in DB (previous release only, not user-defined ones)'
	)
	parser.add_option('-e', '--export', 
			default = False, 
			action = 'store_true', 
			help = 'Export all grades in 2 CSV files: one for user-defined grades, one for previous release grades'
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
	parser.add_option('-k', '--list-with-tag', 
			default = False, 
			action = 'store', 
			type = 'string',
			dest = 'tag',
			help = 'List available grades in DB with a given tag'
	)
	parser.add_option('-o', '--output', 
			default = False, 
			help = 'Ouput directory'
	)
	parser.add_option('-p', '--props', 
			default = False, 
			action = 'store_true', 
			help = 'List grades relative proportions'
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
	parser.add_option('-u', '--user', 
			default = False, 
			help = 'Grades as user'
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
	if options.copy and options.filename:
		parser.error('options -c and -i are mutually exclusive')
	if options.copy and options.list_only:
		parser.error('options -c and -l are mutually exclusive')
	if options.copy and options.delete:
		parser.error('options -c and -d are mutually exclusive')
	if options.export and options.delete:
		parser.error('options -e and -d are mutually exclusive')
	if options.export and options.copy:
		parser.error('options -e and -c are mutually exclusive')
	if options.export and options.list_only:
		parser.error('options -e and -l are mutually exclusive')
	if options.export and options.stats:
		parser.error('options -e and -t are mutually exclusive')
	if options.export and options.filename:
		parser.error('options -e and -i are mutually exclusive')

	try:
		start = time.time()
		if options.stats:
			from terapix.reporting.plain import PlainTextReport
			print PlainTextReport(data = get_stats())
		elif options.list_only:
			from terapix.reporting.csv import CSVReport
			print CSVReport(data = get_grades())
		elif options.tag:
			from terapix.reporting.csv import CSVReport
			print CSVReport(data = get_grades_with_tag(options.tag))
		elif options.filename:
			ingest_grades(options.filename, options.simulate, options.user, verbose = options.verbose)
		elif options.delete:
			delete_grades(options.simulate, verbose = options.verbose)
		elif options.props:
			from terapix.reporting.csv import CSVReport
			print CSVReport(data = get_proportions())
		elif options.copy:
			if not options.user:
				parser.error('option -c must be used with option -u')
			copy_grades(options.simulate, options.user, verbose = options.verbose)
		elif options.export:
			export_grades(options.output, verbose = options.verbose)

		print "Took: %.2fs" % (time.time()-start)
	except KeyboardInterrupt:
		print "Exiting..."
		sys.exit(2)


if __name__ == '__main__':
	main()
