# vim: set ts=4

import sys
from pluginmanager import Spica2Plugin

class Swarp(Spica2Plugin):
	"""
	Plugin for Swarp.

	"""
	def __init__(self):
		Spica2Plugin.__init__(self)

		#
		# REQUIRED members (see doc/writing_plugins/writing_plugins.pdf)
		#
		self.id = 'swarp'
		self.optionLabel = 'Resampling - Coaddition'
		self.description = 'Swarp'
		# Item prefix in shopping cart. This should be short string since
		# the item ID can be prefixed by a user-defined string
		self.itemPrefix = 'SW'
		self.index = 30

		# Main template, rendered in the processing page
		#self.template = 'plugin_swarp.html'
		# Template for custom rendering into the shopping cart
		self.itemCartTemplate = 'plugin_swarp_item_cart.html'
		# Custom javascript
		self.jsSource = 'plugin_swarp.js'

		# Decomment to disable the plugin
		#self.enable = False
