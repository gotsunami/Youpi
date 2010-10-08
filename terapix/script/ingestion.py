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
import os, sys, time, shutil
import smtplib

from types import *
from settings import *
from DBGeneric import *

FITSEXT = '.fits'
GLOBFITS = '*' + FITSEXT
NULLSTRING = ''

# Global variables for debugging purpose. See debug() function.
(INFO, WARNING, FATAL) = ('INFO', 'WARNING', 'FATAL')
DEBUG_LEVELS = (INFO, WARNING, FATAL)

#
# Debugging information is logged to this file which will be sent
# by email at the end of the process
#
CLUSTER_LOG_FILE = NULLSTRING

email = NULLSTRING
script_args = {}
# Ingestion translation table
ittdata = {}

# SQL
ingestionId = -1
g = None

# Custom exceptions
class DebugError(Exception): pass
class IngestionError(Exception): pass
class MissingKeywordError(Exception): pass

class StringBuffer:
	"""
	String buffer class that provide a write method. Can be useful to redirect stdout to a string.
	"""
	def __init__(self):
		self.data = NULLSTRING

	def write(self, data):
		try:
			self.data += data
		except Exception, e:
			debug("StringBuffer exception, could not append data: %s" % e, WARNING)

	def __str__(self):
		return self.data

def getNowDateTime(lt = time.time()):
	"""
	Returns local date time
	"""
	return "%4d-%02d-%02d %02d:%02d:%02d" % time.localtime(lt)[:6]

def getNowTime(lt = time.time()):
	"""
	Returns local time
	"""
	return "%02d:%02d:%02d" % time.localtime(lt)[3:6]
	
def debug(msg, level = INFO):
	"""
	Prints msg (of severity level) to stdout. Usefull for debugging.
	"""

	global clog

	if type(level) is not StringType:
		raise TypeError, "level param must be a string not type " + type(level)

	if level not in DEBUG_LEVELS:
		raise DebugError, "No debugging level named: " + level

	clog.write("%s [%s] %s\n" % (getNowTime(time.time()), level, msg))

def sendmail(status, to, start, end):
	"""
	Send email report (plain text) to user
	"""

	global clog, email, script_args, g, ingestionId

	# Updates end time
	try:
		g.begin()
		g.setTableName('youpi_ingestion')
		g.update(	end_ingestion_date = getNowDateTime(end),
					exit_code = status,
					wheres = {'id': ingestionId} )
		g.con.commit()
	except Exception, e:
		debug(e, FATAL)
		g.con.rollback()

	# Log ingestion process duration
	debug("Ingestion process over. Tooked %.2f sec." % (end - start))

	clog.close()
	out = open(CLUSTER_LOG_FILE, 'r')
	data = out.readlines()
	log = NULLSTRING
	for line in data:
		log += line
	out.close()

	# Deletes temporary log file
	os.remove(CLUSTER_LOG_FILE)

	status_msg = NULLSTRING
	if status == 0:
		status_msg = "normally with status code %d" % status
	else:
		status_msg = "with ERRORS, status code %d" % status

	body = """
This is an automated email from the Youpi system on machine clix.iap.fr.
Please do not reply.

The job has exited %s.

The following options have been set from the Youpi web interface:
- Skip ingestion for non fitsverify compliant images: %s
- Images flagged as VALIDATED: %s
- Allow images to be ingested several times: %s

Data have been processed on %s from directory:
%s

Submitted at: %s
Completed at: %s
Elapsed time: %.02f seconds
		""" % ( status_msg,									# Exit code
				script_args['skip_fitsverify'],				# Skip ingestion (fitsverify)
				script_args['select_validation_status'],	# define the images status for ingestion
				script_args['allow_several_ingestions'],	# Multiple ingestions
				script_args['host'],						# Processing host
				script_args['path'],						# Path to data
				time.asctime(time.localtime(start)), 		# Start
				time.asctime(time.localtime(end)), 			# End
				(end-start)									# Duration
			)

	msg = "Subject: [Youpi] Report for ingestion %s [%d]\r\nFrom: youpi_noreply@iap.fr\r\nTo: %s\r\n\n%s\n%s" % (script_args['ingestion_id'], status, email, body, log) 

	if INGESTION_SEND_MAIL:
		s = smtplib.SMTP('localhost')
		s.sendmail(INGESTION_MAIL_FROM, email, msg)
		s.quit()
	else:
		print msg

	# Stores report into DB (base64 over zlib compression
	try:
		g.begin()
		g.setTableName('youpi_ingestion')
		g.update(	report = base64.encodestring(zlib.compress(msg, 9)).replace('\n', ''),
					wheres = {'id' : ingestionId} )
		g.con.commit()
	except Exception, e:
		debug(e, FATAL)
		g.con.rollback()

