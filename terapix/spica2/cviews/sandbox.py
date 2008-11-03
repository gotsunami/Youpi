
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound
from django.template import Template, Context
#
from terapix.spica2.forms import *
from terapix.spica2.cviews import *
#
from terapix.settings import *

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


def test_js(request):
	hosts = condor_status()
	return render_to_response('testjs.html', {'condor_hosts': hosts })
