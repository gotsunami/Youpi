import cjson as json
import MySQLdb, pyfits
import pprint, re, glob, string
import math, md5, random
import marshal, base64, zlib
import os, os.path, sys, pprint
import socket, time
import xml.dom.minidom as dom
from types import *
from stat import *
#
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect
from django.db.models import get_models
from django.db import IntegrityError
from django.utils.datastructures import *
from django.template import Template, Context, RequestContext
from django.contrib.auth.models import User
from django.views.decorators.cache import cache_page
#
from terapix.youpi.auth import *
from terapix.youpi.cviews import *
from terapix.youpi.models import *
from terapix.youpi.pluginmanager import ApplicationManagerError
from terapix.lib.cluster.condor import get_condor_status, get_requirement_string
from terapix.exceptions import *
#
from terapix.youpi.cviews.ims import _get_pagination_attrs
from terapix.script.preingestion import preingest_table
from terapix.script.DBGeneric import *
import terapix.youpi
from terapix.lib.common import get_title_from_menu_id

@login_required
@profile
def home(request):
	"""
	Condor cluster setup
	"""
	menu_id = 'condorsetup'
	return render_to_response('condorsetup.html', {	
						'custom_condor_req' : request.user.get_profile().custom_condor_req,
						'selected_entry_id'	: menu_id, 
						'title' 			: get_title_from_menu_id(menu_id),
					}, 
					context_instance = RequestContext(request))

@login_required
@cache_page(60*5)
def condor_status(request):
	return HttpResponse(str({'results' : get_condor_status()}), mimetype = 'text/plain')

def get_live_monitoring(request, nextPage = -1):
	"""
	Only Youpi's related job are monitored.
	@param nextPage id of the page of 'limit' results to display. If nextPage == -1
	then full data set is returned.
	"""

	from terapix.lib.cluster.condor import YoupiCondorQueue
	q = YoupiCondorQueue()
	jobs, jobCount = q.getJobs()

	# Max jobs per page
	limit = 10

	res = []
	for job in jobs:
		job.UserData['Owner'] = str(User.objects.filter(id = int(job.UserData['UserID']))[0].username)
		res.append({
			'ClusterId'		: job.ClusterId, 
			'ProcId'		: job.ProcId, 
			'JobStatus'		: job.JobStatus, 
			'RemoteHost'	: job.RemoteHost,
			'JobStartDate'	: job.JobStartDate,
			'JobDuration'	: job.getJobDuration(),
			'UserData'		: job.UserData,
		})

	if nextPage >= 1:
		# Computes total pages
		pageCount = 1
		if jobCount  > limit:
			pageCount = jobCount / limit
			if jobCount % limit > 0:
				pageCount += 1
	
		# Selects res subset according to NextPage and limit
		if nextPage > pageCount:
			nextPage = pageCount

		res = res[(nextPage-1)*limit:limit*nextPage]
		retval = (res, jobCount, pageCount, nextPage)
	else:
		retval = (res, jobCount)

	return retval

@login_required
@profile
def live_monitoring(request):
	try:
		nextPage = request.POST['NextPage']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	# First check for permission
	if not request.user.has_perm('youpi.can_monitor_jobs'):
		return HttpResponse(json.encode({
			'Error': "Sorry, you don't have permission to monitor running jobs on the cluster",
		}), mimetype = 'text/plain')

	res, jobCount, pageCount, nextPage = get_live_monitoring(request, int(nextPage))
	return HttpResponse(json.encode({'results' : res, 'JobCount' : jobCount, 'PageCount' : pageCount, 'nextPage' : nextPage}), mimetype = 'text/plain')

def condor_hosts(request):
	vms = get_condor_status()
	hosts = []
	for vm in vms:
		host = vm[0][vm[0].find('@')+1:]
		if host not in hosts:
			hosts.append(str(host))

	return HttpResponse(str({'Hosts' : hosts}), mimetype = 'text/plain')

def condor_softs(request):
	return HttpResponse(str({'Softs' : [str(soft[0]) for soft in settings.SOFTS]}), mimetype = 'text/plain')

def get_softs_versions(request):
	"""
	Looks for stored softwares version information in DB
	"""

	misc = MiscData.objects.filter(key = 'software_version')
	versions = [] 
	if misc:
		data = marshal.loads(base64.decodestring(misc[0].data))
		for host, info in data.iteritems():
			versions.append([host, info])

	return versions

