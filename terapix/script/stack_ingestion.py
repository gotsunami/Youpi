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

import MySQLdb
import pyfits
import re, glob, string, pprint
import math, md5, random
import marshal, base64, zlib
import os, os.path, sys, time, shutil

from types import *
from settings import *
from DBGeneric import *

NULLSTRING = ''
FITSEXT = '.fits'

g = None
(INFO, WARNING, FATAL) = ('INFO', 'WARNING', 'FATAL')
DEBUG_LEVELS = (INFO, WARNING, FATAL)

# Custom exceptions
class DebugError(Exception): pass
class IngestionError(Exception): pass

def getNowDateTime(lt = None):
	"""
	Returns local date time
	"""
	if not lt: lt = time.time()
	return "%4d-%02d-%02d %02d:%02d:%02d" % time.localtime(lt)[:6]

def debug(msg, level = INFO):
	"""
	Prints msg (of severity level) to stdout. Usefull for debugging.
	"""

	if type(level) is not StringType:
		raise TypeError, "level param must be a string not type " + type(level)

	if level not in DEBUG_LEVELS:
		raise DebugError, "No debugging level named: " + level

	print "%s [%s] %s" % (getNowDateTime(time.time()), level, msg)

def getFITSheader(fitsObj, fitsfile):
	"""
	Returns a valid FITS header if found.
	"""
	try:
		h1 = fitsObj[1].header
	except IndexError, e:
		try:
			h1 = fitsObj[0].header
		except:
			#
			# Trick needed to get FITS info because r.info() prints to stdout
			# directly
			#
			old = sys.stdout
			buf = StringBuffer()
			sys.stdout = buf
			fitsObj.info()
			sys.stdout = old

			debug("Could not find FITS header. Aborted. Reason: %s" % e, WARNING)
			debug("Don't know how to process %s" % fitsfile, WARNING)
			debug("Content of %s is:\n%s" % (fitsfile, buf))
			debug("Skipping processing of %s" % fitsfile, WARNING)
			fitsObj.close()
			raise IngestionError, 'No suitable header found. Could not process this image'
	except Exception, e:
			fitsObj.close()
			debug("Erro while processing header of %s: %s" % (fitsfile, e), FATAL)
			sys.exit(1)

	return h1

def getFITSField(fitsheader, fieldname, default = NULLSTRING):
	"""
	Returns data associated with fieldname. If fieldname exists in FITS header, the 
	returned value is equivalent to header[fieldname]. If fieldname does not exist,
	the exception is catched and logged, the returned value is the content of default.
	"""
	try: data = fitsheader[fieldname]
	except KeyError, e:
		debug("Field not found in file's header (%s)" % e, WARNING)
		return default

	if type(data) == StringType:
		return data.strip()
	else:
		return data

