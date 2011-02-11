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
from terapix.lib.common import get_title_from_menu_id

@login_required
@profile
def home(request):
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

def cart_cookie_check(request):
	"""
	Check for the existence of cookie related to processing cart
	"""
	if 'cart' not in request.session:
		request.session['cart'] = {'plugins' : {}}

	return HttpResponse(str({'data' : 'Cookie set!'}), mimetype = 'text/plain')

def _cart_add_item(request, userData = None):
	"""
	Add one item into the processing cart
	"""
	# Eval misc data wich has to be a dictionnary of custom data
	plugin = request.POST['plugin']
	if userData is None:
		userData = request.POST['userData']
		try:
			if userData[0] == '"' and userData[len(userData)-1] == '"':
				userData = userData[1:-1]
			userData = json.decode(userData)
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
	else:
		# Do not add items twice
		# First remove the results output dir value which is subject to change on 
		# page refresh (random suffix)
		outdir = None
		kw = 'resultsOutputDir'
		if userData.has_key(kw):
			outdir = userData[kw]
		del userData[kw]
		for item in  request.session['cart']['plugins'][plugin]:
			ioutdir = None
			if item['userData'].has_key(kw):
				ioutdir = item['userData'][kw]
				del item['userData'][kw]
			if item['userData'] == userData:
				# Restore item's path
				if ioutdir:
					item['userData'][kw] = ioutdir
				return HttpResponse(json.encode({'warning': 'Item already existing in the processing cart.'}))
			else:
				# Restore item's path
				if ioutdir:
					item['userData'][kw] = ioutdir
		# New item: restore output directory
		if outdir:
			userData[kw] = outdir

	plugObj = manager.getPluginByName(plugin)
	# Useful to get a rather unique item ID in the processing cart
	plugObj.itemCounter += 1

	request.session['cart']['plugins'][plugin].append({ 'date' 			: time.asctime(), 
														'userData' 		: userData,
														'itemCounter' 	: plugObj.itemCounter})

def cart_add_item(request):
	try:
		plugin = request.POST['plugin']
		userData = request.POST['userData']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	_cart_add_item(request)
	return HttpResponse(json.encode({'count': _cart_items_count(request)}), mimetype = 'text/plain')

def cart_add_items(request):
	"""
	Add several items at once into the processing cart
	"""
	try:
		plugin = request.POST['plugin']
		userData = request.POST['userData']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')
	
	if 'cart' not in request.session:
		# Maybe url has been called directly, which is NOT good
		return HttpResponseServerError()

	userData = json.decode(userData)
	for data in userData:
		_cart_add_item(request, data)

	return HttpResponse(json.encode({'count': _cart_items_count(request)}), mimetype = 'text/plain')

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

	return HttpResponse(json.encode({'data' : 'done', 'count': _cart_items_count(request)}), mimetype = 'text/plain')

def cart_delete_items(request):
	"""
	Deletes arbitrary number of items depending on input data
	"""
	if 'cart' not in request.session:
		# Maybe url has been called directly, which is NOT good
		return HttpResponseServerError()

	data = request.POST
	deleted = 0
	for plugin, idxList in data.lists():
		if request.session['cart']['plugins'].has_key(plugin):
			idxList = [int(idx) for idx in idxList]
			idxList.sort(reverse = True)
			for idx in idxList:
				del request.session['cart']['plugins'][plugin][idx]
				if len(request.session['cart']['plugins'][plugin]) == 0:
					del request.session['cart']['plugins'][plugin]
				deleted += 1
		else:
			raise ValueError, "No plugin named " + plugin

	return HttpResponse(json.encode({'deleted' : deleted, 'count': _cart_items_count(request)}), mimetype = 'text/plain')

def _cart_items_count(request):
	"""
	Count items into cart (not a view)
	"""
	if 'cart' not in request.session:
		cart_cookie_check(request)

	count = 0
	for plugin, dataList in request.session['cart']['plugins'].iteritems():
		count += len(dataList)
	return count

def cart_items_count(request):
	"""
	Count items into cart
	"""
	return HttpResponse(json.encode({'count' : _cart_items_count(request)}), mimetype = 'text/plain')

def cart_saved_items_stats(request):
	"""
	Return some statistic on per-plugin saved items
	"""
	stats = {}
	for plugin in manager.plugins:
		items, filtered = read_proxy(request, CartItem.objects.filter(kind__name__exact = plugin.id).order_by('-date'))
		stats[plugin.id] = len(items)
	return HttpResponse(json.encode({'stats' : stats}), mimetype = 'text/plain')

