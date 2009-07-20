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


import cjson as json
import MySQLdb, pyfits
import pprint, re, glob, string
import math, md5, random
import marshal, base64
import os, os.path, sys, pprint
import socket, time
from types import *
#
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, HttpResponseNotFound
from django.db.models import get_models
from django.utils.datastructures import *
from django.template import Template, Context, RequestContext
#
from terapix.youpi.auth import *
from terapix.youpi.models import *
from terapix.script.preingestion import preingest_table
from terapix.script.DBGeneric import *
from terapix.youpi.cviews import *
from terapix.youpi.pluginmanager import PluginManagerError, PluginError
#
from terapix.settings import *

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

def processing_check_config_file_exists(request):
	"""
	Checks if a config file with that name (for a given processing plugin) already exists.
	"""
	try:
		kind = request.POST['Kind']
		name = request.POST['Name']
		type = request.POST['Type']
	except Exception, e:
		return HttpResponseForbidden()

	config = ConfigFile.objects.filter(kind__name__exact = kind, name = name, type__name = type)

	if config:
		exists = 1
	else:
		exists = 0

	return HttpResponse(str({'result' : exists}), mimetype = 'text/plain')

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

def getSQLSignComparator(condTxt):
	c = '='
	if condTxt == 'is different from':
		c = '<>'
	elif condTxt == 'is equal to':
		c = '='
	elif condTxt == 'is greater than':
		c = '>='
	elif condTxt == 'is lower than':
		c = '<='
	elif condTxt == 'contains':
		c = 'LIKE'
	else:
		c = 'LIKE'

	return c

def getConditionalQueryText(request):
	try:
		lines = request.POST['Lines'].split(',')
	except Exception, e:
		return HttpResponseForbidden()

	try:
		# List of selectd values, if any
		multiSel= request.POST['MultiSelection'].split(',')
		hasMultiSel = True
	except:
		hasMultiSel = False

	query = ''
	for i in range(len(lines)):
		# Line number
		j = int(lines[i])
		lineField = request.POST["Line%dField" % j]
		lineCond = request.POST["Line%dCond" % j]
		lineText = request.POST["Line%dText" % j]
	
		if i > 0:
			query += request.POST["Line%dBoolSelect" % j] + WHITESPACE

		if hasMultiSel:
			query += '('

		query += lineField + WHITESPACE
		signCond = getSQLSignComparator(lineCond)

		if signCond == 'LIKE':
			query += signCond + WHITESPACE + '\"%' + lineText + '%\" '
		else:
			query += "%s \"%s\" " % (signCond, lineText)

		if hasMultiSel:
			# For multi-selections, cond will never be LIKE
			k = 'OR'
			if signCond == '<>':
				k = 'AND'
			for sel in multiSel:
				query += "%s %s %s \"%s\" " % (k, lineField, signCond, sel)
			query += ') '

	return query

def preingestion_tables_count(request):
	"""
	"""
	try:
		path = request.POST['path']
	except:
		return HttpResponseForbidden()

	# Look for data
	data = glob.glob("%s*" % path)
	regFitsSearchPattern = '^mcmd\..*\.fits$'

	tables = []
	for file in data:
		if os.path.isfile(file):
			sfile = os.path.basename(file)
			if re.match(regFitsSearchPattern, sfile):
				# This is a fits table file
				tables.append(sfile)

	# Return a basic JSON object
	return HttpResponse(str([{'path' : str(path), 'tables' : [str(e) for e in tables] }]), mimetype = 'text/plain')


def preingestion_run(request):
	"""
	"""

	try:
		table = request.POST['table']
		path = request.POST['path']
	except Exception, e:
		return HttpResponseForbidden()

	db = DB(host = DATABASE_HOST,
			user = DATABASE_USER,
			passwd = DATABASE_PASSWORD,
			db = DATABASE_NAME)

	g = DBGeneric(db.con)

	# Do the job
	try:
		preingest_table(g, table, path)
	except Exception ,e:
		return HttpResponseServerError("Script error: %s" % e)

	return HttpResponse(table + ' done.', mimetype = 'text/plain')

