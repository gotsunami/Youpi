# vim: set ts=4

import sys
from pluginmanager import ProcessingPlugin

class QualityFitsIn(ProcessingPlugin):
	"""
	Plugin for QualityFitsOut.

	Last Quality Evaluation.
	- Need co-added images
	"""

	def __init__(self):
		ProcessingPlugin.__init__(self)

		#
		# REQUIRED members (see doc/writing_plugins/writing_plugins.pdf)
		#
		self.id = 'fitsout'
		self.optionLabel = 'Last Quality Evaluation'
		self.description = 'QualiyFits-Out processing'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'QFO'
		self.index = 40

		# Main template, rendered in the processing page
#		self.template = 'plugin_sextractor.html'
		# Template for custom rendering into the shopping cart
		self.itemCartTemplate = 'plugin_qualityfitsout_item_cart.html'
		# Custom javascript
		self.jsSource = 'plugin_qualityfitsout.js'

		# Decomment to disable the plugin
		self.enable = False

	def process(self, post):
		return 'OUT'
