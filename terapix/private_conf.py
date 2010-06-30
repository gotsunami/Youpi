
# The following values may change at anytime by Youpi developers and should not be 
# modified by anyone, unless you know what your are doing :)

import os, os.path

APP_URL_PREFIX  = '/youpi'
AUP				= APP_URL_PREFIX 	# For short
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL 			= '/media/'

#
IMS_MAX_PER_PAGE	= 50

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
CMD_STIFF			= 'stiff'
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

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Worldwide writable directory to store content accessible under MEDIA_ROOT
MEDIA_TMP = 'pubtmp'

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
	'django.core.context_processors.request',
	'terapix.youpi.context_processors.appmenu',
	'terapix.youpi.context_processors.settings',
	'terapix.youpi.context_processors.version',
)

MIDDLEWARE_CLASSES = (
	'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
	'terapix.middleware.MaintenanceModeMiddleware',
)

ROOT_URLCONF = 'terapix.urls'

INSTALLED_APPS = (
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.sites',
	'django.contrib.admin',
	'django_evolution',
	'terapix.compress',
	'terapix.youpi',
)

SESSION_SAVE_EVERY_REQUEST = True

AUTH_PROFILE_MODULE = 'youpi.siteprofile'


# 
# django-compress app setup
# 
COMPRESS_VERSION = True
COMPRESS_CSS_FILTERS = ['compress.filters.yui.YUICompressorFilter']
COMPRESS_JS_FILTERS = COMPRESS_CSS_FILTERS

COMMON_JS = [
	'js/3rdParty/scriptaculous/prototype.js', 
	'js/3rdParty/scriptaculous/scriptaculous.js', 
	'js/3rdParty/scriptaculous/builder.js',
	'js/3rdParty/scriptaculous/effects.js', 
	'js/3rdParty/scriptaculous/dragdrop.js', 
	'js/3rdParty/Q/q.js', 
	'js/3rdParty/Q/q.informer.js', 
	'js/processingcart.js', 
	'js/common.js', 
	'js/xhr.js',
	'js/menu.js',
]
#
HOME_JS = COMMON_JS[:]
HOME_JS.extend(['js/progressbar.js', 'js/sqlform.js'])
#
INGESTION_JS = COMMON_JS[:]
INGESTION_JS.extend([
	'js/3rdParty/modalbox/modalbox.js', 
	'js/3rdParty/autoSuggest/bsn.AutoSuggest_c_2.0.js', 
	'js/3rdParty/tafelTree/Tree.js', 
	'js/tooltip.js', 
	'js/ingestion.js', 
	'js/filebrowser.js',
	'js/accordion.js',
])
#
TAGS_JS = COMMON_JS[:]
TAGS_JS.extend([
	'js/stylepicker.js', 
	'js/tagwidget.js', 
	'js/tagpanel.js', 
	'js/imageinfowidget.js', 
	'js/imageselector.js', 
	'js/pageswitcher.js', 
	'js/advancedtable.js',
	'js/3rdParty/lightbox2/lightbox.js', 
	'js/3rdParty/modalbox/modalbox.js', 
	'js/3rdParty/autoSuggest/bsn.AutoSuggest_c_2.0.js',
])
#
PROCESSING_JS = COMMON_JS[:]
PROCESSING_JS.extend(['js/3rdParty/tafelTree/Tree.js'])
#
PROCPLUGIN_JS = COMMON_JS[:]
PROCPLUGIN_JS.extend([
	'js/3rdParty/tafelTree/Tree.js',
	'js/3rdParty/modalbox/modalbox.js',
	'js/progressbar.js',
	'js/sqlform.js',
	'js/imageinfowidget.js',
	'js/imageselector.js',
	'js/filebrowser.js',
	'js/3rdParty/windows/js/window.js',
	'js/lightfilebrowser.js',
	'js/configfilewidget.js',
	'js/pathselectorwidget.js',
	'js/pageswitcher.js',
	'js/advancedtable.js',
	'js/3rdParty/autoSuggest/bsn.AutoSuggest_c_2.0.js',
])
#
RESULTS_JS = COMMON_JS[:]
RESULTS_JS.extend([
	'js/gradingwidget.js',
	'js/processinghistorywidget.js',
	'js/pageswitcher.js',
	'js/3rdParty/lightbox2/lightbox.js',
	'js/3rdParty/modalbox/modalbox.js',
	'js/progressbar.js',
])
#
REPORTING_JS = COMMON_JS[:]
REPORTING_JS.extend([
	'js/gradingwidget.js',
	'js/processinghistorywidget.js',
	'js/progressbar.js',
])
#
CART_JS = COMMON_JS[:]
CART_JS.extend([
	'js/3rdParty/modalbox/modalbox.js',
	'js/condorpanel.js',
	'js/accordion.js',
])
#
CONDOR_JS = COMMON_JS[:]
CONDOR_JS.extend([
	'js/advancedtable.js',
	'js/condorpanel.js',
	'js/clusterpolicywidget.js',
	'js/3rdParty/autoSuggest/bsn.AutoSuggest_c_2.0.js',
])
#
PREF_JS = COMMON_JS[:]
PREF_JS.extend([
	'js/condorpanel.js',
	'js/3rdParty/modalbox/modalbox.js',
])
#
REPORT_JS = COMMON_JS[:]
REPORT_JS.extend([
	'js/3rdParty/flotr/lib/canvas2image.js',
	'js/3rdParty/flotr/lib/canvastext.js',
	'js/3rdParty/flotr/flotr-0.2.0-alpha.js',
	'js/3rdParty/modalbox/modalbox.js',
])
#
GRADEPANEL_JS = COMMON_JS[:]
GRADEPANEL_JS.extend([
	'js/gradingwidget.js',
])
#
SINGLERESULT_JS = COMMON_JS[:]
SINGLERESULT_JS.extend([
	'js/gradingwidget.js',
	'js/3rdParty/lightbox2/lightbox.js',
])

