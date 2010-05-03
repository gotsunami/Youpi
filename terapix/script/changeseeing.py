##############################################################################
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

"""
Useful to display/upgrade important data paths.
Run this script with no arguments to get a list of Youpi's data paths.
"""
import pyfits, math
import sys, os, string, curses, os.path
import marshal, base64, types, re
import datetime, time
from optparse import OptionParser
import terapix.lib.common
import xml.dom
from django.conf import settings
from optparse import OptionParser
#
from terapix.youpi.models import *
from terapix.lib.common import get_pixel_scale
import wrapper_processing as wp

sys.path.insert(0, 'lib')

CLUSTER_OUTPUT_PATH = None
VERBOSE = False
SIMULATE = False
STATS_ONLY = False
FORCE_ALL = False
done = 0

def updatePixelScale(g):
	"""
	Updates image pixel scale in youpi_image table.

	@param g DBGeneric instance for DB connection
	"""
	global done
	done = 0
	if STATS_ONLY:
		all_img = Image.objects.all().count()
		nops_img = Image.objects.filter(pixelscale = None).count()
		print "Total of images:                           %5d" % all_img
		print "Total of images with pixel scale value:    %5d" % (all_img-nops_img)
		print "Total of images with no pixel scale value: %5d" % nops_img
		return False
	if FORCE_ALL:
		images = Image.objects.all()
	else:
		images = Image.objects.filter(pixelscale = None)
	total = len(images)
	print "Images to process: %d" % total
	for im in images:
		filename = im.filename
		absimgpath = os.path.join(im.path, filename + '.fits')
		if not SIMULATE:
			im.pixelscale = str(get_pixel_scale(absimgpath))
			im.save()
		vout = " Image %05d/%d %s (%s), pixel scale: %s" % (done+1, total, im.name, im.filename, im.pixelscale)
		if VERBOSE:
			print '-' * 2 + vout + '-' * 30
		else:
			if ps:
				sys.stdout.write('.')
			else:
				sys.stdout.write('F')
			sys.stdout.flush()
		sys.stdout.flush()
		done += 1

def updateQFits(g):
	"""
	Updates all QFits information based on XML output of scamp.xml and psfex.xml

	@param g DBGeneric instance for DB connection
	"""
	global done
	done = 0
	if FORCE_ALL:
		q = """
SELECT f.id, t.results_output_dir, t.id FROM youpi_processing_task AS t, youpi_plugin_fitsin AS f
WHERE f.task_id=t.id
AND t.success=1
"""
	else:
		# Only QFits with no psffwhmmin, psffwhmmax and psffwhm values
		q = """
SELECT f.id, t.results_output_dir, t.id FROM youpi_processing_task AS t, youpi_plugin_fitsin AS f
WHERE f.task_id=t.id
AND t.success=1
AND f.psffwhmmin IS NULL
AND f.psffwhmmax IS NULL
AND f.psffwhm IS NULL
"""
	res = g.execute(q)
	total = len(res)
	if STATS_ONLY:
		print "QFits with no post-processing data:        %5d" % total
		return False

	print "Number of QFits to process: %d" % total
	for r in res:
		image_id = g.execute("SELECT image_id FROM youpi_rel_it WHERE task_id=%d" % r[2])[0][0]
		image = Image.objects.filter(id = image_id)[0]
		userData = {'RealImageName': image.filename}
		vout = " QFits %06d/%d [T: %d F:%d I:%s]" % (done+1, total, r[2], r[0], userData['RealImageName'])
		if VERBOSE:
			print '-' * 2 + vout + '-' * 30
		else:
			sys.stdout.write('.')
			sys.stdout.flush()
		if not SIMULATE:
			try:
				log =  wp.ingestQFitsInResults(r[1], userData, r[0], g)
			except Exception, e:
				print "\nError at%s\nException: %s" % (vout, e)
			g.con.commit()
		done += 1

def main():
	global FORCE_ALL
	global SIMULATE
	global STATS_ONLY
	global VERBOSE

	parser = OptionParser(description = 'Tool for updating image pixel scale and/or QualityFITS output data')
	parser.add_option('-s', '--simulate', 
			action = 'store_true', 
			default = False, 
			help = 'Simulation only, do not alter the database'
	)
	parser.add_option('-k', '--stats', 
			action = 'store_true', 
			default = False, 
			help = 'Display some statistics'
	)
	parser.add_option('-q', '--qfits', 
			action = 'store_true', 
			default = False, 
			help = 'Updates QFits information only'
	)
	parser.add_option('-p', '--pixelscale', 
			action = 'store_true', 
			default = False, 
			help = 'Updates image pixel scale only'
	)
	parser.add_option('-v', '--verbose', 
			action = 'store_true', 
			default = False, 
			help = 'Increase verbosity'
	)
	parser.add_option('-f', '--forceall', 
			action = 'store_true', 
			default = False, 
			help = 'Force recomputing all entries, overwritting preceding results'
	)
	try: opts = sys.argv[1]
	except IndexError: 
		parser.print_help()
		sys.exit(2)

	(options, args) = parser.parse_args()
	if len(args): parser.error('takes no argument at all')
	if not options.qfits and not options.pixelscale:
		parser.error('no action supplied (-q or -p)')
	if options.qfits and options.pixelscale:
		parser.error('options -q and -p are mutually exclusive')

	from DBGeneric import DB, DBGeneric
	db = DB(host = settings.DATABASE_HOST,
			user = settings.DATABASE_USER,
			passwd = settings.DATABASE_PASSWORD,
			db = settings.DATABASE_NAME)
	g = DBGeneric(db.con)
	start = time.time()

	VERBOSE = options.verbose
	STATS_ONLY = options.stats
	SIMULATE = options.simulate
	FORCE_ALL = options.forceall
	try: 
		if options.qfits:
			updateQFits(g)
		if options.pixelscale:
			updatePixelScale(g)
	except KeyboardInterrupt: pass
	print "\nTotal: processed %d entries in %.2f seconds (SIMULATION: %s)." % (done, time.time() - start, SIMULATE)
	db.close()

if __name__ == '__main__':
	main()

