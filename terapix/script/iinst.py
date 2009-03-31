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

import MySQLdb, pprint, random, pyfits, re, glob, string, os, math

connectionObject = MySQLdb.connect(host='dbterapix.iap.fr', user='semah', passwd='s19e5m13a1h8', db='spica2')
if(connectionObject):
	print "connected to database";
	c = connectionObject.cursor()
	#youpi_instrument DATABASE INGESTION
	c.execute("""set autocommit=0""");
	c.execute("""start transaction""");
	c.execute(""" insert into youpi_instrument set name='STACK'""");
	c.execute(""" insert into youpi_instrument set name='MEGACAM'""");
	tes=c.execute(""" insert into youpi_instrument set name='WIRCAM'""");
	if(tes):
		connectionObject.commit();
		print 'transaction done';
	else:
		connectionObject.rollback();
		print 'transaction undone';
else:
	print 'not connected to database';
	
connectionObject.close();
