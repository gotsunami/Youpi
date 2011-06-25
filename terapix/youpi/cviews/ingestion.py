
import os.path, glob, re
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

@login_required
@profile
def home(request):
    """
    Related to ingestion step.
    This is a callback function (as defined in django's urls.py file).
    """

    insts = Instrument.objects.exclude(itt = None)
    q = Image.objects.all().count()
    menu_id = 'ing'
    return render_to_response('ingestion.html', {   
        'ingested'          : q, 
        'selected_entry_id' : menu_id, 
        'title'             : get_title_from_menu_id(menu_id),
        # Available ITTs (Instrument Translation Tables)
        'itranstables'      : [inst.name for inst in insts],
    }, 
    context_instance = RequestContext(request))

@login_required
@profile
def delete_ingestion(request, ing_id):
    """
    Delete ingestion (regarding permissions)
    """
    # FIXME: make a post query, not passing ing_id as parameter!
    try:
        ing = Ingestion.objects.get(id = ing_id)
    except:
        return HttpResponse(json.encode({'error': "This ingestion has not been found"}), mimetype = 'text/plain')

    perms = get_entity_permissions(request, target = 'ingestion', key = int(ing.id))
    if not perms['currentUser']['write']:
        return HttpResponse(json.encode({'error': "You don't have permission to delete this ingestion"}), mimetype = 'text/plain')

    imgs = Image.objects.filter(ingestion = ing)
    rels = Rel_it.objects.filter(image__in = imgs)
    if rels:
        # Processed images, do not delete this ingestion
        return HttpResponse(json.encode({'error': "Some of those ingested images have been processed.<br/>This ingestion can't be deleted."}), mimetype = 'text/plain')
    else:
        # Images have never been processed, the ingestion can safely be deleted
        ing.delete()    
    return HttpResponse(json.encode({'success': True}), mimetype = 'text/plain')

@login_required
@profile
@cache_page(60*15)
def ingestion_img_count(request):
    """
    Returns number of ingested images
    """
    try:
        releaseId = request.POST.get('ReleaseId', None)
    except KeyError, e:
        raise HttpResponseServerError('Bad parameters')

    if releaseId:
        q = Rel_imgrel.objects.filter(release__id = int(releaseId)).count()
    else:
        q = Image.objects.all().count()

    return HttpResponse(str({'Total' : int(q)}), mimetype = 'text/plain')

@login_required
@profile
def get_itt_content(request):
    """
    Returns content of ingestion translation table
    """
    try:
        name = request.POST['Instrument']
    except Exception, e:
        return HttpResponseForbidden()

    inst = Instrument.objects.filter(name = name)
    if not inst:
        return HttpResponseForbidden()

    return HttpResponse(json.encode({'instrument': name, 'content': marshal.loads(zlib.decompress(base64.decodestring(inst[0].itt)))}))

@login_required
@profile
def show_raw_itt_content(request, instname):
    """
    Display raw ITT content
    @param instname Instrument name
    """
    inst = Instrument.objects.filter(name = instname)
    if not inst: return HttpResponseForbidden("No result")

    itt = os.path.join(settings.TRUNK, 'terapix', 'lib', 'itt', 'conf', inst[0].name.lower() + '.conf')
    f = open(itt, 'r')
    content = f.readlines()
    f.close()

    return HttpResponse(''.join(content), mimetype = 'text/plain')

@login_required
@profile
def rename_ingestion(request, ing_id):
    """
    Rename ingestion (regarding permissions)
    """
    # FIXME: make a post query, not passing ing_id as parameter!
    name = request.POST.get('value', None)
    if not name:
        # Fails silently
        return HttpResponse(str(ing.name), mimetype = 'text/plain')
    try:
        ing = Ingestion.objects.get(id = ing_id)
    except:
        return HttpResponse(json.encode({'error': "This ingestion has not been found"}), mimetype = 'text/plain')

    perms = get_entity_permissions(request, target = 'ingestion', key = int(ing.id))
    if not perms['currentUser']['write']:
        return HttpResponse(json.encode({'error': "You don't have permission to delete this ingestion"}), mimetype = 'text/plain')

    orig = ing.label
    try:
        ing.label = name
        ing.save()
    except IntegrityError:
        # Name not available
        return HttpResponse(json.encode({'old': orig, 'error': "An ingestion named <b>%s</b> already exists.<br/>Cannot rename ingestion." % name}), mimetype = 'text/plain')

    return HttpResponse(str(name), mimetype = 'text/plain')

