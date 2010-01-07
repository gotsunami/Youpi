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

# vim: set ts=4

import sys
from terapix.youpi.pluginmanager import ProcessingPlugin
from terapix.exceptions import *

class QualityFitsIn(ProcessingPlugin):
	"""
	Plugin for QualityFitsOut.

	Last Quality Evaluation.
	- Need co-added images
	"""

	def __init__(self):
		ProcessingPlugin.__init__(self)

		self.id = 'fitsout'
		self.optionLabel = 'Last Quality Evaluation'
		self.description = 'QualiyFits-Out processing'
		# Item prefix in processing cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'QFO'
		self.index = 40

		# Template for custom rendering into the processing cart
		self.itemCartTemplate = 'plugin_qualityfitsout_item_cart.html'
		# Custom javascript
		self.jsSource = 'plugin_qualityfitsout.js'

	def process(self, post):
		return 'OUT'