COMPRESS_JS = {
	'default'		: { 'source_filenames': COMMON_JS, 'output_filename': 'js/default.r?-min.js' },
	'home'			: { 'source_filenames': HOME_JS, 'output_filename': 'js/home.r?-min.js' },
	'ingestion'		: { 'source_filenames': INGESTION_JS, 'output_filename': 'js/ingestion.r?-min.js' },
	'tags'			: { 'source_filenames': TAGS_JS, 'output_filename': 'js/tags.r?-min.js' },
	'processing'	: { 'source_filenames': PROCESSING_JS, 'output_filename': 'js/processing.r?-min.js' },
	'procplugin'	: { 'source_filenames': PROCPLUGIN_JS, 'output_filename': 'js/procplugin.r?-min.js' },
	'monitoring'	: { 'source_filenames': COMMON_JS, 'output_filename': 'js/monitoring.r?-min.js' },
	'results'		: { 'source_filenames': RESULTS_JS, 'output_filename': 'js/results.r?-min.js' },
	'reporting'		: { 'source_filenames': REPORTING_JS, 'output_filename': 'js/reporting.r?-min.js' },
	'cart'			: { 'source_filenames': CART_JS, 'output_filename': 'js/cart.r?-min.js' },
	'condor'		: { 'source_filenames': CONDOR_JS, 'output_filename': 'js/condor.r?-min.js' },
	'preferences'	: { 'source_filenames': PREF_JS, 'output_filename': 'js/pref.r?-min.js' },
	'doc'			: { 'source_filenames': COMMON_JS, 'output_filename': 'js/doc.r?-min.js' },
	'genreport'		: { 'source_filenames': COMMON_JS, 'output_filename': 'js/genreport.r?-min.js' },
	'report'		: { 'source_filenames': REPORT_JS, 'output_filename': 'js/report.r?-min.js' },
	'gradepanel'	: { 'source_filenames': GRADEPANEL_JS, 'output_filename': 'js/gradepanel.r?-min.js' },
	'imageinfo'		: { 'source_filenames': COMMON_JS, 'output_filename': 'js/imageinfo.r?-min.js' },
	'singleresult'	: { 'source_filenames': SINGLERESULT_JS, 'output_filename': 'js/singleres.r?-min.js' },
	'softsv'		: { 'source_filenames': COMMON_JS, 'output_filename': 'js/softsv.r?-min.js' },
}

