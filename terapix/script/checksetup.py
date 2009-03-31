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

import sys, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from django.contrib.auth.models import User
	from django.db.models import Q
	from django.db import IntegrityError
	#
	from terapix.youpi.models import *
	from terapix.youpi.pluginmanager import PluginManager
except ImportError:
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)


YOUPI_USER = 'youpiadm'

class LoggerError(Exception): pass

class Logger:
	def __init__(self):
		self.group = None
		self.title = None
		self.indent = 3

	def setGroup(self, group, title):
		"""
		Prints a formatted log message to stdout.
		@param group string group name
		@param title string group's title
		"""
		self.group = group
		self.title = title
		print "[%s] %s" % (group, title)

	def log(self, msg):
		if self.group:
			print "%s%s" % (' ' * self.indent, msg)
		else:
			print msg

def setup_db():
	"""
	Database setup.
	"""

	logger.setGroup('init', 'Setup database with mandatoy data')

	#surveys = Survey.objects.all()
	#if surveys:
		# Check that MEGACAM and WIRCAM instruments exist
#		instrus = Instrument.objects.filter(Q(name = 'MEGACAM') | Q(name = 'WIRCAM'))

	# Default first quality evaluation comments
	logger.log('Adding default first quality evaluation comments')
	comments = ('---', 'Poor seeing (>1.2)', 'Astrometric keyword problem: some CCDs off',
				'D3-i rejection', 'Galaxy counts below/above expectations', 'Some CCDs or half-CCDs missing',
				'Defocus?', 'PSF/Object image doubled', 'Diffuse light contamination', 'Unusual PSF anisotropy pattern',
				'Elongated image', 'Unusual rh-mag. diagram', 'Unusual background image', 'Telescope lost guiding?')

	for com in comments:
		try:
			c = FirstQComment(comment = com)
			c.save()
			logger.log("Added comment: '%s'" % (com))
		except IntegrityError:
			# Already in DB
			pass

	# Default processing kinds
	logger.log('Adding default processing kinds')
	manager = PluginManager()

	for plugin in manager.plugins:
		try:
			kind = Processing_kind(name = plugin.id, label = plugin.optionLabel)
			kind.save()
			logger.log('Added ' + plugin.id)
		except IntegrityError:
			# Already existing
			pass

def setup_users():
	logger.setGroup('users', 'Check if there is at least one user')

	users = User.objects.all().order_by('username')
	if users:
		logger.log("Found %d users" % len(users))
	else:
		logger.log("No user found, adding a default one (%s)" % YOUPI_USER)
		# Add at least one user
		user = User.objects.create_user(username = YOUPI_USER, password = YOUPI_USER)
		user.is_staff = False
		user.is_active = False
		user.save()

def setup_policies():
	logger.setGroup('policies', 'Checking for a defaut ALL condor policy')
	pols = CondorNodeSel.objects.filter(label = 'ALL', is_policy = True)
	if not len(pols):
		logger.log("Not found, adding an ALL policy")
		# Not existing
		pol = CondorNodeSel(label = 'ALL', user = User.objects.all()[0], is_policy = True)
		# Select all nodes matching at least 1 Mb of RAM (so this define a policy which selects all
		# cluster nodes
		pol.nodeselection = 'MEM,G,1,M'
		pol.save()
	else:
		logger.log("ALL policy found")

def setup():
	setup_db()
	setup_users()
	setup_policies()
	

if __name__ == '__main__':
	logger = Logger()
	setup()
