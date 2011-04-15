
import os.path, glob
import cjson as json
import marshal, base64, zlib
import magic, string
import xml.dom.minidom as dom
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
from terapix.youpi.auth import *
from terapix.youpi.models import *
from terapix.youpi.cviews import profile 
from terapix.youpi.views import get_entity_permissions
from terapix.youpi.cviews import manager
from terapix.lib.common import get_title_from_menu_id, NULLSTRING

@login_required
@cache_page(60*5)
def ims_get_collection(request, name):
    """
    Returns a collection for the image selector
    """
    if name == 'object':
        data = Image.objects.all().distinct().values_list('object', flat = True).order_by('object')
    elif name == 'ingestionid':
        data = Ingestion.objects.all().distinct().values_list('label', flat = True).order_by('label')
    elif name == 'channel':
        data = Channel.objects.all().distinct().values_list('name', flat = True).order_by('name')
    elif name == 'instrument':
        data = Instrument.objects.all().distinct().values_list('name', flat = True).order_by('name')
    elif name == 'run':
        data = Run.objects.all().distinct().values_list('name', flat = True).order_by('name')
    elif name == 'tag':
        data = Tag.objects.all().distinct().values_list('name', flat = True).order_by('name')
    elif name == 'grade':
        data = [g[0] for g in GRADE_SET]
    elif name == 'savedselections':
        sels = ImageSelections.objects.all().order_by('date')
        data = []
        for s in sels:
            sList = marshal.loads(base64.decodestring(s.data))
            if len(sList) == 1: data.append(s.name)
    else:
        return HttpResponseBadRequest('Incorrect POST data')

    return HttpResponse(json.encode({'name': name, 'data': [str(d) for d in data]}), mimetype = 'text/plain')

def get_circle_from_multipolygon(alpha_center, delta_center, radius, p = 16):
    """
    Returns a MySQL MULTIPOLYGON object describing a circle with a resolution of p points.
    @param alpha_center right ascension in degrees
    @param delta_center declination in degrees
    @param radius angular degree in degrees
    """
    import math
    from copy import deepcopy
    # Computing selection circle based (p points)
    rot = []
    p -= 1
    if p % 2 == 0:
        t = p/2
    else:
        t = p/2+1

    for i in range(t):
        rot.append(2*math.pi*(i+1)/p)

    ro = deepcopy(rot)
    ro.reverse()
    ro = ro[1:]
    for i in range(len(ro)):
        ro[i] = -ro[i]
    rot.extend(ro)

    p1x, p1y = alpha_center + radius, delta_center
    points = [p1x, p1y]

    for i in range(len(rot)):
        points.append(math.cos(rot[i])*(p1x - alpha_center) - math.sin(rot[i])*(p1y - delta_center) + alpha_center)
        points.append(math.sin(rot[i])*(p1x - alpha_center) + math.cos(rot[i])*(p1y - delta_center) + delta_center)
    points.append(p1x)
    points.append(p1y)

    strf = 'MULTIPOLYGON((('
    for j in range(0, len(points), 2):
        strf += "%f %f," % (points[j], points[j+1])
    strf = strf[:-1] + ')))'

    return strf

def batch_parse_selection(sel):
    """
    Parse a single XML DOM selection.
    """
    label = sel.getElementsByTagName('label')[0].firstChild.nodeValue
    alpha_center = float(sel.getElementsByTagName('alpha')[0].firstChild.nodeValue)
    delta_center = float(sel.getElementsByTagName('delta')[0].firstChild.nodeValue)
    radius = float(sel.getElementsByTagName('radius')[0].firstChild.nodeValue)
    imgs = Image.objects.filter(centerfield__contained = get_circle_from_multipolygon(alpha_center, delta_center, radius, 16))
    
    return {'xml' : str(sel.toxml()), 'name' : str(label), 'count' : len(imgs), 'idList' : string.join([str(img.id) for img in imgs], ',')}

