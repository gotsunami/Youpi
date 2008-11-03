
import time
from types import *
#
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
#
from terapix.spica2.models import *
from terapix.spica2.cviews import *
#
from settings import *

def cart_cookie_check(request):
	"""
	Check for the existence of cookie related to shopping cart
	"""
	if 'cart' not in request.session:
		request.session['cart'] = {'plugins' : {}}

	return HttpResponse(str({'data' : 'Cookie set!'}), mimetype = 'text/plain')

def cart_add_item(request):
	"""
	Add one item into shopping cart
	"""
	try:
		plugin = request.POST['plugin']
		userData = request.POST['userData']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	# Eval misc data wich has to be a dictionnary of custom data
	try:
		userData = eval(userData)
		if not type(userData) is DictType:
			raise TypeError, "Should be a dictionnary."
	except:
		return HttpResponseServerError('Incorrect POST data: ' + userData)

	if 'cart' not in request.session:
		# Maybe url has been called directly, which is NOT good
		return HttpResponseServerError()

	# Add data
	if not request.session['cart']['plugins'].has_key(plugin):
		request.session['cart']['plugins'][plugin] = []

	plugObj = manager.getPluginByName(plugin)
	# Useful to get a rather unique item ID in the shopping cart
	plugObj.itemCounter += 1

	request.session['cart']['plugins'][plugin].append({ 'date' : time.asctime(), 
														'userData' : userData,
														'itemCounter' : plugObj.itemCounter})

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
