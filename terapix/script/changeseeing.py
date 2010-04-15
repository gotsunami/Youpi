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
from terminal import *
os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from django.db import IntegrityError
	from decimal import getcontext
	from django.conf import settings
	from terapix.youpi.models import *
	from django.db import connection
except ImportError:
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)

cur = connection.cursor()

images = Image.objects.all()
for im in images:
	absimgpath = os.path.join(im.path,im.filename+'.fits')
	try:
		hdulist = pyfits.open(absimgpath)
	except IOError:
		print "the %s image, which the location from database to %s doesn't exists, skipping image seeing adjustment..." % (im.filename,im.path)
		continue
	pixelscale = 0
	for i in range(1, len(hdulist)):
		cd11, cd12, cd21, cd22 = hdulist[i].header['CD1_1'], hdulist[i].header['CD1_2'], hdulist[i].header['CD2_1'], hdulist[i].header['CD2_2']
		pixelscale += math.sqrt(math.fabs(cd11*cd22 - cd12*cd21))*3600

	pixelscale = pixelscale/(len(hdulist) - 1)
	q = """
			SELECT psffwhm, psffwhmmin, psffwhmmax FROM youpi_image AS i 
			INNER JOIN youpi_rel_it AS it ON i.id = it.image_id 
			INNER JOIN youpi_processing_task AS t ON t.id = it.task_id 
			INNER JOIN youpi_plugin_fitsin AS f ON f.task_id = t.id 
			WHERE i.name=\'%s\';

		""" % (im.name)

	cur.execute(q)
	res = cur.fetchall()

	if res:
		print "pixel scale mean for %s : %s, with current seeing in pixel : %s, right seeing average value : %s" % (absimgpath, pixelscale,res[0][0],pixelscale*float(res[0][0]))
		u = """
				UPDATE youpi_plugin_fitsin 
				INNER JOIN youpi_processing_task ON youpi_plugin_fitsin.task_id = youpi_processing_task.id 
				INNER JOIN youpi_rel_it ON youpi_processing_task.id = youpi_rel_it.task_id 
				INNER JOIN youpi_image ON youpi_rel_it.image_id = youpi_image.id 
				SET psffwhm = \'%s\', psffwhmmin = \'%s\', psffwhmmax = \'%s\' 
				WHERE youpi_image.name=\'%s\';

		""" % (round(pixelscale*float(res[0][0]),8),round(pixelscale*float(res[0][1]),8),round(pixelscale*float(res[0][2]),8), im.name)
		
		cur.execute(u)
		connection._commit()
	else:
		print "No seeing already updated in data base for image %s" % absimgpath
connection.close()
