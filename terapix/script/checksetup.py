
import sys, os

YOUPI_USER = 'youpiadm'

def log(group, msg):
	"""
	Prints a formatted log message to stdout.
	@param group string group name
	@param msg string message to display
	"""
	print "[%s] %s" % (group, msg)

def sub(msg):
	print " * %s" % msg

def setup_db():
	"""
	Database setup.
	"""

	log('init', 'setup database with mandatoy data')

	#surveys = Survey.objects.all()
	#if surveys:
		# Check that MEGACAM and WIRCAM instruments exist
#		instrus = Instrument.objects.filter(Q(name = 'MEGACAM') | Q(name = 'WIRCAM'))

	# Default first quality evaluation comments
	sub('Adding default first quality evaluation comments')
	comments = ('---', 'Poor seeing (>1.2)', 'Astrometric keyword problem: some CCDs off',
				'D3-i rejection', 'Galaxy counts below/above expectations', 'Some CCDs or half-CCDs missing',
				'Defocus?', 'PSF/Object image doubled', 'Diffuse light contamination', 'Unusual PSF anisotropy pattern',
				'Elongated image', 'Unusual rh-mag. diagram', 'Unusual background image', 'Telescope lost guiding?')

	for com in comments:
		try:
			c = FirstQComment(comment = com)
			c.save()
		except:
			# Already in DB
			pass

	# Default processing kinds

	print 'OK'


def setup_users():
	print "Check if there is at least one user...",
	users = User.objects.all().order_by('username')
	if users:
		print "OK (%d)" % len(users)
	else:
		# Add at least one user
		user = User.objects.create_user(username = YOUPI_USER, password = YOUPI_USER)
		user.is_staff = False
		user.is_active = False
		user.save()

def setup_policies():
	print "Adding defaut ALL condor policy...",
	pols = CondorNodeSel.objects.filter(label = 'ALL', is_policy = True)
	if not len(pols):
		# Not existing
		pol = CondorNodeSel(label = 'ALL', user = User.objects.all()[0], is_policy = True)
		# Select all nodes matching at least 1 Mb of RAM (so this define a policy which selects all
		# cluster nodes
		pol.nodeselection = 'MEM,G,1,M'
		pol.save()
	print "OK"	

def setup():
	setup_db()
	setup_users()
	setup_policies()
	

if __name__ == '__main__':
	os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
	if '..' not in sys.path:
		sys.path.insert(0, '..')

	try:
		from django.contrib.auth.models import User
		from django.db.models import Q
		from terapix.youpi.models import *
	except ImportError:
		print 'Please run this command from the terapix subdirectory.'
		sys.exit(1)

	setup()