def ims_get_images(request, name):
    """
    Returns a list of images
    (r'^youpi/ims/images/(.*?)/$', 'ims_get_images'),
    """
    try:
        cond = request.POST['Condition']
        value = request.POST['Value']
    except Exception, e:
        return HttpResponseForbidden()

    from django.db import connection
    cur = connection.cursor()

    idList = request.POST.get('IdList', False)
    if idList: idList = [int(id) for id in idList.split(',')]

    if name not in ('Ra', 'Dec', 'Name'):
        if value.find(',') > 0:
            value = value.split(',')
        else:
            value = (value,)

    EQ = 'is equal to'
    NEQ = 'is different from'
    GT = 'is greater than'
    LT = 'is lower than'

    if name == 'Run':
        q = """
        SELECT rel.image_id FROM youpi_rel_ri AS rel, youpi_run AS r
        WHERE r.id = rel.run_id
        AND r.name %s IN (%s)
        """ % ('%s', string.join(map(lambda x: "'%s'" % x, value), ','))
        if idList:
            q += "AND rel.image_id IN (%s)"
            if cond == EQ:
                q = q % ('', string.join([str(id) for id in idList], ','))
            else:
                q = q % ('NOT', string.join([str(id) for id in idList], ','))
        else:
            if cond == EQ:
                q = q % ''
            else:
                q = q % 'NOT'
        cur.execute(q)
        res = cur.fetchall()
        data = [r[0] for r in res]

    elif name == 'Tag':
        if idList:
            if cond == EQ:
                q = """
                SELECT DISTINCT(i.id) 
                FROM youpi_image AS i, youpi_rel_tagi AS r, youpi_tag AS t 
                WHERE r.image_id=i.id AND r.tag_id=t.id AND t.name IN (%s) AND i.id IN (%s)""" \
                    % (string.join(map(lambda x: "'%s'" % x, value), ','), string.join(map(lambda x: str(x), idList), ',')) 
            else:
                q = """
                SELECT DISTINCT(i.id) 
                FROM youpi_image AS i, youpi_rel_tagi AS r, youpi_tag AS t 
                WHERE r.image_id=i.id AND r.tag_id=t.id AND t.name NOT IN (%s) AND i.id IN (%s)""" \
                    % (string.join(map(lambda x: "'%s'" % x, value), ','), string.join(map(lambda x: str(x), idList), ',')) 
            cur.execute(q)
            res = cur.fetchall()
            data = [r[0] for r in res]
        else:
            if cond == EQ:
                data = Rel_tagi.objects.filter(tag__name__in = value).values_list('image__id', flat = True)
            else:
                q = """
                SELECT DISTINCT(i.id) 
                FROM youpi_image AS i, youpi_rel_tagi AS r, youpi_tag AS t 
                WHERE r.image_id=i.id AND r.tag_id=t.id AND t.name NOT IN (%s)""" % string.join(map(lambda x: "'%s'" % x, value), ',')
                cur.execute(q)
                res = cur.fetchall()
                data = [r[0] for r in res]

    elif name == 'Object':
        if idList:
            if cond == EQ:
                data = Image.objects.filter(object__in = value, id__in = idList).values_list('id', flat = True).order_by('name')
            else:
                data = Image.objects.exclude(object__in = value).filter(id__in = idList).values_list('id', flat = True).order_by('name')
        else:
            if cond == EQ:
                data = Image.objects.filter(object__in = value).values_list('id', flat = True).order_by('name')
            else:
                data = Image.objects.exclude(object__in = value).values_list('id', flat = True).order_by('name')

    elif name == 'Instrument':
        if idList:
            if cond == EQ:
                data = Image.objects.filter(instrument__name__in = value, id__in = idList).values_list('id', flat = True).order_by('name')
            else:
                data = Image.objects.exclude(instrument__name__in = value).filter(id__in = idList).values_list('id', flat = True).order_by('name')
        else:
            if cond == EQ:
                data = Image.objects.filter(instrument__name__in = value).values_list('id', flat = True).order_by('name')
            else:
                data = Image.objects.exclude(instrument__name__in = value).values_list('id', flat = True).order_by('name')

    elif name == 'Channel':
        if idList:
            if cond == EQ:
                data = Image.objects.filter(channel__name__in = value, id__in = idList).values_list('id', flat = True).order_by('name')
            else:
                data = Image.objects.exclude(channel__name__in = value).filter(id__in = idList).values_list('id', flat = True).order_by('name')
        else:
            if cond == EQ:
                data = Image.objects.filter(channel__name__in = value).values_list('id', flat = True).order_by('name')
            else:
                data = Image.objects.exclude(channel__name__in = value).values_list('id', flat = True).order_by('name')

    elif name == 'Name':
        # Image name
        if idList:
            data = Image.objects.filter(name__icontains = value, id__in = idList).values_list('id', flat = True).order_by('name')
        else:
            data = Image.objects.filter(name__icontains = value).values_list('id', flat = True).order_by('name')

    elif name == 'Ra':
        # FIXME: LT, GT
        if idList:
            data = Image.objects.filter(alpha = value, id__in = idList).values_list('id', flat = True).order_by('name')
        else:
            data = Image.objects.filter(alpha = value).values_list('id', flat = True).order_by('name')

    elif name == 'Dec':
        # FIXME: LT, GT
        if idList:
            data = Image.objects.filter(delta = value, id__in = idList).values_list('id', flat = True).order_by('name')
        else:
            data = Image.objects.filter(delta = value).values_list('id', flat = True).order_by('name')

    elif name == 'Saved':
        sel = ImageSelections.objects.filter(name__in = value)[0]
        sdata = marshal.loads(base64.decodestring(sel.data))
        selIdList = sdata[0]
        if idList:
            # Find the intersections
            realIdList = []
            for id in idList:
                if id in selIdList: realIdList.append(id)
            data = Image.objects.filter(id__in = realIdList).values_list('id', flat = True).order_by('name')
        else:
            data = Image.objects.filter(id__in = selIdList).values_list('id', flat = True).order_by('name')

    elif name == 'IngestionId':
        if idList:
            if cond == EQ:
                data = Image.objects.filter(ingestion__label__in = value, id__in = idList).values_list('id', flat = True).order_by('name')
            else:
                data = Image.objects.exclude(ingestion__label__in = value).filter(id__in = idList).values_list('id', flat = True).order_by('name')
        else:
            if cond == EQ:
                data = Image.objects.filter(ingestion__label__in = value).values_list('id', flat = True).order_by('name')
            else:
                data = Image.objects.exclude(ingestion__label__in = value).values_list('id', flat = True).order_by('name')

    elif name == 'Grade':
        if cond == EQ:
            fitsinIds = FirstQEval.objects.filter(grade__in = value).values_list('fitsin', flat = True).distinct()
        else:
            cur.execute("SELECT DISTINCT(fitsin_id) FROM youpi_firstqeval WHERE grade NOT IN (%s)" \
                % string.join(map(lambda x: "'%s'" % x, value), ','))
            res = cur.fetchall()
            fitsinIds = [r[0] for r in res]

        taskIds = Plugin_fitsin.objects.filter(id__in = fitsinIds).values_list('task', flat = True)
        imgIds = Rel_it.objects.filter(task__id__in = taskIds).values_list('image', flat = True)
        if idList:
            # Find the intersections
            realIdList = []
            for id in idList:
                if id in imgIds: realIdList.append(id)
            data = Image.objects.filter(id__in = realIdList).values_list('id', flat = True).order_by('name')
        else:
            data = Image.objects.filter(id__in = imgIds).values_list('id', flat = True).order_by('name')

    # Format data
    data = [[str(id)] for id in data]

    return HttpResponse(json.encode({'name': name, 'data': data}), mimetype = 'text/plain')

