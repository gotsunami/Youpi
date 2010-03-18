# vim: set ts=4
from django.conf import settings
from django.contrib.auth.models import * 
from django.contrib.auth.decorators import login_required
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden
from django.http import HttpResponseNotFound, HttpResponseRedirect, HttpResponseBadRequest
from django.template import Template, Context, RequestContext
#
from terapix.lib.common import *
from terapix.youpi.models import *
from terapix.youpi.auth import Permissions
from terapix.script.DBGeneric import *
#
import MySQLdb
import re, string
import os, os.path, sys
from types import *
# Custom views
from terapix.exceptions import *
from terapix.youpi.cviews import *
from terapix.youpi.pluginmanager import PluginManagerError

@login_required
@profile
def reporting(request):
	"""
	Page to generate reports.
	"""
	from terapix.youpi.forms import ReportAdvancedImageForm

	# Global (non-plugin related) reports definition
	selopts = """Select a processing type: <select name="kind_select">%s</select>""" % \
			string.join(map(lambda x: """<option value="%s">%s</option>""" % (x[0], x[1]), [(p.id, p.optionLabel) for p in manager.plugins]), '\n')
	reports = [
		{	'id': 'imssavedselections',	
			'title': 'List of saved selections from the image selector (TXT)', 
			'description': 'This report generates a list of all custom saved selections available in the image selector.',
		},
		{	'id': 'procresults', 
			'title': 'List of processing results (CSV)', 
			'options': selopts,
			'description': 'This report generates a CSV file (plain text) with all processing results. Depending on the current state of ' + \
				'the database, it may take some time to generate.',
		},
		{	'id': 'advimgreport',	
			'title': 'Advanced image report (HTML, PDF)',
			'description': 'TODO',
			'template' : 'reports/advanced-image-report-options.html',
			'context': {'form' : ReportAdvancedImageForm()},
		},
	]

	# Sanity checks: looks for manfatory info
	mandatory = ('id', 'title', 'description')
	for r in reports:
		for mand in mandatory:
			if not r.has_key(mand):
				raise ReportIncompleteDefinitionError, "Report has no %s set (required): %s" % (mand, r)
	plugins = manager.plugins
	for p in plugins:
		try:
			rdata = p.reports()
			if not rdata: continue
			for r in rdata:
				for mand in mandatory:
					if not r.has_key(mand):
						raise ReportIncompleteDefinitionError, "Report has no %s set (required): %s" % (mand, r)
		except AttributeError:
			pass

	reports.sort(cmp=lambda x,y: cmp(x['title'], y['title']))

	menu_id = 'reporting'
	return render_to_response('reporting.html', {	
						# Global reports
						'reports'			: reports,
						'plugins' 			: manager.plugins, 
						'selected_entry_id'	: menu_id, 
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

def get_global_report(request, reportId):
	"""
	Generates a global report.
	@param reportId report Id
	"""
	post = request.POST
	if reportId == 'imssavedselections':
		from terapix.reporting.csv import CSVReport
		sels = ImageSelections.objects.all().order_by('date')
		content = []
		k = 1
		for s in sels:
			content.append((k, s.name))
			k += 1
		if not content: return HttpResponse('No saved selections found', mimetype = 'text/plain')
		return HttpResponse(str(CSVReport(data = content, separator = '\t')), mimetype = 'text/plain')

	elif reportId == 'procresults':
		try: kind = post['kind_select']
		except Exception, e:
			return HttpResponseRedirect('/youpi/reporting/')
		from terapix.reporting.csv import CSVReport
		from django.db import connection
		import time
		cur = connection.cursor()
		s = time.time()
		q = """
		SELECT t.success, t.title, t.start_date, u.username, t.hostname, t.clusterId, t.results_output_dir
		FROM youpi_processing_task AS t, auth_user AS u, youpi_processing_kind AS k
		WHERE t.user_id = u.id
		AND t.kind_id = k.id
		AND k.name = '%s'
		ORDER BY t.start_date
		""" % kind
		cur.execute(q)
		res = cur.fetchall()
		content = []
		for r in res:
			status = 'F' # Failed
			if r[0]: status = 'S'
			row = [status]
			row.extend(r[1:])
			content.append(row)
		if not content: return HttpResponse('No results found', mimetype = 'text/plain')
		return HttpResponse(str(CSVReport(data = content)), mimetype = 'text/plain')

	elif reportId == 'advimgreport':
		from terapix.youpi.forms import ReportAdvancedImageForm

		form = ReportAdvancedImageForm(post)
		if form.is_valid(): 
			from django.template.loader import get_template
			tmpl = get_template('reports/advanced-image-report-options.html')
			tdata = tmpl.render(Context({'report': {'context': {'form': form}}}))

			# Builds query
			tables = ['youpi_image AS i']
			tquery = 'SELECT DISTINCT(i.id) FROM %s '
			query = ''
			updated = False
			if post['date_obs_min']:
				query += "dateobs >= '%s'" % post['date_obs_min']
				updated = True
			if post['date_obs_max']:
				if not updated:
					query += "dateobs <= '%s'" % post['date_obs_max']
				else:
					query += " AND dateobs <= '%s'" % post['date_obs_max']
				updated = True
			if post['exptime_min']:
				if updated: query += " AND"
				query += " exptime >= %s" % post['exptime_min']
				updated = True
			if post['exptime_max']:
				if updated: query += " AND"
				query += " exptime <= %s" % post['exptime_max']
				updated = True
			# TODO: radec, radius
			if post['run_id'] and post['run_id'] != '-1':
				tables.append('youpi_rel_ri AS ri')
				if updated: query += " AND"
				query += " ri.run_id = %s AND ri.image_id = i.id" % post['run_id']
				updated = True
			if post['flat']:
				if updated: query += " AND"
				query += ' flat LIKE \'%' + post['flat'] + '%\''
				updated = True
			if post['mask']:
				if updated: query += " AND"
				query += ' mask LIKE \'%' + post['mask'] + '%\''
				updated = True
			if post['object']:
				if updated: query += " AND"
				query += ' object LIKE \'%' + post['object'] + '%\''
				updated = True
			if post['airmass_min']:
				if updated: query += " AND"
				query += ' airmass >= %s' % post['airmass_min']
				updated = True
			if post['airmass_max']:
				if updated: query += " AND"
				query += ' airmass <= %s' % post['airmass_max']
				updated = True
			if post.has_key('tags'):
				tables.append('youpi_rel_tagi AS tagi')
				tagList =  post.getlist('tags')
				if updated: query += " AND"
				query += " tagi.image_id = i.id AND ("
				for tagid in tagList:
					query += ' tagi.tag_id = %s OR' % tagid
				query = query[:-3] + ')'
				updated = True
			if post.has_key('instruments'):
				tables.append('youpi_instrument AS inst')
				instList =  post.getlist('instruments')
				if updated: query += " AND"
				query += " inst.id = i.instrument_id AND ("
				for instid in instList:
					query += ' inst.id = %s OR' % instid
				query = query[:-3] + ')'
				updated = True
			if post.has_key('channels'):
				tables.append('youpi_channel AS chan')
				chanList =  post.getlist('channels')
				if updated: query += " AND"
				query += " chan.id = i.channel_id AND ("
				for chanid in chanList:
					query += ' chan.id = %s OR' % chanid
				query = query[:-3] + ')'
				updated = True
			if post['elongation_min']:
				tables.append('youpi_plugin_fitsin AS fitsin')
				tables.append('youpi_processing_task AS task')
				tables.append('youpi_rel_it AS relit')
				if updated: query += " AND"
				query += ' fitsin.psfelmin >= %s AND fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id' % post['elongation_min']
				updated = True
			if post['elongation_max']:
				if not post['elongation_min']:
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
				if updated: query += " AND"
				query += ' fitsin.psfelmax <= %s AND fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id' % post['elongation_max']
				updated = True
			if post['seeing_min']:
				if not post['elongation_min'] and not post['elongation_max']:
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
				if updated: query += " AND"
				query += ' fitsin.psffwhmmin >= %s AND fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id' % post['seeing_min']
				updated = True
			if post['seeing_max']:
				if not post['elongation_min'] and not post['elongation_max'] and not post['seeing_min']:
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
				if updated: query += " AND"
				query += ' fitsin.psffwhmmax <= %s AND fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id' % post['seeing_max']
				updated = True
			if post['sky_background_min']:
				if not post['elongation_min'] and not post['elongation_max'] and not post['seeing_min'] and not post['seeing_max']:
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
				if updated: query += " AND"
				query += ' fitsin.bkg >= %s AND fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id' % post['sky_background_min']
				updated = True
			if post['sky_background_max']:
				if not post['elongation_min'] and not post['elongation_max'] and not post['seeing_min'] and not post['seeing_max'] and not post['sky_background_min']:
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
				if updated: query += " AND"
				query += ' fitsin.bkg <= %s AND fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id' % post['sky_background_max']
				updated = True
			if post.has_key('grades'):
				if not post['elongation_min'] and not post['elongation_max'] and not post['seeing_min'] and not post['seeing_max'] and not post['sky_background_min'] and not post['sky_background_max']:
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
				tables.append('youpi_firstqeval AS eval')
				gList =  post.getlist('grades')
				if updated: query += " AND"
				query += ' fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id AND eval.fitsin_id = fitsin.id AND ('
				for gid in gList:
					query += " eval.grade = '%s' OR" % gid
				query = query[:-3] + ')'
				updated = True
			if post['comment']:
				if not post['elongation_min'] and not post['elongation_max'] and not post['seeing_min'] and not post['seeing_max'] and not post['sky_background_min'] and not post['sky_background_max']:
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
					if updated: query += " AND"
					query += ' fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id AND eval.fitsin_id = fitsin.id AND '
				if not post.has_key('grades'):
					tables.append('youpi_firstqeval AS eval')
				tables.append('youpi_firstqcomment AS fcom')
				query += ' eval.comment_id = fcom.id AND '
				query += ' (eval.custom_comment LIKE \'%' + post['comment'] + '%\' OR fcom.comment LIKE \'%' + post['comment'] + '%\')'
				updated = True

			tquery = tquery % ','.join(tables)
			if updated: tquery += ' WHERE '
			query = tquery + query + ';'

			# If WHERE not in query, there will be too much results
			if query.find('WHERE') == -1:
				report_content = """
<h3 style="margin-bottom: 20px; color: brown;">Waaaayyy too much results! Please fill in at least one search criterium.</h3>
<input type="button" onclick="var d=this.next('div'); d.visible()?d.hide():d.show(); return false;" value="Toggle selected criteria"/>
<div style="display: none;">
	<div>
		<input id="report_submit" type="submit" value="Generate!"/>
		<div>%s</div>
		<input id="report_submit" type="submit" value="Generate!"/>
	</div>
</div>
</form>
	""" % tdata
				return render_to_response('report.html', {	
									'report_title' 		: 'Advanced image report (HTML, PDF)',
									'report_content' 	: report_content,
									'before_extra_content'	: """<form action="/youpi/report/global/%s/" id="report_form" method="post">""" % reportId,
				}, context_instance = RequestContext(request))


				# First query: fetch image IDs
			db = MySQLdb.connect(host = settings.DATABASE_HOST, user = settings.DATABASE_USER, passwd = settings.DATABASE_PASSWORD, db = settings.DATABASE_NAME)
			cursor = db.cursor()
			cursor.execute(query)
			res = cursor.fetchall()
			res = [str(r[0]) for r in res]

			if not res:
				# No result so far, exit now
				report_content = """
<h3 style="margin-bottom: 20px; color: brown;">No match.</h3>
<input type="button" onclick="var d=this.next('div'); d.visible()?d.hide():d.show(); return false;" value="Toggle selected criteria"/>
<div style="display: none;">
	<div>
		<input id="report_submit" type="submit" value="Generate!"/>
		<div>%s</div>
		<input id="report_submit" type="submit" value="Generate!"/>
	</div>
</div>
</form>
	""" % tdata
				return render_to_response('report.html', {	
									'report_title' 		: 'Advanced image report (HTML, PDF)',
									'report_content' 	: report_content,
									'before_extra_content'	: """<form action="/youpi/report/global/%s/" id="report_form" method="post">""" % reportId,
				}, context_instance = RequestContext(request))
			
			# Builds a second query to gather all requested information
			cols =  post.getlist('show_column_in_report')
			tquery = 'SELECT %s FROM %s WHERE '
			tables = ['youpi_image AS i']
			fields = ['i.id AS img_id', 'i.name AS img_name']
			query = ''
			updated = False
			fitsinTablesInUse = False
			for col in cols:
				if col == 'Image checksum':
					fields.append('i.checksum')
				elif col == 'Image path':
					fields.append('i.path')
				elif col == 'Date obs':
					fields.append('i.dateobs')
				elif col == 'Exptime':
					fields.append('i.exptime')
				# TODO: ra dec, radius
				elif col == 'Run id':
					tables.append('youpi_rel_ri AS ri')
					tables.append('youpi_run AS run')
					fields.append('run.name AS run_name')
					if updated: query += " AND"
					query += " ri.image_id = i.id AND run.id = ri.run_id"
					updated = True
				elif col == 'Flat':
					fields.append('i.flat')
				elif col == 'Mask':
					fields.append('i.mask')
				elif col == 'Object':
					fields.append('i.object')
				elif col == 'Airmass':
					fields.append('i.airmass')
				elif col == 'Instrument':
					fields.append('inst.name AS instrument_name')
					tables.append('youpi_instrument AS inst')
					if updated: query += " AND"
					query += " inst.id = i.instrument_id"
					updated = True
				elif col == 'Channel':
					fields.append('chan.name AS channel_name')
					tables.append('youpi_channel AS chan')
					if updated: query += " AND"
					query += " chan.id = i.channel_id"
					updated = True
				elif col == 'Elongation':
					fields.append('fitsin.psfel AS elongation')
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
					if updated: query += " AND"
					query += ' fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id'
					updated = True
					# Mark fitsin related tables in use
					fitsinTablesInUse = True
				elif col == 'Seeing':
					fields.append('fitsin.psffwhm AS seeing')
					if not fitsinTablesInUse:
						tables.append('youpi_plugin_fitsin AS fitsin')
						tables.append('youpi_processing_task AS task')
						tables.append('youpi_rel_it AS relit')
						if updated: query += " AND"
						query += ' fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id'
						updated = True
						fitsinTablesInUse = True
				elif col == 'Sky background':
					fields.append('fitsin.bkg AS sky_background')
					if not fitsinTablesInUse:
						tables.append('youpi_plugin_fitsin AS fitsin')
						tables.append('youpi_processing_task AS task')
						tables.append('youpi_rel_it AS relit')
						if updated: query += " AND"
						query += ' fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id'
						updated = True
						fitsinTablesInUse = True
						
			# Prepares second query
			tquery = tquery % (', '.join(fields), ', '.join(tables))
			query = tquery + query
			if updated: query += ' AND'
			query += " i.id IN (%s);" % ','.join(res)
			cursor.execute(query)
			res = cursor.fetchall()
			db.close()

			# Final res list
			f_res = []
			for r in res:
				f_res.append(list(r))

			# Handle grades/comments
			if 'Grade' in cols or 'Comment' in cols:
				from terapix.script.grading import get_grades
				grades = get_grades(idList = [r[0] for r in res])
				# Dict with img id as a key
				idGrades = {}
				for g in grades:
					idGrades[g[4]] = g[:-1]

				# Merge grades with previous results
				if 'Grade' in cols:
					if 'Comment' in cols:
						for r in f_res:
							if idGrades.has_key(r[0]):
								r.append(idGrades[r[0]][1])
								r.append(idGrades[r[0]][2])
					else:
						for r in f_res:
							if idGrades.has_key(r[0]):
								r.append(idGrades[r[0]][1])
				else:
					for r in f_res:
						if idGrades.has_key(r[0]):
							r.append(idGrades[r[0]][2])

			# Handle tags
			if 'Tags' in cols:
				imgs = Image.objects.filter(id__in = [r[0] for r in f_res])
				tags = {}
				for img in imgs:
					tags[img.id] = [t.name for t in img.tags()]
				# Merge grades with previous results
				for r in f_res:
					if tags.has_key(r[0]):
						r.append(', '.join(tags[r[0]]))

			res = f_res
			report_content = """
<h2>Matches: %d</h2>
<input type="button" onclick="var d=this.next('div'); d.visible()?d.hide():d.show(); return false;" value="Toggle selected criteria"/>
<div style="display: none;">
	<div>
		<input id="report_submit" type="submit" value="Generate!"/>
		<div>%s</div>
		<input id="report_submit" type="submit" value="Generate!"/>
	</div>
</div>
<div style="color: black;">
	<table style=""" % (len(res), tdata)
			report_content += '"width: 100%;">'

			for row in res:
				report_content += "<tr>"
				for c in row:
					report_content += "<td>%s</td>" % c
				report_content += "</tr>"

			report_content += """
	</table>
</div>
</form>
"""

			return render_to_response('report.html', {	
								'report_title' 		: 'Advanced image report (HTML, PDF)',
								'report_content' 	: report_content,
								'before_extra_content'	: """<form action="/youpi/report/generating/global/%s/" id="report_form" method="post">""" % reportId,
								'after_extra_content': '',
			}, context_instance = RequestContext(request))
		else:
			# Report errors in form
			from django.template.loader import get_template
			tmpl = get_template('reports/advanced-image-report-options.html')
			tdata = tmpl.render(Context({'report': {'context': {'form': form}}}))

			return render_to_response('report.html', {	
								'report_title' 		: 'Advanced image report (HTML, PDF)',
								'report_content' 	: tdata,
								'before_extra_content'	: """<form action="/youpi/report/global/%s/" id="report_form" method="post">""" % reportId,
								'after_extra_content'	: """<input id="report_submit" type="submit" value="Generate!"/></form>""",
			}, context_instance = RequestContext(request))

	return HttpResponseNotFound('Report not found.')

def generating_report(request, pluginId, reportId):
	"""
	Renders intermediate template with a convenient 'Generating report...' message
	while building the report.
	"""
	return render_to_response('generating-report.html', {	
						'params'	: request.POST,
						'target'	: '/youpi/report/' + pluginId + '/' + reportId + '/',
	}, context_instance = RequestContext(request))

def get_report(request, pluginId, reportId):
	"""
	Generate a report
	"""
	if not request.user.has_perm('youpi.can_use_reporting'):
		return HttpResponseForbidden("Sorry, you don't have permission to generate reports")
	try:
		plugObj = manager.getPluginByName(pluginId)
	except PluginManagerError:
		# May be a global report (not plugin related)
		if pluginId == 'global':
			return get_global_report(request, reportId)
		else:
			# Not found
			return HttpResponseNotFound()

	return plugObj.getReport(request, reportId)