def history_preingestion(request):
	"""
	Return a JSON object with data related to preingestions' history
	"""

	try:
		limit = request.POST['limit']
	except Exception, e:
		return HttpResponseServerError("Script error: %s" % e)

	try:
		limit = int(limit)
	except ValueError, e:
		# Unlimitted
		limit = 0

	res = Fitstables.objects.all()

	if limit > 0:
		res = res[:limit]

	#
	# We build a standard header that can be used for table's header.
	# header var must be a list not a tuple since it get passed 'as is' to the json 
	# dictionary
	#
	header = ['Image', 'Instrument', 'Channel', 'Run', 'QSO status', 'Path']

	data = []
	for r in res:
			#
			# Unicode strings have to be converted to basic strings with str()
			# in order to get a valid JSON object
			#
			data.append({	header[0] 	: str(r.name), 
							header[1] 	: str(r.instrument),
							header[2] 	: str(r.channel),
							header[3] 	: str(r.run),
							header[4] 	: str(r.QSOstatus),
							header[5] 	: str(r.fitstable)
			})

	# Be aware that JS code WILL search for data and header members
	json = { 'data' : data, 'header' : header }

	# Return a JSON object
	return HttpResponse(str(json), mimetype = 'text/plain')

def preingestion_table_fields(request):
	"""
	Return a JSON object with data related to table's fields
	"""

	try:
		table = request.POST['table']
	except Exception, e:
		return HttpResponseForbidden()

	db = DB(host = DATABASE_HOST,
			user = DATABASE_USER,
			passwd = DATABASE_PASSWORD,
			db = DATABASE_NAME)

	g = DBGeneric(db.con)

	try:
		res = g.execute("Desc " + table);
	except MySQLdb.DatabaseError, e:
		return HttpResponseServerError("Error: %s" % e)

	return HttpResponse(str({'fields' : [r[0] for r in res]}), mimetype = 'text/plain')

