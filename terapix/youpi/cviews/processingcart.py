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


import time
from types import *
import cjson as json
#
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
#
from terapix.exceptions import *
from terapix.youpi.models import *
from terapix.youpi.cviews import *
from terapix.youpi.auth import read_proxy

def cart_cookie_check(request):
	"""
	Check for the existence of cookie related to processing cart
	"""
	if 'cart' not in request.session:
		request.session['cart'] = {'plugins' : {}}

	return HttpResponse(str({'data' : 'Cookie set!'}), mimetype = 'text/plain')

def cart_add_item(request):
	"""
	Add one item into processing cart
	"""
	try:
		plugin = request.POST['plugin']
		userData = request.POST['userData']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	# Eval misc data wich has to be a dictionnary of custom data
	try:
		if userData[0] == '"' and userData[len(userData)-1] == '"':
			userData = userData[1:-1]
		userData = eval(userData)
		if not type(userData) is DictType:
			raise TypeError, "Should be a dictionnary, not %s" % type(userData)
	except Exception, e:
		return HttpResponseServerError("Incorrect POST data: %s" % e)

	if 'cart' not in request.session:
		# Maybe url has been called directly, which is NOT good
		return HttpResponseServerError()

	# Add data
	if not request.session['cart']['plugins'].has_key(plugin):
		request.session['cart']['plugins'][plugin] = []

	plugObj = manager.getPluginByName(plugin)
	# Useful to get a rather unique item ID in the processing cart
	plugObj.itemCounter += 1

	request.session['cart']['plugins'][plugin].append({ 'date' 			: time.asctime(), 
														'userData' 		: userData,
														'itemCounter' 	: plugObj.itemCounter})

	return HttpResponse(str({'data' : str(userData)}), mimetype = 'text/plain')

def cart_delete_item(request):
	"""
	Delete one item from its plugin
	"""
	try:
		plugin = request.POST['plugin']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	try:
		idx = int(request.POST['idx'])
		deleteAll = False
	except Exception, e:
		deleteAll = True

	if 'cart' not in request.session:
		# Maybe url has been called directly, which is NOT good
		return HttpResponseServerError()

	# Delete data
	if deleteAll:
		del request.session['cart']['plugins'][plugin][:]
	else:
		del request.session['cart']['plugins'][plugin][idx]
		if len(request.session['cart']['plugins'][plugin]) == 0:
			del request.session['cart']['plugins'][plugin]

	return HttpResponse(str({'data' : 'done'}), mimetype = 'text/plain')

def cart_items_count(request):
	"""
	Count items into cart
	"""

	if 'cart' not in request.session:
		cart_cookie_check(request)

	count = 0
	for plugin, dataList in request.session['cart']['plugins'].iteritems():
		count += len(dataList)

	return HttpResponse(str({'count' : count}), mimetype = 'text/plain')

def cart_saved_items_stats(request):
	"""
	Return some statistic on per-plugin saved items
	"""

	stats = {}
	for plugin in manager.plugins:
		items, filtered = read_proxy(request, CartItem.objects.filter(kind__name__exact = plugin.id).order_by('-date'))
		stats[plugin.id] = len(items)

	return HttpResponse(json.encode({'stats' : stats}), mimetype = 'text/plain')