def run_ingestion(stackFile):
	"""
	Ingestion of Stack image
	@param stackFile full path to file
	"""

	global g, user_id
	duration_stime = time.time()
	path = os.path.dirname(stackFile)

	debug("Starting ingestion of stack image: %s" % stackFile)

	res = g.execute("SELECT dflt_group_id, dflt_mode FROM youpi_siteprofile WHERE user_id=%d" % int(user_id))
	perms = {'group_id': res[0][0], 'mode': res[0][1]}
	g.begin()
	try:
		g.setTableName('youpi_ingestion')
		g.insert(	start_ingestion_date = getNowDateTime(duration_stime),
					end_ingestion_date = getNowDateTime(duration_stime),
					# FIXME
					email = '',
					user_id = user_id,
					label = "Stack %s" % os.path.basename(stackFile),
					check_fitsverify  = 0,
					check_qso_status = 0,
					check_multiple_ingestion =0,
					path = path,
					group_id = perms['group_id'],
					mode = perms['mode'],
					exit_code = 0 )
		ingestionId = g.con.insert_id()
	except Exception, e:
		debug(e, FATAL)
		g.con.rollback()
		sys.exit(1)

	# Get instruments
	res = g.execute("""select id, name from youpi_instrument;""")
	instruments = {}
	for inst in res:
		instruments[inst[1]] = (inst[0], re.compile(inst[1], re.I))
	
	#
	# OK, seems like this file can be ingested
	#
	fitsNoExt = os.path.basename(stackFile.replace(FITSEXT, NULLSTRING))

	# MD5 sum computation
	debug("Computing MD5 checksum...")
	stime = time.time()
	checksum = md5.md5(open(stackFile,'rb').read()).hexdigest()
	etime = time.time()
	debug("MD5: %s (%.2f)" % (checksum, etime-stime))

	r = pyfits.open(stackFile)
	try:
		header = getFITSheader(r, stackFile)
	except IngestionError, e:
		# Do not process this image
		debug("Skipping ingestion of %s" % stackFile, WARNING)
		return
		
	# Keywords checks
	t = getFITSField(header, 'telescop')
	detector = getFITSField(header, 'detector')
	o = getFITSField(header, 'object')
	e = getFITSField(header, 'exptime')
	eq = getFITSField(header, 'equinox')
	channel = getFITSField(header, 'filter')

	debug("%s data detected" % detector)

	# Instrument matching
	instrument_id = -1
	for val in instruments.values():
		# Compiled pattern
		cp = val[1]
		if cp.match(detector):
			instrument_id = val[0]

	if instrument_id < 0:
		debug("Matching instrument '%s' not found in DB. Image ingestion skipped." % detector, WARNING)
		sys.exit(1)

	# CHANNEL DATABASE INGESTION
	res = g.execute("""select name from youpi_channel where name="%s";""" % channel)
	if not res:
		try:
			g.setTableName('youpi_channel')
			g.insert(	name = channel,
						instrument_id = instrument_id )
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			g.con.rollback()
			sys.exit(1)
	else:
		debug("Channel %s already existing in DB" % channel)
	
	res = g.execute("""select name, checksum from youpi_image where name = "%s";""" % fitsNoExt)
	old = fitsNoExt
	# Image name found
	if res:
		# Compare checksums
		dbchecksum = res[0][1]
		if checksum == dbchecksum:
			# Do nothing because the same physical image is already ingested
			debug("Image with same name and checksum already ingested. Skipping...")
			return

		# FIXME
		# Different checksums, so go ahead
		#fitsNoExt = freshImageName(fitsNoExt, g)
		#if allowSeveralIngestions != 'yes':
		#	if old != fitsNoExt:
		#		debug("Already ingested. Skipping...")
		#		continue

	# First gets run and channel IDs
	q = """
	SELECT chan.id, i.id
	FROM youpi_channel AS chan, youpi_instrument AS i
	WHERE chan.name = '%s'
	AND i.name = '%s';""" % (channel, detector)
	res = g.execute(q)

	# Then insert image into db
	try:
		g.setTableName('youpi_image')
		g.insert(
			name = fitsNoExt,
			object = o,
			exptime = e,
			equinox = eq,
			ingestion_date = getNowDateTime(),
			checksum = checksum,
			path = path,
			channel_id = res[0][0],
			ingestion_id = ingestionId,
			instrument_id = res[0][1]
		)
	except MySQLdb.DatabaseError, e:
		debug(e, FATAL)
		g.con.rollback()
		sys.exit(1)
	except Exception, e:
		debug(e, FATAL)
		g.con.rollback()
		debug("SQL Query: %s" % q)
		debug("Python error: %s" % e, FATAL)
		sys.exit(1)

	# Computing image sky footprint
	footprint_start = time.time()
	poly = []
	total = range(1, len(r))
	if not total: total = [0]
	for i in total:
		pix1, pix2 = r[i].header['CRPIX1'], r[i].header['CRPIX2']
		val1, val2 =  r[i].header['CRVAL1'], r[i].header['CRVAL2']
		cd11, cd12, cd21, cd22 = r[i].header['CD1_1'], r[i].header['CD1_2'], r[i].header['CD2_1'], r[i].header['CD2_2']
		nax1, nax2 = r[i].header['NAXIS1'], r[i].header['NAXIS2']

		x1,y1 = 1 - pix1, 1 - pix2
		x2,y2 = nax1 - pix1, 1 - pix2
		x3,y3 = nax1 - pix1, nax2 - pix2
		x4,y4 = 1 - pix1, nax2 - pix2

		ra1, dec1, ra2, dec2, ra3, dec3, ra4, dec4 = (	
			val1+cd11*x1+cd12*y1,
			val2+cd21*x1+cd22*y1,
			val1+cd11*x2+cd12*y2,
			val2+cd21*x2+cd22*y2,
			val1+cd11*x3+cd12*y3,
			val2+cd21*x3+cd22*y3,
			val1+cd11*x4+cd12*y4,
			val2+cd21*x4+cd22*y4 
		)
		poly.append("(%.20f %.20f, %.20f %.20f, %.20f %.20f, %.20f %.20f, %.20f %.20f)" % (ra1, dec1, ra2, dec2, ra3, dec3, ra4, dec4, ra1, dec1))

	q = "GeomFromText(\"MULTIPOLYGON(("
	for p in poly: q += "%s, " % p
	q = q[:-2] + "))\")"
	
	try: g.execute("""UPDATE youpi_image SET skyfootprint=%s WHERE name="%s";""" % (q, fitsNoExt))
	except Exception, e:
		debug(e, FATAL)
		g.con.rollback()
		sys.exit(1)

	# Preparing data to insert centerfield point
	# FIXME
	ra = de = 0
	cf = "GeomFromText('POINT(%s %s)')" % (ra, de)
	qu = """UPDATE youpi_image SET centerfield=%s WHERE name="%s";""" % (cf, fitsNoExt)
	try: g.execute(qu)
	except Exception, e:
		debug(e, FATAL)
		g.con.rollback()

	debug("Sky footprint/centerfield took: (%.3f)" % (time.time()-footprint_start))
	debug("Ingested in database as '%s'" % fitsNoExt)

	# Commits for that image
	g.con.commit()
	debug("Stack ingestion done. Took %.2fs." % (time.time() - duration_stime))
	sys.exit(0)
	

if __name__ == '__main__':
	print "Running from the CLI"
	# Connection object to MySQL database 
	try:
		db = DB(host = DATABASE_HOST,
				user = DATABASE_USER,
				passwd = DATABASE_PASSWORD,
				db = DATABASE_NAME)

		# Beginning transaction
		g = DBGeneric(db.con)

		res = g.execute("SELECT id, username FROM auth_user LIMIT 1")
		debug("Proceeding as user '%s'" % res[0][1])
		user_id = res[0][0]
		run_ingestion(sys.argv[1])

	except MySQLdb.DatabaseError, e:
		debug(e, FATAL)
		sys.exit(1)

	except IndexError, e:
		debug("Incorrect arguments passed to the script: %s" % e, FATAL)
		sys.exit(1)