@login_required
@profile
def ims_import_selections(request):
    """
    Batch import selections of images.
    Import all selection files in a directory. File names are matched against a pattern.
    For each file the selection is matched. If ok creates a new saved selection. If at least one image is missing from 
    a selection description, no saved selection is created at all, instead reports a warning.
    """
    post = request.POST
    try:
        path = post['Path']
        patterns = post['Patterns'].split(';')
        # FIXME
        #onTheFly = json.decode(request.POST['OnTheFly'])
    except:
        raise PluginError, "invalid post parameters %s" % post

    res = {}
    MAX_FILE_SIZE = 256 * 1024 # In Kb
    STEP = 10

    files = []
    try:
        for pat in patterns:
            pfiles = glob.glob(os.path.join(path, pat))
            files.extend(pfiles)
    except:
        res['error'] = 'An error occured when looking for files in the provided path. Please check your path and try again'

    try: 
        pos = int(post['Pos'])
        total = int(post['Total'])
        skipped = int(post.get('Skipped', 0))
    except:
        # First call to this function
        # Compute total
        total = len(files);
        skipped = 0
        pos = 0

    profile = request.user.get_profile()
    mag = magic.open(magic.MAGIC_NONE)
    mag.load()

    res['skipped'] = skipped
    profile = request.user.get_profile()
    frame = range(len(files))[pos:]
    z = 0
    warnings = []
    for k in frame:
        if pos == total: break
        pos += 1
        z += 1
        try:
            # Check magic number. Must be equal to 'ASCII text'
            if mag.file(files[k]).find('ASCII') == -1 and os.path.getsize(files[k]) > MAX_FILE_SIZE:
                res['skipped'] += 1
                continue
            f = open(files[k])
            lines = f.readlines()
            f.close()
        except Exception, e:
            res['error'] = str(e)
            break

        fileName = files[k]
        basename = fileName[:fileName.rfind('.')]
        lines = [li[:-1] for li in lines]
        namemd5 = []
        idList = []
        j = 0
        for line in lines:
            # Skip comments
            if line.find('#') == 0: 
                j += 1
                continue
            sp = line.split(',')
            if len(sp) == 1:
                sp[0] = sp[0].strip()
                imgs = Image.objects.filter(name__exact = sp[0])
                if not imgs:
                    warnings.append("In %s (Line %d): image '%s' not found, will not make a selection from this file" % (os.path.basename(fileName), j+1, sp[0]))
                    break
                else:
                    img = imgs[len(imgs)-1]
                    idList.append(img.id)
            elif len(sp) == 2:
                sp[0] = sp[0].strip()
                sp[1] = sp[1].strip()
                namemd5.append(sp)
                imgs = Image.objects.filter(name__exact = sp[0], checksum = sp[1])
                if not imgs:
                    warnings.append("In %s (Line %d): image '%s' (%s) not found, will not make a selection from this file" % (os.path.basename(fileName), j+1, sp[0], sp[1]))
                    break
                else:
                    img = imgs[len(imgs)-1]
                    idList.append(img.id)
            else:
                # Line not well-formatted
                res['error'] = "Line %d is not well-formatted: should be image_name[, md5sum]" % j+1
                break
            j += 1

        # Do not save the selection if at least one file is missing, continue to next file
        if warnings: continue

        # Tag images on-the-fly
        # FIXME
        #if onTheFly: tag_mark_images(request, True, idList, [basename])

        sList = base64.encodestring(marshal.dumps([idList])).replace('\n', NULLSTRING)
        selname = os.path.basename(basename)
        try:
            # Updates entry
            imgSelEntry = ImageSelections.objects.filter(name = selname)[0]
            imgSelEntry.data = sList
            success = write_proxy(request, imgSelEntry)
            if not success:
                warnings.append("In %s: could not save the selection" % os.path.basename(fileName))
        except:
            # ... or inserts a new one
            imgSelEntry = ImageSelections(name = selname, data = sList, user = request.user, mode = profile.dflt_mode, group = profile.dflt_group)
            imgSelEntry.save()
            success = True
        res['success'] = success

        if z > STEP: break

    res['warnings'] = warnings
    res['total'] = total
    res['pos'] = pos 
    if total == 0: res['percent'] = 0
    else: res['percent'] = pos*100./total

    return HttpResponse(json.encode({'result': res}))

