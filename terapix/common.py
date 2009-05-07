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

from terapix.exceptions import FileNotFoundError
import os.path

def findPath(file):
	for path in os.environ['PATH'].split(':'):
		abspath = os.path.join(path, file)
		if os.path.exists(abspath):
			if os.path.isfile(abspath):
				return path

	raise FileNotFoundError, "File %s not found in paths: %s" % (file, os.environ['PATH'])

