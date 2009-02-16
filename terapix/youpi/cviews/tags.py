
import time
from types import *
#
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
#
from terapix.youpi.models import *
from terapix.youpi.cviews import *
#
from settings import *

def fetch_tags(request):
	"""
	Returns all available tags
	"""

	tags = Tag.objects.all().order_by('name')

	return HttpResponse(str({'tags' : [str(tag.name) for tag in tags]}), mimetype = 'text/plain')

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
			'name': str(tag.name),
			'style': str(tag.style),
			'date': str(tag.date),
			'comment': str(tag.comment),
			'username': str(tag.user.username),
		}
	else:
		info = {}

	return HttpResponse(str({'info' : info}), mimetype = 'text/plain')

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

	try:
		tag = Tag(name = name, user = request.user, comment = comment, style = style)
		tag.save()
	except Exception, e:
		return HttpResponse(str({'Error' : str(e)}), mimetype = 'text/plain')

	return HttpResponse(str({'saved' : str(name)}), mimetype = 'text/plain')

