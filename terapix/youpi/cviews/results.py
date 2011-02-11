
import os.path
import cjson as json
import marshal, base64, zlib
#
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.cache import cache_page
from django.db import IntegrityError
from django.shortcuts import render_to_response
from django.template import RequestContext
#
from terapix.youpi.models import *
from terapix.youpi.cviews import profile 
from terapix.youpi.views import get_entity_permissions
from terapix.lib.common import get_title_from_menu_id
from terapix.youpi.cviews import manager

@login_required
@profile
def home(request):
    """
    Related to results page.
    This is a callback function (as defined in django's urls.py file).
    """
    dirs = []
    active_users = User.objects.filter(is_active = True)
    menu_id = 'results'
    return render_to_response('results.html', { 
        'tags'              : Tag.objects.all().order_by('name'),
        'users'             : active_users,
        'plugins'           : manager.plugins, 
        'selected_entry_id' : menu_id, 
        'title'             : get_title_from_menu_id(menu_id),
    }, 
    context_instance = RequestContext(request))

@login_required
@profile
def delete_processing_task(request):
    """
    Delete a processing task
    """
    try:
        taskId = request.POST['TaskId']
    except KeyError, e:
        raise HttpResponseServerError('Bad parameters')

    success = False
    try:
        task = Processing_task.objects.filter(id = taskId)[0]
        rels = Rel_it.objects.filter(task = task)
        if task.kind.name == 'fitsin':
            data =  Plugin_fitsin.objects.filter(task = task)[0]
            grades = FirstQEval.objects.filter(fitsin = data)
            for g in grades:
                g.delete()
        elif task.kind.name == 'fitsout':
            data =  Plugin_fitsout.objects.filter(task = task)[0]
        elif task.kind.name == 'scamp':
            data =  Plugin_scamp.objects.filter(task = task)[0]
        elif task.kind.name == 'swarp':
            data =  Plugin_swarp.objects.filter(task = task)[0]
        elif task.kind.name == 'skel':
            data = None
        elif task.kind.name == 'sex':
            data =  Plugin_sex.objects.filter(task = task)[0]
        else:
            raise TypeError, 'Unknown data type to delete:' + task.kind.name

        for r in rels: r.delete()
        if data: data.delete()
        task.delete()
        success = True
    except IndexError:
        # Associated data not available (should be)
        for r in rels: r.delete()
        task.delete()
        success = True
    except Exception, e:
        return HttpResponse(str({'Error' : str(e)}), mimetype = 'text/plain')

    resp = {
        'success'   : success,
        'pluginId'  : task.kind.name,
        'results_output_dir' : task.results_output_dir,
    } 
    return HttpResponse(json.encode(resp), mimetype = 'text/plain')

def task_filter(request):
    try:
        # May be a list of owners
        owner = request.POST.getlist('Owner')
        status = request.POST['Status']
        kindid = request.POST['Kind']
        # Max results per page
        maxPerPage = int(request.POST['Limit'])
        # page # to return
        targetPage = int(request.POST['Page'])
        tags = request.POST.getlist('Tag')
    except KeyError, e:
        raise HttpResponseServerError('Bad parameters')

    # First check for permission
    if not request.user.has_perm('youpi.can_view_results'):
        return HttpResponse(json.encode({
            'Error': "Sorry, you don't have permission to view processing results",
        }), mimetype = 'text/plain')

    from lib.processing import find_tasks

    nb_suc = nb_failed = 0
    res = []
    # Check status
    anyStatus = False
    success = failure = True
    if status == 'successful': failure = False
    elif status == 'failed': success = False

    # Check owner
    owner = owner[0]
    if owner == 'my':
        owner = request.user.username
    elif owner == 'all':
        owner = None

    # Get tasks
    tasks = find_tasks(tags, task_id=None, kind=kindid, user=owner, success=success, failure=failure)
    tasksIds = [int(t.id) for t in tasks]
    filtered = False

    plugin = manager.getPluginByName(kindid)

    # Plugins can optionally filter/alter the result set
    try:
        tasksIds = plugin.filterProcessingHistoryTasks(request, tasksIds)
    except AttributeError:
        # Not implemented
        pass

    lenAllTasks = len(tasksIds)

    if len(tasksIds) > maxPerPage:
        pageCount = len(tasksIds)/maxPerPage
        if len(tasksIds) % maxPerPage > 0:
            pageCount += 1
    else:
        pageCount = 1

    # Tasks ids for the page
    tasksIds = tasksIds[(targetPage-1)*maxPerPage:targetPage*maxPerPage]
    tasks = Processing_task.objects.filter(id__in = tasksIds).order_by('-end_date')
    for t in tasks:
        if t.success:
            nb_suc += 1
        else:
            nb_failed += 1

        tdata = {   'Success'       : t.success,
                    'Name'          : str(t.kind.name),
                    'Label'         : str(t.kind.label),
                    'Id'            : str(t.id),
                    'User'          : str(t.user.username),
                    'Start'         : str(t.start_date),
                    'End'           : str(t.end_date),
                    'Duration'      : str(t.end_date-t.start_date),
                    'Node'          : str(t.hostname),
                    'Title'         : str(t.title),
        }
        
        # Looks for plugin extra data, if any
        try:
            extra = plugin.getProcessingHistoryExtraData(t.id)
            if extra:
                tdata['Extra'] = extra
        except AttributeError:
            # No method for extra data
            pass
        res.append(tdata)

    resp = {
        'filtered' : filtered,
        'results' : res, 
        'Stats' : { 
            'nb_success'    : nb_suc, 
            'nb_failed'     : nb_failed, 
            'nb_total'      : nb_suc + nb_failed,
            'pageCount'     : pageCount,
            'curPage'       : targetPage,
            'TasksIds'      : tasksIds,
            'nb_big_total'  : lenAllTasks,
        },
    } 

    # Looks for plugin extra data, if any
    try:
        extraHeader = plugin.getProcessingHistoryExtraHeader(request, tasks)
        if extraHeader: resp['ExtraHeader'] = extraHeader
    except AttributeError:
        # No method for extra header data
        pass
    return HttpResponse(json.encode(resp), mimetype = 'text/plain')