def clear_softs_versions(request):
	"""
	Delete stored softwares versions stored into DB
	"""
	misc = MiscData.objects.filter(key = 'software_version')
	misc.delete()
	return HttpResponse(str({'Versions' : 'deleted'}), mimetype = 'text/plain')

def softs_versions(request):
	return HttpResponse(str({'Versions' : get_softs_versions(request)}), mimetype = 'text/plain')

def query_condor_node_for_versions(request):
	"""
	Sends a Condor job on a given host to retrieve softwares versions.
	First checks that a pending or running Condor job for this task is not running (to prevent job flooding)
	"""
	try:
		node = request.POST['Node']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	descr = str("Sofware version check on %s" % node)

	# Requirement string
	req = "slot1@%s" % node
	custom_req = request.user.get_profile().custom_condor_req
	if custom_req: req = "\"%s\" && (%s)" % (req, custom_req)

	# Check if information is stored
	misc = MiscData.objects.filter(key = 'software_version')
	if misc:
		data = marshal.loads(base64.decodestring(misc[0].data))
		for host, info in data.iteritems():
			if host == node:
				return HttpResponse(str({'Versions' : get_softs_versions(request)}), mimetype = 'text/plain')

	# Find what's running
	res, count =  get_live_monitoring(request)

	for job in res:
		if job['UserData']['Descr'] == descr:
			# NOP
			return HttpResponse(str({'Versions' : 0}), mimetype = 'text/plain')


	# Content of YOUPI_USER_DATA env variable passed to Condor
	userData = {'Descr' 		: descr,
				'Node' 			: str(node),
				'UserID' 		: str(request.user.id)}

 	# Generates CSF
	submit_file_path = os.path.join(settings.TRUNK, 'terapix')
	condor_submit_file = """
#
# Condor submission file
# Please not that this file has been generated automatically by Youpi
#
executable              = %s/soft_version_check.py
universe                = vanilla
transfer_executable     = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_input_files    = %s/local_conf.py, %s/settings.py, %s/DBGeneric.py, %s/NOP
initialdir				= %s
transfer_output_files   = NOP
# YOUPI_USER_DATA = %s
environment             = PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin:/opt/condor/bin; YOUPI_USER_DATA=%s
arguments               = "%s"
log                     = /tmp/VCHECK.log.$(Cluster).$(Process)
error                   = /tmp/VCHECK.err.$(Cluster).$(Process)
output                  = /tmp/VCHECK.out.$(Cluster).$(Process)
notification            = Error
notify_user             = monnerville@iap.fr
requirements            = Name == %s
queue
""" % (	os.path.join(submit_file_path, 'script'),
		submit_file_path, 
		submit_file_path, 
		os.path.join(submit_file_path, 'script'),
		submit_file_path, 
		os.path.join(submit_file_path, 'script'),
		userData, 
		base64.encodestring(marshal.dumps(userData)).replace('\n', ''), 
		base64.encodestring(marshal.dumps(userData)).replace('\n', ''), 
		req )

	csf = "/tmp/csf_version_check-%s-%s.txt" % (node, time.time())
	f = open(csf, 'w')
	f.write(condor_submit_file);
	f.close();

	job = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_submit %s 2>&1" % csf))
	job.close()

	return HttpResponse(str({'Versions' : []}), mimetype = 'text/plain')

def job_cancel(request):
	"""
	Cancel one Job or more job. POST arg used are clusterId and procId.
	"""

	post = request.POST
	rmJobs = []

	what = post.get('What', None)
	if what == 'allmine':
		res, count = get_live_monitoring(request)
		for job in res:
			if int(job['UserData']['UserID']) == int(request.user.id):
				rmJobs.append("%s.%s" % (job['ClusterId'], job['ProcId']))

	elif what == 'all':
		res, count = get_live_monitoring(request)
		rmJobs = ["%s.%s" % (job['ClusterId'], job['ProcId']) for job in res]

	elif what is None:
		cluster = str(post['ClusterId'])
		proc = str(post['ProcId'])
		rmJobs = ["%s.%s" % (cluster, proc)]
	
	pipe = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_rm %s" % string.join(rmJobs, ' ')))
	data = pipe.readlines()
	pipe.close()

	return HttpResponse(str({'CancelCount' : len(rmJobs)}), mimetype = 'text/plain')