def _get_pagination_attrs(page, full_data, data_len):
    """
    Gets pagination attributes
    """
    # Pagination handling
    #count = len(full_data)
    count = data_len
    if page == 0:
        currentPage = 1
    else:
        currentPage = int(page)
    maxPerPage = settings.IMS_MAX_PER_PAGE
    nbPages = count / maxPerPage
    if count % maxPerPage > 0:
        nbPages += 1

    # Finds window boundaries
    wmin = maxPerPage * (currentPage-1)
    if count - wmin > maxPerPage:
        window = full_data[wmin: wmin + maxPerPage]
    else:
        window = full_data[wmin:]
    return currentPage, nbPages, window

def processing_imgs_from_idlist_post(request):
    """
    Builds an SQL query based on POST data, executes it and returns a JSON object containing results.
    """
    try:
        ids = request.POST['Ids']
        page = request.POST.get('Page', 0)
        pageStatus = request.POST.get('PageStatus', None)
    except Exception, e:
        return HttpResponseBadRequest('Incorrect POST data')

    # Build integer list from ranges
    ids = unremap(ids).split(',')
    currentPage, nbPages, window = _get_pagination_attrs(page, ids, len(ids))

    # Get image data for currentPage
    images = Image.objects.filter(id__in = window)

    content = []
    for img in images:
        rels = Rel_tagi.objects.filter(image = img)
        tags = Tag.objects.filter(id__in = [r.tag.id for r in rels]).order_by('name')
        if tags:
            cls = 'hasTags'
        else:
            cls = ''
        content.append([int(img.id), 
                        str("<span class=\"imageTag %s\">%s.fits</span><div style=\"width: 200px;\">%s</div>" % 
                            (cls,       # Class name
                             img.name,  # Image name
                             string.join([str("<span class=\"tagwidget\" style=\"%s;\">%s</span>" % (t.style, t.name)) for t in tags], '')))])

    return HttpResponse(str({'TotalPages': int(nbPages), 'CurrentPage': currentPage, 'Headers': ['Image Name/Tags'], 'Content' : content}), mimetype = 'text/plain')

