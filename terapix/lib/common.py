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

import os.path, types

def get_title_from_menu_id(menuId):
	from youpi.context_processors import appmenu
	parts = appmenu(None)['menu'].values()
	for p in parts:
		for m in p:
			if m['id'] == menuId:
				return m['title']
	return None

def get_pixel_scale(imgpath):
	"""
	Computes an image's pixel scale

	@param imgpath full path to the image on the filesystem
	@returns a computes image pixel scale value (float)
	"""
	if type(imgpath) != types.StringType:
		raise TypeError, "imgpath must be a string"
	import pyfits, math
	# Do not put this function in the wrapper processing script 
	# because it is used by the ingestion script on the cluster too.
	try: hdulist = pyfits.open(imgpath)[1:]
	except IOError:
		raise IOError, "The image could not be found at %s. Skipped." % imgpath

	pixelscale = 0.
	if len(hdulist):
		for i in range(1, len(hdulist)):
			cd11, cd12, cd21, cd22 = hdulist[i].header['CD1_1'], hdulist[i].header['CD1_2'], hdulist[i].header['CD2_1'], hdulist[i].header['CD2_2']
			pixelscale += math.sqrt(math.fabs(cd11*cd22 - cd12*cd21))*3600
		pixelscale = pixelscale/(len(hdulist) - 1)
	else:
		hdulist.close()
		raise ValueError, "No MEF file found in %s (maybe a stack?). Skipped" % imgpath

	hdulist.close()
	return pixelscale

