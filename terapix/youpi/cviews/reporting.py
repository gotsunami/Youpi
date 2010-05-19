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
#
from terapix.exceptions import *
from terapix.reporting import ReportFormat , global_reports
from terapix.youpi.cviews import *
from terapix.youpi.pluginmanager import PluginManagerError

@login_required
@profile
def reporting(request):
	"""
	Page to generate reports.
	"""
	from terapix.youpi.forms import ReportAdvancedImageForm

	# Sanity checks: looks for manfatory info
	mandatory = ('id', 'title', 'description', 'formats')
	for r in global_reports:
		for mand in mandatory:
			if not r.has_key(mand):
				raise ReportIncompleteDefinitionError, "Report '%s' has no '%s' set (required)" % (r['title'], mand)
	plugins = manager.plugins
	for p in plugins:
		try:
			rdata = p.reports()
			if not rdata: continue
			for r in rdata:
				for mand in mandatory:
					if not r.has_key(mand):
						raise ReportIncompleteDefinitionError, "Report '%s' has no '%s' set (required)" % (r['title'], mand)
		except AttributeError:
			pass

	global_reports.sort(cmp=lambda x,y: cmp(x['title'], y['title']))

	menu_id = 'reporting'
	return render_to_response('reporting.html', {	
						# Global reports
						'reports'			: global_reports,
						'plugins' 			: manager.plugins, 
						'selected_entry_id'	: menu_id, 
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

@login_required
def get_global_report(request, reportId, format):
	"""
	Generates a global report.
	@param reportId report Id
	@param format report's output format
	"""
	post = request.POST
	if format not in ReportFormat.formats():
		raise ValueError, "unsupported report output format: " + format

	ext = format.lower()
	fname = "%s-%s.%s" % (request.user.username, reportId, ext)

	if reportId == 'imssavedselections':
		title = 'List of saved selections from the image selector'
		sels = ImageSelections.objects.all().order_by('date')
		if not sels: 
			return render_to_response('report.html', {	
				'report_title' 		: title,
				'report_content' 	: "No saved selections found.",
			}, context_instance = RequestContext(request))

		if format != ReportFormat.HTML:
			fout = open(os.path.join(settings.MEDIA_ROOT, settings.MEDIA_TMP, fname), 'w')

			if format == ReportFormat.CSV:
				import csv
				writer = csv.writer(fout)
				k = 1
				for s in sels:
					writer.writerow([k, s.name])
					k += 1
			elif format == ReportFormat.TXT:
				for s in sels:
					fout.write(s.name + '\n')
			elif format == ReportFormat.PDF:
				for s in sels:
					fout.write(s.name + '\n')

			fout.close()
			return render_to_response('report.html', {	
								'report_title' 		: title,
								'report_content' 	: "<div class=\"report-download\"><a href=\"%s\">Download %s file report</a></div>" % 
									(os.path.join('/media', settings.MEDIA_TMP, fname), format),
			}, context_instance = RequestContext(request))
		else:
			content = []
			for s in sels:
				content.append(s.name)
			return render_to_response('report.html', {	
								'report_title' 		: title,
								'report_content' 	: '<br/>'.join(content),
			}, context_instance = RequestContext(request))

	elif reportId == 'procresults':
		title = 'List of processing results'
		try: kind = post['kind_select']
		except Exception, e:
			return HttpResponseRedirect('/youpi/reporting/')
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
		if not res: 
			return render_to_response('report.html', {	
				'report_title' 		: title,
				'report_content' 	: "No results found.",
			}, context_instance = RequestContext(request))

		content = []
		for r in res:
			status = 'F' # Failed
			if r[0]: status = 'S'
			row = [status]
			row.extend(r[1:])
			content.append(row)

		if format != ReportFormat.HTML:
			fout = open(os.path.join(settings.MEDIA_ROOT, settings.MEDIA_TMP, fname), 'w')

			if format == ReportFormat.CSV:
				import csv
				writer = csv.writer(fout)
				for row in content:
					writer.writerow(row)
			elif format == ReportFormat.TXT:
				for row in content:
					for c in row:
						fout.write(str(c) + ' ')
					fout.write('\n')
			elif format == ReportFormat.PDF:
				for row in content:
					fout.write(str(row) + '\n')

			fout.close()
			return render_to_response('report.html', {	
								'report_title' 		: title,
								'report_content' 	: "<div class=\"report-download\"><a href=\"%s\">Download %s file report</a></div>" % 
									(os.path.join('/media', settings.MEDIA_TMP, fname), format),
			}, context_instance = RequestContext(request))
		else:
			# HTML
			return render_to_response('report.html', {	
								'report_title' 		: title,
								'report_content' 	: '<br/>'.join([' '.join(str(r)) for r in content]),
			}, context_instance = RequestContext(request))

	elif reportId == 'advimgreport':
		from terapix.youpi.forms import ReportAdvancedImageForm
		form = ReportAdvancedImageForm(post)
		title = 'Advanced image report'

		if form.is_valid(): 
			from django.template.loader import get_template
			tmpl = get_template('reports/advanced-image-report-options.html')
			tdata = tmpl.render(Context({'report': {'context': {'form': form}}}))
			report_columns = post.getlist('show_column_in_report')

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
			if post['run_id'] and post['run_id'] != '-1':
				tables.append('youpi_rel_ri AS ri')
				if updated: query += " AND"
				query += " ri.run_id = %s AND ri.image_id = i.id" % post['run_id']
				updated = True
			if post['flat']:
				if updated: query += " AND"
				query += ' i.flat LIKE \'%' + post['flat'] + '%\''
				updated = True
			if post['mask']:
				if updated: query += " AND"
				query += ' i.mask LIKE \'%' + post['mask'] + '%\''
				updated = True
			if post['object']:
				if updated: query += " AND"
				query += ' i.object LIKE \'%' + post['object'] + '%\''
				updated = True
			if post['airmass_min']:
				if updated: query += " AND"
				query += ' i.airmass >= %s' % post['airmass_min']
				updated = True
			if post['airmass_max']:
				if updated: query += " AND"
				query += ' i.airmass <= %s' % post['airmass_max']
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
				query += ' fitsin.psffwhm >= %s AND fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id' % post['seeing_min']
				updated = True
			if post['seeing_max']:
				if not post['elongation_min'] and not post['elongation_max'] and not post['seeing_min']:
					tables.append('youpi_plugin_fitsin AS fitsin')
					tables.append('youpi_processing_task AS task')
					tables.append('youpi_rel_it AS relit')
				if updated: query += " AND"
				query += ' fitsin.psffwhm <= %s AND fitsin.task_id = task.id AND relit.task_id = task.id AND relit.image_id = i.id' % post['seeing_max']
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
			if query.find('youpi_processing_task') > 0:
				query = tquery + query + ' AND task.success=1;'
			else:
				query = tquery + query

			# If WHERE not in query, there will be too much results
			if query.find('WHERE') == -1 and not post['right_ascension_RA']:
				report_content = """
<h3 style="margin-bottom: 20px; color: brown;">Waaaayyy too much results! Please fill in at least one search criterium.</h3>
<script type="text/javascript">
	report_menu_insert('Toggle selected criteria', function() {var d=$('criteria'); d.visible()?d.hide():d.show();});
	report_menu_insert('Generate!', function() {d=$('report_form').submit();});
</script>
<div id="criteria" style="display: none;">
	<div>%s</div>
</div>
</form>
	""" % tdata
				return render_to_response('report.html', {	
									'report_title' 		: title,
									'report_content' 	: report_content,
									'before_extra_content'	: """<form action="/youpi/report/global/%s/%s/" id="report_form" method="post">""" % (reportId, format),
				}, context_instance = RequestContext(request))

			# First query: fetch image IDs
			db = MySQLdb.connect(host = settings.DATABASE_HOST, user = settings.DATABASE_USER, passwd = settings.DATABASE_PASSWORD, db = settings.DATABASE_NAME)
			cursor = db.cursor()
			cursor.execute(query)
			res = cursor.fetchall()

			# Check if a specified zone is targeted
			if post['right_ascension_RA'] and post['declination_DEC'] and post['radius']:
				ids = [r[0] for r in res]
				from terapix.youpi.views import get_circle_from_multipolygon
				# Get image subset from defined polygon
				imgs = Image.objects.filter(centerfield__contained = get_circle_from_multipolygon(
					form.cleaned_data['right_ascension_RA'], 
					form.cleaned_data['declination_DEC'], 
					form.cleaned_data['radius']), id__in = ids)
				res = [(img.id,) for img in imgs]

			if not res:
				# No result so far, exit now
				report_content = """
<h3 style="margin-bottom: 20px; color: brown;">No match.</h3>
<script type="text/javascript">
	report_menu_insert('Toggle selected criteria', function() {var d=$('criteria'); d.visible()?d.hide():d.show();});
	report_menu_insert('Generate!', function() {d=$('report_form').submit();});
</script>
<div id="criteria" style="display: none;">
	<div>%s</div>
</div>
</form>
	""" % tdata
				return render_to_response('report.html', {	
									'report_title' 		: title,
									'report_content' 	: report_content,
									'before_extra_content'	: """<form action="/youpi/report/global/%s/%s/" id="report_form" method="post">""" % (reportId, format),
				}, context_instance = RequestContext(request))
			
			# Builds a second query to gather all requested information
			res = [str(r[0]) for r in res]
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
				elif col == 'Right ascension (RA)':
					fields.append('i.alpha')
				elif col == 'Declination (DEC)':
					fields.append('i.delta')
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
			if query.find('youpi_processing_task') > 0:
				query += " i.id IN (%s) AND task.success=1;" % ','.join(res)
			else:
				query += " i.id IN (%s);" % ','.join(res)
			cursor.execute(query)
			res = cursor.fetchall()
			db.close()

			# Too much results?
			if len(res) > 1500:
				report_content = """
<h3 style="margin-bottom: 20px; color: brown;">Waaaayyy too much results (>1500)! For performance reasons, please refine your selection criteria.</h3>
<script type="text/javascript">
	report_menu_insert('Toggle selected criteria', function() {var d=$('criteria'); d.visible()?d.hide():d.show();});
	report_menu_insert('Generate!', function() {d=$('report_form').submit();});
</script>
<div id="criteria" style="display: none;">
	<div>%s</div>
</div>
</form>
	""" % tdata
				return render_to_response('report.html', {	
									'report_title' 		: title,
									'report_content' 	: report_content,
									'before_extra_content'	: """<form action="/youpi/report/global/%s/%s/" id="report_form" method="post">""" % (reportId, format),
				}, context_instance = RequestContext(request))

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
				# Make the 'Tags' column be the last in report_columns
				report_columns = [col for col in cols if col != 'Tags']
				report_columns.append('Tags')

			res = f_res

			if format != ReportFormat.HTML:
				fout = open(os.path.join(settings.MEDIA_ROOT, settings.MEDIA_TMP, fname), 'w')
				if format == ReportFormat.CSV:
					import csv
					writer = csv.writer(fout)
					for row in range(len(res)):
						writer.writerow(res[row])
				elif format == ReportFormat.TXT:
					for row in range(len(res)):
						fout.write(' '.join([str(s) for s in res[row]]) + '\n')
				elif format == ReportFormat.PDF:
					for row in range(len(res)):
						fout.write(' '.join([str(s) for s in res[row]]) + '\n')
				fout.close()
				return render_to_response('report.html', {	
									'report_title' 		: title,
									'report_content' 	: "<div class=\"report-download\"><a href=\"%s\">Download %s file report</a></div>" % 
										(os.path.join('/media', settings.MEDIA_TMP, fname), format),
				}, context_instance = RequestContext(request))

			import terapix.script.wrapper_processing as wrapper
			selName = "%s-%s-%s" % (reportId, request.user.username, wrapper.getNowDateTime())
			report_content = """
<h2>Matches: %d</h2>
<script type="text/javascript">
	report_menu_insert('Toggle selected criteria', function() {var d=$('criteria'); d.visible()?d.hide():d.show();});
	report_menu_insert('Generate!', function() {d=$('report_form').submit();});
	report_menu_insert('Save as image selection', function() {
		boxes.confirm("<p>This will save the current result set as an image selection for the image selector.</p><p>You will be able to " +
			"load this selection later with the 'Saved selection' criterium in the image selector.</p><p>Proceed?</p>", function() {
			var r = new HttpRequest(null,null,function() {Notifier.notify('New image selection saved under "%s"');});
			var post = {IdList: '%s', Name: '%s'};
			r.send('%s', $H(post).toQueryString());
		});
	});
</script>
<div id="criteria" style="display: none;">
	<div>%s</div>
</div>
<div style="padding-top: 10px; color: black;">
	<div style="width: %s;" id="rtable"></div>
</div>
</form>
"""	% (len(res), selName, "[[%s]]" % ','.join([str(r[0]) for r in res]), selName,
	reverse('terapix.youpi.views.processing_save_image_selection'), tdata, '98%'
)

			# Columns type in final report
			tnumbers = ('Right ascension (RA)', 'Declination (DEC)')
			body_end = """
<script type="text/javascript" src="http://www.google.com/jsapi"></script>
<script type="text/javascript">
	google.load('visualization', '1', {packages:['table']});
	google.setOnLoadCallback(drawTable);
	function drawTable() {
		var data = new google.visualization.DataTable();"""

			body_end += """
		data.addColumn('string', 'Image Name');"""
			for k in range(len(report_columns)):
				body_end += """
		data.addColumn('string', '%s');""" % report_columns[k]
			body_end += """
		data.addRows(%d);""" % len(res)

			for row in range(len(res)):
				body_end += """
		data.setCell(%d, 0, '<a target="_blank" href="%s">%s</a>');""" % (row, reverse('terapix.youpi.views.gen_image_header', args=[res[row][0]]), res[row][1])
				for col in range(len(res[row]))[2:]:
					body_end += """
		data.setCell(%d, %d, '%s');""" % (row, col-1, res[row][col])

			body_end += """
		var table = new google.visualization.Table($('rtable'));
		table.draw(data, {showRowNumber: true, allowHtml: true});
	}
</script>
"""

			return render_to_response('report.html', {	
								'report_title' 		: title,
								'report_content' 	: report_content,
								'before_extra_content'	: """<form action="/youpi/report/generating/global/%s/%s/" id="report_form" method="post">""" % (reportId, format),
								# Use Google chart table API
								'body_end': body_end,
			}, context_instance = RequestContext(request))
		else:
			# Report errors in form
			from django.template.loader import get_template
			tmpl = get_template('reports/advanced-image-report-options.html')
			tdata = tmpl.render(Context({'report': {'context': {'form': form}}}))
			report_content = """
<script type="text/javascript">
	report_menu_insert('Generate!', function() {d=$('report_form').submit();});
</script>
<div id="criteria">
	<div>%s</div>
</div>""" % tdata

			return render_to_response('report.html', {	
								'report_title' 		: title,
								'report_content' 	: report_content,
								'before_extra_content'	: """<form action="/youpi/report/global/%s/%s/" id="report_form" method="post">""" % (reportId, format),
			}, context_instance = RequestContext(request))

	return HttpResponseNotFound('Report not found.')

def generating_report(request, pluginId, reportId):
	"""
	Renders intermediate template with a convenient 'Generating report...' message
	while building the report.
	"""
	return render_to_response('generating-report.html', {	
						# list() to keep multiple values
						'params'	: request.POST.lists(),
						'target'	: '/youpi/report/' + pluginId + '/' + reportId + '/',
	}, context_instance = RequestContext(request))

def get_report(request, pluginId, reportId, format):
	"""
	Generate a report
	@param pluginId plugin's id or global
	@param reportId report's unique id
	@param format report's output format
	"""
	if not request.user.has_perm('youpi.can_use_reporting'):
		return HttpResponseForbidden("Sorry, you don't have permission to generate reports")
	try:
		plugObj = manager.getPluginByName(pluginId)
	except PluginManagerError:
		# May be a global report (not plugin related)
		if pluginId == 'global':
			return get_global_report(request, reportId, format)
		else:
			# Not found
			return HttpResponseNotFound()

	return plugObj.getReport(request, reportId, format)