def open_populate(request, behaviour, tv_name, path):
    """
    DEPRECATED: open_populate_generic instead.

    This function returns a list of JSON objects to generate a dynamic Ajax treeview.
    The argument path is a path to directory structure (see views.py for further details). it 
    is equal to the value of 'openlink' in a JSON branch definition.

    This function is specific to tafelTreeview.
    """

    #
    # The POST request will always contain a branch_id variable when the present function 
    # is called dynamically by the tree issuing the Ajax query
    #
    try:
        nodeId = request.POST['branch_id']
    except:
        # May be usefull for debugging purpose
        return HttpResponse("Path debug: %s, %s, %s" % (path, behaviour, tv_name))

    json = []
    fitsSearchPattern = '*.fits'
    regFitsSearchPattern = '^.*\.fits$'

    if behaviour == 'binary_tables':
        # Patterns change
        fitsSearchPattern = 'mcmd.*.fits'
        regFitsSearchPattern = '^mcmd\..*\.fits$'

    # Look for data
    data = glob.glob("/%s/*" % str(path))

    dirs = []
    for e in data:
        if os.path.isdir(e):
            dirs.append(e)
        elif os.path.isfile(e):
            if re.match(regFitsSearchPattern, e):
                # This is a fits file
                json.append( {
                    'id'  : os.path.basename(e),
                    'txt' : os.path.basename(e),
                    'img' : 'forward.png'
                })


    for d in dirs:
        # Check if this directory contains any FITS file
        fitsFiles = glob.glob("%s/%s" % (d, fitsSearchPattern))

        label = os.path.split(d)[1]
        id = "%s_%s" % (str(path), label)
        id = id.replace('/', '_')
        if len(fitsFiles):
            nodeText = """%s <font class="image_count">(%d)</font>""" % (label, len(fitsFiles))
        else:
            nodeText = label

        json.append( {
            'id' : id,
            'txt' : nodeText,
            'canhavechildren' : 1,
            'onopenpopulate' : str(tv_name) + '.branchPopulate',
            'syspath' : "/%s/%s/" % (str(path), label),
            'openlink' : settings.AUP + "/populate/%s/%s/%s/%s/" % (str(behaviour), str(tv_name), str(path), label),
            'num_fits_children' : len(fitsFiles)
        })
    return HttpResponse(str(json), mimetype = 'text/plain')

def open_populate_generic(request, patterns, fb_name, path):
    """
    This function returns a list of JSON objects to generate a dynamic Ajax treeview.
    The argument path is a path to directory structure (see views.py for further details). it 
    is equal to the value of 'openlink' in a JSON branch definition.

    This function is specific to tafelTreeview.

    patterns: file search patterns (comma-separated list)
    fb_name: FileBrowser global variable name
    path: path to data
    """
    if path[0] == '/':
        path = path[1:]
    #
    # The POST request will always contain a branch_id variable when the present function 
    # is called dynamically by the tree issuing the Ajax query
    #
    try:
        nodeId = request.POST['branch_id']
    except:
        # May be usefull for debugging purpose
        return HttpResponse("Path debug: %s, %s, %s" % (path, patternList, fb_name))

    json = []

    patternList = patterns.split(',')
    regSearchPatternList = []
    for pat in patternList:
        regSearchPatternList.append(pat.replace('.', '\.').replace('*', '.*'))

    # Look for data
    data = glob.glob("/%s/*" % str(path))

    dirs = []
    for e in data:
        if os.path.isdir(e):
            dirs.append(e)
        elif os.path.isfile(e):
            for rsp in regSearchPatternList:
                if re.match(rsp, e):
                    # This is a file
                    json.append( {
                        'id'  : os.path.basename(e),
                        'txt' : os.path.basename(e),
                        'img' : 'forward.png'
                    })
                    break

    for d in dirs:
        # Check if this directory contains any file matching searchPattern
        files = []
        for pat in patternList:
            files.extend(glob.glob("%s/%s" % (d, pat)))

        label = os.path.split(d)[1]
        id = "%s_%s" % (str(path), label)
        id = id.replace('/', '_')
        if len(files):
            nodeText = """%s <font class="image_count">(%d)</font>""" % (label, len(files))
        else:
            nodeText = label

        json.append( {
            'id' : id,
            'txt' : nodeText,
            'canhavechildren' : 1,
            'onopenpopulate' : str(fb_name) + '.getResultHandler()',
            'syspath' : "/%s/%s/" % (str(path), label),
            'openlink' : settings.AUP + "/populate_generic/%s/%s/%s/%s/" % (str(patterns), str(fb_name), str(path), label),
            'num_children' : len(files)
        })
    return HttpResponse(str(json), mimetype = 'text/plain')

