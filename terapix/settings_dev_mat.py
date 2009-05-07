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

# Django settings for terapix project.

from terapix.common import findPath
import os, os.path

#
# Local configuration file (site specific)
#
HOME 			= '/home/nis/monnerville/'
TRUNK 			= os.path.join(HOME, 'youpi')
APP_URL_PREFIX  = '/youpi'
AUP				= APP_URL_PREFIX 	# For short
#
CONDOR_BIN_PATH = findPath('condor_q')
#
CONDORFILE 		= '/tmp/condor.mathias'
CONDOR_OUTPUT 	= '/tmp/condor.mathias.out'
CONDOR_ERROR 	= '/tmp/condor.mathias.error'
CONDOR_LOG 		= '/tmp/condor.mathias.log'
CONDOR_LOG_DIR	= '/tmp'
#
# Plugins configuration files directory
#
PLUGINS_CONF_DIR = os.path.join(TRUNK, 'terapix', 'youpi', 'plugins', 'conf')
#
# ImageMagick support
#
HAS_CONVERT 		= True
CMD_CONVERT			= '/usr/bin/convert'
CONVERT_THUMB_OPT 	= '-resize 60x' # Default thumbnail size width: 60px
CMD_CONVERT_THUMB	= "%s %s" % (CMD_CONVERT, CONVERT_THUMB_OPT)
#
CMD_STIFF			= '/usr/bin/stiff'
CMD_IMCOPY			= '/usr/local/bin/imcopy'
#
IMS_MAX_PER_PAGE	= 50

#
# Software info (to get versioning information)
#
SOFTS = (	('Condor', 		os.path.join(CONDOR_BIN_PATH, 'condor'), 		# command
							'-v',							# argument to version version information 
							'Version: (.*?) \w'),			# RegExp to retreive version number only
			('MissFITS',	'/usr/local/bin/missfits', 
							'-v', 
							'version (.*?) \('),
			('PSFEx',		'/usr/local/bin/psfex', 
							'-v', 
							'version (.*?) \('),
			('QualityFITS', '/usr/local/bin/qualityFITS', 
							'-V', 
							'version (.*?) conf'),
			('Sextractor', 	'/usr/local/bin/sex', 
							'-v', 
							'version (.*?) \('),
			('Scamp', 		'/usr/local/bin/scamp', 
							'-v', 
							'version (.*?) \('),
			('Swarp', 		'/usr/bin/swarp', 
							'-v', 
							'version (.*?) \('),
			('WeightWatcher',	'/usr/local/bin/ww', 
							'-v', 
							'version (.*?) \(')
		)

PROCESSING_OUTPUT = '/data/mix4/raid1/spica-DEV/'
FTP_URL = 'ftp://mix4/'
#
# TPX_CONDOR_UPLOAD_URL
#
# condor_transfer.pl env var used to know where to transfer data 
# back
#
TPX_CONDOR_UPLOAD_URL = FTP_URL + PROCESSING_OUTPUT
#
# WWW_FITSIN_PREFIX
#
# Used to build URI to QFITS html data path (image name + 'qualityFITS' directory
# will be appended). 
# Ex: http://clix.iap.fr:9000/893265p_04/qualityFITS/ will be used 
# for image '893265p_04.fits'.
#
WWW_FITSIN_PREFIX = 'http://clix.iap.fr:9000/'
WWW_SCAMP_PREFIX = WWW_FITSIN_PREFIX
WWW_SWARP_PREFIX = WWW_FITSIN_PREFIX
WWW_SEX_PREFIX = WWW_FITSIN_PREFIX
#
# Enabe Skeleton demo plugin if True. Should be turned off on production system
#
PROCESSING_SKELETON_ENABLE = True

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_OPTIONS = {"init_command": "SET storage_engine=INNODB"}
DATABASE_NAME = 'spica2dev'             # Or path to database file if using sqlite3.
DATABASE_USER = 'dev'             # Not used with sqlite3.
DATABASE_PASSWORD = 'dev'         # Not used with sqlite3.
DATABASE_HOST = 'dbterapix.iap.fr'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Custom login/logout URLS
LOGIN_URL = '/youpi/accounts/login/'
LOGOUT_URL = '/youpi/accounts/logout/'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(TRUNK, 'terapix', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://clix.clic.iap.fr'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'matu*!)^6fu)jp-(q%d4r-n&ynpx9_xs)48+t)6tv#o)!0e(aw6js'

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