#
# FIXME
# DEPRECATED
# This function should be removed. Not used anymore by the image selector.
# However some JS code still call it...
#
def preingestion_custom_query(request):
	"""
	Builds an SQL query based on POST data, executes it and returns a JSON object containing results.
	"""

	try:
		table = request.POST['Table']
		displayField = request.POST['DisplayField']
		#
		# Line'n'Field, Line'n'Cond, Line'n'Text for n>=0
		# and Line'n'BoolSelect for n>0
		#
		lines = request.POST['Lines'].split(',')
		orderBy = request.POST['OrderBy']
		hide = request.POST['Hide']
		releaseId = request.POST.get('ReleaseId', None)
	except Exception, e:
		return HttpResponseForbidden()

	try:
		limit = int(request.POST['Limit'])
	except Exception, e:
		# No limit
		limit = 0

	simpleQuery = False
	try:
		ftable = request.POST['Ftable']
		ftableField = request.POST['FtableField']
		ftableFieldValue = request.POST['FtableFieldValue']
		ftableId = request.POST['FtableId']
		fkId = request.POST['FkId']
	except Exception, e:
		simpleQuery = True

	try:
		# Search through subset only
		idList = request.POST['IdList']
		idField = request.POST['IdField']
	except Exception, e:
		idList = None

	try:
		# Search through subset only
		dist = request.POST['Distinct']
		distinct = True
	except:
		distinct = False

	try:
		revert = request.POST['Revert']
		revert = True
	except:
		revert = False

	try:
		condTxt = request.POST["Line0Cond"]
		contTxt = True
	except:
		contTxt = False

	query = 'SELECT' + WHITESPACE

	try:
		# List of selectd values, if any
		multiSel= request.POST['MultiSelection'].split(',')
		hasMultiSel = True
	except:
		hasMultiSel = False

	if simpleQuery:
		try:
			tableField = request.POST['TableField']
			tableFieldValue = request.POST['TableFieldValue']
		except:
			tableField = None

		if distinct:
			query += "DISTINCT("

		if displayField == 'all':
			query += '*'
		else:
			query += displayField

		if distinct:
			query += ")"
	
		query += WHITESPACE + "FROM %s WHERE " % table
		if not idList:
			query += getConditionalQueryText(request)
			
		if tableField:
			c = getSQLSignComparator(condTxt)
			query += "%s %s \"%s\" " % (tableField, c, tableFieldValue)

		if idList:
			line0 = True
			try:
				line0Field = request.POST['Line0Field']
				line0Text = request.POST['Line0Text']
			except Exception, e:
				line0 = False

			c = getSQLSignComparator(condTxt)

			if not line0:
				query += "%s IN (%s) " % (idField, idList)
			else:
				if hasMultiSel:
					query += "%s IN (%s) AND ( %s %s \"%s\" " % (idField, idList, line0Field, c, line0Text)
					k = 'OR'
					if c == '<>':
						k = 'AND'
					for sel in multiSel:
						query += "%s %s %s \"%s\" " % (k, line0Field, c, sel)
					query += ') '
				else:
					query += "%s IN (%s) AND %s %s \"%s\" " % (idField, idList, line0Field, c, line0Text)

		query += "ORDER BY %s" % orderBy
	
		if limit > 0:
			query += " LIMIT %d;" % limit

	else:
		# Join 2 tables, more complex query
		query += 'a.'
		if displayField == 'all':
			query += '*'
		else:
			query += displayField

		if idList:
			c = getSQLSignComparator(condTxt)
			query += " FROM %s AS a, %s AS b WHERE a.%s=b.%s AND " % (table, ftable, fkId, ftableId)

			if hasMultiSel:
				query += "(b.%s %s \"%s\"" % (ftableField, c, ftableFieldValue)
				k = 'OR'
				if c == '<>':
					k = 'AND'

				for sel in multiSel:
					query += " %s b.%s %s \"%s\"" % (k, ftableField, c, sel)
				query += ')'
			else:
				query += "b.%s %s \"%s\"" % (ftableField, c, ftableFieldValue)

			if revert:
				query += " AND b.%s " % idField
			else:
				query += " AND a.%s " % idField

			query += "IN (%s)" % idList
		else:
			query += " FROM %s AS a, %s AS b WHERE a.%s=b.%s AND (" % (table, ftable, fkId, ftableId)
			c = getSQLSignComparator(condTxt)

			if hasMultiSel:
				query += "b.%s %s \"%s\"" % (ftableField, c, ftableFieldValue)
				k = 'OR'
				if c == '<>':
					k = 'AND'

				# For multi-selections, cond will never be LIKE
				for sel in multiSel:
					query += " %s b.%s %s \"%s\"" % (k, ftableField, c, sel)
			else:
				query += "b.%s %s \"%s\"" % (ftableField, c, ftableFieldValue)

			query += ')'

	# Now executes query
	db = DB(host = DATABASE_HOST,
			user = DATABASE_USER,
			passwd = DATABASE_PASSWORD,
			db = DATABASE_NAME)

	g = DBGeneric(db.con)

	try:
		res = g.execute(query);
	except MySQLdb.DatabaseError, e:
		return HttpResponseServerError("Error: %s [Query: \"%s\"]" % (e, query))
	except Exception, e:
		return HttpResponse(str({'query' : "%s [Error] %s" % (str(query), e), 'fields' : [], 'data' : [], 'hidden' : str(hide).split(',')}), mimetype = 'text/plain')

	data = []
	for r in res:
		line = []
		for f in r:
			line.append(str(f))
		data.append(line)

	# See PEP-0249 for further details
	tableFields = [r[0] for r in g.cursor.description]

	return HttpResponse(str({'query' : str(query), 'fields' : tableFields, 'data' : data, 'hidden' : str(hide).split(',')}), mimetype = 'text/plain')

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
		sels, filtered = read_proxy(request, ImageSelections.objects.all().order_by('date'))
		data = []
		for s in sels:
			sList = marshal.loads(base64.decodestring(s.data))
			if len(sList) == 1: data.append(s.name)
	else:
		return HttpResponseBadRequest('Incorrect POST data')

	return HttpResponse(json.encode({'name': name, 'data': [str(d) for d in data]}), mimetype = 'text/plain')

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


def processing_get_imgs_ids_from_release(request):
	"""
	Returns a dictionnary with images Ids that belong to a release
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