def freshImageName(nameWithoutExt, g):
	"""
	Generates a new image name based on nameWithoutExt. Current implementation only append an 
	underscore and a digit to the name and returns it.
	"""

	global email

	newName = nameWithoutExt
	
	try:
		res = g.execute("select name from youpi_image where name like '" + nameWithoutExt + '%\';')
	except MySQLdb.DatabaseError, e:
		debug(e, FATAL)
		sendmail(1, email, time.time(), time.time())
		sys.exit(1)

	newName += '_' + str(len(res))

	return newName

def getFITSField(hdulist, fieldname, default = None):
	"""
	Returns data associated with fieldname. 
	fieldname is a Youpi keyword starting by 'Y'.
	If fieldname does not exist, the exception is catched and logged, the returned 
	value is the content of default.
	"""

	data = None
	srcKeyword = ittdata[fieldname]['SRC']
	# Looking for user-defined string
	if srcKeyword.startswith('"') and srcKeyword.endswith('"'):
		return srcKeyword[1:-1]

	# Looking for FITS keyword in all extensions
	for hdu in hdulist:
		try:
			data = str(hdu.header[srcKeyword]).strip()
		except KeyError:
			# Keyword not found in this extension, continue
			pass

	if not data:
		# Keyword not found in any extension
		if default:
			return default
		else:
			debug("\tMissing '%s' keyword; not found in header file" % srcKeyword, WARNING)
			raise MissingKeywordError, fieldname

	return data

