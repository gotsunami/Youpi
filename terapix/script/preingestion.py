#!/usr/bin/env python

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

import pyfits,time, os,glob,re
import os.path
import sys
import datetime,time
from DBGeneric import *
sys.path.insert(0, '..')
from settings import *

def dico(dat1,tbdata2):
	
	sup = len(tbdata2) - 1
	inf = 0
	
	while sup > inf + 1:
		if datetime.datetime(*(time.strptime(tbdata2[(inf+sup)/2].field('start_time'),"%Y/%m/%d,%H:%M:%S")[0:6])) < dat1 :
			inf = ((inf+sup)/2)
		else:
			sup = ((inf+sup)/2)
	return sup

def preingest_table(g, fitstable, path):
	"""
	g: DBGeneric instance
	fitsTable name, path to table
	"""

	inserts = 0
	updates = 0

	f = pyfits.open(os.path.join(path, fitstable))
	tbdata = f[4].data
	
	#for absorption parameters
	tbdata2 = f[8].data
	print 'Processing', fitstable

	g.begin()
	g.setTableName('youpi_fitstables')

	

	for i in tbdata:
		name = i.field('filename')
		name = name.replace('.fits','')
		# TODO: fix this
		if name == 'NA':
			continue
		
		#matching "(\d)*s" images in fitstables
		if re.search('s',name):
			continue
		#matching "(\d)*o" images in fitstables
		if re.search('o',name):
			continue

		run = i.field('runid')
		instrument = i.field('instrument')
		channel = i.field('filter')
		qso = i.field('QSO_status')
		is_phot = i.field('is_phot')
		object = i.field('object')

		dat1 = datetime.datetime(*(time.strptime((i.field('expdate_ut')),"%Y/%m/%d,%H:%M:%S")[0:6]))
		
		if tbdata2 == None:
			continue
		
		index = dico(dat1,tbdata2)
		
		#
		#BUG to fix :not the right value because index error problem
		#
		#plus1 = datetime.datetime(*(time.strptime(tbdata2[index + 1].field('start_time'),"%Y/%m/%d,%H:%M:%S")[0:6]))
		#moin1 = datetime.datetime(*(time.strptime(tbdata2[index - 1].field('start_time'),"%Y/%m/%d,%H:%M:%S")[0:6]))

		#if (plus1 - dat1) > (dat1 - moin1):
			#absorption = tbdata2[index -1 ].field('zp_obs')  # when index - 1 < 0  NO VALUE FOUND
			#absorption_err = tbdata2[index - 1].field('zp_err') # when index - 1 < 0  NO VALUE FOUND
		#else:
			#absorption = tbdata2[index + 1 ].field('zp_obs')  # when index + 1 > len(tbdata2) NO VALUE FOUND
			#absorption_err = tbdata2[index + 1].field('zp_err') # when index + 1 > len(tbdata2) NO VALUE FOUND
		
		absorption = tbdata2[index].field('zp_obs')
		absorption_err = tbdata2[index].field('zp_err')
		
		try:
			g.insert(	name = name,
						instrument = instrument,
						run = run,
						channel = channel,
						qsostatus = qso,
						is_phot = is_phot,
						object = object,
						
						#for absorption parameters
						absorption = absorption,
						absorption_err = absorption_err,
						fitstable = os.path.join(path, fitstable) )

			inserts += 1
		except Exception, e:
			code = e[0]
			if code != 1062:
				g.con.rollback()
				print "Error:", e
				print name, run, instrument, channel, qso
				sys.exit(1)

			# Try update query
			res = g.execute("SELECT id FROM youpi_fitstables WHERE name='%s' AND run='%s' AND channel='%s'" %
				(name, run, channel))
			id = res[0][0]
			try:
				g.update(	name = name,
							instrument = instrument,
							run = run,
							channel = channel,
							qsostatus = qso,
							is_phot = is_phot,
							object = object,
						
							#for absorption parameters
							absorption = absorption,
							absorption_err = absorption_err,
							wheres = {'id' : id} )

				updates += 1
			except Exception, e:
				g.con.rollback()
				print "Error:", e
				print "Id:", id
				print g.query
				sys.exit(1)
	
	f.close()
	g.con.commit()

	return (inserts, updates)


if __name__ == '__main__':
	try:
		path = sys.argv[1]
	except:
		print "Usage: %s <path_to_data>" % sys.argv[0]
		sys.exit(1)

	os.chdir(path)
	files = glob.glob('mcmd.*.fits')

	db = DB(host = DATABASE_HOST,
		user = DATABASE_USER,
		passwd = DATABASE_PASSWORD,
		db = DATABASE_NAME)

	g = DBGeneric(db.con)

	start = time.time()
	for table in files:
		preingest_table(g, table, path)

	print "Time elapsed: %.02f" % (time.time()-start)
