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

# Base Django settings for terapix project.
# Parts of it can be overwritten by creating a new settings file:
#
# my_setting.py:
# from settings_base import *
# HOME = '/my/home'
#
# FIXME: This is a -dist file that must be filled with you
# FIXME: own values. Lines that require a modification end 
# with a FIXME comment.

import os, os.path


##########################################################################################################
#
# You will certainly need to overwrite those variables to match your local site configuration
#
##########################################################################################################


HOME 				= '/path/to/youpi/parent/dir/' 	# FIXME

# ImageMagick support
#
HAS_CONVERT 		= True
CMD_CONVERT			= '/path/to/convert'			# FIXME
#
CMD_STIFF			= '/path/to/stiff'				# FIXME
CMD_IMCOPY			= '/path/to/imcopy'				# FIXME

PROCESSING_OUTPUT 	= '/output/path/for/results/'	# FIXME
FTP_URL 			= 'ftp://hostname/'				# FIXME

# Used to build URI to QFITS html data path (image name + 'qualityFITS' directory
# will be appended). 
# Ex: http://clix.iap.fr:9000/893265p_04/qualityFITS/ will be used 
# for image '893265p_04.fits'.
WWW_FITSIN_PREFIX 	= 'http://web_hostname/'		# FIXME
WWW_SCAMP_PREFIX 	= WWW_FITSIN_PREFIX
WWW_SWARP_PREFIX 	= WWW_FITSIN_PREFIX
WWW_SEX_PREFIX 		= WWW_FITSIN_PREFIX

# Administrators: put your name and email to receive notifications
# when a problem occurs
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# MySQL settings
DATABASE_NAME 		= 'dbname'						# FIXME
DATABASE_USER 		= 'user'						# FIXME 
DATABASE_PASSWORD 	= 'pass'						# FIXME
DATABASE_HOST 		= 'hostname'					# FIXME. Set to empty string for localhost
DATABASE_PORT 		= ''             				# Set to empty string for default

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE 			= 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE 		= 'en-us'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL 			= 'http://hostname/path'					# FIXME



##########################################################################################################
#
# The remaining of the file can be left unchanged, unless you know what you are doing
#
##########################################################################################################



DEBUG = False
TEMPLATE_DEBUG = DEBUG
MANAGERS = ADMINS

TRUNK 			= os.path.join(HOME, 'youpi')
APP_URL_PREFIX  = '/youpi'
AUP				= APP_URL_PREFIX 	# For short

# Log files used during image ingestion 
# with Condor 
CONDORFILE 		= '/tmp/condor_ingestion_submit'
CONDOR_OUTPUT 	= '/tmp/condor_ingestion.out'
CONDOR_ERROR 	= '/tmp/condor_ingestion.error'
CONDOR_LOG 		= '/tmp/condor_ingestion.log'
CONDOR_LOG_DIR	= '/tmp'

# MySQL settings
# Warning: Youpi has been tested only with MySQL
DATABASE_ENGINE 	= 'mysql' 
DATABASE_OPTIONS 	= {"init_command": "SET storage_engine=INNODB"}

# Plugins configuration files directory
#
PLUGINS_CONF_DIR = os.path.join(TRUNK, 'terapix', 'youpi', 'plugins', 'conf')

# Image Magick
#
CONVERT_THUMB_OPT 	= '-resize 60x' # Default thumbnail size width: 60px
CMD_CONVERT_THUMB	= "%s %s" % (CMD_CONVERT, CONVERT_THUMB_OPT)
#
IMS_MAX_PER_PAGE	= 50

# condor_transfer.pl env var used to know where to transfer data 
# back
TPX_CONDOR_UPLOAD_URL = FTP_URL + PROCESSING_OUTPUT


# FIXME: move code
class FileNotFoundError(Exception): pass
def findPath(file):
	for path in os.environ['PATH'].split(':'):
		abspath = os.path.join(path, file)
		if os.path.exists(abspath):
			if os.path.isfile(abspath):
				return path

	raise FileNotFoundError, "File %s not found in paths: %s" % (file, os.environ['PATH'])

# Looks for the condor_q path in the PATH 
# env variable
CONDOR_BIN_PATH = findPath('condor_q')

# Software info (to get versioning information)
#
CMD_SCAMP			= 'scamp'
CMD_SWARP			= 'swarp'
CMD_SEX				= 'sex'
SOFTS = (	('Condor', 		os.path.join(CONDOR_BIN_PATH, 'condor'), 		# command
							'-v',							# argument to version version information 
							'Version: (.*?) \w'),			# RegExp to retreive version number only
			('MissFITS',	'missfits', 
							'-v', 
							'version (.*?) \('),
			('PSFEx',		'psfex', 
							'-v', 
							'version (.*?) \('),
			('QualityFITS', 'qualityFITS', 
							'-V', 
							'version (.*?) conf'),
			('Sextractor', 	CMD_SEX,
							'-v', 
							'version (.*?) \('),
			('Scamp', 		CMD_SCAMP,
							'-v', 
							'version (.*?) \('),
			('Swarp', 		CMD_SWARP,
							'-v', 
							'version (.*?) \('),
			('WeightWatcher',	'ww', 
							'-v', 
							'version (.*?) \(')
		)

# Custom login/logout URLS
LOGIN_URL = '/youpi/accounts/login/'
LOGOUT_URL = '/youpi/accounts/logout/'

# Enabe Skeleton demo plugin if True. Should be turned off on production 
# system
PROCESSING_SKELETON_ENABLE = False

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(TRUNK, 'terapix', 'media')

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'youpiu*!)^6fu)jp-(q%d4r-n&ynpx9_xs)48+t)6tv#o)!0e(aw6js'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

# Django default processors + custom ones from Youpi
TEMPLATE_CONTEXT_PROCESSORS = (
	'django.core.context_processors.auth',
	'django.core.context_processors.debug',
	'django.core.context_processors.i18n',
	'django.core.context_processors.media',
	'terapix.youpi.context_processors.appmenu',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'terapix.urls'

TEMPLATE_DIRS = os.path.join(TRUNK, 'terapix','templates')

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.admin',
	'terapix.youpi',
)

SESSION_SAVE_EVERY_REQUEST = True

AUTH_PROFILE_MODULE = 'youpi.siteprofile'

# Override all FIXME sections with your values
from local_conf import *