def condor_ingestion(request):
	"""
	Callback for running a Condor ingestion.
	"""

	# HOST_DOMAIN
	try:
		path = request.POST['Path']
		ingestionId = request.POST['IngestionId']
		email = request.POST.get('ReportEmail', settings.CONDOR_NOTIFY_USER)
		checkAllowSeveralTimes = request.POST.get('CheckAllowSeveralTimes', 'no')
		checkSkipVerify = request.POST.get('CheckSkipVerify', 'no')
		selectValidationStatus = request.POST.get('SelectValidationStatus', 'no')
		ittname = request.POST['Itt']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	# First check for permission
	if not request.user.has_perm('youpi.can_submit_jobs'):
		return HttpResponse(json.encode({
			'Error': "Sorry, you don't have permission to submit jobs on the cluster",
		}), mimetype = 'text/plain')

	# Find machine
	clean_path = re.sub(settings.FILE_BROWSER_ROOT_DATA_PATH, '', path)
	m = re.search(settings.INGESTION_HOST_PATTERN, clean_path)
	machine = settings.INGESTION_DEFAULT_HOST
	if m: 
		try:
			host = m.group(1)
			# Now searches among user-defined mappings
			for pattern, value in settings.INGESTION_HOSTS_MAPPING.iteritems():
				if re.match(pattern, host):
					machine = value.replace('\1', host)
					break
		except IndexError:
			machine = settings.INGESTION_DEFAULT_HOST

	#
	# Dictionnary that will be serialized with marshal module and passed
	# to the script as a string (argument 1). Note that the result of the serialization 
	# is base64 encoded to avoid bad caracter handling. The condor ingestion script 
	# will then de-serialize its first argument to access the data
	#
	script_args = { 'path'						: path,
					'email' 					: email,
					'user_id' 					: request.user.id,
					'ingestion_id' 				: ingestionId,
					'allow_several_ingestions' 	: checkAllowSeveralTimes,
					'skip_fitsverify' 			: checkSkipVerify,
					'select_validation_status' 	: selectValidationStatus,
					'host' 						: machine,
					'ittname'					: ittname,
	}

	# Content of YOUPI_USER_DATA env variable passed to Condor
	userData = { 'Descr' 		: str("Ingestion (%s) of FITS images " % ingestionId),
				'UserID' 		: str(request.user.id)}

	submit_file_path = os.path.join(settings.TRUNK, 'terapix')
	node = "Machine == \"%s\"" % machine

	# Add any custom Condor requirements, if any
	custom_req = request.user.get_profile().custom_condor_req

	# if custom_rep exists machine is composed by node and custom condor requirements from the condor setup panel
	if custom_req:
		machine = "((%s) && (%s))" % (node, custom_req)
	else:
		# if not machine only compose the requirements
		machine = node

	f = open(settings.CONDORFILE + '_' + ingestionId, 'w')
	f.write("""
executable = %(script)s/ingestion.py
universe                = vanilla
transfer_executable     = True
requirements            = %(req)s

# Arguments (base64 encoded + python serialization with marshal)
# Args equal to: %(clear_args)s
arguments               = "%(args)s"

should_transfer_files   = YES
when_to_transfer_output = ON_EXIT_OR_EVICT
transfer_input_files    = %(project_root)s/local_conf.py, %(project_root)s/settings.py, %(project_root)s/private_conf.py, %(script)s/DBGeneric.py, %(project_root)s/NOP
initialdir				= %(script)s
transfer_output_files   = NOP
# Logs
# YOUPI_USER_DATA = %(clear_userdata)s
environment             = PATH=/usr/local/bin:/usr/bin:/bin:/opt/bin:/opt/condor/bin; YOUPI_USER_DATA=%(userdata)s
output                  = %(log_output)s
error                   = %(log_error)s
log                     = %(log_log)s
queue
""" % {	
	'script'		: os.path.join(submit_file_path, 'script'), 
	'req'			: machine, 
	'clear_args'	: str(script_args),
	'args'			: base64.encodestring(marshal.dumps(script_args)).replace('\n', NULLSTRING),
	'project_root'	: submit_file_path,
	'clear_userdata': userData,
	'userdata'		: base64.encodestring(marshal.dumps(userData)).replace('\n', ''), 
	'log_output'	: settings.CONDOR_OUTPUT + '_' + ingestionId,
	'log_error'		: settings.CONDOR_ERROR + '_' + ingestionId,
	'log_log'		: settings.CONDOR_LOG + '_' + ingestionId,
})

	f.close()

	job = os.popen(os.path.join(settings.CONDOR_BIN_PATH, "condor_submit %s 2>&1" % (settings.CONDORFILE + '_' + ingestionId)))
	resp = job.readlines()
	job.close()

	try:
		error = ''
		jobid = re.findall('(\d+)', resp[2])[1]
	except Exception, e:
		error = resp
		jobid = 'null'

	return HttpResponse(json.encode({
		'Path' 			: path, 
		'IngestionId' 	: ingestionId, 
		'Host' 			: node,
		'JobId' 		: jobid,
		'Error'			: error,
	}), mimetype = 'text/plain')

