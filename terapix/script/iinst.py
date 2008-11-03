#!/usr/bin/env python 

import MySQLdb, pprint, random, pyfits, re, glob, string, os, math

connectionObject = MySQLdb.connect(host='dbterapix.iap.fr', user='semah', passwd='s19e5m13a1h8', db='spica2')
if(connectionObject):
	print "connected to database";
	c = connectionObject.cursor()
	#spica2_instrument DATABASE INGESTION
	c.execute("""set autocommit=0""");
	c.execute("""start transaction""");
	c.execute(""" insert into spica2_instrument set name='STACK'""");
	c.execute(""" insert into spica2_instrument set name='MEGACAM'""");
	tes=c.execute(""" insert into spica2_instrument set name='WIRCAM'""");
	if(tes):
		connectionObject.commit();
		print 'transaction done';
	else:
		connectionObject.rollback();
		print 'transaction undone';
else:
	print 'not connected to database';
	
connectionObject.close();
