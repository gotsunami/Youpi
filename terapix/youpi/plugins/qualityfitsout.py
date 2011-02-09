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
