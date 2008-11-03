#!/usr/bin/env python

import time, sys
from DBGeneric import *

sys.path.insert(0, '..')
from settings import *

CSV_DELIM = ','

def get_report(g, csvFile):
	"""
	"""

	report = ''
	info = [] 

	try:
		f = open(csvFile, 'r')
		content = f.readlines()
		f.close()
	except:
		print "Error opening %s for reading. Aborted." % csvFile
		sys.exit(1)

	info.append(('CSV File', csvFile))
	info.append(('Field Delimiter', CSV_DELIM))
	info.append(('File Entries', len(content)))

	# Search database matches
	photcs = {}
	names = '('
	for line in content:
		name, flat, photc = line.split(',')
		names += "'%s'," % name
		photcs[name] = photc
		
	names = names[:-1] + ')'
	res = g.execute("SELECT  name, flat, photc FROM spica2_image WHERE name IN %s" % names)

	info.append(('DB Entries', len(res)))

	diff_photc = 0
	null_photc = 0
	for r in res:
		try:
			if float(r[2]) != float(photcs[r[0]]):
				diff_photc += 1
		except TypeError:
				# photc is NULL
				diff_photc += 1
				null_photc += 1

	info.append(('No PHOTC', null_photc))
	info.append(('Diff PHOTC', diff_photc))

	for i in info:
		report += "%-20s : %s\n" % (i[0], str(i[1]))

	return (report, photcs, res)


if __name__ == '__main__':
	try:
		csvFile = sys.argv[1]
	except:
		print "Usage: %s <csv_file>" % sys.argv[0]
		sys.exit(1)

	db = DB(host 	= DATABASE_HOST,
			user 	= DATABASE_USER,
			passwd 	= DATABASE_PASSWORD,
			db 		= DATABASE_NAME)

	g = DBGeneric(db.con)


	report, photcs, dbEntries = get_report(g, csvFile)
	print report

	try:
		ans = raw_input("Do you want to merge PHOTC data from the file into the database? ")
		if ans in ('y', 'Y', 'yes', 'YES'):
			start = time.time()
			g.begin()
			g.setTableName('spica2_image')

			try:
				update = 0
				for e in dbEntries:
					g.update(photc = photcs[e[0]], wheres = {'name' : e[0]})
					update += 1
				g.con.commit()
			except:
				g.con.rollback()
				print "Error:", e
				sys.exit(1)

			print "Done. %d PHOTC fields merged." % update
			print "Time elapsed: %.02f sec" % (time.time()-start)
		else:
			print "Nothing merged."
			sys.exit(0)
	except KeyboardInterrupt:
		print "\nExiting... nothing merged."
		sys.exit(0)