def get_selected_ids_from_pagination(request):
    """
    Returns a list of ids of selected images (in pagination mode)
    """
    try:
        ids = request.POST['Ids']
        pageStatus = request.POST['PageStatus'].split('_')
    except Exception, e:
        return HttpResponseBadRequest('Incorrect POST data')

    # Build integer list from ranges
    ids = unremap(ids).split(',')
    range = settings.IMS_MAX_PER_PAGE
    idList = []

    k = j = 0
    pages = []
    while j < len(pageStatus):
        pages.append(ids[k:k+range])
        k += range
        j += 1

    k = 0
    for page in pages:
        ps = pageStatus[k].split(',')
        if ps[0] == 's':
            tmp = ps[1:][:]
            tmp.reverse()
            for unchecked in tmp:
                del page[int(unchecked)]
        elif ps[0] == 'u':
            tmp = []
            for checked in ps[1:]:
                tmp.append(page[int(checked)])
            page = tmp
        else:
            return HttpResponse(str({'Error': 'pageStatus POST data bad formatted'}))

        idList.extend(page)
        k += 1

    count = len(idList)
    idList = string.join(idList, ',')
    return HttpResponse(str({'idList': str(idList), 'count': int(count)}), mimetype = 'text/plain')

def remap(idList):
    """
    Build a list of ranges from an integer suite:

    IN:  1,2,3,4,6,7,8,9,11,12,13,20,22,23,24,25,30,40,50,51,52,53,54,60
    OUT: 1-4,6-9,11-13,20-20,22-25,30-30,40-40,50-54,60-60
    """
    idList = idList.split(',')
    idList = [int(id) for id in idList]
    idList.sort()
    
    ranges = []
    i = idList[0]
    ranges.append(i)
    
    for k in range(len(idList)-1):
        if idList[k+1] > idList[k]+1:
            ranges.append(idList[k])
            ranges.append(idList[k+1])
    
    ranges.append(idList[-1])
    
    maps = ''
    for k in range(0, len(ranges)-1, 2):
        maps += "%s-%s," % (ranges[k], ranges[k+1])
    
    return maps[:-1]

def unremap(ranges):
    """
    Build an integer suite from a list of ranges:

    IN:  1-4,6-9,11-13,20-20,22-25,30-30,40-40,50-54,60-60
    OUT: 1,2,3,4,6,7,8,9,11,12,13,20,22,23,24,25,30,40,50,51,52,53,54,60
    """
    ranges = ranges.split(',')
    idList = ''

    for r in ranges:
        r = r.split('-')
        r = [int(j) for j in r]
        idList += string.join([str(j) for j in range(r[0], r[1]+1)], ',') + ','

    return idList[:-1]