@login_required
@profile
def get_condor_requirement_string(request):
	"""
	Get requirement string from saved policy
	"""
	try:
		name = request.POST['Name']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	error = req = '' 
	try:
		policy = CondorNodeSel.objects.filter(label = name, is_policy = True)[0]
		vms = get_condor_status()
		req = get_requirement_string(policy.nodeselection, vms)
	except Exception, e:
		error = e

	return HttpResponse(str({	'ReqStr': str(req), 
								'Error'	: str(error)
							}), mimetype = 'text/plain')


@login_required
@profile
def compute_requirement_string(request):
	"""
	Compute Condor's requirement string
	"""
	try:
		params = request.POST['Params']
	except KeyError, e:
		raise HttpResponseServerError('Bad parameters')

	vms = get_condor_status()
	req = get_requirement_string(str(params), vms)
	return HttpResponse(str({'ReqString': str(req)}), mimetype = 'text/plain')

def del_condor_node_selection(request):
	"""
	Delete Condor node selection. 
	No deletion is allowed if at least one policy is using that selection.
	No deletion is allowed if at least Condor Default Setup rules is using that selection.
	"""

	try:
		label = request.POST['Label']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	# First check for permission
	if not request.user.has_perm('youpi.delete_condornodesel'):
		return HttpResponse(str({
			'Error': "Sorry, you don't have permission to delete custom selections",
		}), mimetype = 'text/plain')

	profiles = SiteProfile.objects.all()
	for p in profiles:
		try:
			data = marshal.loads(base64.decodestring(str(p.dflt_condor_setup)))
		except EOFError:
			# No data found, unable to decodestring
			data = None

		if data:
			for plugin in data.keys():
				if data[plugin]['DS'] == label:
					return HttpResponse(str({'Error' : str("Cannot delete selection '%s'. User '%s' references it in his/her default selection preferences menu." 
								% (label, p.user.username))}), mimetype = 'text/plain')

	pols = CondorNodeSel.objects.filter(is_policy = True)
	if pols:
		for pol in pols:
			if pol.nodeselection.find(label) >= 0:
				return HttpResponse(str({'Error' : str("Some policies depends on this selection. Unable to delete selection '%s'." % label)}), 
					mimetype = 'text/plain')

	sel = CondorNodeSel.objects.filter(label = label, is_policy = False)[0]
	sel.delete()

	return HttpResponse(str({'Deleted' : str(label)}), mimetype = 'text/plain')

def del_condor_policy(request):
	"""
	Delete Condor policy
	"""

	try:
		label = request.POST['Label']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	# First check for permission
	if not request.user.has_perm('youpi.delete_condornodesel'):
		return HttpResponse(str({
			'Error': "Sorry, you don't have permission to delete custom policies",
		}), mimetype = 'text/plain')

	profiles = SiteProfile.objects.all()
	for p in profiles:
		try:
			data = marshal.loads(base64.decodestring(str(p.dflt_condor_setup)))
		except EOFError:
			# No data found, unable to decodestring
			data = None

		if data:
			for plugin in data.keys():
				if data[plugin]['DP'].find(label) >= 0:
					return HttpResponse(str({'Error' : str("Cannot delete policy '%s'. User '%s' references it in his/her default selection preferences menu." 
								% (label, p.user.username))}), mimetype = 'text/plain')

	sel = CondorNodeSel.objects.filter(label = label, is_policy = True)[0]
	sel.delete()

	return HttpResponse(str({'Deleted' : str(label)}), mimetype = 'text/plain')

def get_condor_node_selections(request):
	"""
	Returns Condor nodes selections.
	"""
	sels = CondorNodeSel.objects.filter(is_policy = False).order_by('label')
	return HttpResponse(str({'Selections' : [str(sel.label) for sel in sels]}), mimetype = 'text/plain')

