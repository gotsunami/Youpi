# vim: set ts=4

from django.contrib import auth
from django.contrib.auth.models import *
from django.contrib.auth.decorators import login_required
from django.contrib.gis.db import models
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect, HttpResponseBadRequest
from django.db.models import get_models
from django.db.models import Q
from django.utils.datastructures import *
from django.template import Template, Context, RequestContext
#
from terapix.youpi.forms import *
from terapix.youpi.models import *
from terapix.script.preingestion import preingest_table
from terapix.script.DBGeneric import *
from terapix.script.ingestion import getNowDateTime
#
import MySQLdb, pyfits
import pprint, re, glob, string
import math, md5, random
import marshal, base64
import os, os.path, sys, pprint
import socket, time
from types import *
from copy import deepcopy
#
from settings import *

# Custom views
from terapix.youpi.pluginmanager import PluginManagerError, PluginError
from terapix.youpi.cviews.shoppingcart import *
from terapix.youpi.cviews.condor import *
from terapix.youpi.cviews.preingestion import *
from terapix.youpi.cviews.plot import *
from terapix.youpi.cviews.processing import *

app_menu = { 	'normal' : 
				( 	
					{'title' : 'Home', 				'id' : 'home', 			'href' : AUP},
					{'title' : 'Pre-ingestion',		'id' : 'preingestion',	'href' : AUP + '/preIngestion/'},
					{'title' : 'Ingestion', 		'id' : 'ing', 			'href' : AUP + '/ingestion/'},
					{'title' : 'Processing', 		'id' : 'processing', 	'href' : AUP + '/processing/'},
					{'title' : 'Processing Results','id' : 'results',	 	'href' : AUP + '/results/'},
					{'title' : 'Active Monitoring', 'id' : 'monitoring', 	'href' : AUP + '/monitoring/'}
				),
				'apart' :
				( 	
					# Display order is inverted
					{'title' : 'Preferences', 		'id' : 'preferences', 	'href' : AUP + '/preferences/'},
					{'title' : 'Condor Setup', 		'id' : 'condorsetup', 	'href' : AUP + '/condor/setup/'},
					{'title' : 'Shopping cart',		'id' : 'shoppingcart', 	'href' : AUP + '/cart/'}
				)
			}

@login_required
@profile
def index(request):
	"""
	This is the main entry point (root) of the web application.
	This is a callback function (as defined in django's urls.py file).
	"""
	return render_to_response('index.html', 
					{	'Debug' 			: DEBUG,
						'menu'				: app_menu,
						'selected_entry_id'	: 'home' }, 
					context_instance = RequestContext(request))

@login_required
@profile
def preferences(request):
	"""
	Preferences template
	"""
	import ConfigParser
	config = ConfigParser.RawConfigParser()

	# Looks for themes
	theme_dirs = glob.glob(os.path.join(MEDIA_ROOT, 'themes', '*'))
	themes = []

	for dir in theme_dirs:
		try:
			config.read(os.path.join(dir, 'META'))
		except:
			# No META data, theme not conform
			pass

		if not os.path.isfile(os.path.join(dir, 'screenshot.png')):
			# No screenshot available, theme not conform
			continue

		themes.append({	'name' 			: config.get('Theme', 'Name'),
						'author' 		: config.get('Theme', 'Author'),
						'author_uri'	: config.get('Theme', 'Author URI'),
						'description' 	: config.get('Theme', 'Description'),
						'version' 		: config.get('Theme', 'Version'),
						'short_name'	: os.path.basename(dir),
						})

	for k in range(len(themes)):
		if themes[k]['short_name'] == request.user.get_profile().guistyle:
			break

	policies = CondorNodeSel.objects.filter(is_policy = True).order_by('label')
	selections = CondorNodeSel.objects.filter(is_policy = False).order_by('label')

	return render_to_response('preferences.html', 
					{	'Debug' 			: DEBUG,
						'themes'			: themes,
						'plugins' 			: manager.plugins, 
						'current_theme'		: themes[k],
						'policies'			: policies,
						'selections'		: selections,
						'menu'				: app_menu,
						'selected_entry_id'	: 'preferences' }, 
					context_instance = RequestContext(request))

@login_required
@profile
def condor_setup(request):
	"""
	Condor cluster setup
	"""
	return render_to_response('condorsetup.html', 
					{	'Debug' 			: DEBUG,
						'menu'				: app_menu,
						'selected_entry_id'	: 'condorsetup' }, 
					context_instance = RequestContext(request))

@login_required
@profile
def documentation(request):
	"""
	Documentation template
	"""
	return render_to_response('documentation.html', 
					{	'Debug' 			: DEBUG,
						'menu'				: app_menu,
						'selected_entry_id'	: 'documentation' }, 
					context_instance = RequestContext(request))

