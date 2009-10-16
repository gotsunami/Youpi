from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from optparse import make_option
import os, os.path, sys
import string

class Command(BaseCommand):
	option_list = BaseCommand.option_list + (
		make_option('--wsgi', dest = 'wsgi', default = False, action = 'store_true', 
			help="Generates the WSGI configuration file to use with your web server (for production)."),
		make_option('--apache', action = 'store_true', dest = 'apache', default = False,
			help="Show the Apache directives to add to your httpd.conf to setup Youpi for production."),
	)
	help = "Check Youpi setup"

	def setup_dist(self, filename, **replace):
		"""
		Performs -dist file substitutions.
		"""
		pwd = os.getcwd()
		install_path = pwd[:pwd.rfind(os.sep)]
		deploy_path = os.path.join(install_path, 'deploy')
		target_full = os.path.join(deploy_path, filename)

		try:
			dist = open(os.path.join(deploy_path, filename + '-dist'))
			try:
				content = dist.readlines()
			finally:
				dist.close()
		except IOError, e:
			raise CommandError("%s" % e)

		t = string.Template(''.join(content))
		try:
			out = open(target_full, 'w')
			content = (t.substitute(installation_path = install_path, deploy_path = deploy_path, 
				target_full = target_full, **replace))
			out.write(content)
		except IOError, e:
			raise CommandError("%s" % e)
		finally:
			out.close()

		print "The file %s\nhas been successfully generated to match your configuration." % target_full
		return content

	def handle(self, *args, **options):
		from django.conf import settings
		wsgi = options['wsgi']
		apache = options['apache']
		
		if not (wsgi or apache):
			from django.core.management import call_command
			# First checks that all models are synced
			print "Running syncdb..."; sys.stdout.flush()
			call_command('syncdb')
			# Check for schema evolutions
			call_command('evolve', execute = True)

			# Now check setup
			print "Running checksetup..."
			from terapix.script import checksetup
			checksetup.run()
			return

		if wsgi:
			self.setup_dist('django.wsgi', tmp = '/tmp')
			print "You may run\n\n  python manage.py checksetup --apache\n\nto get Apache config setup information."

		if apache:
			content = self.setup_dist('youpi.conf')
			print "You may add this to your httpd.conf:\n\n%s" % content
