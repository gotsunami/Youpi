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

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
#
from terapix.youpi.auth import *
from terapix.youpi.cviews import *
from terapix.youpi.models import *
#
import cjson as json
import time
from types import *

@login_required
@profile
def fetch_tags(request):
	"""
	Returns all available tags
	"""

	tags, filtered = read_proxy(request, Tag.objects.all().order_by('name'))
	data = [{	'name'		: tag.name, 
				'style'		: tag.style, 
				'comment'	: tag.comment, 
				'username'	: tag.user.username, 
				'date'		: str(tag.date)} 
			for tag in tags] 

	return HttpResponse(json.encode({'tags': data, 'filtered': filtered}), mimetype = 'text/plain')

@login_required
@profile
def get_tag_info(request):
	"""
	Returns one tag's information or empty dictionnary if tag does not exist
	"""

	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseForbidden()

	tag = Tag.objects.filter(name__exact = name)

	if tag:
		tag = tag[0]
		info = {
			'name'		: tag.name,
			'style'		: tag.style,
			'date'		: str(tag.date),
			'comment'	: tag.comment,
			'username'	: tag.user.username,
		}
	else:
		info = {}

	return HttpResponse(json.encode({'info' : info}), mimetype = 'text/plain')

@login_required
@profile
def get_images_from_tags(request):
	"""
	Returns list of matching images ids (formatted for Image Selector)
	"""
	# FIXME: not used?

	try:
		tags = eval(request.POST['Tags'])
	except Exception, e:
		return HttpResponseForbidden()

	rels = Rel_tagi.objects.filter(tag__name__in = tags)

	candidates = {}
	for t in tags:
		candidates[t] = []
		for r in rels:
			if r.tag.name == t:
				candidates[t].append(r.image.id)

	idList = []
	for id in candidates[candidates.keys()[0]]:
		keep = True
		for t in candidates.keys()[1:]:
			if id not in candidates[t]:
				keep = False
				break
		if keep:
			idList.append([str(id)])

	return HttpResponse(json.encode({'fields': ['id'], 'data': idList, 'hidden': ['']}), mimetype = 'text/plain')

@login_required
@profile
def save_tag(request):
	"""
	Saves new tag to DB.
	"""

	try:
		name = request.POST['Name']
		comment = request.POST.get('Comment', '')
		# CSS style
		style = request.POST['Style']
	except Exception, e:
		return HttpResponseForbidden()

	# First check for permission
	if not request.user.has_perm('youpi.add_tag'):
		return HttpResponse(json.encode({
			'Error': "Sorry, you don't have permission to add tags",
		}), mimetype = 'text/plain')

	profile = request.user.get_profile()
	try:
		tag = Tag(name = name, user = request.user, comment = comment, style = style, mode = profile.dflt_mode, group = profile.dflt_group)
		tag.save()
	except Exception, e:
		return HttpResponse(str({'Error' : str(e)}), mimetype = 'text/plain')

	return HttpResponse(str({'saved' : str(name)}), mimetype = 'text/plain')

@login_required
@profile
def update_tag(request):
	"""
	Updates tag
	"""

	try:
		key = request.POST['NameOrig']
		name = request.POST['Name']
		comment = request.POST.get('Comment', '')
		style = request.POST['Style'] # CSS style
	except Exception, e:
		return HttpResponseForbidden()

	tag = Tag.objects.filter(name__exact = key)[0]
	try:
		tag.name = name
		tag.comment = comment
		tag.style = style
		success = write_proxy(request, tag)
	except Exception, e:
		return HttpResponse(str({'Error' : str(e)}), mimetype = 'text/plain')

	return HttpResponse(json.encode({'updated': name, 'oldname': key, 'success': success}), mimetype = 'text/plain')

@login_required
@profile
def delete_tag(request):
	"""
	Deletes tag
	"""

	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseForbidden()

	try:
		tag = Tag.objects.filter(name__exact = name)[0]
		success = write_proxy(request, tag, delete = True)
	except Exception, e:
		return HttpResponse(str({'Error' : str(e)}), mimetype = 'text/plain')

	return HttpResponse(json.encode({'success': success, 'deleted' : name}), mimetype = 'text/plain')

@login_required
@profile
def tag_mark_images(request, createTag = False, idList = None, tagnames = None):
	"""
	Marks image(s) with tag(s).
	@param idList list of images to tag (optional)
	@param tags list of tag names (optional)
	"""

	try:
		tagnames = eval(request.POST['Tags'])
		idList = eval(request.POST['IdList'])[0]
	except Exception, e:
		# Check function parameters
		if not (idList and tagnames):
			return HttpResponseForbidden()

	profile = request.user.get_profile()
	# Marked image count
	marked = 0
	images = Image.objects.filter(id__in = idList)
	tags = Tag.objects.filter(name__in = tagnames)
	if not tags and createTag:
		for t in tagnames:
			z = Tag(name = t, user = request.user, comment = '', style = 'background-color: brown; color:white; border:medium none -moz-use-text-color;', mode = profile.dflt_mode, group = profile.dflt_group)
			z.save()
		tags = Tag.objects.filter(name__in = tagnames)

	imgtags = Rel_tagi.objects.filter(image__in = images)

	try:
		for img in images:
			newrel = False
			for tag in tags:
				try:
					tagi = Rel_tagi(image = img, tag = tag)
					tagi.save()
					newrel = True
				except IntegrityError:
					# Already tagged
					pass
			if newrel:
				marked += 1
	except Exception, e:
		return HttpResponse(str({'Error' : str(e)}), mimetype = 'text/plain')

	return HttpResponse(str({'marked' : marked}), mimetype = 'text/plain')

@login_required
@profile
def tag_unmark_images(request):
	"""
	Unmarks image(s) with tag(s)
	"""

	try:
		tags = eval(request.POST['Tags'])
		idList = eval(request.POST['IdList'])[0]
	except Exception, e:
		return HttpResponseForbidden()

	# Unmarked image count
	unmarked = 0
	images = Image.objects.filter(id__in = idList)
	tags = Tag.objects.filter(name__in = tags)
	imgtags = Rel_tagi.objects.filter(image__in = images, tag__in = tags)

	for rel in imgtags:
		rel.delete()
		unmarked += 1

	return HttpResponse(str({'unmarked' : int(unmarked)}), mimetype = 'text/plain')