@login_required
@profile
def cart_view(request):
	"""
	Renders shopping cart view.
	"""

	cartHasData = False
	if 'cart' not in request.session:
		request.session['cart'] = {'plugins' : {}}

	for plugin, dataList in request.session['cart']['plugins'].iteritems():
		plugObj = manager.getPluginByName(plugin)
		if len(dataList):
			plugObj.setData(dataList)
			cartHasData = True
		else:
			plugObj.removeData()

	return render_to_response('shoppingcart.html', 
				{	'plugins' 			: manager.plugins, 
					'cartHasData' 		: cartHasData, 
					'Debug' 			: DEBUG, 
					'menu'				: app_menu,
					# Cluster node available policies + selections
					'nodePolicies'		: ['a', 'b', 'c'],
					'selected_entry_id'	: 'shoppingcart', 
					'misc' 				: manager
				},
				context_instance = RequestContext(request))

@login_required
@profile
def processing(request):
	return render_to_response('processing.html', 
					{ 	'plugins' 			: manager.plugins,
						'Debug' 			: DEBUG,
						'processing_output' : PROCESSING_OUTPUT,
						'menu'				: app_menu,
						'selected_entry_id'	: 'processing' }, 
					context_instance = RequestContext(request))

@login_required
@profile
def preingestion(request):
	"""
	Related to preIngestion step
	"""
	
	return render_to_response('preingestion.html', 
					{	'hostname'			: socket.gethostname(), 
						'menu'				: app_menu,
						'selected_entry_id'	: 'preingestion', 
						'Debug' 			: DEBUG },
					context_instance = RequestContext(request))

@login_required
@profile
def ing(request):
	"""
	Related to ingestion step.
	This is a callback function (as defined in django's urls.py file).
	"""

	q = Image.objects.all().count()
	return render_to_response('ingestion.html', 
					{	'ingested' 			: q, 
						'menu'				: app_menu,
						'selected_entry_id'	: 'ing', 
						'Debug' 			: DEBUG }, 
					context_instance = RequestContext(request))

@login_required
@profile
def monitoring(request):
	"""
	Related to monitoring.
	This is a callback function (as defined in django's urls.py file).
	"""

	return render_to_response('monitoring.html', 
					{	'Debug' 			: DEBUG, 
						'menu'				: app_menu,
						'selected_entry_id'	: 'monitoring' }, 
					context_instance = RequestContext(request))

@login_required
@profile
def results(request):
	"""
	Related to results page.
	This is a callback function (as defined in django's urls.py file).
	"""

	dirs = []
	ts = Processing_task.objects.all()
	for t in ts:
		if t.results_output_dir not in dirs:
			dirs.append(t.results_output_dir)

	return render_to_response('results.html', 
					{	'Debug' 			: DEBUG, 
						'plugins' 			: manager.plugins, 
						'menu'				: app_menu,
						'selected_entry_id'	: 'results', 
						'outputDirs' 		: dirs }, 
					context_instance = RequestContext(request))

@login_required
@profile
def render_plugin(request, pluginId):
	try:
		plugin = manager.getPluginByName(pluginId)
	except PluginManagerError, msg:
		return HttpResponseNotFound("Error: %s" % msg)

	return render_to_response('processing_plugin.html',
					{ 	'plugin' 			: plugin,
						'Debug' 			: DEBUG,
						'menu'				: app_menu,
						'selected_entry_id'	: 'processing', 
						'processing_output' : PROCESSING_OUTPUT }, 
					context_instance = RequestContext(request))

@login_required
@profile
def soft_version_monitoring(request):
	return render_to_response(
			'softs_versions.html', 
			{	'report' 			: len(SOFTS), 
				'menu'				: app_menu,
				'selected_entry_id'	: 'monitoring', 
				'Debug' 			: DEBUG },
			context_instance = RequestContext(request))

@login_required
@profile
def show_ingestion_report(request, ingestionId):
	ing = Ingestion.objects.filter(id = ingestionId)[0]
	report = ing.report
	if report:
		report = str(zlib.decompress(base64.decodestring(ing.report)))
	else:
		report = 'No report found... maybe the processing is not finished yet?'

	return render_to_response(
			'ingestion_report.html', 
			{	'report' 			: report, 
				'menu'				: app_menu,
				'selected_entry_id'	: 'ing', 
				'Debug' 			: DEBUG },
			context_instance = RequestContext(request))

@login_required
@profile
def single_result(request, pluginId, taskId):
	"""
	Same content as the page displayed by related plugin.
	"""

	plugin = manager.getPluginByName(pluginId)
	if not plugin:
		return HttpResponseNotFound("""<h1><span style="color: red;">Invalid URL. Result not found.</h1></span>""")

	try:
		task = Processing_task.objects.filter(id = int(taskId))[0]
	except IndexError:
		# TODO: set a better page for that
		return HttpResponseNotFound("""<h1><span style="color: red;">Result not found.</h1></span>""")

	return render_to_response(
				'single_result.html', 
				{	'pid' 				: pluginId, 
					'tid'	 			: taskId,
					'Debug' 			: DEBUG,
					'menu'				: app_menu,
					'selected_entry_id'	: 'results', 
					'plugin' 			: plugin }, 
				context_instance = RequestContext(request))


