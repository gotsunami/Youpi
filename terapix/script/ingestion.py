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

# SQL
ingestionId = -1
g = None

# Custom exceptions
class DebugError(Exception): pass
class IngestionError(Exception): pass

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
	
def debug(msg, level = INFO):
	"""
	Prints msg (of severity level) to stdout. Usefull for debugging.
	"""

	global clog

	if type(level) is not StringType:
		raise TypeError, "level param must be a string not type " + type(level)

	if level not in DEBUG_LEVELS:
		raise DebugError, "No debugging level named: " + level

	clog.write("%s [%s] %s\n" % (getNowDateTime(time.time()), level, msg))

def sendmail(status, to, start, end, runame):
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
		runame = 'ERROR'

	# Log ingestion process duration
	debug("Ingestion process over. It tooked %.2f sec." % (end - start))

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


def getFITSheader(fitsObj, fitsfile, duration_stime):
	"""
	Returns a valid FITS header if found.
	"""

	global email

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
			sendmail(1, email, duration_stime, time.time(), 'UNKNOWN')
			sys.exit(1)

	return h1

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
		sendmail(1, email, time.time(), time.time(), 'freshImageName() error')
		sys.exit(1)

	newName += '_' + str(len(res))

	return newName

def getFITSField(fitsheader, fieldname, default = NULLSTRING):
	"""
	Returns data associated with fieldname. If fieldname exists in FITS header, the 
	returned value is equivalent to header[fieldname]. If fieldname does not exist,
	the exception is catched and logged, the returned value is the content of default.
	"""

	try:
		data = fitsheader[fieldname]
	except KeyError, e:
		debug("\tField not found in file's header (%s)" % e, WARNING)
		return default

	return data