def processing_imgs_remap_ids(request):
    """
    Rewrite idList to prevent too long GET queries
    """
    try:
        idList = request.POST['IdList']
    except Exception, e:
        return HttpResponseBadRequest('Incorrect POST data')
    return HttpResponse(str({'mapList' : remap(idList)}), mimetype = 'text/plain')

def processing_save_image_selection(request):
    """
    Saves image selection to DB.
    """
    try:
        name = request.POST['Name']
        idList = eval(request.POST['IdList'])
    except Exception, e:
        return HttpResponseForbidden()

    # Base64 encoding + marshal serialization
    sList = base64.encodestring(marshal.dumps(idList)).replace('\n', NULLSTRING)
    profile = request.user.get_profile()
    try:
        # Updates entry
        imgSelEntry = ImageSelections.objects.filter(name = name)[0]
        imgSelEntry.data = sList
        success = write_proxy(request, imgSelEntry)
    except:
        # ... or inserts a new one
        imgSelEntry = ImageSelections(name = name, data = sList, user = request.user, mode = profile.dflt_mode, group = profile.dflt_group)
        imgSelEntry.save()
        success = True
    return HttpResponse(json.encode({'name': name, 'id': imgSelEntry.id, 'success': success}), mimetype = 'text/plain')

def processing_get_image_selections(request):
    """
    Returns image selections.
    """
    try:
        name = request.POST['Name']
        all = False
    except Exception, e:
        all = True

    mode = request.POST.get('Mode', 'Single') # Single or Batch
    idList = []

    if not all:
        try:
            sels, filtered = read_proxy(request, ImageSelections.objects.filter(name = name))
            if sels:
                sel = sels[0]
                # marshal de-serialization + base64 decoding
                idList = marshal.loads(base64.decodestring(str(sel.data)))
            if mode == 'Single' and len(idList) > 1:
                idList = []
        except:
            # Not found
            pass
    else:
        sels, filtered = read_proxy(request, ImageSelections.objects.all().order_by('name'))
        for s in sels:
            sList = marshal.loads(base64.decodestring(s.data))
            if mode == 'Single' and len(sList) == 1:
                idList.append([s.name, sList])
            elif mode == 'Batch' and len(sList) > 1:
                idList.append([s.name, sList])

    count = len(idList)
    return HttpResponse(json.encode({'data' : idList, 'count' : count, 'filtered': filtered}), mimetype = 'text/plain')

def processing_delete_image_selection(request):
    """
    Deletes one (stored) image selection
    """
    try:
        name = request.POST['Name']
    except Exception, e:
        return HttpResponseForbidden()

    try:
        sel = ImageSelections.objects.filter(name = name)[0]
        success = write_proxy(request, sel, delete = True)
    except Exception, e:
        return HttpResponse(str({'Error' : str(e)}), mimetype = 'text/plain')

    return HttpResponse(json.encode({'success': success, 'data' : name}), mimetype = 'text/plain')

def processing_get_imgs_ids_from_release(request):
    """
    Returns a dictionnary with images Ids that belong to a release
    FIXME: not used
    """
    try:
        releaseId = request.POST['ReleaseId']
    except Exception, e:
        return HttpResponseForbidden()

    rels = Rel_imgrel.objects.filter(release__id = int(releaseId))
    data = []
    for rel in rels:
        data.append([str(rel.image.id)])

    return HttpResponse(str({'fields' : ['id'], 'data' : data}))

def upload_file(request):
    """
    Uploads a file into temporary directory.
    exit_code != 0 if any problem found.
    """
    exitCode = 0
    errMsg = ''
    try:
        try:
            files = request.FILES
            keys = files.keys()
        except:
            raise Exception, "Bad file submitted"

        if len(keys):
            k = keys[0]
            content = files[k].read()
        else:
            raise Exception, "Could not get file content"

        # Valid XML file, save it to disk
        filename = files[k].name
        f = open('/tmp/' + request.user.username + '_' + filename, 'w')
        f.write(content)
        f.close()
        
    except Exception, e:
        exitCode = 1
        content = ''
        filename = ''
        errMsg = str(str(e))
    return HttpResponse(str({'filename' : str(filename), 'length' : len(content), 'exit_code' : exitCode, 'error_msg' : errMsg }), mimetype = 'text/html')