def logout(request):
	auth.logout(request)
	# Redirect to home page
	return HttpResponseRedirect(AUP)

def browse_api(request, type):
	if type == 'py' or type == 'python':
		path = 'py/html/'
	elif type == 'js' or type == 'javascript':
		path = 'js/'
	else:
		return HttpResponseNotFound('No API of that name exits.')

	# Redirect to API doc
	return HttpResponseRedirect('http://clix.iap.fr:8001/' + path)

def index2(request):
	try:
		param = request.POST['Param']
		value = request.POST['Value']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data: %s' % e)
	
	error = warning = ''

	try:
		if param == 'survey':
			if not Survey.objects.filter(name__iexact = value):
				if len(value) == 0 :
					warning = 'Please, enter a non-empty string'
				else:
					sur = Survey(name = value)
					sur.save()
					m = Rel_us(user_id = request.user.id, survey_id = sur.id)
					m.save()
			else:
				warning = 'Survey already existing'

		if param == 'instrument':
			survey = request.POST['Survey']

			if not Instrument.objects.filter(name__iexact = value):
				if len(value) == 0 :
					warning = 'Please, enter a non-empty string'
				else:
					ins = Instrument(name = value)
					ins.save()
					g = Survey.objects.filter(name__iexact = survey)[0]
					i = Rel_si(survey_id = g.id, instrument_id = ins.id)
					i.save()
			else:
				warning = 'Instrument already existing'

		if param == 'release':
			instrument = request.POST['Instrument']

			if not Release.objects.filter(label__iexact = value):
				if len(value) == 0 :
					warning = 'Please, enter a non-empty string'
				else:
					rel = Release(label = value,releasedate = getNowDateTime())
					rel.save()
					ins = Instrument.objects.filter(name__iexact = instrument)[0]
					i = Rel_rinst(release_id =rel.id, instrument_id = ins.id)
					i.save()
			else:
				warning = 'Instrument already existing'


	except Exception, e:
		error = e

		
	resp = {'Survey' : str(value), 'Error' : str(error),'Warning' : warning}

	return HttpResponse(str(resp), mimetype = 'text/plain')

def local_ingestion(request):
	"""
	Callback for running a local ingestion.
	This is a callback function (as defined in django's urls.py file).
	"""
	path  = request.POST['path']
	connectionObject = MySQLdb.connect(host = DATABASE_HOST, user = DATABASE_USER, passwd = DATABASE_PASSWORD, db = DATABASE_NAME)
		
	if connectionObject:
		os.chdir(path)
		try:
			verify = request.POST['verify']
		except MultiValueDictKeyError:
			verify = '0'
		
		list_fits1 = glob.glob('*.fits')
		f = open('/tmp/verify.log', 'wa')
		
		while list_fits1 <> []:
			fitsfile = list_fits1.pop()
		
			fitsverify = os.popen("fitsverify -q -e %s" % fitsfile)
			k = fitsverify.readlines()
			fitsverify.close()

			if (verify == '1'):
				f.write(str(k)+'\n')
	
			r = pyfits.open(fitsfile)
			h1 = r[1].header
			
			# DBinstrument
			instrname, telescope, detector = (h1['instrume'], h1['telescop'],  h1['detector'])
			
			# DBimage
			object = h1['object']
			
			# DBchannel
			chaname = h1['filter']
			
			# DBrun
			runame = h1['runid']
			
			c = connectionObject.cursor()
	
			#
			# RUN DATABASE INGESTION
			#
			c.execute('start transaction')
			test = c.execute("select Name from youpi_run where name='%s'" % runame)
			if test == 0:
				if (detector == 'MegaCam' or  telescope == 'CFHT 3.6m' or instrname == 'MegaPrime'):
					test1 = c.execute("insert into youpi_run set Name='%s', instrument_id=2" % runame)
					if test1:
						connectionObject.commit()
					else:
						connectionObject.rollback()
	
				elif (detector == 'WIRCam' or telescope == 'CFHT 3.6m' or instrname == 'WIRCam'):
					test2 = c.execute("insert into youpi_run set Name='%s', instrument_id=3" % runame)
					if test2:
						connectionObject.commit()
					else:
						connectionObject.rollback()
	
			else:
				print 'Run known'
				
			#
			# CHANNEL DATABASE INGESTION
			#
			c.execute('start transaction')
			tust = c.execute("select Name from youpi_channel where name='%s'" % chaname)
			if (tust == 0):
				
				if (detector == 'MegaCam' and  telescope == 'CFHT 3.6m' and instrname == 'MegaPrime'):
					test3 = c.execute("insert into youpi_channel set Name='%s', instrument_id=2" % chaname)
					if test3:
						connectionObject.commit()
					else:
						connectionObject.rollback()
	
					
				elif (detector == 'WIRCam' and telescope == 'CFHT 3.6m' and instrname == 'WIRCam'):
					test4 = c.execute("insert into youpi_channel set Name='%s', instrument_id=3" % chaname)
					if test4:
						connectionObject.commit()
					else:
						connectionObject.rollback()
	
			else:
				print "channel known"
		f.close()
			

		#
		# IMAGE
		#
		os.chdir(path)
		list_fits2 = glob.glob('*.fits')
		for fitsfile in list_fits2:
			
			checksum = md5.md5(open(fitsfile, 'rb').read()).hexdigest()
			r = pyfits.open(fitsfile)
			h1 = r[1].header
			
			# DBinstrument
			i = h1['instrume']
			t = h1['telescop']
			det = h1['detector']
			
			# DBimage
			o = h1['object']
			a = h1['airmass']
			e = h1['exptime']
			d = h1['DATE-OBS']
			eq = h1['equinox']
			
			# DBchannel
			chaname = h1['filter']
			
			# DBrun
			runame = h1['runid']
			c.execute('start transaction')
			mj = fitsfile.replace('.fits', '')
			tast = c.execute("select name from youpi_image where name='%s'" % mj)
	
			if tast == 1:
				break
			elif tast == 0:
				weight = re.search('_weight.fits', fitsfile)
				if weight:
					break
	
				testa = c.execute("select Name from youpi_run where name='%s'" % runame)
				m = fitsfile.replace('.fits', '')
	
				if testa == 1:
					if (det == 'MegaCam' or  t == 'CFHT 3.6m' or i == 'MegaPrime'):
						c.execute("select id from youpi_run where instrument_id = 2 and Name='%s'" % runame)
						rows = c.fetchone()

						c.execute("select id from youpi_channel where instrument_id = 2 and Name='%s'" % chaname)
						row = c.fetchone()
						
						c.execute("insert into youpi_image set run_id='%s', calibrationkit_id=1, instrument_id=2, channel_id='%s', Name='%s', object='%s', airmass='%s', exptime='%s', dateobs='%s', equinox='%s', checksum='%s'" % (rows[0], row[0], m, o, a, e, d, eq, checksum))
			
					elif (det == 'WIRCam' or t == 'CFHT 3.6m' or i == 'WIRCam'):
						c.execute("select id from youpi_run where instrument_id=3 and Name='%s'" % runame)
						rows = c.fetchone()
						
						c.execute("select id from youpi_channel where instrument_id=3 and Name='%s'" % chaname)
						row = c.fetchone()
	
						c.execute("insert into youpi_image set run_id='%s', calibrationkit_id=2, instrument_id=3, channel_id='%s', Name='%s', object='%s', airmass='%s', exptime='%s', dateobs='%s', equinox='%s', checksum='%s'" % (rows[0],row[0],m,o,a,e,d,eq,checksum))
			
			connectionObject.commit()
	else:
		print 'Not connected to the Database'
	rows = open('/tmp/verify.log', 'r').readlines()
	return render_to_response('popup.htm', {'names': rows})



