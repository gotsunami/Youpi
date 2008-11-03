#!/usr/bin/env python

import MySQLdb
import sys
import wrapper_processing as w

from types import *
sys.path.insert(0, '..')
from settings import *
from DBGeneric import *

g = None

def doit():
	qfitsins = g.execute("SELECT id FROM youpi_plugin_fitsin")
	print "Total: %d images have been successfully qualityFITSed (first quality evaluation)" % len(qfitsins)

	i = 1
	for entry in qfitsins:
		print "---> Image %03d / %03d follows:" % (i, len(qfitsins))
		w.ingestQFitsInResults(entry[0], g);
		g.con.commit()
		i += 1

if __name__ == '__main__':
	# Connection object to MySQL database 
	try:
		db = DB(host = DATABASE_HOST,
				user = DATABASE_USER,
				passwd = DATABASE_PASSWORD,
				db = DATABASE_NAME)

		# Beginning transaction
		g = DBGeneric(db.con)

		doit()

	except MySQLdb.DatabaseError, e:
		debug(e, FATAL)
		sys.exit(1)
