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

# Django settings for terapix project.

from settings_base import *

# Local configuration file (site specific)
#
HOME 			= '/usr/local/www/data'
CONDORFILE 		= '/tmp/condor.prod'
CONDOR_OUTPUT 	= '/tmp/condor.prod.out'
CONDOR_ERROR 	= '/tmp/condor.prod.error'
CONDOR_LOG 		= '/tmp/condor.prod.log'
#
PROCESSING_OUTPUT = '/data/fcix5/raid2/youpi-OUTPUT/PROD/'
FTP_URL = 'ftp://fcix5/'
#
WWW_FITSIN_PREFIX = 'http://youpix.iap.fr:9900/'
#
ADMINS = (
	('Mathias Monnerville', 'monnerville@iap.fr'),
)
#
DATABASE_NAME 		= 'spica2'
DATABASE_USER 		= 'semah'
DATABASE_PASSWORD 	= 's19e5m13a1h8'
DATABASE_HOST 		= 'dbterapix.iap.fr'
