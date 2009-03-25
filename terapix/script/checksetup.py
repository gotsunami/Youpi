
import sys, os

YOUPI_USER = 'youpiadm'

def setup_users():
	print "Check there is at least one user...",
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
	setup_users()
	setup_policies()
	

if __name__ == '__main__':
	os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
	if '..' not in sys.path:
		sys.path.insert(0, '..')

	from django.contrib.auth.models import User
	from terapix.youpi.models import *

	setup()