def ims_get_image_list_from_file(request):
    """
    Parse content of fileName and returns an image selection
    """
    try:
        fileName = request.POST['Filename']
        onTheFly = json.decode(request.POST['OnTheFly'])
    except Exception, e:
        return HttpResponseBadRequest('Incorrect POST data')

    errMsg = ''
    try:
        f = open('/tmp/' + request.user.username + '_' + fileName)
        lines = f.readlines()
        f.close()
    except Exception, e:
        errMsg = "%s" % e

    basename = fileName[:fileName.rfind('.')]
    lines = [li[:-1] for li in lines]
    warnings = []
    # Separate lines with image name only (to issue only one SQL query)
    nameonly = []
    # ...from lines with image name and checksum (one SQL query per line)
    namemd5 = []
    idList = []
    j = comments = 0
    for line in lines:
        # Skip comments
        if line.find('#') == 0: 
            j += 1
            comments += 1
            continue
        sp = line.split(',')
        if len(sp) == 1:
            sp[0] = sp[0].strip()
            imgs = Image.objects.filter(name__exact = sp[0])
            if not imgs:
                warnings.append("Line %d: image '%s' not found" % (j+1, sp[0]))
            else:
                img = imgs[len(imgs)-1]
                idList.append(img.id)
        elif len(sp) == 2:
            sp[0] = sp[0].strip()
            sp[1] = sp[1].strip()
            namemd5.append(sp)
            imgs = Image.objects.filter(name__exact = sp[0], checksum = sp[1])
            if not imgs:
                warnings.append("Line %d: image '%s' (%s) not found" % (j+1, sp[0], sp[1]))
            else:
                img = imgs[len(imgs)-1]
                idList.append(img.id)
        else:
            # Line not well-formatted
            errMsg = "Line %d is not well-formatted: should be image_name[, md5sum]" % j+1
            break
        j += 1

    # Tag images on-the-fly
    if onTheFly: 
        from terapix.youpi.cviews.tags import tag_mark_images 
        tag_mark_images(request, True, idList, [basename])

    return HttpResponse(json.encode({
        'tagged': onTheFly, 
        'tagname': basename, 
        'warnings': warnings, 
        'error': errMsg, 
        'foundCount': len(idList), 
        'total' : len(lines)-comments, 
        'idList' : idList}), mimetype = 'text/plain')

def batch_parse_content(request):
    """
    Parse XML content of file fileName to find out selections.
    This comes AFTER dtd validation so nothing to worry about.
    """
    try:
        fileName = request.POST['Filename']
    except Exception, e:
        return HttpResponseBadRequest('Incorrect POST data')

    f = '/tmp/' + request.user.username + '_' + fileName
    doc = dom.parse(f)
        
    data = doc.getElementsByTagName('selection')
    selections = []
    for sel in data:
        selections.append(batch_parse_selection(sel))
    return HttpResponse(str({'result' : {'nbSelections' : len(selections), 'selections' : selections}}), mimetype = 'text/plain')

def batch_view_content(request, fileName):
    """
    Parse XML content of file fileName to find out selections.
    """
    fileName = '/tmp/' + request.user.username + '_' + fileName
    try:
        f = open(fileName)
        data = f.readlines()
        f.close()
    except IOError:
        return HttpResponseNotFound('File not found.')
    return HttpResponse(string.join(data), mimetype = 'text/xml')

def batch_view_selection(request):
    """
    Returns selection content
    """
    try:
        xmlstr = request.POST['XML']
    except Exception, e:
        return HttpResponseBadRequest('Incorrect POST data')

    doc = dom.parseString(xmlstr)
    data = doc.getElementsByTagName('selection')[0]
    sel = batch_parse_selection(data);
    imgs = Image.objects.filter(id__in = sel['idList'].split(',')).order_by('name');

    return HttpResponse(str({'name' : str(sel['name']), 'data' : [[str(img.name), str(img.path)] for img in imgs]}), mimetype = 'text/plain')