def aff_img(request,image_name):
	"""
	Displays (popup) an image image_name.
	This is a callback function (as defined in django's urls.py file).
	"""

	db = MySQLdb.connect(host = DATABASE_HOST, user = DATABASE_USER, passwd = DATABASE_PASSWORD, db = DATABASE_NAME)
	cursor = db.cursor()
	cursor.execute("SELECT * FROM youpi_image where name='%s'" % image_name)
	list_param = []
	for rows in cursor.fetchall():
		list_param.append({'rows':rows})
	db.close()

	return render_to_response('popup.htm', {'names': rows})

def open_populate(request, behaviour, tv_name, path):
	"""
	This function returns a list of JSON objects to generate a dynamic Ajax treeview.
	The argument path is a path to directory structure (see views.py for further details). it 
	is equal to the value of 'openlink' in a JSON branch definition.

	This function is specific to tafelTreeview.
	"""

	#
	# The POST request will always contain a branch_id variable when the present function 
	# is called dynamically by the tree issuing the Ajax query
	#
	try:
		nodeId = request.POST['branch_id']
	except:
		# May be usefull for debugging purpose
		return HttpResponse("Path debug: %s, %s, %s" % (path, behaviour, tv_name))

	json = []
	fitsSearchPattern = '*.fits'
	regFitsSearchPattern = '^.*\.fits$'

	if behaviour == 'binary_tables':
		# Patterns change
		fitsSearchPattern = 'mcmd.*.fits'
		regFitsSearchPattern = '^mcmd\..*\.fits$'

	# Look for data
	data = glob.glob("/%s/*" % str(path))

	dirs = []
	for e in data:
		if os.path.isdir(e):
			dirs.append(e)
		elif os.path.isfile(e):
			if re.match(regFitsSearchPattern, e):
				# This is a fits file
				json.append( {
					'id'  : os.path.basename(e),
					'txt' : os.path.basename(e),
					'img' : 'forward.png'
				})


	for d in dirs:
		# Check if this directory contains any FITS file
		fitsFiles = glob.glob("%s/%s" % (d, fitsSearchPattern))

		label = os.path.split(d)[1]
		id = "%s_%s" % (str(path), label)
		id = id.replace('/', '_')
		if len(fitsFiles):
			nodeText = """%s <font class="image_count">(%d)</font>""" % (label, len(fitsFiles))
		else:
			nodeText = label

		json.append( {
			'id' : id,
			'txt' : nodeText,
			'canhavechildren' : 1,
			'onopenpopulate' : str(tv_name) + '.branchPopulate',
			'syspath' : "/%s/%s/" % (str(path), label),
			'openlink' : AUP + "/populate/%s/%s/%s/%s/" % (str(behaviour), str(tv_name), str(path), label),
			'num_fits_children' : len(fitsFiles)
		})
			

	return HttpResponse(str(json), mimetype = 'text/plain')


