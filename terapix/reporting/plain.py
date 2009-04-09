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

"""
Class to generate plain text reports
"""

from types import ListType, TupleType
import string

class PlainTextReport:
	def __init__(self, data = []):
		if type(data) != ListType and type(data) != TupleType:
			raise TypeError, "data must be a list or tuple"

		# Explicit cast
		if type(data) == TupleType:
			data = list(data)

		self.data = data

	def __repr__(self):
		return "<Plain text report, data length=%lu>" % len(self.data)

	def __str__(self):
		for k in range(len(self.data)):
			self.data[k] = string.join(["%-20s" % str(col) for col in self.data[k]], ' ')
		return string.join(self.data, '\n')
