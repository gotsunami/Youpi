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

os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from decimal import getcontext
	from terapix.youpi.models import *
	from terapix.lib.common import get_pixel_scale
	#
	from django.conf import settings
	from django.db import IntegrityError, connection
except ImportError, e:
	raise ImportError, e
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)

def main():
	cur = connection.cursor()
	images = Image.objects.filter(pixelscale = None)
	print "Images to process: %d" % len(images)
	k = 0
	for im in images:
		absimgpath = os.path.join(im.path, im.filename + '.fits')
		im.pixelscale = str(get_pixel_scale(absimgpath))
		im.save()
		sys.stdout.flush()
		k += 1
		print k

#			q = """
#					SELECT psffwhm, psffwhmmin, psffwhmmax FROM youpi_image AS i 
#					INNER JOIN youpi_rel_it AS it ON i.id = it.image_id 
#					INNER JOIN youpi_processing_task AS t ON t.id = it.task_id 
#					INNER JOIN youpi_plugin_fitsin AS f ON f.task_id = t.id 
#					WHERE i.name=\'%s\';
#		
#				""" % (im.name)
#
#			cur.execute(q)
#			res = cur.fetchall()
#
#			if res:
#				print "pixel scale mean for %s : %s, with current seeing in pixel : %s, right seeing average value : %s" % (absimgpath, pixelscale,res[0][0],pixelscale*float(res[0][0]))
#				u = """
#						UPDATE youpi_plugin_fitsin 
#						INNER JOIN youpi_processing_task ON youpi_plugin_fitsin.task_id = youpi_processing_task.id 
#						INNER JOIN youpi_rel_it ON youpi_processing_task.id = youpi_rel_it.task_id 
#						INNER JOIN youpi_image ON youpi_rel_it.image_id = youpi_image.id 
#						SET psffwhm = \'%s\', psffwhmmin = \'%s\', psffwhmmax = \'%s\' 
#						WHERE youpi_image.name=\'%s\';
#				""" % (round(pixelscale*float(res[0][0]), 8), round(pixelscale*float(res[0][1]),8), round(pixelscale*float(res[0][2]),8), im.name)
#				
#				cur.execute(u)
#				connection._commit()
#			else:
#				print "No seeing already updated in data base for image %s" % absimgpath
	connection.close()

if __name__ == '__main__':
	#main()
	import wrapper_processing as wp
	psfexFieldNames = (
		'FWHM_Min', 'FWHM_Mean', 'FWHM_Max', 'Elongation_Min', 'Elongation_Mean', 
		'Elongation_Max', 'Chi2_Min', 'Chi2_Mean', 'Chi2_Max', 'Residuals_Min',
		'Residuals_Mean', 'Residuals_Max', 'Asymetry_Min', 'Asymetry_Mean',
		'Asymetry_Max', 'NStars_Accepted_Min', 'NStars_Accepted_Mean', 
		'NStars_Accepted_Max', 
	)
#	print wp.parse_psfex_xml('/tmp/psfex.xml', psfexFieldNames)

	from DBGeneric import DB, DBGeneric
	db = DB(host = settings.DATABASE_HOST,
			user = settings.DATABASE_USER,
			passwd = settings.DATABASE_PASSWORD,
			db = settings.DATABASE_NAME)
	g = DBGeneric(db.con)
	wp.ingestQFitsInResults(35824, g)
	g.con.commit()
	db.close()


