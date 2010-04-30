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
Useful to display/upgrade important data paths.
Run this script with no arguments to get a list of Youpi's data paths.
"""
import pyfits, math
import sys, os, string, curses, os.path
import marshal, base64, types, re
import datetime, time
from optparse import OptionParser
import xml.dom

os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')
	sys.path.insert(0, 'lib')

try:
	from decimal import getcontext
	import wrapper_processing as wp
	from terapix.youpi.models import *
	from terapix.lib.common import get_pixel_scale
	#
	from django.conf import settings
	from django.db import IntegrityError, connection
except ImportError, e:
	raise ImportError, e
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)

CLUSTER_OUTPUT_PATH = None
VERBOSE = False
done = 0

def main(g):
	global done
	images = Image.objects.filter(pixelscale = None)
	only_img = False
	if only_img:
		print "Images to process: %d" % len(images)
		k = 0
		for im in images:
			absimgpath = os.path.join(im.path, im.filename + '.fits')
			im.pixelscale = str(get_pixel_scale(absimgpath))
			im.save()
			sys.stdout.flush()
			k += 1
			print k

	q = """
SELECT f.id, t.results_output_dir, t.id FROM youpi_processing_task AS t, youpi_plugin_fitsin AS f
WHERE f.task_id=t.id
AND t.success=1
"""
	res = g.execute(q)
	total = len(res)
	print "Number of QFits to process: %d" % total

	for r in res:
		image_id = g.execute("SELECT image_id FROM youpi_rel_it WHERE task_id=%d" % r[2])[0][0]
		image = Image.objects.filter(id = image_id)[0]
		userData = {'RealImageName': image.filename}
		vout = " QFits %06d/%d [T: %d F:%d I:%s]" % (done+1, total, r[2], r[0], userData['RealImageName'])
		if VERBOSE:
			print '-' * 2 + vout + '-' * 30
			print log
		else:
			sys.stdout.write('.')
			sys.stdout.flush()
		try:
			log =  wp.ingestQFitsInResults(r[1], userData, r[0], g)
		except Exception, e:
			print "\nError at%s\nException: %s" % (vout, e)
		g.con.commit()
		done += 1

if __name__ == '__main__':
	from DBGeneric import DB, DBGeneric
	db = DB(host = settings.DATABASE_HOST,
			user = settings.DATABASE_USER,
			passwd = settings.DATABASE_PASSWORD,
			db = settings.DATABASE_NAME)
	g = DBGeneric(db.con)
	start = time.time()
	try:
		main(g)
	except KeyboardInterrupt:
		pass
	print "\nTotal: processed %d qfits in %.2f seconds." % (done, time.time() - start)

	db.close()
