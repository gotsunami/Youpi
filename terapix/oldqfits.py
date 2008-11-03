#!/usr/bin/env python 

import MySQLdb, pprint, random, pyfits, re, glob, numpy, string, os, math



db = MySQLdb.connect(host='dbterapix.iap.fr', user='pipeline', passwd='pipeline', db='dbspica')
if(db):
	file = open('res.txt','w');
        print "connected to database";
	c = db.cursor()
	c.execute("""select TitreId, NoteQF from Auto_status""");
	result = c.fetchone();
	while (1):
		print (result[0],result[1]);