def get_condor_selection_members(request):
	"""
	Returns Condor selection members.
	"""
	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	data = CondorNodeSel.objects.filter(label = name, is_policy = False)
	error = ''

	if data:
		members = marshal.loads(base64.decodestring(str(data[0].nodeselection)))
		members = [str(s) for s in members]
	else:
		members = '';
		error = 'No selection of that name.'

	return HttpResponse(str({'Members' : members, 'Error' : error}), mimetype = 'text/plain')

def get_condor_policies(request):
	"""
	Returns Condor policies.
	"""
	sels = CondorNodeSel.objects.filter(is_policy = True).order_by('label')
	return HttpResponse(str({'Policies' : [str(sel.label) for sel in sels]}), mimetype = 'text/plain')

def get_policy_data(request):
	"""
	Returns policy serialized data
	"""
	try:
		name = request.POST['Name']
	except Exception, e:
		return HttpResponseBadRequest('Incorrect POST data')

	data = CondorNodeSel.objects.filter(label = name, is_policy = True)
	error = serial = ''

	if data:
		serial = str(data[0].nodeselection)
	else:
		error = 'No policy of that name.'
	return HttpResponse(str({'Serial' : serial, 'Error' : error}), mimetype = 'text/plain')

def save_condor_custom_reqstr(request):
	"""
	Save Condor custom requirement string
	"""
	try:
		reqstr = request.POST['Req']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	if not request.user.has_perm('youpi.can_change_custom_condor_req'):
		return HttpResponseForbidden("Sorry, you don't have permission save custom Condor requirements")

	try:
		p = request.user.get_profile()
		p.custom_condor_req = reqstr
		p.save()
	except Exception, e:
		return HttpResponse(str({'Error' : "%s" % e}), mimetype = 'text/plain')
	return HttpResponse(str({'Status' : str('saved')}), mimetype = 'text/plain')

def save_condor_node_selection(request):
	"""
	Save Condor nodes selection
	"""
	try:
		selHosts = request.POST['SelectedHosts'].split(',')
		label = request.POST['Label']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	# First check for permission
	if not request.user.has_perm('youpi.add_condornodesel'):
		return HttpResponse(str({
			'Error': "Sorry, you don't have permission to add custom selections",
		}), mimetype = 'text/plain')

	sels = CondorNodeSel.objects.filter(label = label, is_policy = False)
	if sels:
		return HttpResponse(str({'Error' : str("'%s' label is already used, please use another name." % label)}), 
					mimetype = 'text/plain')

	nodesel = base64.encodestring(marshal.dumps(selHosts)).replace('\n', '')
	sel = CondorNodeSel(user = request.user, label = label, nodeselection = nodesel)
	sel.save()

	return HttpResponse(str({'Label' : str(label), 'SavedCount' : len(selHosts)}), mimetype = 'text/plain')

def save_condor_policy(request):
	"""
	Save Condor custom policy
	"""
	try:
		label = request.POST['Label']
		serial = request.POST['Serial']
	except Exception, e:
		return HttpResponseServerError('Incorrect POST data.')

	# First check for permission
	if not request.user.has_perm('youpi.add_condornodesel'):
		return HttpResponse(str({
			'Error': "Sorry, you don't have permission to add custom policies",
		}), mimetype = 'text/plain')

	try:
		sels = CondorNodeSel.objects.filter(label = label, is_policy = True)
		if sels:
			if sels[0].user != request.user:
				# Only owner can update its policy
				return HttpResponse(str({'Error' : 'Only selection owner can update its policies. Policy not overwritten.'}), mimetype = 'text/plain')
			else:
				sel = sels[0]
				sel.nodeselection = serial
		else:
			sel = CondorNodeSel(user = request.user, label = label, nodeselection = serial, is_policy = True)

		sel.save()
		
	except Exception, e:
		return HttpResponse(str({'Error' : "%s" % e}), mimetype = 'text/plain')
	return HttpResponse(str({'Label' : str(label), 'Policy' : str(serial)}), mimetype = 'text/plain')