def dir_stats(request):
    """
    From the results page, return statistics about finished processing in result output dir.
    """
    try:
        dir = request.POST['ResultsOutputDir']
    except KeyError, e:
        raise HttpResponseServerError('Bad parameters')

    task = Processing_task.objects.filter(results_output_dir = dir)[0]
    plugin = manager.getPluginByName(task.kind.name)
    stats = plugin.getOutputDirStats(dir)

    return HttpResponse(str({   'PluginId'  : str(plugin.id),
                                'Stats'     : stats }),
                                mimetype = 'text/plain')

@login_required
@profile
@cache_page(60*5)
def get_all_results_output_dir(request):
    outdirs = Processing_task.objects.values_list('results_output_dir', flat=True).distinct().order_by('results_output_dir')
    return HttpResponse(json.encode({'output_dirs': map(str, outdirs)}), mimetype = 'text/plain')

@login_required
@profile
def single_result(request, pluginId, taskId):
    """
    Same content as the page displayed by related plugin.
    """
    plugin = manager.getPluginByName(pluginId)
    if not plugin:
        return HttpResponseNotFound("""<h1><span style="color: red;">Invalid URL. Result not found.</h1></span>""")

    try:
        task = Processing_task.objects.filter(id = int(taskId))[0]
    except IndexError:
        # TODO: set a better page for that
        return HttpResponseNotFound("""<h1><span style="color: red;">Result not found.</h1></span>""")

    menu_id = 'results'
    return render_to_response( 'single_result.html', {  
        'pid'               : pluginId, 
        'tid'               : taskId,
        'selected_entry_id' : menu_id, 
        'plugin'            : plugin,
        'title'             : get_title_from_menu_id(menu_id),
    }, 
    context_instance = RequestContext(request))

@login_required
@profile
def grading_panel(request, pluginId, fitsId):
    """
    Image grading panel.
    """
    plugin = manager.getPluginByName(pluginId)
    path = plugin.getUrlToGradingData(request, fitsId)

    # TODO: handle cases other than qfits-in
    # Looks for existing grade
    f = Plugin_fitsin.objects.filter(id = int(fitsId))[0]
    m = FirstQEval.objects.filter(user = request.user, fitsin = f)
    evals = FirstQEval.objects.filter(fitsin = f).order_by('-date')
    comments = FirstQComment.objects.all()
    prev_releaseinfo =  Plugin_fitsin.objects.filter(id = int(fitsId))

    if m:
        grade = m[0].grade
        userPCommentId = m[0].comment.id
        customComment = m[0].custom_comment
    else:
        grade = None
        userPCommentId = None
        customComment = None
    
    return render_to_response('grading_panel.html', {   
        'www'       : path, 
        'pluginId'  : pluginId,
        'fitsId'    : fitsId,
        'userGrade' : grade,
        'comments'  : comments,
        'userPCommentId' : userPCommentId,
        'customComment' : customComment,
        'evals'     : evals,
        'prev_releaseinfo'  : prev_releaseinfo,
    }, 
    context_instance = RequestContext(request))

@login_required
@profile
def grading_cancel(request, pluginId, fitsId):
    """
    Cancels a grade.
    """
    plugin = manager.getPluginByName(pluginId)

    # TODO: handle cases other than qfits-in
    # Looks for existing grade
    f = Plugin_fitsin.objects.filter(id = int(fitsId))[0]
    m = FirstQEval.objects.filter(user = request.user, fitsin = f)
    evals = FirstQEval.objects.filter(fitsin = f).order_by('-date')
    comments = FirstQComment.objects.all()
    prev_releaseinfo =  Plugin_fitsin.objects.filter(id = int(fitsId))

    if m:
        m.delete()
    
    return render_to_response('grading_panel.html', {   
        'pluginId'  : pluginId,
        'fitsId'    : fitsId,
        'comments'  : comments,
        'evals'     : evals,
        'prev_releaseinfo'  : prev_releaseinfo,
    }, 
    context_instance = RequestContext(request))

@login_required
@profile
def image_grading(request, pluginName, fitsId):
    """
    Image grading template.
    """
    plugin = manager.getPluginByName(pluginName)
    if plugin:
        try:
            path = plugin.getUrlToGradingData(request, fitsId)
        except IndexError:
            return HttpResponseRedirect(settings.AUP + '/results/')
    else:
        return HttpResponseRedirect(settings.AUP + '/results/')
    return render_to_response('grading.html', {'www' : path, 'pluginName' : pluginName, 'fitsId' : fitsId}, context_instance = RequestContext(request))

