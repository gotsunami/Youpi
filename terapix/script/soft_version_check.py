#!/usr/bin/env python 

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

from types import *
import MySQLdb
import os, os.path
import sys, time, string
import marshal, base64, zlib
import socket
import re, shutil
#
sys.path.insert(0, '..')
from settings import *
from DBGeneric import *

NULLSTRING = ''
userData = {}

g = None

# Custom exceptions
class WrapperError(Exception): pass

def getNowDateTime(lt = time.time()):
	"""
	Returns local date time
	"""
	return "%4d-%02d-%02d %02d:%02d:%02d" % time.localtime(lt)[:6]

def process(userData):
	"""
	Try to get software versions.
	"""

	user_id = userData['UserID']
	node = userData['Node']
	key = 'software_version'
	res = g.execute("SELECT id, data FROM youpi_miscdata WHERE `key`=\"%s\"" % key)
	group_id = g.execute("SELECT dflt_group_id FROM youpi_siteprofile WHERE user_id=%s" % user_id)[0][0]

	versions = {}
	for soft in SOFTS:
		job = os.popen("%s %s" % (soft[1], soft[2]))
		try:
			versions[soft[0]] = re.search(soft[3], job.readlines()[0]).group(1)
		except:
			versions[soft[0]] = 0
		job.close()

	if len(res):
		# Old data found, updates
		try:
			data = marshal.loads(base64.decodestring(str(res[0][1])))
			data[node] = versions

			g.begin()
			g.setTableName('youpi_miscdata')
			g.update(	data = base64.encodestring(marshal.dumps(data)).replace('\n', ''),
						wheres = {'id': res[0][0]})
			g.con.commit()
		except Exception, e:
			raise WrapperError, e
	else:
		# No data related to versions
		try:
			g.begin()
			g.setTableName('youpi_miscdata')
			g.insert(	key = key,
						user_id = user_id,
						group_id = group_id,
						data = base64.encodestring(marshal.dumps({node : versions})).replace('\n', ''))
			g.con.commit()
		except Exception, e:
			raise WrapperError, e

	print versions
	

if __name__ == '__main__':
	# Connection object to MySQL database 
	try:
		db = DB(host = DATABASE_HOST,
				user = DATABASE_USER,
				passwd = DATABASE_PASSWORD,
				db = DATABASE_NAME)

		# Beginning transaction
		g = DBGeneric(db.con)

		# Related to Condor transfer_ouput_file
		try:
			shutil.copyfile('DBGeneric.pyc', '/tmp/DBGeneric.pyc')
		except:
			pass

		#
		# De-serialize data passed as a string into arg 1
		#
		userData = marshal.loads(base64.decodestring(sys.argv[1]))
		process(userData)

	except MySQLdb.DatabaseError, e:
		print "Error:", e
		sys.exit(1)

	except IndexError, e:
		print "Error:", e
		sys.exit(1)