def open_populate_generic(request, patterns, fb_name, path):
	"""
	This function returns a list of JSON objects to generate a dynamic Ajax treeview.
	The argument path is a path to directory structure (see views.py for further details). it 
	is equal to the value of 'openlink' in a JSON branch definition.

	This function is specific to tafelTreeview.

	patterns: file search patterns (comma-separated list)
	fb_name: FileBrowser global variable name
	path: path to data
	"""

	if path[0] == '/':
		path = path[1:]

	#
	# The POST request will always contain a branch_id variable when the present function 
	# is called dynamically by the tree issuing the Ajax query
	#
	try:
		nodeId = request.POST['branch_id']
	except:
		# May be usefull for debugging purpose
		return HttpResponse("Path debug: %s, %s, %s" % (path, patternList, fb_name))

	json = []

	patternList = patterns.split(',')
	regSearchPatternList = []
	for pat in patternList:
		regSearchPatternList.append(pat.replace('.', '\.').replace('*', '.*'))

	# Look for data
	data = glob.glob("/%s/*" % str(path))

	dirs = []
	for e in data:
		if os.path.isdir(e):
			dirs.append(e)
		elif os.path.isfile(e):
			for rsp in regSearchPatternList:
				if re.match(rsp, e):
					# This is a file
					json.append( {
						'id'  : os.path.basename(e),
						'txt' : os.path.basename(e),
						'img' : 'forward.png'
					})
					break

	for d in dirs:
		# Check if this directory contains any file matching searchPattern
		files = []
		for pat in patternList:
			files.extend(glob.glob("%s/%s" % (d, pat)))

		label = os.path.split(d)[1]
		id = "%s_%s" % (str(path), label)
		id = id.replace('/', '_')
		if len(files):
			nodeText = """%s <font class="image_count">(%d)</font>""" % (label, len(files))
		else:
			nodeText = label

		json.append( {
			'id' : id,
			'txt' : nodeText,
			'canhavechildren' : 1,
			'onopenpopulate' : str(fb_name) + '.getResultHandler()',
			'syspath' : "/%s/%s/" % (str(path), label),
			'openlink' : AUP + "/populate_generic/%s/%s/%s/%s/" % (str(patterns), str(fb_name), str(path), label),
			'num_children' : len(files)
		})
			

	return HttpResponse(str(json), mimetype = 'text/plain')

def history_ingestion(request):
	"""
	Return a JSON object with data related to ingestions' history
	"""

	try:
		limit = request.POST['limit']
	except Exception, e:
		return HttpResponseForbidden()

	try:
		limit = int(limit)
	except ValueError, e:
		# Unlimitted
		limit = 0

	res = Ingestion.objects.all().order_by('-start_ingestion_date')

	if limit > 0:
		res = res[:limit]

	#
	# We build a standard header that can be used for table's header.
	# header var must be a list not a tuple since it get passed 'as is' to the json 
	# dictionary
	#
	header = ['start', 'duration', 'ID', 'user', 'fitsverify', 'qsostatus', 'multiple', 'exit', 'log']

	data = []
	for ing in res:
			#
			# Unicode strings have to be converted to basic strings with str()
			# in order to get a valid JSON object.
			# Each header[j] is a list of (display value, type[, value2]).
			# type allows client-side code to known how to display the value.
			#
			data.append({	header[0] 	: [str(ing.start_ingestion_date), 'str'],
							header[1] 	: [str(ing.end_ingestion_date-ing.start_ingestion_date), 'str'],
							header[2] 	: [str(ing.label), 'str'],
							header[3] 	: [str(ing.user.username), 'str'],
							header[4]	: [ing.check_fitsverify, 'check'],
							header[5] 	: [ing.check_QSO_status, 'check'],
							header[6]	: [ing.check_multiple_ingestion, 'check'],
							header[7]	: [ing.exit_code, 'exit'],
							header[8]	: ['View log', 'link', str(AUP + "/history/ingestion/report/%d/" % ing.id)]
			})

	# Be aware that JS code WILL search for data and header keys
	json = { 'data' : data, 'header' : header }

	# Return a JSON object
	return HttpResponse(str(json), mimetype = 'text/plain')