def run_ingestion():
	"""
	Ingestion procedure of FITS images in the database
	"""

	global log, email, script_args, ingestionId, g, ittdata

	email = script_args['email']
	user_id = script_args['user_id']
	path = script_args['path']
	ingestion_id = script_args['ingestion_id']

	# parsing otherArgs

	duration_stime = time.time()

	debug('Starting data processing from ' + path)

	os.chdir(path)
	fitsFiles = glob.glob(GLOBFITS)

	idx = 0
	total = len(fitsFiles)
	debug("Number of images to process: %d" % total)

	try:
		res = g.execute("""select id, itt from youpi_instrument where name="%s";""" % script_args['ittname'])
	except MySQLdb.DatabaseError, e:
		debug(e, FATAL)
		sendmail(1, email, duration_stime, time.time())
		sys.exit(1)
	instrument_id = res[0][0]
	# Get current ingestion translation table
	ittdata = marshal.loads(zlib.decompress(base64.decodestring(res[0][1])))
	debug("Selected instrument: %s" % script_args['ittname'])

	if script_args['select_validation_status'] == 'yes':
		vStatus = 'VALIDATED'
	else:
		vStatus = 'OBSERVED'
	debug("Every images will be flagged as %s during the ingestion" % vStatus)

	# 
	# Due to integrity constraints, entries have to be created into
	# youpi_ingestion
	#

	# Add a new entry into youpi_ingestion table
	vars = [['skip_fitsverify', 0], ['select_validation_status', 0], ['allow_several_ingestions', 0]]

	for i in vars:
		if script_args[i[0]] == 'yes':
			i[1] = 1

	res = g.execute("SELECT dflt_group_id, dflt_mode FROM youpi_siteprofile WHERE user_id=%d" % int(user_id))
	perms = {'group_id': res[0][0], 'mode': res[0][1]}
	try:
		g.begin()
		g.setTableName('youpi_ingestion')
		g.insert(	start_ingestion_date = getNowDateTime(duration_stime),
					end_ingestion_date = getNowDateTime(duration_stime),
					email = email,
					user_id = user_id,
					label = ingestion_id,
					check_fitsverify  = vars[0][1],
					is_validated = vars[1][1],
					check_multiple_ingestion = vars[2][1],
					path = path,
					group_id = perms['group_id'],
					mode = perms['mode'],
					exit_code = 0 )
		ingestionId = g.con.insert_id()
		g.con.commit()

	except Exception, e:
		debug(e, FATAL)
		g.con.rollback()
		sendmail(1, email, duration_stime, time.time())
		sys.exit(1)

	global is_validated_for_image
	is_validated_for_image = vars[1][1]

	#
	# Get instruments
	#
	try:
		res = g.execute("""select id, name from youpi_instrument;""")
	except MySQLdb.DatabaseError, e:
		debug(e, FATAL)
		sendmail(1, email, duration_stime, time.time())
		sys.exit(1)
	
	instruments = {}
	for inst in res:
		instruments[inst[1]] = (inst[0], re.compile(inst[1], re.I))
	
	for fitsfile in fitsFiles:
		g.begin()

		#
		# Check that file is FITS compliant
		#
		try:
			skip_fitsverify = script_args['skip_fitsverify']
		except KeyError, e:
			debug(e, FATAL)
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)
			
		process = True
		# Current image index
		idx += 1

		debug("%03d/%03d %s" % (idx, total, fitsfile))
		
		fitsverify = os.system(CMD_FITSVERIFY + " -q -e %s" % fitsfile)
		
		if skip_fitsverify == 'yes':
			#
			# skip ingestion when fitsverify return 1 and fits verify option is not checked
			#
			if fitsverify != 0:
				# FITS file not compliant...
				debug("\tFitsverify: may have fitsverify problems and won't be ingested", WARNING)
				process  = False
			else:
				debug("\tFitsverify: OK" )
		else:
			if fitsverify != 0:
				debug("\tFitsverify: may have fitsverify problems", WARNING)
			else:
				debug("\tFitsverify: OK" )

		if not process:
			 continue
		
		#
		# OK, seems like this file can be ingested
		#
		fitsNoExt = fitsfile.replace(FITSEXT, NULLSTRING)

		# MD5 sum computation
		stime = time.time()
		checksum = md5.md5(open(fitsfile,'rb').read()).hexdigest()
		etime = time.time()
		debug("\tmd5: %s (%.2f)" % (checksum, etime-stime))

		hdulist = pyfits.open(fitsfile)
		hdulist.close()
		debug("\tHDUs: %d (primary HDU + %d extensions)" % (len(hdulist), len(hdulist) - 1))

		try:
			h_runid = getFITSField(hdulist, 'YRUN', 'UNKNOWN')
			h_instrument = getFITSField(hdulist, 'YINSTRUMENT')
			h_telescop = getFITSField(hdulist, 'YTELESCOP')
			h_detector = getFITSField(hdulist, 'YDETECTOR')
			h_object = getFITSField(hdulist, 'YOBJECT')
			h_airmass = getFITSField(hdulist, 'YAIRMASS')
			h_exptime = getFITSField(hdulist, 'YEXPTIME')
			h_dateobs = getFITSField(hdulist, 'YDATEOBS')
			h_equinox = getFITSField(hdulist, 'YEQUINOX')
			h_filter = getFITSField(hdulist, 'YFILTER')
			h_ra = getFITSField(hdulist, 'YRA')
			h_dec = getFITSField(hdulist, 'YDEC')
		except MissingKeywordError, fieldname:
			debug("\tImage %s Skipped" % fitsfile, WARNING)
			continue

		try:
			h_flat = getFITSField(hdulist, 'YFLAT')
			if h_flat:
				fl = h_flat.split('.fits')
				if re.search("\.fit\[(\d+)\]", fl[0]):
					h_flat = re.sub('\.fit\[(\d+)\]','', fl[0]) + FITSEXT
				else:
					h_flat = fl[0] + FITSEXT

		except MissingKeywordError:
			# Missing flat info don't halt image ingestion
			debug("\tMissing flat information in header", WARNING)
			h_flat = NULLSTRING

		try:
			h_mask = getFITSField(hdulist, 'YMASK')
			if h_mask:
				ma = h_mask.split('.fits')
				h_mask = ma[0] + FITSEXT
		except MissingKeywordError:
			# Missing flat info don't halt image ingestion
			debug("\tMissing mask information in header", WARNING)
			h_mask = NULLSTRING

		#
		# RUN DATABASE INGESTION
		#
		try:
			res = g.execute("""select Name from youpi_run where name="%s";""" % h_runid)
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)
		except Exception, e:
			debug("%s Run name unknown (%s), skipping file..." % (fitsfile, e))
			continue
		
		debug("\t%s data detected" % h_detector)

		if not res:
			try:
				g.setTableName('youpi_run')
				g.insert(	name = h_runid,
							instrument_id = instrument_id )
			except MySQLdb.DatabaseError, e:
				debug(e, FATAL)
				g.con.rollback()
				sendmail(1, email, duration_stime, time.time())
				sys.exit(1)
		else:
			print "%s: run %s already existing in DB" % (fitsfile, h_runid)

		#
		# CHANNEL DATABASE INGESTION
		#
		try:
			res = g.execute("""select Name from youpi_channel where name="%s";""" % h_filter)
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)

		if not res:
			try:
				g.setTableName('youpi_channel')
				g.insert(	name = h_filter,
							instrument_id = instrument_id )
			except MySQLdb.DatabaseError, e:
				debug(e, FATAL)
				g.con.rollback()
				sendmail(1, email, duration_stime, time.time())
				sys.exit(1)
		else:
			print "%s: channel %s already existing in DB" % (fitsfile, h_filter)
	
		#
		# Image ingestion
		#
	
		#
		# Youpi does not (yet!) deal with weight maps generated 
		# by QFits
		#
		weight = re.search('_weight' + FITSEXT, fitsfile);

		if weight:
			debug("%s is a weight map. Skipping..." % fitsfile)
			continue

		try:
			res = g.execute("""select name, checksum from youpi_image where name = "%s";""" % fitsNoExt);
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)
			
		try:
			allowSeveralIngestions = script_args['allow_several_ingestions']
		except KeyError, e:
			debug(e, FATAL)
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)

		#
		# Ingest image under a different name, according to a renaming policy 
		# defined into freshImageName()
		#
		
		old = fitsNoExt
		# Image name found
		if res:
			# Compare checksums
			dbchecksum = res[0][1]
			if checksum == dbchecksum:
				# Option On will allow multiple ingestion(for same checksum, computation of new name)
				if allowSeveralIngestions == 'yes':
					fitsNoExt = freshImageName(fitsNoExt, g)
					debug("\tImage %s with same name and checksum: multiple option state to ON, Ingestion..." % fitsfile)
				
				else:
					debug("\tImage %s with same name and checksum: multiple option state to OFF, Skipping..." % fitsfile)
					continue
			else:
				debug("Image %s already exists in database (same odometer number for different checksum). Skipping..." % fitsfile, WARNING)
				continue

		# First gets run and channel IDs
		try:
			q = """
			SELECT run.id, chan.id
			FROM youpi_run AS run, youpi_channel AS chan
			WHERE run.name = '%s'
			AND chan.name = '%s';""" % (h_runid, h_filter)
			res = g.execute(q)

		except MySQLdb.DatabaseError, e:
			debug("MySQL error: %s" % e, FATAL)
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)
		except Exception, e:
			debug("Unable to process SQL query: %s. Skipping image" % q, WARNING)
			continue
		
		# Then insert image into db
		try:
			g.setTableName('youpi_image')
			g.insert(
				name = fitsNoExt,
				object = h_object,
				airmass = h_airmass,
				exptime = h_exptime,
				dateobs = h_dateobs,
				equinox = h_equinox,
				ingestion_date = getNowDateTime(),
				checksum = checksum,
				flat = h_flat,
				mask = h_mask,
				path = path,
				alpha = h_ra,
				delta = h_dec,
				is_validated = is_validated_for_image,
				channel_id = res[0][1],
				ingestion_id = ingestionId,
				instrument_id = instrument_id
			)
	
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			g.con.rollback()
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)
	
		except Exception, e:
			debug(e, FATAL)
			g.con.rollback()
			debug("SQL Query: %s" % q)
			debug("Python error: %s" % e, FATAL)
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)

		# Filling youpi_rel_ri table
		# Warning: this block of code uses the last_insert_id() feature thus should not be
		# moved
		try:
			g.setTableName('youpi_rel_ri')
			g.insert( run_id = res[0][0], image_id = g.con.insert_id() )
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			g.con.rollback()
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)
		except Exception, e:
			debug(e, FATAL)
			g.con.rollback()
			debug("SQL Query: %s" % q)
			debug("Python error: %s" % e, FATAL)
			sendmail(1, email, duration_stime, time.time())
			sys.exit(1)

		#
		# Computing image sky footprint
		#
		footprint_start = time.time()
		poly = []
		for i in range(1, len(hdulist)):
			pix1, pix2 = hdulist[i].header['CRPIX1'], hdulist[i].header['CRPIX2']
			val1, val2 = hdulist[i].header['CRVAL1'], hdulist[i].header['CRVAL2']
			cd11, cd12, cd21, cd22 = hdulist[i].header['CD1_1'], hdulist[i].header['CD1_2'], hdulist[i].header['CD2_1'], hdulist[i].header['CD2_2']
			nax1, nax2 = hdulist[i].header['NAXIS1'], hdulist[i].header['NAXIS2']

			x1,y1 = 1 - pix1, 1 - pix2
			x2,y2 = nax1 - pix1, 1 - pix2
			x3,y3 = nax1 - pix1, nax2 - pix2
			x4,y4 = 1 - pix1, nax2 - pix2

			ra1, dec1, ra2, dec2, ra3, dec3, ra4, dec4 = (
				val1+cd11 * x1+cd12*y1,
				val2+cd21 * x1+cd22*y1,
				val1+cd11 * x2+cd12*y2,
				val2+cd21 * x2+cd22*y2,
				val1+cd11 * x3+cd12*y3,
				val2+cd21 * x3+cd22*y3,
				val1+cd11 * x4+cd12*y4,
				val2+cd21 * x4+cd22*y4
			)

			poly.append("(%.20f %.20f, %.20f %.20f, %.20f %.20f, %.20f %.20f, %.20f %.20f)" % (ra1, dec1, ra2, dec2, ra3, dec3, ra4, dec4, ra1, dec1))

		q = "GeomFromText(\"MULTIPOLYGON(("
		for p in poly:
				q += "%s, " % p
		q = q[:-2] + "))\")"
		
		try:
			g.begin()
			g.execute("""UPDATE youpi_image SET skyfootprint=%s WHERE name="%s";""" % (q, fitsNoExt))
			g.con.commit()
		except Exception, e:
			debug(e, FATAL)
			g.con.rollback()
			h_runid = 'ERROR'

		#
		# Preparing data to insert centerfield point
		#
		cf = "GeomFromText('POINT(%s %s)')" % (h_ra, h_dec)
		qu = """UPDATE youpi_image SET centerfield=%s WHERE name="%s";""" % (cf, fitsNoExt)
		try:
			g.begin()
			g.execute(qu)
			g.con.commit()
		except Exception, e:
			debug(e, FATAL)
			g.con.rollback()
			h_runid = 'ERROR'

		debug("\tSky footprint/centerfield took: (%.2f)" % (time.time()-footprint_start))
		# Done
		debug("\tIngested in database as '%s'" % fitsNoExt)
	
		# Commits for that image
		g.con.commit()
			
	duration_etime = time.time()

	# Send email notification to user
	sendmail(0, email, duration_stime, duration_etime)
	
if __name__ == '__main__':
	# Connection object to MySQL database 
	try:
		db = DB(host = DATABASE_HOST,
				user = DATABASE_USER,
				passwd = DATABASE_PASSWORD,
				db = DATABASE_NAME)

		# Beginning transaction
		g = DBGeneric(db.con)

		# Related to Condor transfer_ouput_file
		try:
			shutil.copyfile('DBGeneric.pyc', '/tmp/DBGeneric.pyc')
		except:
			pass

		#
		# De-serialize data passed as a string into arg 1
		#
		script_args = marshal.loads(base64.decodestring(sys.argv[1]))

		CLUSTER_LOG_FILE = "%s-%s.%s" % (CONDOR_OUTPUT, script_args['ingestion_id'], md5.md5(str(time.time())).hexdigest())
		clog = open(CLUSTER_LOG_FILE, 'w')
		run_ingestion()

	except MySQLdb.DatabaseError, e:
		debug(e, FATAL)
		sendmail(1, 'monnerville@iap.fr', time.time(), time.time())
		sys.exit(1)

	except IndexError, e:
		debug("Incorrect arguments passed to the script: %s" % e, FATAL)
		sendmail(1, 'monnerville@iap.fr', time.time(), time.time())
		sys.exit(1)
