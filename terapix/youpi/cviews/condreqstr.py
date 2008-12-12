# vim: set ts=4

import os, string
import xml.dom.minidom as dom
import base64, marshal
#
from terapix.youpi.models import *

def get_condor_status():
	"""
	This function is usefull to get a list of hosts attached to condor (part of the cluster) in real time.
	A list of lists is returned : [[ vm_full_name1, state1], [vm_full_name2, state2]...]

	short_host_name may be one of 'mix3', 'mix4' etc.
	state is one of 'Idle' or 'Running'.
	"""

	pipe = os.popen("/opt/condor/bin/condor_status -xml")
	data = pipe.readlines()
	pipe.close()

	doc = dom.parseString(string.join(data))
	nodes = doc.getElementsByTagName('c')

	vms = []
	cur = 0
	for n in nodes:
		data = n.getElementsByTagName('a')

		for a in data:
			if a.getAttribute('n') == 'Name':
				name = a.firstChild.firstChild.nodeValue
				vms.append([str(name), 0])
			elif a.getAttribute('n') == 'Activity':
				status = a.firstChild.firstChild.nodeValue
				vms[cur][1] = str(status)
				cur += 1

	return vms

def get_requirement_string(params, vms):
	"""
	Returns Condor's requirement string for a *POLICY*
	"""

	# De-serialization mappings
	cdeserial = {
		'G' : '>=',
		'L' : '<=',
		'E' : '='
	}
	sdeserial = {
		'M'	: 1,
		'G'	: 1024,
		'T'	: 1024 * 1024
	}

	params = params.split('#')
	nodes = [vm[0] for vm in vms]

	crit = {}
	for p in params:
		d = p.split(',')
		if not crit.has_key(d[0]):
			crit[d[0]] = []
		crit[d[0]].append(d[1:])

	req = 'Requirements = ('

	# Memory
	if crit.has_key('MEM'):
		req += '('
		for mem in crit['MEM']:
			comp, val, unit = mem
			req += "Memory %s %d && " % (cdeserial[comp], int(val)*sdeserial[unit])
		req = req[:-4] + ')'

	# Disk
	if crit.has_key('DSK'):
		if req[-1] == ')':
			req += ' && '
		req += '('
		for dsk in crit['DSK']:
			comp, val, unit = dsk
			req += "Disk %s %d && " % (cdeserial[comp], int(val)*sdeserial[unit])
		req = req[:-4] + ')'

	# Host name
	vm_sel = []
	if crit.has_key('HST'):
		for hst in crit['HST']:
			comp, val = hst
			for vm in nodes:
				m = re.search(val, vm)
				if m:
					if comp == 'M':
						vm_sel.append(vm)
				else:
					if comp == 'NM':
						vm_sel.append(vm)

	# Filter slots
	if crit.has_key('SLT'):
		for slt in crit['SLT']:
			comp, selname = slt
			sel = CondorNodeSel.objects.filter(label = selname)[0]
			data = marshal.loads(base64.decodestring(sel.nodeselection))
			if not crit.has_key('HST') and comp == 'NB':
				vm_sel = nodes
			for n in data:
				# Belongs to
				if comp == 'B':
					vm_sel.append(n)
				else:
					if n in vm_sel:
						try:
							while 1:
								vm_sel.remove(n)
						except:
							pass

	# Finally build host selection
	if vm_sel:
		if req[-1] == ')':
			req += ' && '
		req += '('
		for vm in vm_sel:
			req += "Name == '%s' || " % vm
		req = req[:-4] + ')'
	
	req += ')'

	return req

def get_requirement_string_from_selection(selName):
	"""
	Returns Condor's requirement string for a *SELECTION*
	@param selName - string: name of node selection
	"""

	sel = CondorNodeSel.objects.filter(label = selName, is_policy = False)[0]
	hosts = marshal.loads(base64.decodestring(sel.nodeselection))
	req = 'Requirements = (('
	for host in hosts:
		req += "Name == '%s' || " % host
	req = req[:-3] + '))'

	return req

