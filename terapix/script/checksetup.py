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

import sys, os, string, stat
os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from django.conf import settings
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
RWXALL = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO

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

	def endGroup(self):
		self.group = None

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

	# Default config types
	logger.log('Adding default configuration file types')
	for type in ('config', 'param'):
		try:
			t = ConfigType(name = type)
			t.save()
			logger.log('Added type ' + type)
		except IntegrityError:
			# Already existing
			pass

	# Check user profile
	user = User.objects.all()[0]
	try:
		p = user.get_profile()
	except:
		# Create a new profile
		groups = user.groups.all()
		if not groups:
			# No user groups; add default one
			grp = Group(name = user.username)
			try:
				grp.save()
			except IntegrityError:
				# Already exits
				grp = Group.objects.filter(name = user.username)[0]
			user.groups.add(grp)
		else:
			grp = groups[0]

		p = SiteProfile(user = user, dflt_group = grp, dflt_mode = '640')
		p.save()

	# Default configuration files
	logger.log('Adding default configuration files')
	t = ConfigType.objects.filter(name = 'config')[0]
	for plugin in manager.plugins:
		try:
			name = os.path.join(settings.TRUNK, 'terapix', 'youpi', 'plugins', 'conf', plugin.id + '.conf.default')
			f = open(name, 'r')
			config = string.join(f.readlines())
			f.close()
		except IOError, e:
			print "!", name

		k = Processing_kind.objects.filter(name__exact = plugin.id)[0]
		try:
			m = ConfigFile(kind = k, name = 'default', content = config, group = p.dflt_group, mode = p.dflt_mode, type = t, user = user)
			m.save()
		except:
			# Cannot save, already exits: do nothing
			pass

	# Add default parameter file for Sextractor (sex.param.default)

	try:
		name = os.path.join(settings.TRUNK, 'terapix', 'youpi', 'plugins', 'conf', 'sex.param.default')
		f = open(name, 'r')
		param = string.join(f.readlines())
		f.close()
	except IOError, e:
		print "!", name

	try:
		t = ConfigType.objects.filter(name = 'param')[0]
		k = Processing_kind.objects.filter(name__exact = 'sex')[0]
		m = ConfigFile(kind = k, name = 'default', content = param, type = t, user = user, group = p.dflt_group, mode = p.dflt_mode)
		m.save()
	except:
		# Cannot save, already exits: do nothing
		pass


def setup_users():
	logger.setGroup('users', 'Check if there is at least one user')

	users = User.objects.all().order_by('username')
	if users:
		logger.log("Found %d users" % len(users))
	else:
		logger.log("No user found, adding a default one (%s)" % YOUPI_USER)
		# Add at least one user
		user = User.objects.create_user(username = YOUPI_USER, email = 'root@localhost', password = YOUPI_USER)
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
		logger.log("Policy 'ALL' found")

def check_local_conf():
	"""
	The settings.py conf file always try to import a local_conf.py file which may
	be used for local settings. Since this local_conf.py is not versionned at all,
	this function ensure that at least an empty local_conf.py file is available 
	to prevent any import issues.
	"""
	logger.endGroup()
	try:
		import terapix.local_conf
	except ImportError:
		f = open(os.path.join(os.getcwd(), 'local_conf.py'), 'w')
		f.write("# Add your local customizations here\n");
		f.close()
		logger.log('Created local_conf.py')

def setup_tmp_media():
	"""
	Check that settings.MEDIA_TMP directory exists and is worldwide writable
	"""
	logger.endGroup()
	mediadir = os.path.join(settings.MEDIA_ROOT, settings.MEDIA_TMP)
	if not os.path.exists(mediadir):
		os.mkdir(mediadir)
		os.chmod(mediadir, RWXALL)
		logger.log("Created missing %s directory" % settings.MEDIA_TMP)
	else:
		# check permissions
		try:
			os.chmod(mediadir, RWXALL) 
			logger.log("Permissions OK for %s" % mediadir)
		except OSError, e:
			logger.log("! Unable to set 0777 permissions to '%s' directory.\nPlease set the permissions accordingly." % mediadir)
			sys.exit(1)

def setup():
	setup_users()
	setup_db()
	setup_policies()
	check_local_conf()
	setup_tmp_media()

def run():
	global logger 
	logger = Logger()
	setup()
	
if __name__ == '__main__':
	run()
