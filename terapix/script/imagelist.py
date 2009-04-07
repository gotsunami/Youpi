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

"""
Returns a list of all ingested images
"""

import sys, os, string
os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from django.db import IntegrityError
	#
	from terapix.settings import *
	from terapix.youpi.models import *
except ImportError:
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)

def main():
	images = Image.objects.all().order_by('name')
	print "Data paths for %d images:" % len(images)
	sys.stdout.flush()

	k = 0
	for img in images:
		print "%05d %s%s.fits" % (k, img.path, img.name)
		sys.stdout.flush()
		k += 1

if __name__ == '__main__':
	main()
