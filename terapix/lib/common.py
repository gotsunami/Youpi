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

import os, os.path, types

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

class Template(object):
	"""
	Almost similar to the builtin string#Template class but substitution patterns 
	can be specified using {before,after}_pattern.
	@param content template string
	@param before_pattern string to use as part of the pattern to recognize (start)
	@param after_pattern string to use as part of the pattern to recognize (end)
	"""
	def __init__(self, content, before_pattern = '##', after_pattern = '##'):
		self.__content = content
		self.__bpat = before_pattern
		self.__apat = after_pattern

	@property
	def initial_content(self):
		"""
		Returns original content
		"""
		return self.__content

	def substitute(self, **kwords):
		content = self.__content
		for k, v in kwords.iteritems():
			content = content.replace("%s%s%s" % (self.__bpat, k, self.__apat), v)
		return content

def get_static_url(output_dir):
	"""
	Returns the appropriate YOUPI_STATIC_URLS entry according to output_dir (member
	of settings.PROCESSING_OUTPUT)
	@param output_dir output directory
	@return matched http URI for serving results
	"""
	import types
	try:
		from django.conf import settings
		PROCESSING_OUTPUT = settings.PROCESSING_OUTPUT
		YOUPI_STATIC_URLS = settings.YOUPI_STATIC_URLS
	except:
		# For the WP script
		from settings import PROCESSING_OUTPUT, YOUPI_STATIC_URLS
	if type(output_dir) != types.StringType and type(output_dir) != types.UnicodeType:
		raise TypeError, "output_dir must be a directory path (string)"
	for i in range(len(PROCESSING_OUTPUT)):
		if output_dir.find(PROCESSING_OUTPUT[i]) == 0:
			return YOUPI_STATIC_URLS[i]
	raise ValueError, "No match, could not resolve static url for path %s" % output_dir

def get_tpx_condor_upload_url(output_dir):
	"""
	Builds a path suitable for condor_transfert.pl TPX_CONDOR_UPLOAD_URL env variable.
	Given a supported output_dir (member of settings.PROCESSING_OUTPUT), it will return the 
	concatenation with the matched settings.FTP_URL (same index).
	@param output_dir output directory
	@return URI suitable for settings.CMD_CONDOR_TRANSFER
	"""
	import types
	from django.conf import settings

	if type(output_dir) != types.StringType and type(output_dir) != types.UnicodeType:
		raise TypeError, "output_dir must be a directory path (string)"
	for i in range(len(settings.PROCESSING_OUTPUT)):
		if output_dir.find(settings.PROCESSING_OUTPUT[i]) == 0:
			return settings.FTP_URL[i] + output_dir
	raise ValueError, "No match, could not get FTP_URL for path %s" % output_dir

def get_temp_dir(level1, level2, addDate=True):
	"""
	Builds a temporary directory name from level1 and level2 args and the current date, like
	/base_tmp/username/plugin_id/YYYY-MM-DD/ if level1=username and level2=plugin_id.

	The new directory path is then created.
	"""
	if type(level1) not in types.StringTypes or type(level2) not in types.StringTypes:
		raise TypeError, "Both args must be strings"
	from datetime import date
	from django.conf import settings
	path = os.path.join(settings.BASE_TEMP_DIR, level1, level2)
	if addDate:
		path = os.path.join(path, date.today().isoformat())
	try:
		os.makedirs(path)
	except OSError:
		# Already exists
		pass
	return path

