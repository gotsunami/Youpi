#############################################################################
#
# Copyright (c) 2008-2010 Terapix Youpi development team. All Rights Reserved.
#                    Mathias Monnerville <monnerville@iap.fr>
#                    Gregory Semah <semah@iap.fr>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
##############################################################################

import sys, os, os.path, types
import pyfits, re, datetime
import marshal, zlib, base64
import MySQLdb
from DBGeneric import *
import settings

def genImageDotHead(image_id):
	"""
	Generate a FITS image's .head file. The image file is first accessed to get the number 
	of HDUs (extansions). Then keywords mapping is retrieved from the instrument's ITT in 
	order to get a proper HDU data.
	@return tuple of hdudata and total number of hdus in this image (primary + extansions)
	"""
	db = DB(host = settings.DATABASE_HOST,
			user = settings.DATABASE_USER,
			passwd = settings.DATABASE_PASSWORD,
			db = settings.DATABASE_NAME)

	# Beginning transaction
	g = DBGeneric(db.con)

	if type(image_id) != types.IntType:
		raise ValueError, "first argument image_id must be an integer"

	r = g.execute("""
SELECT im.path, im.name, ru.name, ins.itt, ins.name, im.dateobs, cha.name, im.flat, 
im.airmass, im.equinox, im.object, im.exptime, im.mask, im.alpha, im.delta
FROM youpi_image AS im, youpi_instrument AS ins, youpi_channel AS cha, youpi_rel_ri AS ri, youpi_run AS ru
WHERE im.id=%d 
AND im.instrument_id=ins.id
AND im.channel_id=cha.id
AND ri.image_id = im.id
AND ru.id = ri.run_id
""" % image_id)
	if not r: raise LookupError, "no image found with ID: %s" % image_id
	r = r[0]

	fname = os.path.join(r[0], r[1] + '.fits')
	if not os.path.exists(fname):
		fname = re.sub(r'_\d+\.fits$', '.fits', fname)

	hdulist = pyfits.open(fname)
	hdulist.close()

	# Get instrument translation table
	itt = marshal.loads(zlib.decompress(base64.decodestring(r[3])))

	try: run = r[2]
	except: run = None

	data = {
		'YRUN'			: run, 
#		'YDETECTOR': , 
#		'YTELESCOP': , 
		'YINSTRUMENT'	: r[4],
		'YDATEOBS'		: r[5],
		'YFILTER'		: r[6],
		'YFLAT'			: r[7],
		'YAIRMASS'		: r[8],
		'YEQUINOX'		: r[9],
		'YOBJECT'		: r[10],
		'YEXPTIME'		: r[11],
		'YMASK'			: r[12],
		'YRA'			: r[13],
		'YDEC'			: r[14],
	}

	hdudata = {}
	for k, v in data.iteritems():
		try: 
			val = float(str(v))
		except ValueError:
			if isinstance(v, datetime.datetime):
				v = v.isoformat()
			val = "'%s'" % v

		if itt[k].has_key('MAP'): 
			# Unmapped keyword are ignored since they are available in 
			# the image's header
			hdudata["%-8s" % itt[k]['MAP'][:8]] = val

	missing = []
	# Keyword copy feature (+KEYWORD)
	if itt.has_key('+COPY'):
		# List of missing keywords (not found in src image)
		for kw in itt['+COPY']:
			data = None
			# Search keyword in all extensions
			for hdu in hdulist:
				try: data = str(hdu.header[kw]).strip()
				except KeyError:
					# Keyword not found in this extension, continue
					pass
			if data: hdudata["%-8s" % kw[:8]] = data
			else: missing.append(kw)

	return (hdudata, len(hdulist), missing)

def main():
	if len(sys.argv) != 2:
		print "Usage: %s image_db_id" % sys.argv[0]
		sys.exit(1)

	data, lenght, missing = genImageDotHead(int(sys.argv[1]))
	if len(data):
		for i in range(lenght):
			for k, v in data.iteritems():
				print "%s = %s" % (k, v)
			print "END"

if __name__ == '__main__':
	main()
