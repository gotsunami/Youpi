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
# ##############################################################################

"""
Set of functions to deal with authentication within Youpi.
"""

from django.db import models
#
import re
from terapix.exceptions import *
from types import *

bits_range = [0, 2, 4, 6]

class Permissions:
	class user: pass
	class group: pass
	class others: pass

	def __init__(self, mode):
		self.mode = mode

		# Various sanity checks
		try: mode = int(mode)
		except ValueError:
			raise PermissionsConvertError, 'Input permissions must be an integer (3 octal digits)'

		mode = str(mode)
		if len(mode) != 3:
			raise PermissionsConvertError, 'Input permissions must have exactly 3 octal digits'

		bits = [int(b) for b in re.findall(r'\d', mode)]
		if True in [m > 6 for m in bits]:
			raise PermissionsConvertError, 'Mode bit must not be greater than 6'

		
		if False in [m in bits_range for m in bits]:
			raise PermissionsConvertError, 'Mode bit must be one of 0, 2, 4, 6'

		self.user.read = self.user.write = False
		self.group.read = self.group.write = False
		self.others.read = self.others.write = False

		# User
		if bits[0] == 4 or bits[0] == 6:
			self.user.read = True
		if bits[0] == 2 or bits[0] == 6:
			self.user.write = True

		# Group
		if bits[1] == 4 or bits[1] == 6:
			self.group.read = True
		if bits[1] == 2 or bits[1] == 6:
			self.group.write = True

		# Others
		if bits[2] == 4 or bits[2] == 6:
			self.others.read = True
		if bits[2] == 2 or bits[2] == 6:
			self.others.write = True

	def toJSON(self):
		"""
		Permissions instance to JSON conversion
		"""
		return {
			'user' : {'read': int(self.user.read), 'write': int(self.user.write)}, 
			'group' : {'read': int(self.group.read), 'write': int(self.group.write)}, 
			'others' : {'read': int(self.others.read), 'write': int(self.others.write)}
		}

	def toOctal(self):
		"""
		Permissions instance to Octal conversion
		"""
		u = g = o = 0
		if self.user.read: u += 4
		if self.user.write: u += 2
		if self.group.read: g += 4
		if self.group.write: g += 2
		if self.others.read: o += 4
		if self.others.write: o += 2

		return "%s%s%s" % (u, g, o)

	def __get_unix_mode(self):
		"""
		Builds and returns a UNIX-like mode string
		For example: rw-r----- for 640 access
		"""
		unix = ''
		if self.user.read: 		unix += 'r'
		else: unix += '-'
		if self.user.write: 	unix += 'w'
		else: unix += '-'
		unix += '-'

		if self.group.read: 	unix += 'r'
		else: unix += '-'
		if self.group.write: 	unix += 'w'
		else: unix += '-'
		unix += '-'

		if self.others.read: 	unix += 'r'
		else: unix += '-'
		if self.others.write: 	unix += 'w'
		else: unix += '-'
		unix += '-'

		return unix

	def __str__(self):
		return "%s (%s)" % (self.__get_unix_mode(), self.toOctal())

	def __repr__(self):
		return "<Permission %s: %s>" % (self.toOctal(), self.__get_unix_mode())


def read_proxy(request, results):
	"""
	Read permissions proxy.

	Deals with Youpi's permissions tranparently by returning appropriate 
	content. Use it from your views by encapsulating your Django model queries:

	Instead of writing:
	tags = Tag.objects.all()

	Write instead:
	tags, filtered = read_proxy(request, Tag.objects.all())

	@param request Django request instance
	@param results Django's query QuerySet
	@return A tuple (subset, filtered)
	"""

	if type(results) != models.query.QuerySet:
		raise TypeError, 'Result set must be a Django QuerySet'

	if not results: return results, False
	if not isinstance(results[0], models.Model):
		raise TypeError, 'Must be a list of Django Model instances'

	try:
		m = results[0].mode
	except AttributeError, e:
		raise PermissionsError, 'This result set does not support permissions'

	allow = []
	filtered = False
	for r in results:
		p = Permissions(r.mode)
		if not p.others.read:
			if r.user == request.user and p.user.read: 
				allow.append(r)
				continue
			if r.group in request.user.groups.all() and p.group.read: 
				allow.append(r)
				continue
		else:
			allow.append(r)
			continue
		# Access not granted
		filtered = True
		
	return allow, filtered

def write_proxy(request, model, delete = False):
	"""
	Write permissions proxy.

	Deals with Youpi's permissions tranparently by returning appropriate 
	content. Use it from your views by encapsulating your Django model queries:

	Instead of writing:
	tag.save() or tag.delete()

	Write instead:
	write_proxy(request, tag) or write_proxy(request, tag, delete = True)

	@param request Django request instance
	@param model Django model
	@param delete Delete action (instead of save/update) when true [default: False]
	@return boolean: True if data successfully written
	"""

	if not isinstance(model, models.Model):
		raise TypeError, 'model parameter must a Django Model'

	try:
		m = model.mode
	except AttributeError, e:
		raise PermissionsError, 'This result set does not support permissions'

	p = Permissions(model.mode)

	write = False
	if (model.user == request.user and p.user.write) or \
		(model.group in request.user.groups.all() and p.group.write) or \
		p.others.write:
		write = True

	if write:
		if delete: model.delete()
		else: model.save()

	return write

