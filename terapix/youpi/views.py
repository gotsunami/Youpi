
# vim: set ts=4

import cjson as json
import MySQLdb, pyfits
import pprint, re, glob, string
import md5, random
import marshal, base64
import os, os.path, sys, pprint
import socket, time
from types import *
#
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import views
from django.contrib.auth.models import * 
from django.contrib.auth.decorators import login_required
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect, HttpResponseBadRequest
from django.db.models import get_models
from django.db.models import Q
from django.utils.datastructures import *
from django.template import Template, Context, RequestContext
from django.views.decorators.cache import cache_page
#
from terapix.exceptions import *
from terapix.lib.common import *
from terapix.lib import pretty
from terapix.script.preingestion import preingest_table
from terapix.script.DBGeneric import *
from terapix.script.ingestion import getNowDateTime
from terapix.youpi.auth import Permissions
from terapix.youpi.cviews import profile
from terapix.youpi.models import *
from terapix.youpi.pluginmanager import manager, ApplicationManagerError, PluginError

@login_required
@profile
def home(request):
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
def processing(request):
	menu_id = 'processing'
	# Add info for can_use_plugin_* permissions
	for p in manager.plugins:
		p.accessGranted = request.user.has_perm('youpi.can_use_plugin_' + p.id)

	return render_to_response('processing.html', { 	
						'plugins' 			: manager.plugins,
						'processing_output' : list(settings.PROCESSING_OUTPUT),
						'selected_entry_id'	: menu_id,
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def render_plugin(request, pluginId):
	try:
		plugin = manager.getPluginByName(pluginId)
	except ApplicationManagerError, msg:
		return HttpResponseNotFound("Error: %s" % msg)

	if not request.user.has_perm('youpi.can_use_plugin_' + pluginId):
		return HttpResponseForbidden("Sorry, you don't have permission to use the %s plugin" % plugin.description)

	menu_id = 'processing'
	# Computes a random seed that will be used by plugins to generate 
	# unique processing output data path
	import random, hashlib
	return render_to_response('processing_plugin.html', { 	
						'plugin' 			: plugin,
						'selected_entry_id'	: menu_id, 
						'processing_output' : list(settings.PROCESSING_OUTPUT),
						'title' 			: plugin.id.capitalize(),
						'random_seed'		: hashlib.md5(str(time.time()/random.randint(0, 100000))).hexdigest()[:8],
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
		import traceback
		if settings.DEBUG:
			print '-' * 60
			print '-- Processing plugin exception occured! Traceback follows'
			print '-' * 60
			traceback.print_exc(file = sys.stdout)
			print '-' * 60
		raise PluginEvalError, e

	# Response must be a JSON-like object
	return HttpResponse(json.encode({'result': res}), mimetype = 'text/plain')

def get_image_info_raw(id):
	"""
	Returns information about image
	"""
	img = Image.objects.filter(id = int(id))[0]

	try: runName = Rel_ri.objects.filter(image = img)[0].run.name
	except: runName = None
	
	if img.is_validated == True:
		vStatus = 'VALIDATED'
	else:
		vStatus = 'OBSERVED'
	
	return {
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
		'imgid'		: img.id,
	}

@login_required
@profile
def get_image_info(request):
	"""
	Returns information about image
	"""
	try:
		id = request.POST['Id']
	except:
		return HttpResponseBadRequest('Incorrect POST data: %s' % e)
	
	try:
		data = get_image_info_raw(id)
	except Exception, e:
		return HttpResponse(str({'Error': "%s" % e}), mimetype = 'text/plain')

	return HttpResponse(json.encode({'info': data}), mimetype = 'text/plain')

@login_required
@profile
def view_image(request, taskId):
	"""
	View image in browser using iipimage
	"""
	try:
		task = Processing_task.objects.get(id = int(taskId))
	except Exception, e:
		raise 

	image = Rel_it.objects.get(task = task).image
	return render_to_response('iipimageviewer.html', {	
		'directory': task.results_output_dir,
		'fullpath': os.path.join(task.results_output_dir, image.filename + '.tif'),
	}, 
	context_instance = RequestContext(request))

@login_required
@profile
def gen_image_header(request, image_id):
	"""
	Generates image .ahead file
	"""
	from terapix.script import genimgdothead
	try:
		img = Image.objects.filter(id = image_id)[0]
		dhead, numext, missing = genimgdothead.genImageDotHead(int(img.id))
	except:
		return HttpResponseBadRequest("Error: image not found")

	hasHeader = False
	rawHead = ''
	if dhead:
		dhead = genimgdothead.formatHeader(dhead)
		rawHead = genimgdothead.getRawHeader(dhead, numext)
		hasHeader = True

	# Extra data
	img.info = get_image_info_raw(image_id)
	img.related = Rel_it.objects.filter(image = img).order_by('-id')
	menu_id = 'processing'
	return render_to_response('imageinfo.html', {	
		'selected_entry_id'	: menu_id, 
		'title' 			: get_title_from_menu_id(menu_id),
		'img'				: img,
		'rawHeader'			: rawHead,
		'hasHeader'			: hasHeader,
		'missing'			: missing,
	}, 
	context_instance = RequestContext(request))

	return HttpResponse(json.encode({'info': headdata}), mimetype = 'text/plain')

def get_entity_permissions(request, target, key):
	"""
	Returns permissions for a given entity.
	The return value is a JSON object like:

	{'user' : {'read': true, 'write': true},
	 'group': {'read': true, 'write': false},
	 'others': {'read': false, 'write': false}}

	Note that this is NOT a Django view. See get_permissions() instead.

	@param target Target entity to query
	@param key Used to identify an entity element
	"""
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
	elif target == 'ingestion':
		ent = Ingestion.objects.filter(id = key)[0]
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

	return {
		'mode'			: str(perms), 
		'perms'			: perms.toJSON(), 
		'isOwner'		: isOwner,
		'username'		: ent.user.username,
		'groupname'		: ent.group.name,
		'groups'		: groups,
		'currentUser' 	: {'read': cuser_read, 'write': cuser_write},
	}

@login_required
@profile
def ping(request):
	"""
	Ping. Return HTTP 200 response.
	"""
	return HttpResponse(json.encode('pong'), mimetype = 'text/plain')

def maintenance(request):
	"""
	Renders maintenance template
	"""
	if hasattr(settings, 'MAINTENANCE') and not settings.MAINTENANCE:
		return HttpResponseRedirect(reverse('terapix.youpi.views.index'))
	return render_to_response('maintenance.html')

def main_test_runner(request):
	"""
	Youpi's JSUnit test runner.
	"""
	return render_to_response('unittesting/testRunner.html', context_instance = RequestContext(request))

def main_test_suite(request):
	"""
	Youpi's JSUnit test suite.
	"""
	return render_to_response('unittesting/test_suite.html', context_instance = RequestContext(request))

def get_test(request, name):
	"""
	Gets Youpi's JSUnit test by name.
	"""
	return render_to_response("unittesting/tests/%s.html" % name, context_instance = RequestContext(request))

@login_required
@profile
def autocomplete(request, key, value):
	"""
	Auto-completes <input> fields
	"""
	value = value.split('=')[1]
	res = []

	if key == 'IngestionName':
		data = Ingestion.objects.filter(label__istartswith = value)
		for d in data:
			res.append({'value' : str(d.label), 'info' : str("%s - %s" % (d.user.username, d.start_ingestion_date))})
	elif key == 'ImageSelections':
		data = ImageSelections.objects.filter(name__istartswith = value)
		for d in data:
			res.append({'value' : str(d.name), 'info' : str("%s - %s" % (d.user.username, d.date))})
	elif key == 'ConfigFile':
		data = ConfigFile.objects.filter(name__istartswith = value)
		for d in data:
			res.append({'value' : str(d.name), 'info' : str("%s - %s" % (d.user.username, d.date))})
	elif key == 'CondorSavedSelections':
		data = CondorNodeSel.objects.filter(label__istartswith = value, is_policy = False)
		for d in data:
			res.append({'value' : str(d.label), 'info' : str("%s - %s" % (d.user.username, d.date))})
	elif key == 'CondorSavedPolicies':
		data = CondorNodeSel.objects.filter(label__istartswith = value, is_policy = True)
		for d in data:
			res.append({'value' : str(d.label), 'info' : str("%s - %s" % (d.user.username, d.date))})
	elif key == 'Tag':
		data = Tag.objects.filter(name__istartswith = value).order_by('name')
		for d in data:
			res.append({'value' : str(d.name), 'info' : str("%s - %s" % (d.user.username, d.date))})

	return HttpResponse(str({'results' : res}), mimetype = 'text/plain')

def processing_check_config_file_exists(request):
	"""
	Checks if a config file with that name (for a given processing plugin) already exists.
	"""
	try:
		kind = request.POST['Kind']
		name = request.POST['Name']
		type = request.POST['Type']
	except Exception, e:
		return HttpResponseForbidden()

	config = ConfigFile.objects.filter(kind__name__exact = kind, name = name, type__name = type)
	if config:
		exists = 1
	else:
		exists = 0
	return HttpResponse(str({'result' : exists}), mimetype = 'text/plain')

