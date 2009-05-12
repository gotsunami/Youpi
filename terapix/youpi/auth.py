##############################################################################
#
# Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
#                    Mathias Monnerville <monnerville@iap.fr>
#                    Gregory Semah <semah@iap.fr>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.  # ##############################################################################

"""
Set of functions to deal with authentication within Youpi.
"""

import re
from terapix.exceptions import *

bits_range = [0, 2, 4, 6]

class Permissions:
	class user:
		read = write = False
	class group:
		read = write = False
	class others:
		read = write = False

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

