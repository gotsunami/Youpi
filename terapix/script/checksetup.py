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

import sys, os, string, stat, shutil
import marshal, base64, glob, zlib
os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from django.conf import settings
	from django.contrib.auth.models import User, Permission
	from django.db.models import Q
	from django.db import IntegrityError
	#
	from terapix.youpi.models import *
	from terapix.youpi.pluginmanager import ApplicationManager
	from terapix.lib.itt.instconfig import InstrumentConfig
except ImportError, e:
	print "Please run this command from the terapix subdirectory: %s" % e
	sys.exit(1)

YOUPI_USER = 'youpiadm'
RWXALL = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
manager = None # Global manager

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
	global manager
	logger.setGroup('init', 'Setup database with mandatoy data')

	# Checks for available instruments
	instrus = Instrument.objects.filter(Q(name = 'Megacam') | Q(name = 'Wircam'))
	if not instrus:
		for name in ('Megacam', 'Wircam'):
			i = Instrument(name = name)
			i.save()
			logger.log("Added instrument: '%s'" % (name))
	else:
		logger.log('Default instruments found')

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
	manager = ApplicationManager()

	for plugin in manager.plugins:
		try:
			kind = Processing_kind(name = plugin.id, label = plugin.optionLabel)
			kind.save()
			action = "Added"
		except IntegrityError:
			# Already existing, then possibliy updates label
			kind = Processing_kind.objects.filter(name = plugin.id)[0]
			kind.label = plugin.optionLabel
			kind.save()
			action = "Updated"
		logger.log("%s '%s' processing kind" % (action, plugin.id))

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

	# Adding user profile for all registered users
	users = User.objects.all()
	for user in users:
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

	user = User.objects.all()[0]

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

def setup_itt():
	"""
	Check ingestion translations tables
	"""
	instrus = Instrument.objects.filter(Q(name = 'Megacam') | Q(name = 'Wircam'))
	for ins in instrus:
		ins.name = ins.name.upper()
		ins.save()

	itts = glob.glob(os.path.join(settings.TRUNK, 'terapix', 'lib', 'itt', 'conf', '*.conf'))
	for itt in itts:
		name = os.path.basename(itt)[:-5].upper()
		inst = Instrument.objects.filter(name = name)
		# Parse it and get dictionnary mapping
		ic = InstrumentConfig(itt)
		content = ic.parse()
		zcontent = base64.encodestring(zlib.compress(marshal.dumps(content), 9)).replace('\n', '')
		if inst:
			# Instrument already existing
			inst = inst[0]
			inst.itt = zcontent
			inst.save()
			logger.log("Updated ITT for instrument %s" % name)
		else:
			inst = Instrument(name = name, itt = zcontent)
			inst.save()
			logger.log("Added instrument %s and ITT" % name)

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

def setup_default_condor_setup():
	"""
	Checks that all users have a default condor setup in their profile (for every plugin).
	Already existing values will remain untouched, missing default setup will be added.
	"""
	logger.setGroup('condor', 'Checking that all users have a default condor setup in their profile')
	users = User.objects.all()
	for user in users:
		p = user.get_profile()
		if len(p.dflt_condor_setup) == 0:
			# No default Condor setup rules
			logger.log("Missing Condor setup in %s's profile" % user.username)
			setup = {}
			for plugin in manager.plugins:
				# Default is to use the ALL policy
				setup[plugin.id] = {'DB': 'policy', 'DS': '', 'DP': 'ALL'}
			p.dflt_condor_setup = base64.encodestring(marshal.dumps(setup)).replace('\n', '')
			p.save()
			logger.log("Added default Condor setup rules for %s" % user.username)
		else:
			# Ok, existing but maybe default rules for some (newly created?) plugins are missing
			setup = marshal.loads(base64.decodestring(p.dflt_condor_setup))
			updated = False
			for plugin in manager.plugins:
				if not setup.has_key(plugin.id):
					setup[plugin.id] = {'DB': 'policy', 'DS': '', 'DP': 'ALL'}
					updated = True
			p.dflt_condor_setup = base64.encodestring(marshal.dumps(setup)).replace('\n', '')
			p.save()
			if updated:
				logger.log("Updated default Condor setup rules for %s" % user.username)
			else:
				logger.log("Default Condor setup rules for %s look good" % user.username)

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

def setup_icons():
	"""
	Checks that all plugins have an icon in img/16x16, img/32x32 and img/48x48 directories (for every theme).
	If not found, copy plugin.png to `plugin.id`.png
	"""
	logger.endGroup()
	logger.setGroup('icons', 'Checking that all plugins have a 16x16, 32x32 and 48x48 existing icon')
	tdirs = glob.glob(os.path.join(settings.MEDIA_ROOT, 'themes', '*'))
	for plugin in manager.plugins:
		for td in tdirs:
			for res in ('16x16', '32x32', '48x48'):
				dst = os.path.join(td, 'img', res, plugin.id + '.png')
				if not os.path.exists(dst):
					logger.log("Plugin '%s': no suitable icon found in %s, adding one..." % (plugin.id, res))
					shutil.copy(os.path.join(settings.MEDIA_ROOT, 'themes', 'default', 'img', res, 'plugin.png'), dst)

def check_plugin_permissions():
	"""
	Add custom can_use_plugin_* permissions for registered plugins
	"""
	logger.endGroup()
	logger.setGroup('permissions', 'check custom permissions for registered plugins')
	# Get permission content_type from existing can_submit_jobs permission
	p = Permission.objects.filter(codename = 'can_submit_jobs')[0]
	ct = p.content_type
	for plugin in manager.plugins:
		perm_name = 'can_use_plugin_' + plugin.id
		p = Permission.objects.filter(codename = perm_name)
		if p:
			logger.log("Permission %s found" % perm_name)
		else:
			np = Permission(name = ("Can use %s plugin" % plugin.description)[:50], content_type = ct, codename = perm_name)
			np.save()
			logger.log("Added %s permission" % perm_name)

def setup():
	setup_users()
	setup_db()
	setup_itt()
	setup_policies()
	setup_default_condor_setup()
	check_local_conf()
	setup_tmp_media()
	setup_icons()
	check_plugin_permissions()

def run():
	global logger 
	logger = Logger()
	setup()
	
if __name__ == '__main__':
	run()