def remap(idList):
	"""
	Build a list of ranges from an integer suite:

	IN:  1,2,3,4,6,7,8,9,11,12,13,20,22,23,24,25,30,40,50,51,52,53,54,60
	OUT: 1-4,6-9,11-13,20-20,22-25,30-30,40-40,50-54,60-60
	"""

	idList = idList.split(',')
	idList = [int(id) for id in idList]
	idList.sort()
	
	ranges = []
	i = idList[0]
	ranges.append(i)
	
	for k in range(len(idList)-1):
		if idList[k+1] > idList[k]+1:
			ranges.append(idList[k])
			ranges.append(idList[k+1])
	
	ranges.append(idList[-1])
	
	maps = ''
	for k in range(0, len(ranges)-1, 2):
		maps += "%s-%s," % (ranges[k], ranges[k+1])
	
	return maps[:-1]

def unremap(ranges):
	"""
	Build an integer suite from a list of ranges:

	IN:  1-4,6-9,11-13,20-20,22-25,30-30,40-40,50-54,60-60
	OUT: 1,2,3,4,6,7,8,9,11,12,13,20,22,23,24,25,30,40,50,51,52,53,54,60
	"""

	ranges = ranges.split(',')
	idList = ''

	for r in ranges:
		r = r.split('-')
		r = [int(j) for j in r]
		idList += string.join([str(j) for j in range(r[0], r[1]+1)], ',') + ','

	return idList[:-1]

def processing_imgs_remap_ids(request):
	"""
	Rewrite idList to prevent too long GET queries
	"""
	try:
		idList = request.POST['IdList']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	return HttpResponse(str({'mapList' : remap(idList)}), mimetype = 'text/plain')

def processing_imgs_from_idlist(request, ids):
	"""
	Builds an SQL query based on POST data, executes it and returns a JSON object containing results.
	"""

	# Build integer list from ranges
	ids = unremap(ids)

	# Now executes query
	db = DB(host = DATABASE_HOST,
			user = DATABASE_USER,
			passwd = DATABASE_PASSWORD,
			db = DATABASE_NAME)

	g = DBGeneric(db.con)
	query = """
SELECT a.id, a.name, b.name, a.object, c.name, a.alpha, a.delta 
FROM youpi_image AS a, youpi_run AS b, youpi_channel AS c
WHERE a.id IN (%s)
AND a.run_id = b.id
AND a.channel_id = c.id
ORDER BY a.name
""" % ids

	try:
		res = g.execute(query);
	except MySQLdb.DatabaseError, e:
		return HttpResponseServerError("Error: %s [Query: \"%s\"]" % (e, query))

	xml = """<?xml version="1.0" encoding="utf-8"?>
<rows>
	<head>
        <column width="50" type="ch" align="center" color="lightblue" sort="str">Select</column>
        <column width="100" type="ro" align="center" sort="str">Name</column>
        <column width="100" type="ro" align="center" sort="str">Run ID</column>
        <column width="100" type="ro" align="center" sort="str">Object</column>
        <column width="100" type="ro" align="center" sort="str">Channel</column>
        <column width="120" type="ro" align="center" sort="int">Ra</column>
        <column width="120" type="ro" align="center" sort="int">Dec</column>
		<settings>
			<colwidth>px</colwidth>
		</settings>
	</head>"""

	for img in res:
		xml += "<row id=\"%s\"><cell>1</cell><cell>%s</cell><cell>%s</cell><cell>%s</cell><cell>%s</cell><cell>%s</cell><cell>%s</cell></row>" % img
	
	xml += '</rows>'

	return HttpResponse(xml, mimetype = 'text/xml')

def processing_imgs_from_idlist_post(request):
	"""
	Builds an SQL query based on POST data, executes it and returns a JSON object containing results.
	"""

	try:
		ids = request.POST['Ids']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	# Build integer list from ranges
	ids = unremap(ids)

	# Now executes query
	db = DB(host = DATABASE_HOST,
			user = DATABASE_USER,
			passwd = DATABASE_PASSWORD,
			db = DATABASE_NAME)

	g = DBGeneric(db.con)
	query = """
SELECT a.id, a.name, b.name, a.object, c.name, a.alpha, a.delta 
FROM youpi_image AS a, youpi_run AS b, youpi_channel AS c
WHERE a.id IN (%s)
AND a.run_id = b.id
AND a.channel_id = c.id
ORDER BY a.name
""" % ids

	try:
		res = g.execute(query);
	except MySQLdb.DatabaseError, e:
		return HttpResponseServerError("Error: %s [Query: \"%s\"]" % (e, query))

	content  =[]
	for img in res:
		content.append([str(i) for i in img])

	return HttpResponse(str({'Headers': ['Name', 'Run ID', 'Object', 'Channel', 'Ra', 'Dec'], 'Content' : content}), mimetype = 'text/plain')

def processing_plugin(request):
	"""
	Entry point for client-side JS code to call any registered plugin's method
	"""

	try:
		pluginName = request.POST['Plugin']
		method = request.POST['Method']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	plugin = manager.getPluginByName(pluginName)
	try:
		res = eval('plugin.' + method + '(request)')
	except Exception, e:
		raise PluginError, e

	# Response must be a JSON-like object
	return HttpResponse(str({'result' : res}), mimetype = 'text/plain')

