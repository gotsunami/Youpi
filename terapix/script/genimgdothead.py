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
os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from terapix.youpi.models import *
except ImportError, e:
	print "Please run this command from the terapix subdirectory: %s" % e
	sys.exit(1)

def genImageDotHead(image_id):
	"""
	Generate a FITS image's .head file. The image file is first accessed to get the number 
	of HDUs (extansions). Then keywords mapping is retrieved from the instrument's ITT in 
	order to get a proper HDU data.
	@return tuple of hdudata and total number of hdus in this image (primary + extansions)
	"""
	if type(image_id) != types.IntType:
		raise ValueError, "first argument image_id must be an integer"
	try: img = Image.objects.filter(id = image_id)[0]
	except:
		raise LookupError, "no image found with ID: %s" % image_id

	fname = os.path.join(img.path, img.name + '.fits')
	if not os.path.exists(fname):
		fname = re.sub(r'_\d+\.fits$', '.fits', fname)

	hdulist = pyfits.open(fname)
	hdulist.close()

	# Get instrument translation table
	itt = marshal.loads(zlib.decompress(base64.decodestring(img.instrument.itt)))

	try: run = Rel_ri.objects.filter(image = img)[0].run.name
	except: run = None

	data = {
		'YRUN'			: run, 
#		'YDETECTOR': , 
#		'YTELESCOP': , 
		'YINSTRUMENT'	: img.instrument.name, 
		'YDATEOBS'		: img.dateobs, 
		'YFILTER'		: img.channel.name,
		'YFLAT'			: img.flat,
		'YAIRMASS'		: img.airmass,
		'YEQUINOX'		: img.equinox,
		'YOBJECT'		: img.object,
		'YEXPTIME'		: img.exptime,
		'YMASK'			: img.mask,
		'YRA'			: img.alpha,
		'YDEC'			: img.delta,
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
			hdudata[itt[k]['MAP']] = val

	return (hdudata, len(hdulist))

def main():
	if len(sys.argv) != 2:
		print "Usage: %s image_db_id" % sys.argv[0]
		sys.exit(1)

	data, lenght = genImageDotHead(int(sys.argv[1]))
	if len(data):
		for i in range(lenght):
			for k, v in data.iteritems():
				print "%s = %s" % (k, v)
			print "END"

if __name__ == '__main__':
	main()
