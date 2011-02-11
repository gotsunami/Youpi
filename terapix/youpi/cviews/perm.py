
import os.path
import cjson as json
import marshal, base64, zlib
#
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.cache import cache_page
from django.db import IntegrityError
from django.shortcuts import render_to_response
from django.template import RequestContext
#
from terapix.youpi.models import *
from terapix.youpi.cviews import profile 
from terapix.youpi.views import get_entity_permissions
from terapix.lib.common import get_title_from_menu_id

@login_required
@profile
def get_permissions(request):
	"""
	Returns permissions for a given entity. See get_entry_permissions().
	"""
	post = request.POST
	try:
		# Target entity
		target = post['Target']
		# Unique key to identify an element in table
		key = post['Key']
	except Exception, e:
		raise PluginError, "POST argument error. Unable to process data."
	return HttpResponse(json.encode(get_entity_permissions(request, target, key)), mimetype = 'text/plain')

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
	elif target == 'ingestion':
		ent = Ingestion.objects.filter(id = key)[0]
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
	perms = Permissions(p.dflt_mode)

	return HttpResponse(json.encode({
		'perms'			: perms.toJSON(),
		'default_group'	: str(p.dflt_group),
		'perms_octal'	: perms.toOctal(),
		'username'		: request.user.username,
	}), mimetype = 'text/plain')