def batch_view_content(request, fileName):
	"""
	Parse XML content of file fileName to find out selections.
	"""

	fileName = '/tmp/' + request.user.username + '_' + fileName
	try:
		f = open(fileName)
		data = f.readlines()
		f.close()
	except IOError:
		return HttpResponseNotFound('File not found.')

	return HttpResponse(string.join(data), mimetype = 'text/xml')

def batch_view_selection(request):
	"""
	Returns selection content
	"""

	try:
		xmlstr = request.POST['XML']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	doc = dom.parseString(xmlstr)
	data = doc.getElementsByTagName('selection')[0]
	sel = batch_parse_selection(data);

	imgs = Image.objects.filter(id__in = sel['idList'].split(',')).order_by('name');

	return HttpResponse(str({'name' : str(sel['name']), 'data' : [[str(img.name), str(img.path)] for img in imgs]}), mimetype = 'text/plain')

def get_circle_from_multipolygon(alpha_center, delta_center, radius, p):
	"""
	Returns a MySQL MULTIPOLYGON object describing a circle with a resolution of p points.
	"""

	# Computing selection circle based (p points)
	rot = []
	p -= 1
	if p % 2 == 0:
		t = p/2
	else:
		t = p/2+1

	for i in range(t):
		rot.append(2*math.pi*(i+1)/p)

	ro = deepcopy(rot)
	ro.reverse()
	ro = ro[1:]
	for i in range(len(ro)):
		ro[i] = -ro[i]
	rot.extend(ro)

	p1x, p1y = alpha_center + radius, delta_center

	points = [p1x, p1y]

	for i in range(len(rot)):
		points.append(math.cos(rot[i])*(p1x - alpha_center) - math.sin(rot[i])*(p1y - delta_center) + alpha_center)
		points.append(math.sin(rot[i])*(p1x - alpha_center) + math.cos(rot[i])*(p1y - delta_center) + delta_center)

	points.append(p1x)
	points.append(p1y)

	strf = 'MULTIPOLYGON((('
	for j in range(0, len(points), 2):
		strf += "%f %f," % (points[j], points[j+1])
	strf = strf[:-1] + ')))'

	return strf

def batch_parse_selection(sel):
	"""
	Parse a single XML DOM selection.
	"""

	label = sel.getElementsByTagName('label')[0].firstChild.nodeValue
	alpha_center = float(sel.getElementsByTagName('alpha')[0].firstChild.nodeValue)
	delta_center = float(sel.getElementsByTagName('delta')[0].firstChild.nodeValue)
	radius = float(sel.getElementsByTagName('radius')[0].firstChild.nodeValue)

	imgs = Image.objects.filter(centerfield__contained = get_circle_from_multipolygon(alpha_center, delta_center, radius, 16))
	
	return {'xml' : str(sel.toxml()), 'name' : str(label), 'count' : len(imgs), 'idList' : string.join([str(img.id) for img in imgs], ',')}

def batch_parse_content(request):
	"""
	Parse XML content of file fileName to find out selections.
	This comes AFTER dtd validation so nothing to worry about.
	"""

	try:
		fileName = request.POST['Filename']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	import xml.dom.minidom as dom
	f = '/tmp/' + request.user.username + '_' + fileName
	doc = dom.parse(f)
		
	data = doc.getElementsByTagName('selection')
	selections = []
	for sel in data:
		selections.append(batch_parse_selection(sel))

	return HttpResponse(str({'result' : {'nbSelections' : len(selections), 'selections' : selections}}), mimetype = 'text/plain')
	
def upload_file(request):
	"""
	Checks for file upload. Must be name xmlfile, must be a valid XML file.
	exit_code != 0 if any problem found.
	"""

	exitCode = 0
	errMsg = ''
	try:
		try:
			files = request.FILES
			keys = files.keys()
		except:
			raise Exception, "Bad file submitted"

		if len(keys):
			k = keys[0]
			content = files[k]['content']
		else:
			raise Exception, "Could not get file content (Maybe check that your <input> file has a name and that your form definition is correct)."

		import xml.dom.minidom as dom
		doc = dom.parseString(content)

		# Valid XML file, save it to disk
		filename = files[k]['filename']
		f = open('/tmp/' + request.user.username + '_' + filename, 'w')
		f.write(content)
		f.close()
		
	except Exception, e:
		exitCode = 1
		content = ''
		filename = ''
		errMsg = str(str(e))

	return HttpResponse(str({'filename' : str(filename), 'length' : len(content), 'exit_code' : exitCode, 'error_msg' : errMsg }), mimetype = 'text/html')

