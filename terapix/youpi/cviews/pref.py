
import os.path, glob
import cjson as json
import marshal, base64, zlib
#
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Permission 
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.cache import cache_page
from django.db import IntegrityError
from django.shortcuts import render_to_response
from django.template import RequestContext
#
from terapix.youpi.models import *
from terapix.youpi.cviews import profile 
from terapix.youpi.views import get_entity_permissions
from terapix.youpi.cviews import manager
from terapix.lib.common import get_title_from_menu_id

@login_required
@profile
def home(request):
	"""
	Preferences template
	"""
	import ConfigParser
	config = ConfigParser.RawConfigParser()

	# Looks for themes
	theme_dirs = glob.glob(os.path.join(settings.MEDIA_ROOT, 'themes', '*'))
	themes = []

	for dir in theme_dirs:
		try:
			config.read(os.path.join(dir, 'META'))
		except:
			# No META data, theme not conform
			pass

		if not os.path.isfile(os.path.join(dir, 'screenshot.png')):
			# No screenshot available, theme not conform
			continue

		themes.append({	'name' 			: config.get('Theme', 'Name'),
						'author' 		: config.get('Theme', 'Author'),
						'author_uri'	: config.get('Theme', 'Author URI'),
						'description' 	: config.get('Theme', 'Description'),
						'version' 		: config.get('Theme', 'Version'),
						'short_name'	: os.path.basename(dir),
						})

	for k in range(len(themes)):
		if themes[k]['short_name'] == request.user.get_profile().guistyle:
			break

	policies = CondorNodeSel.objects.filter(is_policy = True).order_by('label')
	selections = CondorNodeSel.objects.filter(is_policy = False).order_by('label')
	try:
		p = request.user.get_profile()
		config = marshal.loads(base64.decodestring(str(p.dflt_condor_setup)))
	except EOFError:
		config = None

	# Global permissions (non data related)
	user = request.user
	glob_perms = [
		['Can submit jobs on the cluster', 			'youpi.can_submit_jobs'],
		['Can view ingestion logs', 				'youpi.can_view_ing_logs'],
		['Can add tags', 							'youpi.add_tag'],
		['Can monitor running jobs on the cluster', 'youpi.can_monitor_jobs'],
		['Can view processing results', 			'youpi.can_view_results'],
		['Can grade qualityFITSed images', 			'youpi.can_grade'],
		['Can generate reports', 					'youpi.can_use_reporting'],
		['Can run a software version check', 		'youpi.can_run_softvc'],
		['Can add custom policy or selection', 		'youpi.add_condornodesel'],
		['Can delete custom policy or selection', 	'youpi.delete_condornodesel'],
		['Can change custom Condor requirements', 	'youpi.can_change_custom_condor_req'],
	]
	# Adds can_use_plugin_* permissions, generated on-the-fly by the checksetup script
	perms = Permission.objects.filter(codename__startswith = 'can_use_plugin_')
	for pperm in perms:
		glob_perms.append([pperm.name, 'youpi.' + pperm.codename])

	menu_id = 'preferences'
	return render_to_response('preferences.html', {	
						'themes'			: themes,
						'plugins' 			: manager.plugins, 
						'current_theme'		: themes[k],
						'policies'			: policies,
						'selections'		: selections,
						'config'			: config,
						'selected_entry_id'	: menu_id, 
						'title' 			: get_title_from_menu_id(menu_id),
						'global_perms'		: [{'label': p[0], 'perm': user.has_perm(p[1])} for p in glob_perms],
					}, 
					context_instance = RequestContext(request))

@login_required
@profile
def set_current_theme(request):
	"""
	Set default user theme
	"""
	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	p = request.user.get_profile()
	p.guistyle = name
	p.save()
	return HttpResponse(str({'Default': str(name)}), mimetype = 'text/plain')

@login_required
@profile
def pref_load_condor_config(request):
	"""
	Load per-user default condor setup. Can be empty if user never saved its Condor default 
	config.
	"""
	try:
		p = request.user.get_profile()
		data = marshal.loads(base64.decodestring(str(p.dflt_condor_setup)))
	except EOFError:
		# No data found, unable to decodestring
		config = None
	return HttpResponse(str({'config': str(data)}), mimetype = 'text/plain')

@login_required
@profile
def pref_save_condor_config(request):
	"""
	Save per-user default condor setup
	"""
	kinds = ('DB', 'DP', 'DS')
	try:
		defaults = [request.POST[p].split(',') for p in kinds]
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	condor_setup = {}
	k = 0
	for plugin in manager.plugins:
		condor_setup[plugin.id] = {}
		j = 0
		for kind in kinds:
			try:
				if len(defaults[j][k]):
					condor_setup[plugin.id][kind] = str(defaults[j][k])
				else:
					condor_setup[plugin.id][kind] = ''
			except IndexError:
				condor_setup[plugin.id][kind] = ''
			j += 1
		k += 1

	try:
		p = request.user.get_profile()
		p.dflt_condor_setup = base64.encodestring(marshal.dumps(condor_setup)).replace('\n', '')
		p.save()
	except Exception, e:
		return HttpResponse(str({'Error': str(e)}), mimetype = 'text/plain')
	return HttpResponse(str({'Setup': str(condor_setup)}), mimetype = 'text/plain')

