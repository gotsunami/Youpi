#!/usr/bin/env python 

import MySQLdb, pprint, random, pyfits, re, glob, numpy, string, os, math

connectionObject = MySQLdb.connect(host='localhost', user='semah', passwd='', db='spica');

if(connectionObject):
	print "connected to database";
	c = connectionObject.cursor();
	c.execute("""set autocommit = 0""");

	os.chdir('/home/semah/youpi/image');
	k = glob.glob('*.fits');#creation de la liste repondant au format FITS
	#print k
	while k <> []:
		cpt = 1;
		fitsfile = k.pop();#fitsfile est l'element que l'on enleve a la liste de fits pour etre processer
		r = pyfits.open(fitsfile);
		h1 = r[1].header;
		
		#DBinstrument
		instrname = h1['instrume'];
		telescope = h1['telescop'];
		detector = h1['detector'];
		
		#DBchannel
		chaname = h1['filter'];
		
		#DBrun
		runame = h1['runid'];
		
		#RUN DATABASE INGESTION
		c.execute("""start transaction""");
		test = c.execute("""select Name from spica_run where name=\'%s\'""" %(runame));
		if (test == 0):
			if (detector == 'MegaCam' and  telescope == 'CFHT 3.6m' and instrname == 'MegaPrime'):
				test1 = c.execute(""" insert into spica_run set Name =\'%s\',instrument_id = 2 """ %(runame));
				if (test1):
					connectionObject.commit();
					print 'transaction done';
				else:
					connectionObject.rollback();
					print 'transaction undone';
			elif (detector == 'WIRCam' and telescope == 'CFHT 3.6m' and instrname == 'WIRCam'):
				test2 = c.execute(""" insert into spica_run set Name =\'%s\',instrument_id = 3 """ %(runame));
				if (test2):
					connectionObject.commit();
					print 'transaction done';
				else:
					connectionObject.rollback();
					print 'transaction undone';


else:
	print 'not connected to database';
	
connectionObject.close();