def save_condor_node_selection(request):
	"""
	Save Condor nodes selection
	"""
	try:
		selHosts = request.POST['SelectedHosts'].split(',')
		label = request.POST['Label']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	sels = CondorNodeSel.objects.filter(label = label, is_policy = False)
	if sels:
		return HttpResponse(str({'Error' : str("'%s' label is already used, please use another name." % label)}), 
					mimetype = 'text/plain')

	nodesel = base64.encodestring(marshal.dumps(selHosts)).replace('\n', '')
	sel = CondorNodeSel(user = request.user, label = label, nodeselection = nodesel)
	sel.save()

	return HttpResponse(str({'Label' : str(label), 'SavedCount' : len(selHosts)}), mimetype = 'text/plain')

def save_condor_policy(request):
	"""
	Save Condor custom policy
	"""
	try:
		label = request.POST['Label']
		serial = request.POST['Serial']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	try:
		sels = CondorNodeSel.objects.filter(label = label, is_policy = True)
		if sels:
			if sels[0].user != request.user:
				# Only owner can update its policy
				return HttpResponse(str({'Error' : 'Only selection owner can update its policies. Policy not overwritten.'}), mimetype = 'text/plain')
			else:
				sel = sels[0]
				sel.nodeselection = serial
		else:
			sel = CondorNodeSel(user = request.user, label = label, nodeselection = serial, is_policy = True)

		sel.save()
		
	except Exception, e:
		return HttpResponse(str({'Error' : "%s" % e}), mimetype = 'text/plain')

	return HttpResponse(str({'Label' : str(label), 'Policy' : str(serial)}), mimetype = 'text/plain')

def del_condor_node_selection(request):
	"""
	Delete Condor node selection. 
	No deletion is allowed if at least one policy is using that selection.
	"""

	try:
		label = request.POST['Label']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	sel = CondorNodeSel.objects.filter(label = label, is_policy = False)[0]
	pols = CondorNodeSel.objects.filter(is_policy = True)
	if pols:
		for pol in pols:
			if pol.nodeselection.find(label) >= 0:
				return HttpResponse(str({'Error' : str("Some policies depends on this selection. Unable to delete selection '%s'." % label)}), 
					mimetype = 'text/plain')

	sel.delete()

	return HttpResponse(str({'Deleted' : str(label)}), mimetype = 'text/plain')

def del_condor_policy(request):
	"""
	Delete Condor policy
	"""

	try:
		label = request.POST['Label']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	sel = CondorNodeSel.objects.filter(label = label, is_policy = True)[0]
	sel.delete()

	return HttpResponse(str({'Deleted' : str(label)}), mimetype = 'text/plain')

def get_condor_node_selections(request):
	"""
	Returns Condor nodes selections.
	"""

	sels = CondorNodeSel.objects.filter(is_policy = False).order_by('label')

	return HttpResponse(str({'Selections' : [str(sel.label) for sel in sels]}), mimetype = 'text/plain')

def get_condor_policies(request):
	"""
	Returns Condor policies.
	"""

	sels = CondorNodeSel.objects.filter(is_policy = True).order_by('label')

	return HttpResponse(str({'Policies' : [str(sel.label) for sel in sels]}), mimetype = 'text/plain')

def get_condor_selection_members(request):
	"""
	Returns Condor selection members.
	"""

	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	data = CondorNodeSel.objects.filter(label = name, is_policy = False)
	error = ''

	if data:
		members = marshal.loads(base64.decodestring(str(data[0].nodeselection)))
		members = [str(s) for s in members]
	else:
		members = '';
		error = 'No selection of that name.'

	return HttpResponse(str({'Members' : members, 'Error' : error}), mimetype = 'text/plain')

def get_policy_data(request):
	"""
	Returns policy serialized data
	"""

	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	data = CondorNodeSel.objects.filter(label = name, is_policy = True)
	error = serial = ''

	if data:
		serial = str(data[0].nodeselection)
	else:
		error = 'No policy of that name.'

	return HttpResponse(str({'Serial' : serial, 'Error' : error}), mimetype = 'text/plain')

@login_required
@profile
def set_current_theme(request):
	"""
	Set default user theme
	"""
	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	p = request.user.get_profile()
	p.guistyle = name
	p.save()

	return HttpResponse(str({'Default': str(name)}), mimetype = 'text/plain')

@login_required
@profile
def pref_save_condor_config(request):
	"""
	Save per-user default condor setup
	"""
	try:
		db = request.POST['DB'].split(',')
		dp = request.POST['DP'].split(',')
		ds = request.POST['DS'].split(',')
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	condor_setup = {}
	k = 0
	for plugin in manager.plugins:
		condor_setup[plugin.id] = {}
		condor_setup[plugin.id]['DB'] = db[k]
		condor_setup[plugin.id]['DP'] = dp[k]
		condor_setup[plugin.id]['DS'] = ds[k]
		k += 1

	try:
		p = request.user.get_profile()
		p.dflt_condor_setup = base64.encodestring(marshal.dumps(condor_setup)).replace('\n', '')
		p.save()
	except Exception, e:
		return HttpResponse(str({'Error': str(e)}), mimetype = 'text/plain')

	return HttpResponse(str({'Setup': str(condor_setup)}), mimetype = 'text/plain')

if __name__ == '__main__':
	print 'Cannot be run from the command line.'
	sys.exit(2)