@login_required
@profile
def history_ingestion(request):
    """
    Return a JSON object with data related to ingestions' history
    """
    try:
        limit = request.POST['limit']
    except Exception, e:
        return HttpResponseForbidden()

    try:
        limit = int(limit)
    except ValueError, e:
        # Unlimitted
        limit = 0

    # First check for permission
    if not request.user.has_perm('youpi.can_view_ing_logs'):
        return HttpResponse(str({
            'Error': "Sorry, you don't have permission to view ingestion logs",
        }), mimetype = 'text/plain')

    if limit > 0:
        rset = Ingestion.objects.all().order_by('-start_ingestion_date')[:limit]
    else:
        rset = Ingestion.objects.all().order_by('-start_ingestion_date')

    res, filtered = read_proxy(request, rset)

    #
    # We build a standard header that can be used for table's header.
    # header var must be a list not a tuple since it get passed 'as is' to the json 
    # dictionary
    #
    header = ['start', 'duration', 'ID', 'user', 'fitsverified', 'validated', 'multiple', 'exit', 'log']

    data = []
    for ing in res:
        # Current user permissions
        isOwner = ing.user == request.user
        groups = [g.name for g in request.user.groups.all()]
        cuser_write = False
        perms = Permissions(ing.mode)

        if (isOwner and perms.user.write) or \
            (ing.group.name in groups and perms.group.write) or \
            perms.others.write:
            cuser_write = True

        #
        # Unicode strings have to be converted to basic strings with str()
        # in order to get a valid JSON object.
        # Each header[j] is a list of (display value, type[, value2]).
        # type allows client-side code to known how to display the value.
        #
        data.append({   
            header[0]: [str(pretty.date(ing.start_ingestion_date)) + ' (' + str(ing.start_ingestion_date) + ')', 'str'],
            header[1]: [str(ing.end_ingestion_date-ing.start_ingestion_date), 'str'],
            header[2]: [str(ing.label), 'str'],
            header[3]: [str(ing.user.username), 'str'],
            header[4]: [ing.check_fitsverify, 'check'],
            header[5]: [ing.is_validated, 'check'],
            header[6]: [ing.check_multiple_ingestion, 'check'],
            header[7]: [ing.exit_code, 'exit'],
            header[8]: ['View log', 'link', str(settings.AUP + "/history/ingestion/report/%d/" % ing.id)],
            # Give user permissions for this ingestion
            'perms': json.encode(get_entity_permissions(request, target = 'ingestion', key = int(ing.id))),
            'id': int(ing.id),
            'imgcount': int(Image.objects.filter(ingestion = ing).count()),
        })

    # Be aware that JS code WILL search for data and header keys
    out = {'data': data, 'header': header}

    # Return a JSON object
    return HttpResponse(str(out), mimetype = 'text/plain')

@login_required
@profile
def show_ingestion_report(request, ingestionId):
    try: ing = Ingestion.objects.filter(id = ingestionId)[0]
    except:
        return HttpResponseNotFound('Ingestion report not found.')
    report = ing.report
    if report:
        report = str(zlib.decompress(base64.decodestring(ing.report)))
    else:
        report = 'No report found... maybe the processing is not finished yet?'

    menu_id = 'ing'
    return render_to_response( 'ingestion_report.html', {   
        'report'            : report, 
        'selected_entry_id' : menu_id, 
        'title'             : get_title_from_menu_id(menu_id),
    },
    context_instance = RequestContext(request))

@login_required
@profile
@cache_page(60*30)
def stats_ingestion(request):
    """
    Returns stats about ingestion
    """
    total_images = Image.objects.all().count()
    instruments = Instrument.objects.all().order_by('name')
    imgs_per_instru = []
    for inst in instruments:
        imgcount = Image.objects.filter(instrument = inst).count()
        try: percent = imgcount*100./total_images
        except ZeroDivisionError: percent = 0
        imgs_per_instru.append({'instrument': str(inst.name), 'count': int(imgcount), 'percent': percent})

    channels = Channel.objects.all().order_by('name')
    imgs_per_channel = []
    for c in channels:
        imgCount = Image.objects.filter(channel = c).count()
        try: percent = imgCount*100./total_images
        except ZeroDivisionError: percent = 0
        imgs_per_channel.append({'channel': str(c.name), 'count': int(imgCount), 'percent': percent})

    data = {
        'totalImages'           : int(total_images),
        'totalPerInstrument'    : imgs_per_instru,
        'imgsPerChannel': imgs_per_channel,
    }
    return HttpResponse(str({'info': data}), mimetype = 'text/plain')

@login_required
@profile
@cache_page(60*30)
def stats_processing(request):
    """
    Returns stats about processings
    """
    total_tasks = Processing_task.objects.all().count()
    kinds = Processing_kind.objects.all().order_by('name')
    tasks_per_kind = []
    for k in kinds:
        taskcount = Processing_task.objects.filter(kind = k).count()
        if total_tasks: percent = taskcount*100./total_tasks
        else: percent = 0
        tasks_per_kind.append({'kind': str(k.name), 'count': int(taskcount), 'percent': percent})

    failed_tasks = Processing_task.objects.filter(success = 0).count()

    data = {
        'tasksTotal'    : int(total_tasks),
        'failedTasks'   : int(failed_tasks),
        'tasksPerKind'  : tasks_per_kind,
    }
    return HttpResponse(str({'info': data}), mimetype = 'text/plain')

@login_required
@profile
@cache_page(60*15)
def ingestion_exists(request, id):
    """
    Returns true if ingestion id already exists
    """
    exists = True
    try:
        q = Ingestion.objects.get(label__icontains=id)
    except Ingestion.DoesNotExist:
        exists = False
    return HttpResponse(json.encode({'Exists': exists}), mimetype = 'application/json')
