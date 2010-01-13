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

# vim: set ts=4

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import views
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
from terapix.lib.common import *
from terapix.youpi.models import *
from terapix.youpi.auth import Permissions
from terapix.script.preingestion import preingest_table
from terapix.script.DBGeneric import *
from terapix.script.ingestion import getNowDateTime
#
import cjson as json
import MySQLdb, pyfits
import pprint, re, glob, string
import math, md5, random
import marshal, base64
import os, os.path, sys, pprint
import socket, time
import magic
from types import *
from copy import deepcopy
# Custom views
from terapix.exceptions import *
from terapix.youpi.pluginmanager import PluginManagerError, PluginError
from terapix.youpi.cviews.processingcart import *
from terapix.youpi.cviews.condor import *
from terapix.youpi.cviews.preingestion import *
from terapix.youpi.cviews.plot import *
from terapix.youpi.cviews.processing import *
from terapix.youpi.cviews.tags import *

@login_required
@profile
def index(request):
	"""
	This is the main entry point (root) of the web application.
	This is a callback function (as defined in django's urls.py file).
	"""

	menu_id = 'home'
	return render_to_response('index.html', {	
							'selected_entry_id'	: menu_id,
							'title' 			: get_title_from_menu_id(menu_id),
						},
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
	theme_dirs = glob.glob(os.path.join(settings.MEDIA_ROOT, 'themes', '*'))
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
	try:
		p = request.user.get_profile()
		config = marshal.loads(base64.decodestring(str(p.dflt_condor_setup)))
	except EOFError:
		config = None

	# Global permissions (non data related)
	user = request.user
	glob_perms = [
		['Can submit jobs on the cluster', 			'youpi.can_submit_jobs'],
		['Can view ingestion logs', 				'youpi.can_view_ing_logs'],
		['Can add tags', 							'youpi.add_tag'],
		['Can monitor running jobs on the cluster', 'youpi.can_monitor_jobs'],
		['Can view processing results', 			'youpi.can_view_results'],
		['Can grade qualityFITSed images', 			'youpi.can_grade'],
		['Can generate reports', 					'youpi.can_use_reporting'],
		['Can run a software version check', 		'youpi.can_run_softvc'],
	]

	menu_id = 'preferences'
	return render_to_response('preferences.html', {	
						'themes'			: themes,
						'plugins' 			: manager.plugins, 
						'current_theme'		: themes[k],
						'policies'			: policies,
						'selections'		: selections,
						'config'			: config,
						'selected_entry_id'	: menu_id, 
						'title' 			: get_title_from_menu_id(menu_id),
						'global_perms'		: [{'label': p[0], 'perm': user.has_perm(p[1])} for p in glob_perms],
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def condor_setup(request):
	"""
	Condor cluster setup
	"""
	menu_id = 'condorsetup'
	return render_to_response('condorsetup.html', {	
						'custom_condor_req' : request.user.get_profile().custom_condor_req,
						'selected_entry_id'	: menu_id, 
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def documentation(request):
	"""
	Documentation template
	"""
	menu_id = 'documentation'
	return render_to_response('documentation.html', {	
						'selected_entry_id'	: menu_id,
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def cart_view(request):
	"""
	Renders processing cart view.
	"""

	cartHasData = False
	if 'cart' not in request.session:
		request.session['cart'] = {'plugins' : {}}

	# Current items for user session
	cart_items = []
	for plugin, dataList in request.session['cart']['plugins'].iteritems():
		plugObj = manager.getPluginByName(plugin)
		if len(dataList):
			plugObj.setData(dataList)
			cartHasData = True
			cart_items.append(plugObj)
		else:
			plugObj.removeData()

	policies = CondorNodeSel.objects.filter(is_policy = True).order_by('label')
	selections = CondorNodeSel.objects.filter(is_policy = False).order_by('label')

	menu_id = 'processingcart'
	return render_to_response('processingcart.html', {	
					'cart_plugins' 		: cart_items, 
					'plugins' 			: manager.plugins, 
					'cartHasData' 		: cartHasData, 
					# Cluster node available policies + selections
					'policies'			: policies,
					'selections'		: selections,
					'selected_entry_id'	: menu_id, 
					'misc' 				: manager,
					'title' 			: get_title_from_menu_id(menu_id),
				},
				context_instance = RequestContext(request))

@login_required
@profile
def processing(request):
	menu_id = 'processing'
	return render_to_response('processing.html', { 	
						'plugins' 			: manager.plugins,
						'processing_output' : settings.PROCESSING_OUTPUT,
						'selected_entry_id'	: menu_id,
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def ing(request):
	"""
	Related to ingestion step.
	This is a callback function (as defined in django's urls.py file).
	"""

	insts = Instrument.objects.exclude(itt = None)
	q = Image.objects.all().count()
	menu_id = 'ing'
	return render_to_response('ingestion.html', {	
						'ingested' 			: q, 
						'selected_entry_id'	: menu_id, 
						'title' 			: get_title_from_menu_id(menu_id),
						# Available ITTs (Instrument Translation Tables)
						'itranstables'		: [inst.name for inst in insts],
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def monitoring(request):
	"""
	Related to monitoring.
	This is a callback function (as defined in django's urls.py file).
	"""

	menu_id = 'monitoring'
	return render_to_response('monitoring.html', {	
						'selected_entry_id'	: menu_id,
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
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

	menu_id = 'results'
	return render_to_response('results.html', {	
						'plugins' 			: manager.plugins, 
						'selected_entry_id'	: menu_id, 
						'outputDirs' 		: dirs,
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def reporting(request):
	"""
	Page to generate reports.
	"""
	# Standard (non-plugin related) reports definition
	selopts = """Select a processing type: <select name="kind_select">%s</select>""" % \
			string.join(map(lambda x: """<option value="%s">%s</option>""" % (x[0], x[1]), [(p.id, p.optionLabel) for p in manager.plugins]), '\n')
	reports = [
			{'id': 'imssavedselections',	'title': 'List of saved selections from image selector'},
			{'id': 'procresults', 			'title': 'List of processing results', 'options': selopts},
	]
	reports.sort(cmp=lambda x,y: cmp(x['title'], y['title']))

	menu_id = 'reporting'
	return render_to_response('reporting.html', {	
						# Global reports
						'reports'			: reports,
						'plugins' 			: manager.plugins, 
						'selected_entry_id'	: menu_id, 
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def tags(request):
	"""
	Related to tags page.
	This is a callback function (as defined in django's urls.py file).
	"""

	menu_id = 'tags'
	return render_to_response('tags.html', { 
					'selected_entry_id'	: menu_id,
					'title' 			: get_title_from_menu_id(menu_id),
				}, 
			context_instance = RequestContext(request))

@login_required
@profile
def render_plugin(request, pluginId):
	try:
		plugin = manager.getPluginByName(pluginId)
	except PluginManagerError, msg:
		return HttpResponseNotFound("Error: %s" % msg)

	menu_id = 'processing'
	return render_to_response('processing_plugin.html', { 	
						'plugin' 			: plugin,
						'selected_entry_id'	: menu_id, 
						'processing_output' : settings.PROCESSING_OUTPUT,
						'title' 			: plugin.id.capitalize(),
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def soft_version_monitoring(request):
	menu_id = 'monitoring'
	return render_to_response( 'softs_versions.html', {	
				'report' 			: len(settings.SOFTS), 
				'selected_entry_id'	: menu_id, 
				'title' 			: get_title_from_menu_id(menu_id),
			},
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

	menu_id = 'ing'
	return render_to_response( 'ingestion_report.html', {	
				'report' 			: report, 
				'selected_entry_id'	: menu_id, 
				'title' 			: get_title_from_menu_id(menu_id),
			},
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

	menu_id = 'results'
	return render_to_response( 'single_result.html', {	
					'pid' 				: pluginId, 
					'tid'	 			: taskId,
					'selected_entry_id'	: menu_id, 
					'plugin' 			: plugin,
					'title' 			: get_title_from_menu_id(menu_id),
				}, 
				context_instance = RequestContext(request))


def logout(request):
	auth.logout(request)
	# Redirect to home page
	return HttpResponseRedirect(settings.AUP)

def browse_api(request, type):
	if type == 'py' or type == 'python':
		path = 'py/html/'
	elif type == 'js' or type == 'javascript':
		path = 'js/'
	else:
		return HttpResponseNotFound('No API of that name exits.')

	# Redirect to API doc
	return HttpResponseRedirect('http://clix.iap.fr:8001/' + path)

def aff_img(request,image_name):
	"""
	Displays (popup) an image image_name.
	This is a callback function (as defined in django's urls.py file).
	"""

	db = MySQLdb.connect(host = settings.DATABASE_HOST, user = settings.DATABASE_USER, passwd = settings.DATABASE_PASSWORD, db = settings.DATABASE_NAME)
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
			'openlink' : settings.AUP + "/populate/%s/%s/%s/%s/" % (str(behaviour), str(tv_name), str(path), label),
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
			'openlink' : settings.AUP + "/populate_generic/%s/%s/%s/%s/" % (str(patterns), str(fb_name), str(path), label),
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

	# First check for permission
	if not request.user.has_perm('youpi.can_view_ing_logs'):
		return HttpResponse(str({
			'Error': "Sorry, you don't have permission to view ingestion logs",
		}), mimetype = 'text/plain')

	res = Ingestion.objects.all().order_by('-start_ingestion_date')

	if limit > 0:
		res = res[:limit]

	#
	# We build a standard header that can be used for table's header.
	# header var must be a list not a tuple since it get passed 'as is' to the json 
	# dictionary
	#
	header = ['start', 'duration', 'ID', 'user', 'fitsverified', 'validated', 'multiple', 'exit', 'log']

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
							header[5] 	: [ing.is_validated, 'check'],
							header[6]	: [ing.check_multiple_ingestion, 'check'],
							header[7]	: [ing.exit_code, 'exit'],
							header[8]	: ['View log', 'link', str(settings.AUP + "/history/ingestion/report/%d/" % ing.id)]
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

def processing_imgs_from_idlist_post(request):
	"""
	Builds an SQL query based on POST data, executes it and returns a JSON object containing results.
	"""

	try:
		ids = request.POST['Ids']
		page = request.POST.get('Page', 0)
		pageStatus = request.POST.get('PageStatus', None)
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	# Build integer list from ranges
	ids = unremap(ids).split(',')

	# Pagination handling
	count = len(ids)
	if page == 0:
		currentPage = 1
	else:
		currentPage = int(page)
	maxPerPage = settings.IMS_MAX_PER_PAGE
	nbPages = count / maxPerPage
	if count % maxPerPage > 0:
		nbPages += 1

	# Finds window boundaries
	wmin = maxPerPage * (currentPage-1)
	if count - wmin > maxPerPage:
		window = ids[wmin: wmin + maxPerPage]
	else:
		window = ids[wmin:]

	# Get image data for currentPage
	images = Image.objects.filter(id__in = window)

	content = []
	for img in images:
		rels = Rel_tagi.objects.filter(image = img)
		tags = Tag.objects.filter(id__in = [r.tag.id for r in rels]).order_by('name')
		if tags:
			cls = 'hasTags'
		else:
			cls = ''
		content.append([int(img.id), 
						str("<span class=\"imageTag %s\">%s.fits</span><div style=\"width: 200px;\">%s</div>" % 
							(cls, 		# Class name
							 img.name, 	# Image name
							 string.join([str("<span class=\"tagwidget\" style=\"%s;\">%s</span>" % (t.style, t.name)) for t in tags], '')))])

	return HttpResponse(str({'TotalPages': int(nbPages), 'CurrentPage': currentPage, 'Headers': ['Image Name/Tags'], 'Content' : content}), mimetype = 'text/plain')

def get_selected_ids_from_pagination(request):
	"""
	Returns a list of ids of selected images (in pagination mode)
	"""

	try:
		ids = request.POST['Ids']
		pageStatus = request.POST['PageStatus'].split('_')
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	# Build integer list from ranges
	ids = unremap(ids).split(',')
	range = settings.IMS_MAX_PER_PAGE
	idList = []

	k = j = 0
	pages = []
	while j < len(pageStatus):
		pages.append(ids[k:k+range])
		k += range
		j += 1

	k = 0
	for page in pages:
		ps = pageStatus[k].split(',')
		if ps[0] == 's':
			for unchecked in ps[1:]:
				del page[int(unchecked)]
		elif ps[0] == 'u':
			tmp = []
			for checked in ps[1:]:
				tmp.append(page[int(checked)])
			page = tmp
		else:
			return HttpResponse(str({'Error': 'pageStatus POST data bad formatted'}))

		idList.extend(page)
		k += 1

	count = len(idList)
	idList = string.join(idList, ',')

	return HttpResponse(str({'idList': str(idList), 'count': int(count)}), mimetype = 'text/plain')

def processing_plugin(request):
	"""
	Entry point for client-side JS code to call any registered plugin's method
	"""

	try:
		pluginName = request.POST['Plugin']
		method = request.POST['Method']
	except Exception, e:
		raise PostDataError, e

	if method == 'getTaskInfo':
		if not request.user.has_perm('youpi.can_view_results'):
			return HttpResponseForbidden("Sorry, you don't have permission to view processing results")
	elif method == 'process':
		if not request.user.has_perm('youpi.can_submit_jobs'):
			return HttpResponse(str({'result': {
				'Error': "Sorry, you don't have permission to submit jobs on the cluster",
			}}), mimetype = 'text/plain')

	plugin = manager.getPluginByName(pluginName)
	try:
		res = eval('plugin.' + method + '(request)')
	except Exception, e:
		raise PluginEvalError, e

	# Response must be a JSON-like object
	return HttpResponse(json.encode({'result': res}), mimetype = 'text/plain')

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
	Uploads a file into temporary directory.
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
			content = files[k].read()
		else:
			raise Exception, "Could not get file content"

		# Valid XML file, save it to disk
		filename = files[k].name
		f = open('/tmp/' + request.user.username + '_' + filename, 'w')
		f.write(content)
		f.close()
		
	except Exception, e:
		exitCode = 1
		content = ''
		filename = ''
		errMsg = str(str(e))

	return HttpResponse(str({'filename' : str(filename), 'length' : len(content), 'exit_code' : exitCode, 'error_msg' : errMsg }), mimetype = 'text/html')

def get_global_report(request, reportId):
	"""
	Generates a global report.
	@param reportId report Id
	"""
	post = request.POST
	if reportId == 'imssavedselections':
		from terapix.reporting.csv import CSVReport
		sels = ImageSelections.objects.all().order_by('date')
		content = []
		k = 1
		for s in sels:
			content.append((k, s.name))
			k += 1
		if not content: return HttpResponse('No saved selections found', mimetype = 'text/plain')
		return HttpResponse(str(CSVReport(data = content, separator = '\t')), mimetype = 'text/plain')

	elif reportId == 'procresults':
		try: kind = post['kind_select']
		except Exception, e:
			return HttpResponseRedirect('/youpi/reporting/')
		from terapix.reporting.csv import CSVReport
		from django.db import connection
		cur = connection.cursor()
		s = time.time()
		q = """
		SELECT t.success, t.title, t.start_date, u.username, t.hostname, t.clusterId, t.results_output_dir
		FROM youpi_processing_task AS t, auth_user AS u, youpi_processing_kind AS k
		WHERE t.user_id = u.id
		AND t.kind_id = k.id
		AND k.name = '%s'
		ORDER BY t.start_date
		""" % kind
		cur.execute(q)
		res = cur.fetchall()
		content = []
		for r in res:
			status = 'F' # Failed
			if r[0]: status = 'S'
			row = [status]
			row.extend(r[1:])
			content.append(row)
		if not content: return HttpResponse('No results found', mimetype = 'text/plain')
		return HttpResponse(str(CSVReport(data = content)), mimetype = 'text/plain')

	return HttpResponseNotFound('Report not found.')

def get_report(request, pluginId, reportId):
	"""
	Generate a report
	"""
	if not request.user.has_perm('youpi.can_use_reporting'):
		return HttpResponseForbidden("Sorry, you don't have permission to generate reports")
	try:
		plugObj = manager.getPluginByName(pluginId)
	except PluginManagerError:
		# May be a global report (not plugin related)
		if pluginId == 'global':
			return get_global_report(request, reportId)
		else:
			# Not found
			return HttpResponseNotFound()

	return plugObj.getReport(request, reportId)

def ims_get_image_list_from_file(request):
	"""
	Parse content of fileName and returns an image selection
	"""

	try:
		fileName = request.POST['Filename']
		onTheFly = json.decode(request.POST['OnTheFly'])
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	errMsg = ''
	try:
		f = open('/tmp/' + request.user.username + '_' + fileName)
		lines = f.readlines()
		f.close()
	except Exception, e:
		errMsg = "%s" % e


	basename = fileName[:fileName.rfind('.')]
	lines = [li[:-1] for li in lines]
	warnings = []
	# Separate lines with image name only (to issue only one SQL query)
	nameonly = []
	# ...from lines with image name and checksum (one SQL query per line)
	namemd5 = []
	idList = []
	j = comments = 0
	for line in lines:
		# Skip comments
		if line.find('#') == 0: 
			j += 1
			comments += 1
			continue
		sp = line.split(',')
		if len(sp) == 1:
			sp[0] = sp[0].strip()
			imgs = Image.objects.filter(name__startswith = sp[0])
			if not imgs:
				warnings.append("Line %d: image '%s' not found" % (j+1, sp[0]))
			else:
				img = imgs[len(imgs)-1]
				idList.append(img.id)
		elif len(sp) == 2:
			sp[0] = sp[0].strip()
			sp[1] = sp[1].strip()
			namemd5.append(sp)
			imgs = Image.objects.filter(name__startswith = sp[0], checksum = sp[1])
			if not imgs:
				warnings.append("Line %d: image '%s' (%s) not found" % (j+1, sp[0], sp[1]))
			else:
				img = imgs[len(imgs)-1]
				idList.append(img.id)
		else:
			# Line not well-formatted
			errMsg = "Line %d is not well-formatted: should be image_name[, md5sum]" % j+1
			break
		j += 1

	# Tag images on-the-fly
	if onTheFly: tag_mark_images(request, True, idList, [basename])

	return HttpResponse(json.encode({
		'tagged': onTheFly, 
		'tagname': basename, 
		'warnings': warnings, 
		'error': errMsg, 
		'foundCount': len(idList), 
		'total' : len(lines)-comments, 
		'idList' : idList}), mimetype = 'text/plain')

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

def save_condor_custom_reqstr(request):
	"""
	Save Condor custom requirement string
	"""
	try:
		reqstr = request.POST['Req']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	try:
		p = request.user.get_profile()
		p.custom_condor_req = reqstr
		p.save()
	except Exception, e:
		return HttpResponse(str({'Error' : "%s" % e}), mimetype = 'text/plain')

	return HttpResponse(str({'Status' : str('saved')}), mimetype = 'text/plain')

def del_condor_node_selection(request):
	"""
	Delete Condor node selection. 
	No deletion is allowed if at least one policy is using that selection.
	No deletion is allowed if at least Condor Default Setup rules is using that selection.
	"""

	try:
		label = request.POST['Label']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	profiles = SiteProfile.objects.all()
	for p in profiles:
		try:
			data = marshal.loads(base64.decodestring(str(p.dflt_condor_setup)))
		except EOFError:
			# No data found, unable to decodestring
			data = None

		if data:
			for plugin in data.keys():
				if data[plugin]['DS'] == label:
					return HttpResponse(str({'Error' : str("Cannot delete selection '%s'. User '%s' references it in his/her default selection preferences menu." 
								% (label, p.user.username))}), mimetype = 'text/plain')

	pols = CondorNodeSel.objects.filter(is_policy = True)
	if pols:
		for pol in pols:
			if pol.nodeselection.find(label) >= 0:
				return HttpResponse(str({'Error' : str("Some policies depends on this selection. Unable to delete selection '%s'." % label)}), 
					mimetype = 'text/plain')

	sel = CondorNodeSel.objects.filter(label = label, is_policy = False)[0]
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

	profiles = SiteProfile.objects.all()
	for p in profiles:
		try:
			data = marshal.loads(base64.decodestring(str(p.dflt_condor_setup)))
		except EOFError:
			# No data found, unable to decodestring
			data = None

		if data:
			for plugin in data.keys():
				if data[plugin]['DP'].find(label) >= 0:
					return HttpResponse(str({'Error' : str("Cannot delete policy '%s'. User '%s' references it in his/her default selection preferences menu." 
								% (label, p.user.username))}), mimetype = 'text/plain')

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

	kinds = ('DB', 'DP', 'DS')
	try:
		defaults = [request.POST[p].split(',') for p in kinds]
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	condor_setup = {}
	k = 0
	for plugin in manager.plugins:
		condor_setup[plugin.id] = {}
		j = 0
		for kind in kinds:
			try:
				if len(defaults[j][k]):
					condor_setup[plugin.id][kind] = str(defaults[j][k])
				else:
					condor_setup[plugin.id][kind] = ''
			except IndexError:
				condor_setup[plugin.id][kind] = ''
			j += 1
		k += 1

	try:
		p = request.user.get_profile()
		p.dflt_condor_setup = base64.encodestring(marshal.dumps(condor_setup)).replace('\n', '')
		p.save()
	except Exception, e:
		return HttpResponse(str({'Error': str(e)}), mimetype = 'text/plain')

	return HttpResponse(str({'Setup': str(condor_setup)}), mimetype = 'text/plain')

@login_required
@profile
def pref_load_condor_config(request):
	"""
	Load per-user default condor setup. Can be empty if user never saved its Condor default 
	config.
	"""

	try:
		p = request.user.get_profile()
		data = marshal.loads(base64.decodestring(str(p.dflt_condor_setup)))
	except EOFError:
		# No data found, unable to decodestring
		config = None

	return HttpResponse(str({'config': str(data)}), mimetype = 'text/plain')

@login_required
@profile
def get_image_info(request):
	"""
	Returns information about image
	"""

	try:
		id = request.POST['Id']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	try:
		img = Image.objects.filter(id = int(id))[0]
	except Exception, e:
		return HttpResponse(str({'Error': "%s" % e}), mimetype = 'text/plain')

	try: runName = Rel_ri.objects.filter(image = img)[0].run.name
	except: runName = None
	
	if img.is_validated == True:
		vStatus = 'VALIDATED'
	else:
		vStatus = 'OBSERVED'

	data = {
		'name'		: img.name + '.fits',
		'path'		: img.path,
		'alpha'		: str(img.alpha),
		'delta'		: str(img.delta),
		'exptime'	: str(img.exptime),
		'checksum'	: img.checksum,
		'flat'		: img.flat,
		'mask'		: img.mask,
		'reg'		: img.reg,
		'status'	: vStatus,
		'instrument': img.instrument.name,
		'run'		: runName,
		'channel'	: img.channel.name,
		'ingestion'	: img.ingestion.label,
		'ing start'	: str(img.ingestion.start_ingestion_date),
		'ing end'	: str(img.ingestion.end_ingestion_date),
		'ing by'	: img.ingestion.user.username,
	}

	return HttpResponse(json.encode({'info': data}), mimetype = 'text/plain')

@login_required
@profile
def stats_ingestion(request):
	"""
	Returns stats about ingestion
	"""

	total_images = Image.objects.all().count()
	instruments = Instrument.objects.all().order_by('name')
	imgs_per_instru = []
	for inst in instruments:
		imgcount = Image.objects.filter(instrument = inst).count()
		try: percent = imgcount*100./total_images
		except ZeroDivisionError: percent = 0
		imgs_per_instru.append({'instrument': str(inst.name), 'count': int(imgcount), 'percent': percent})

	channels = Channel.objects.all().order_by('name')
	imgs_per_channel = []
	for c in channels:
		imgCount = Image.objects.filter(channel = c).count()
		try: percent = imgCount*100./total_images
		except ZeroDivisionError: percent = 0
		imgs_per_channel.append({'channel': str(c.name), 'count': int(imgCount), 'percent': percent})

	data = {
		'totalImages' 			: int(total_images),
		'totalPerInstrument' 	: imgs_per_instru,
		'imgsPerChannel': imgs_per_channel,
	}

	return HttpResponse(str({'info': data}), mimetype = 'text/plain')

@login_required
@profile
def stats_processing(request):
	"""
	Returns stats about processings
	"""

	total_tasks = Processing_task.objects.all().count()
	kinds = Processing_kind.objects.all().order_by('name')
	tasks_per_kind = []
	for k in kinds:
		taskcount = Processing_task.objects.filter(kind = k).count()
		if total_tasks: percent = taskcount*100./total_tasks
		else: percent = 0
		tasks_per_kind.append({'kind': str(k.name), 'count': int(taskcount), 'percent': percent})

	failed_tasks = Processing_task.objects.filter(success = 0).count()

	data = {
		'tasksTotal' 	: int(total_tasks),
		'failedTasks'	: int(failed_tasks),
		'tasksPerKind' 	: tasks_per_kind,
	}

	return HttpResponse(str({'info': data}), mimetype = 'text/plain')

@login_required
@profile
def get_condor_log_files_links(request):
	"""
	Returns a dictionnary with entries for the log, error and output filenames 
	that should be used by plugins generating Condor submission files.
	@return Dictionnary with paths to Condor log files
	"""

	post = request.POST
	try:
		taskId = post['TaskId']
	except Exception, e:
		raise PluginError, "POST argument error. Unable to process data."

	task = Processing_task.objects.filter(id = taskId)[0]
	pattern = os.path.join(settings.CONDOR_LOG_DIR, task.kind.name.upper() + '.%s.' + task.clusterId)
	logs = {
		'log': pattern % 'log', 
		'error': pattern % 'err', 
		'out': pattern % 'out',
	}
	sizes = {'log': 0, 'error': 0, 'out': 0}

	for kind, path in logs.iteritems():
		try:
			sizes[kind] = int(os.path.getsize(path))
			logs[kind] = str("""<a href="/youpi/cluster/log/%s/%s/" target="_blank">%s</a>""" % (kind, taskId, logs[kind][logs[kind].rfind('/')+1:]))
		except OSError:
			logs[kind] = ''

	return HttpResponse(str({'logs': logs, 'sizes': sizes}), mimetype = 'text/plain')

@login_required
@profile
def show_condor_log_file(request, kind, taskId):
	"""
	Display Condor log file for a given kind and taskId
	@param kind one of 'log', 'error', 'out'
	@param taskId task Id
	"""

	if kind not in ('log', 'error', 'out'):
		return HttpResponseBadRequest('Bad request')

	try:
		task = Processing_task.objects.filter(id = taskId)[0]
	except:
		return HttpResponseBadRequest('Bad request')

	pattern = os.path.join(settings.CONDOR_LOG_DIR, task.kind.name.upper() + '.%s.' + task.clusterId)

	logs = {
		'log': pattern % 'log', 
		'error': pattern % 'err', 
		'out': pattern % 'out',
	}

	try:
		f = open(logs[kind], 'r')
		data = string.join(f.readlines(), '')
		if not data:
			data = 'Empty file.'
		f.close()
	except IOError:
		data = 'Log file not found on server (has it been deleted?)'

	return HttpResponse(str(data), mimetype = 'text/plain')

@login_required
@profile
def get_permissions(request):
	"""
	Returns permissions for a given entity.
	The return value is a JSON object like:

	{'user' : {'read': true, 'write': true},
	 'group': {'read': true, 'write': false},
	 'others': {'read': false, 'write': false}}
	"""

	post = request.POST
	try:
		# Target entity
		target = post['Target']
		# Unique key to identify an element in table
		key = post['Key']
	except Exception, e:
		raise PluginError, "POST argument error. Unable to process data."

	ent = None
	if target == 'tag':
		tag = Tag.objects.filter(name = key)[0]
		ent = tag
	elif target == 'task':
		task = Processing_task.objects.filter(id = key)[0]
		ent = task
	elif target == 'imgsel':
		# Image selections
		sel = ImageSelections.objects.filter(name = key)[0]
		ent = sel
	elif target == 'config':
		config = ConfigFile.objects.filter(id = key)[0]
		ent = config
	elif target == 'cartitem':
		carti = CartItem.objects.filter(id = key)[0]
		ent = carti
	elif target == 'profile':
		prof = SiteProfile.objects.filter(user = request.user)[0]
		ent = prof
	else:
		raise PermissionsError, "Permissions for target %s not supported" % target

	isOwner = ent.user == request.user
	groups = [g.name for g in request.user.groups.all()]

	# Current user permissions
	if target == 'profile':
		cuser_read = cuser_write = True
		ent.group = ent.dflt_group
		perms = Permissions(ent.dflt_mode)
	else:
		cuser_read = cuser_write = False
		perms = Permissions(ent.mode)

	if (isOwner and perms.user.read) or \
		(ent.group.name in groups and perms.group.read) or \
		perms.others.read:
		cuser_read = True
	if (isOwner and perms.user.write) or \
		(ent.group.name in groups and perms.group.write) or \
		perms.others.write:
		cuser_write = True

	return HttpResponse(json.encode({
		'mode'			: str(perms), 
		'perms'			: perms.toJSON(), 
		'isOwner'		: isOwner,
		'username'		: ent.user.username,
		'groupname'		: ent.group.name,
		'groups'		: groups,
		'currentUser' 	: {'read': cuser_read, 'write': cuser_write},
	}), mimetype = 'text/plain')

@login_required
@profile
def set_permissions(request):
	"""
	Sets permissions for a given entity.
	The return value is a JSON object like:
	Perms is a string like: 1,1,1,0,0,0 specifying read/write bits for user/group/others respectively
	"""

	post = request.POST
	try:
		# Target entity
		target = post['Target']
		# Unique key to identify an element in table
		key = post['Key']
		# New perms to apply
		perms = post['Perms']
		group = post['Group']
	except Exception, e:
		raise PluginError, "POST argument error. Unable to process data."

	# Deserialize perms
	perms = [int(i) for i in perms.split(',')]
	# Owner can always read
	u = 4
	g = o = 0
	if perms[1] == 1: u += 2
	# Group
	if perms[2] == 1: g += 4
	if perms[3] == 1: g += 2
	# Others
	if perms[4] == 1: o += 4
	if perms[5] == 1: o += 2
	perms = "%d%d%d" % (u, g, o)

	group = Group.objects.filter(name = group)[0]
	isOwner = False
	error = ''

	if target == 'tag':
		tag = Tag.objects.filter(name = key)[0]
		ent = tag
	elif target == 'task':
		task = Processing_task.objects.filter(id = key)[0]
		ent = task
	elif target == 'imgsel':
		# Image selections
		sel = ImageSelections.objects.filter(name = key)[0]
		ent = sel
	elif target == 'config':
		config = ConfigFile.objects.filter(id = key)[0]
		ent = config
	elif target == 'cartitem':
		carti = CartItem.objects.filter(id = key)[0]
		ent = carti
	elif target == 'profile':
		prof = SiteProfile.objects.filter(user = request.user)[0]
		ent = prof
	else:
		raise PermissionsError, "Permissions for target %s not supported" % target

	if ent.user != request.user:
		error = 'Operation Not Allowed'
	else:
		if target == 'profile': 
			ent.dflt_group = group
			ent.dflt_mode = perms
		else:
			ent.mode = perms
			ent.group = group
		ent.save()

	return HttpResponse(json.encode({'Error': error, 'Mode': perms}), mimetype = 'text/plain')

@login_required
@profile
def get_user_default_permissions(request):
	"""
	Returns user default permissions
	{'default_mode': <mode>, 'default_group': <group>'}
	"""

	p = request.user.get_profile()

	return HttpResponse(str({
		'perms'	: Permissions(p.dflt_mode).toJSON(),
		'default_group'	: str(p.dflt_group),
	}), mimetype = 'text/plain')

@login_required
@profile
def ims_import_selections(request):
	"""
	Batch import selections of images.
	Import all selection files in a directory. File names are matched against a pattern.
	For each file the selection is matched. If ok creates a new saved selection. If at least one image is missing from 
	a selection description, no saved selection is created at all, instead reports a warning.
	"""
	post = request.POST
	try:
		path = post['Path']
		patterns = post['Patterns'].split(';')
		# FIXME
		#onTheFly = json.decode(request.POST['OnTheFly'])
	except:
		raise PluginError, "invalid post parameters %s" % post

	res = {}
	MAX_FILE_SIZE = 256 * 1024 # In Kb
	STEP = 10

	files = []
	try:
		for pat in patterns:
			pfiles = glob.glob(os.path.join(path, pat))
			files.extend(pfiles)
	except:
		res['error'] = 'An error occured when looking for files in the provided path. Please check your path and try again'

	try: 
		pos = int(post['Pos'])
		total = int(post['Total'])
		skipped = int(post.get('Skipped', 0))
	except:
		# First call to this function
		# Compute total
		total = len(files);
		skipped = 0
		pos = 0

	profile = request.user.get_profile()
	mag = magic.open(magic.MAGIC_NONE)
	mag.load()

	res['skipped'] = skipped
	profile = request.user.get_profile()
	frame = range(len(files))[pos:]
	z = 0
	warnings = []
	for k in frame:
		if pos == total: break
		pos += 1
		z += 1
		try:
			# Check magic number. Must be equal to 'ASCII text'
			if mag.file(files[k]).find('ASCII') == -1 and os.path.getsize(files[k]) > MAX_FILE_SIZE:
				res['skipped'] += 1
				continue
			f = open(files[k])
			lines = f.readlines()
			f.close()
		except Exception, e:
			res['error'] = str(e)
			break

		fileName = files[k]
		basename = fileName[:fileName.rfind('.')]
		lines = [li[:-1] for li in lines]
		namemd5 = []
		idList = []
		j = 0
		for line in lines:
			# Skip comments
			if line.find('#') == 0: 
				j += 1
				continue
			sp = line.split(',')
			if len(sp) == 1:
				sp[0] = sp[0].strip()
				imgs = Image.objects.filter(name__startswith = sp[0])
				if not imgs:
					warnings.append("In %s (Line %d): image '%s' not found, will not make a selection from this file" % (os.path.basename(fileName), j+1, sp[0]))
					break
				else:
					img = imgs[len(imgs)-1]
					idList.append(img.id)
			elif len(sp) == 2:
				sp[0] = sp[0].strip()
				sp[1] = sp[1].strip()
				namemd5.append(sp)
				imgs = Image.objects.filter(name__startswith = sp[0], checksum = sp[1])
				if not imgs:
					warnings.append("In %s (Line %d): image '%s' (%s) not found, will not make a selection from this file" % (os.path.basename(fileName), j+1, sp[0], sp[1]))
					break
				else:
					img = imgs[len(imgs)-1]
					idList.append(img.id)
			else:
				# Line not well-formatted
				res['error'] = "Line %d is not well-formatted: should be image_name[, md5sum]" % j+1
				break
			j += 1

		# Do not save the selection if at least one file is missing, continue to next file
		if warnings: continue

		# Tag images on-the-fly
		# FIXME
		#if onTheFly: tag_mark_images(request, True, idList, [basename])

		sList = base64.encodestring(marshal.dumps([idList])).replace('\n', NULLSTRING)
		selname = os.path.basename(basename)
		try:
			# Updates entry
			imgSelEntry = ImageSelections.objects.filter(name = selname)[0]
			imgSelEntry.data = sList
			success = write_proxy(request, imgSelEntry)
			if not success:
				warnings.append("In %s: could not save the selection" % os.path.basename(fileName))
		except:
			# ... or inserts a new one
			imgSelEntry = ImageSelections(name = selname, data = sList, user = request.user, mode = profile.dflt_mode, group = profile.dflt_group)
			imgSelEntry.save()
			success = True
		res['success'] = success

		if z > STEP: break

	res['warnings'] = warnings
	res['total'] = total
	res['pos'] = pos 
	if total == 0: res['percent'] = 0
	else: res['percent'] = pos*100./total

	return HttpResponse(json.encode({'result': res}))

if __name__ == '__main__':
	print 'Cannot be run from the command line.'
	sys.exit(2)