def run_ingestion():
	"""
	Ingestion procedure of FITS images in the database
	"""

	global log, email, script_args, ingestionId, g

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
		sendmail(1, email, duration_stime, time.time(), 'ERROR')
		sys.exit(1)

	is_validated_for_image = vars[1][1]

	#
	# Get instruments
	#
	try:
		res = g.execute("""select id, name from youpi_instrument;""")
	except MySQLdb.DatabaseError, e:
		debug(e, FATAL)
		sendmail(1, email, duration_stime, time.time(), '')
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
			sendmail(1, email, duration_stime, time.time(), runame)
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
				debug("\tiFitsverify: may have fitsverify problems and won't be ingested", WARNING)
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

		r = pyfits.open(fitsfile)
		try:
			header = getFITSheader(r, fitsfile, duration_stime)
		except IngestionError, e:
			# Do not process this image
			debug("Skippin ingestion of %s" % fitsfile, WARNING)
			continue
		
		#
		# RUNID is mandatory. A default run UNKNOWN is used when RUNID info is not 
		# found in the FITS header
		#
		runame = getFITSField(header, 'runid', 'UNKNOWN')

		# DBinstrument
		i = getFITSField(header, 'instrume')
		t = getFITSField(header, 'telescop')
		detector = getFITSField(header, 'detector')
		o = getFITSField(header, 'object')
		a = getFITSField(header, 'airmass')
		e = getFITSField(header, 'exptime')
		d = getFITSField(header, 'DATE-OBS')
		eq = getFITSField(header, 'equinox')
		chaname = getFITSField(header, 'filter')
		flat = getFITSField(header,'IMRED_FF')
		mask = getFITSField(header,'IMRED_MK')
		if flat:
			fl = flat.split('.fits')
			flat = fl[0] + FITSEXT
		if mask:
			ma = mask.split('.fits')
			mask = ma[0] + FITSEXT
		ra = getFITSField(header,'RA_DEG')
		de = getFITSField(header,'DEC_DEG') 

		#
		# RUN DATABASE INGESTION
		#
		try:
			res = g.execute("""select Name from youpi_run where name="%s";""" % runame)
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			sendmail(1, email, duration_stime, time.time(), runame)
			sys.exit(1)
		except Exception, e:
			debug("%s Run name unknown (%s), skipping file..." % (fitsfile, e))
			continue
		
		debug("\t%s data detected" % detector)

		instrument_id = -1
		for val in instruments.values():
			# Compiled pattern
			cp = val[1]
			if cp.match(detector):
				instrument_id = val[0]

		if instrument_id < 0:
			debug("Matching instrument '%s' not found in DB. Image ingestion skipped." % detector, WARNING)
			continue

		if not res:
			if detector == 'MegaCam' or i == 'MegaPrime':
				try:
					g.setTableName('youpi_run')
					g.insert(	name = runame,
								instrument_id = instrument_id )
				except MySQLdb.DatabaseError, e:
					debug(e, FATAL)
					g.con.rollback()
					sendmail(1, email, duration_stime, time.time(), runame)
					sys.exit(1)

			elif (detector == 'WIRCam' or i == 'WIRCam'):
				try:
					g.setTableName('youpi_run')
					g.insert(	name = runame,
								instrument_id = instrument_id )
				except MySQLdb.DatabaseError, e:
					debug(e, FATAL)
					g.con.rollback()
					sendmail(1, email, duration_stime, time.time(), runame)
					sys.exit(1)

			# elif (...)
			# Other detectors go here
		else:
			print "%s: run %s already existing in DB" % (fitsfile, runame)

		#
		# CHANNEL DATABASE INGESTION
		#
		try:
			res = g.execute("""select Name from youpi_channel where name="%s";""" % chaname)
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			sendmail(1, email, duration_stime, time.time(), runame)
			sys.exit(1)

		if not res:
			if detector == 'MegaCam' and t == 'CFHT 3.6m' and i == 'MegaPrime':
				try:
					g.setTableName('youpi_channel')
					g.insert(	name = chaname,
								instrument_id = instrument_id )
				except MySQLdb.DatabaseError, e:
					debug(e, FATAL)
					g.con.rollback()
					sendmail(1, email, duration_stime, time.time(), runame)
					sys.exit(1)
				
			elif detector == 'WIRCam' and t == 'CFHT 3.6m' and i == 'WIRCam':
				try:
					g.setTableName('youpi_channel')
					g.insert(	name = chaname,
								instrument_id = instrument_id )
				except MySQLdb.DatabaseError, e:
					debug(e, FATAL)
					g.con.rollback()
					sendmail(1, email, duration_stime, time.time(), runame)
					sys.exit(1)
		else:
			print "%s: channel %s already existing in DB" % (fitsfile, chaname)
	
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
			sendmail(1, email, duration_stime, time.time(), runame)
			sys.exit(1)
			
		try:
			allowSeveralIngestions = script_args['allow_several_ingestions']
		except KeyError, e:
			debug(e, FATAL)
			sendmail(1, email, duration_stime, time.time(), runame)
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
				# Do nothing because the same physical image is already ingested
				debug("\tImage with same name and checksum already ingested. Skipping...")
				continue

			# Different checksums, so go ahead
			fitsNoExt = freshImageName(fitsNoExt, g)
			if allowSeveralIngestions != 'yes':
				if old != fitsNoExt:
					debug("\tAlready ingested. Skipping...")
					continue

		#
		# Image not yet ingested
		# select validation status
		#


		if detector == 'MegaCam' or  i == 'MegaPrime':
			iname = 'Megacam'
	
		elif detector == 'WIRCam' or i == 'WIRCam':
			iname = 'Wircam'
		else:
			# TODO: other type of detector ?
			debug("Could not detect image's instrument type. Skipping...", WARNING)
			continue
	
		# First gets run and channel IDs
		try:
			q = """
			SELECT run.id, chan.id, i.id
			FROM youpi_run AS run, youpi_channel AS chan, youpi_instrument AS i
			WHERE run.name = '%s'
			AND chan.name = '%s'
			AND i.name = '%s';""" % (runame, chaname, iname)
			res = g.execute(q)

		except MySQLdb.DatabaseError, e:
			debug("MySQL error: %s" % e, FATAL)
			sendmail(1, email, duration_stime, time.time(), runame)
			sys.exit(1)
		except Exception, e:
			debug("Unable to process SQL query: %s. Skipping image" % q, WARNING)
			continue
		

		# Then insert image into db
		try:
			g.setTableName('youpi_image')
			g.insert(
				name = fitsNoExt,
				object = o,
				airmass = a,
				exptime = e,
				dateobs = d,
				equinox = eq,
				ingestion_date = getNowDateTime(),
				checksum = checksum,
				flat = flat,
				mask = mask,
				path = path,
				alpha = ra,
				delta = de,
				is_validated = is_validated_for_image,
				channel_id = res[0][1],
				ingestion_id = ingestionId,
				instrument_id = res[0][2]
			)
	
		except MySQLdb.DatabaseError, e:
			debug(e, FATAL)
			g.con.rollback()
			sendmail(1, email, duration_stime, time.time(), runame)
			sys.exit(1)
	
		except Exception, e:
			debug(e, FATAL)
			g.con.rollback()
			debug("SQL Query: %s" % q)
			debug("Python error: %s" % e, FATAL)
			sendmail(1, email, duration_stime, time.time(), runame)
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
			sendmail(1, email, duration_stime, time.time(), runame)
			sys.exit(1)
	
		except Exception, e:
			debug(e, FATAL)
			g.con.rollback()
			debug("SQL Query: %s" % q)
			debug("Python error: %s" % e, FATAL)
			sendmail(1, email, duration_stime, time.time(), runame)
			sys.exit(1)

		#
		# Computing image sky footprint
		#
		footprint_start = time.time()
		poly = []
		for i in range(1,len(r)):
			pix1,pix2 = r[i].header['CRPIX1'],r[i].header['CRPIX2']
			val1,val2 =  r[i].header['CRVAL1'],r[i].header['CRVAL2']
			cd11,cd12,cd21,cd22 = r[i].header['CD1_1'],r[i].header['CD1_2'],r[i].header['CD2_1'],r[i].header['CD2_2']
			nax1,nax2 = r[i].header['NAXIS1'],r[i].header['NAXIS2']

			x1,y1 = 1 - pix1, 1 - pix2
			x2,y2 = nax1 - pix1, 1 - pix2
			x3,y3 = nax1 - pix1, nax2 - pix2
			x4,y4 = 1 - pix1, nax2 - pix2

			# Manu's Method
			ra1, dec1, ra2, dec2, ra3, dec3, ra4, dec4 = (	val1+cd11*x1+cd12*y1,
			val2+cd21*x1+cd22*y1,
			val1+cd11*x2+cd12*y2,
			val2+cd21*x2+cd22*y2,
			val1+cd11*x3+cd12*y3,
			val2+cd21*x3+cd22*y3,
			val1+cd11*x4+cd12*y4,
			val2+cd21*x4+cd22*y4 )

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
			runame = 'ERROR'

		#
		# Preparing data to insert centerfield point
		#
		cf = "GeomFromText('POINT(%s %s)')" % (ra, de)
		qu = """UPDATE youpi_image SET centerfield=%s WHERE name="%s";""" % (cf, fitsNoExt)
		try:
			g.begin()
			g.execute(qu)
			g.con.commit()
		except Exception, e:
			debug(e, FATAL)
			g.con.rollback()
			runame = 'ERROR'

		debug("\tSky footprint/centerfield took: (%.2f)" % (time.time()-footprint_start))
		# Done
		debug("\tIngested in database as '%s'" % fitsNoExt)
	
		# Commits for that image
		g.con.commit()
			
	duration_etime = time.time()

	# Send email notification to user
	sendmail(0, email, duration_stime, duration_etime, runame)
	
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
		sendmail(1, 'monnerville@iap.fr', time.time(), time.time(), 'UNKNOWN')
		sys.exit(1)

	except IndexError, e:
		debug("Incorrect arguments passed to the script: %s" % e, FATAL)
		sendmail(1, 'monnerville@iap.fr', time.time(), time.time(), 'UNKNOWN')
		sys.exit(1)