#
DEFAULT_CSS = [
	'themes/default/css/global.css', 
	'themes/default/css/dashboard.css', 
	'themes/default/css/layout.css', 
	'themes/default/css/menu.css',
]
#
ING_CSS = DEFAULT_CSS[:]
ING_CSS.extend([
	'js/3rdParty/modalbox/modalbox.css',
	'themes/default/css/history.css', 
	'js/3rdParty/autoSuggest/css/autosuggest_inquisitor.css', 
	'js/3rdParty/tafelTree/css/tree.css', 
	'themes/default/css/tooltip.css',
	'themes/default/css/accordion.css',
])
#
TAGS_CSS = DEFAULT_CSS[:]
TAGS_CSS.extend([
	'js/3rdParty/lightbox2/css/lightbox.css',
	'js/3rdParty/modalbox/modalbox.css',
	'js/3rdParty/autoSuggest/css/autosuggest_inquisitor.css',
])
#
PROCESSING_CSS = DEFAULT_CSS[:]
PROCESSING_CSS.extend([
	'js/3rdParty/tafelTree/css/tree.css',
	'themes/default/css/tooltip.css',
])
#
PROCPLUGIN_CSS = DEFAULT_CSS[:]
PROCPLUGIN_CSS.extend([
	'js/3rdParty/tafelTree/css/tree.css',
	'themes/default/css/tooltip.css',
	'js/3rdParty/modalbox/modalbox.css',
	'js/3rdParty/windows/themes/default.css',
	'js/3rdParty/windows/themes/alphacube.css',
	'js/3rdParty/autoSuggest/css/autosuggest_inquisitor.css',
])
#
RESULTS_CSS = DEFAULT_CSS[:]
RESULTS_CSS.extend([
	'js/3rdParty/lightbox2/css/lightbox.css',
	'js/3rdParty/modalbox/modalbox.css',
])
#
CART_CSS = DEFAULT_CSS[:]
CART_CSS.extend([
	'themes/default/css/history.css',
	'js/3rdParty/modalbox/modalbox.css',
	'themes/default/css/accordion.css',
])
#
CONDOR_CSS = DEFAULT_CSS[:]
CONDOR_CSS.extend([
	'themes/default/css/tooltip.css',
	'js/3rdParty/autoSuggest/css/autosuggest_inquisitor.css',
])
#
PREF_CSS = DEFAULT_CSS[:]
PREF_CSS.extend([
	'themes/default/css/history.css',
	'js/3rdParty/modalbox/modalbox.css',
])
#
SINGLERES_CSS = DEFAULT_CSS[:]
SINGLERES_CSS.extend([
	'js/3rdParty/lightbox2/css/lightbox.css',
])
#
LOGIN_CSS = DEFAULT_CSS[:]
LOGIN_CSS.extend([
	'themes/default/css/login.css',
])
#
REPORT_CSS = DEFAULT_CSS[:]
REPORT_CSS.extend([
	'js/3rdParty/modalbox/modalbox.css',
])

COMPRESS_CSS = {
	'default'		: { 'source_filenames': DEFAULT_CSS, 'output_filename': 'themes/default/css/default.r?-min.css' },
	'ingestion'		: { 'source_filenames': ING_CSS, 'output_filename': 'themes/default/css/ingestion.r?-min.css' },
	'tags'			: { 'source_filenames': TAGS_CSS, 'output_filename': 'themes/default/css/tags.r?-min.css' },
	'processing'	: { 'source_filenames': PROCESSING_CSS, 'output_filename': 'themes/default/css/processing.r?-min.css' },
	'procplugin'	: { 'source_filenames': PROCPLUGIN_CSS, 'output_filename': 'themes/default/css/procplugin.r?-min.css' },
	'monitoring'	: { 'source_filenames': DEFAULT_CSS, 'output_filename': 'themes/default/css/monitoring.r?-min.css' },
	'results'		: { 'source_filenames': RESULTS_CSS, 'output_filename': 'themes/default/css/results.r?-min.css' },
	'reporting'		: { 'source_filenames': DEFAULT_CSS, 'output_filename': 'themes/default/css/reporting.r?-min.css' },
	'report'		: { 'source_filenames': REPORT_CSS, 'output_filename': 'themes/default/css/report.r?-min.css' },
	'cart'			: { 'source_filenames': CART_CSS, 'output_filename': 'themes/default/css/cart.r?-min.css' },
	'condor'		: { 'source_filenames': CONDOR_CSS, 'output_filename': 'themes/default/css/condor.r?-min.css' },
	'preferences'	: { 'source_filenames': PREF_CSS, 'output_filename': 'themes/default/css/prefs.r?-min.css' },
	'singleresult'	: { 'source_filenames': SINGLERES_CSS, 'output_filename': 'themes/default/css/singleres.r?-min.css' },
	'login'			: { 'source_filenames': LOGIN_CSS, 'output_filename': 'themes/default/css/login.r?-min.css' },
}
# 
# End of django-compress app setup
# 

