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
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound
from django.template import Template, Context
#
from terapix.youpi.forms import *
from terapix.youpi.cviews import *

def test_form(request):
	if request.method == 'POST':
		myform = ContactForm(request.POST)
#		if myform.is_valid():
#			raise "valid"
	else:
		myform = ContactForm()

	t = Template("<html><body>Form:<br/> <form action=\".\" method=\"POST\"><table>{{ form.as_table }}</table><p><input type=\"submit\" value=\"Submit\"/></p></form></body>")
	html = t.render(Context({'form' : myform}))

	return HttpResponse(html)
