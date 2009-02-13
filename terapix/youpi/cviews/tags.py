
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