@login_required
@profile
def get_condor_log_files_links(request):
	"""
	Returns a dictionnary with entries for the log, error and output filenames 
	that should be used by plugins generating Condor submission files.
	@return Dictionnary with paths to Condor log files
	"""
	post = request.POST
	try:
		taskId = post['TaskId']
	except Exception, e:
		raise PluginError, "POST argument error. Unable to process data."

	task = Processing_task.objects.filter(id = taskId)[0]

	import terapix.lib.cluster.condor as condor
	csf = condor.YoupiCondorCSF(request, task.kind.name)
	logs = csf.getLogFilenames(user=task.user, date=task.start_date.date())
	for k,v in logs.iteritems():
		logs[k] = v + '.' + task.clusterId

	sizes = {'log': 0, 'error': 0, 'out': 0}

	for kind, path in logs.iteritems():
		try:
			sizes[kind] = int(os.path.getsize(path))
			logs[kind] = str("""<a href="%s" target="_blank">%s</a>""" % (reverse('terapix.youpi.views.show_condor_log_file', args=[kind, taskId]), logs[kind][logs[kind].rfind('/')+1:]))
		except OSError:
			logs[kind] = ''

	return HttpResponse(str({'logs': logs, 'sizes': sizes}), mimetype = 'text/plain')

@login_required
@profile
def show_condor_log_file(request, kind, taskId):
	"""
	Display Condor log file for a given kind and taskId
	@param kind one of 'log', 'error', 'out'
	@param taskId task Id
	"""
	if kind not in ('log', 'error', 'out'):
		return HttpResponseBadRequest('Bad request')

	try:
		task = Processing_task.objects.filter(id = taskId)[0]
	except:
		return HttpResponseBadRequest('Bad request')

	import terapix.lib.cluster.condor as condor
	csf = condor.YoupiCondorCSF(request, task.kind.name)
	logs = csf.getLogFilenames(user=task.user, date=task.start_date.date())
	for k,v in logs.iteritems():
		logs[k] = v + '.' + task.clusterId

	try:
		f = open(logs[kind], 'r')
		data = string.join(f.readlines(), '')
		if not data:
			data = 'Empty file.'
		f.close()
	except IOError:
		data = 'Log file not found on server (has it been deleted?)'
	return HttpResponse(str(data), mimetype = 'text/plain')

@login_required
@profile
def monitoring(request):
	"""
	Related to monitoring.
	This is a callback function (as defined in django's urls.py file).
	"""
	menu_id = 'monitoring'
	return render_to_response('monitoring.html', {	
        'selected_entry_id'	: menu_id,
        'title' 			: get_title_from_menu_id(menu_id),
    }, 
    context_instance = RequestContext(request))

@login_required
@profile
def soft_version_monitoring(request):
	menu_id = 'monitoring'
	return render_to_response( 'softs_versions.html', {	
        'report' 			: len(settings.SOFTS), 
        'selected_entry_id'	: menu_id, 
        'title' 			: get_title_from_menu_id(menu_id),
    },
    context_instance = RequestContext(request))

@login_required
@profile
def history_cluster_jobs(request):
	"""
	Returns cluster jobs information for a given page
	"""
	page = request.POST.get('Page', 1)
	try: page = int(page)
	except ValueError, e:
		page = 1

	# First check for permission
#	if not request.user.has_perm('youpi.can_view_ing_logs'):
#		return HttpResponse(str({
#			'Error': "Sorry, you don't have permission to view ingestion logs",
#		}), mimetype = 'text/plain')

	tasks = Processing_task.objects.all().order_by('-start_date')
	currentPage, nbPages, window = _get_pagination_attrs(page, tasks, tasks.count())

	header = ['Job Label', 'Username', 'Kind', 'Start Date', 'Duration', 'Success', 'Hostname', 'Cluster Id',]
	data = []
	for t in window:
		data.append([
			str("<a target=\"_blank\" href=\"%s\">%s</a>" % (reverse('terapix.youpi.views.single_result', args = [t.kind.name, t.id]), t.title)),
			str(t.user.username), 
			str("<b>%s</b>" % t.kind.name.capitalize()), 
			str(t.start_date), 
			str(t.end_date - t.start_date), 
			t.success, 
			str(t.hostname), 
			str(t.clusterId), 
		])
	for k in range(len(data)):
		if data[k][5]:
			cls = 'success'
		else:
			cls = 'failure'
		data[k] = ["<label class=\"%s\">%s</label>" % (cls, r) for r in data[k]]
	data.insert(0, header)
	return HttpResponse(json.encode({'Headers': [], 'Content': data, 'CurrentPage': currentPage, 'TotalPages': nbPages}), mimetype = 'text/plain')

