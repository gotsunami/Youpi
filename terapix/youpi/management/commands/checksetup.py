from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from optparse import make_option

class Command(BaseCommand):
	help = "Check Youpi setup"

	def handle(self, *args, **options):
		from django.conf import settings
		from terapix.script import checksetup

		checksetup.run()
