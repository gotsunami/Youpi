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

from types import *
import os.path, time
import xml.dom.minidom as dom
#
import matplotlib
# Do NOT use GTK backend
matplotlib.use('Agg')
from matplotlib.pylab import *
from random import *
#
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
#
from terapix.youpi.models import *
from terapix.youpi.cviews import *

def rand_color():
	"""
	Built an RGB string based on random number between 0 and 0.9 for each color R,G,B:w
 
	"""
	f = "%.2f,%.2f,%.2f" %(uniform(0,0.9),uniform(0,0.9),uniform(0,0.9))	
	randcolor = list([float(m) for m in f.split(',')])
	return randcolor



def plot_sky_selections(request):
	"""
	Plot sky selections.

	Working POST parameters are:
	- Filename: name of server-side XML file used to retreive selections content
	- Selections: list of selections
	"""

	try:
		fileName = request.POST['Filename']
		plotCenter = int(request.POST.get('PlotCenter', '0'))
		selections = []
		withXML = True
	except Exception, e:
		try:
			selections = request.POST['Selections']
			if selections[:2] == '[[':
				selections = eval(selections)
				withXML = False
			else:
				raise Exception, 'Bad Selection parameter'
		except Exception, e:
			return HttpResponseBadRequest("Incorrect POST data: %s" % e)

	# Plot initializations
	font = { 'fontname' : 'Arial',
			 'fontsize' : '8' }
	
	rc('axes', labelsize = 8, edgecolor = '#6600CC', facecolor = '#F0F8FF', titlesize = '8', labelcolor = 'g', linewidth = '0.5')
	rc('legend', fontsize = 6, shadow = False, axespad = 0.7, pad = 0.1, isaxes = False)
	rc('xtick', labelsize = 6)
	rc('ytick', labelsize = 6)
		
	fig = figure()
	fig.add_subplot(111, projection='aitoff')

	title('Selections on sky sphere',fontsize=14)
	xlabel('Ra',font,color='r')
	ylabel('Dec',font,color='r')
	grid(True,aa=True,linewidth=0.3)

	rot = [	math.pi/6, 
			math.pi/3, 
			math.pi/2, 
			2*math.pi/3, 
			5*(math.pi)/6, 
			math.pi, 
			-5*(math.pi)/6, 
			-2*math.pi/3, 
			-math.pi/2, 
			-math.pi/3, 
			-math.pi/6, 
			0 ]

	if withXML:
		f = '/tmp/' + request.user.username + '_' + fileName
		doc = dom.parse(f)
		data = doc.getElementsByTagName('selection')
		for sel in data:
			label = sel.getElementsByTagName('label')[0].firstChild.nodeValue
			alpha_center = float(sel.getElementsByTagName('alpha')[0].firstChild.nodeValue)
			delta_center = float(sel.getElementsByTagName('delta')[0].firstChild.nodeValue)
			radius = float(sel.getElementsByTagName('radius')[0].firstChild.nodeValue)
			bbx = []
			bby = []
			reso = 12  
			bbx.append(alpha_center + radius)
			bby.append(delta_center)
			for i in range(0,reso):
				bbx.append(math.cos(rot[i])*(bbx[0] - alpha_center) - math.sin(rot[i])*(bby[0] - delta_center) + alpha_center)
				bby.append(math.sin(rot[i])*(bbx[0] - alpha_center) + math.cos(rot[i])*(bby[0] - delta_center) + delta_center)
	
			for j in range(len(bbx)):
				if bbx[j] >= 180:
					bbx[j] -= 360 
	
			for k in range(len(bbx)):
				bbx[k] *= (math.pi)/180
			for l in range(len(bby)):
				bby[l] *= (math.pi)/180
	
			x = []
			y = []
			x.append(alpha_center)
			y.append(delta_center)
	
			if x[0] >= 180:
				x[0] -= 360
	
			x[0] *= (math.pi)/180
			y[0] *= (math.pi)/180
			
			randcolor = rand_color()

			scatter(x,y, s = 1, marker = 'o', antialiased=True, label='_nolegend_',color = randcolor)	
	
			plot(bbx, bby, color = randcolor, linewidth=0.5, label= label+ " (Ra = "+str(alpha_center)+", Dec = "+str(delta_center)+", radius = "+str(radius)+")", aa = 'True')
			
		if plotCenter:
			x = []
			y = []
			imgs = Image.objects.all()
			for i in imgs:
				x.append(i.centerfield.x)
				y.append(i.centerfield.y)

			for i in range(len(x)):
				if x[i] >= 180:
					x[i] -= 360
				x[i] *= (math.pi)/180

			for i in range(len(y)):
				y[i] *= (math.pi)/180

			scatter(x,y, s = 0.002, marker = 'o', antialiased=True, label=  'Center of images',color = rand_color())
		legend()

	else:
		data = []
		for sel in selections:
			x = []
			y = []
			imgs = Image.objects.filter(id__in = sel)
			for i in imgs:
				x.append(i.centerfield.x)
				y.append(i.centerfield.y)

			for i in range(len(x)):
				if x[i] >= 180:
					x[i] -= 360
				x[i] *= (math.pi)/180

			for i in range(len(y)):
				y[i] *= (math.pi)/180
				
			scatter(x,y, s = 0.002, marker = 'o', antialiased=True, label=str(len(sel)) + ' images',color = rand_color())	
			legend()


	# Save images to disk
	imgRoot = 'sky'
	imgName = os.path.join(settings.MEDIA_ROOT, 'pubtmp', imgRoot + '.png')
	tnName = os.path.join(settings.MEDIA_ROOT, 'pubtmp', imgRoot + '_tn.png')

	savefig(imgName, dpi=140)
	savefig(tnName, dpi=40)

	clf() 

	return HttpResponse(str({'nbSelections' : len(data), 
						'imgName' : str('/media/pubtmp/' + imgRoot + '.png'), 
						'tnName' : str('/media/pubtmp/' + imgRoot + '_tn.png'), 'sels' : selections }), 
						mimetype = 'text/plain')

