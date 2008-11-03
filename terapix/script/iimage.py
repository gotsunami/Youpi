#/usr/bin/env python 

import MySQLdb, pprint, random, pyfits, re, glob, numpy, string, os, math

connectionObject = MySQLdb.connect(host='localhost', user='semah', passwd='', db='spica');
if(connectionObject):
        print "connected to database";
	c = connectionObject.cursor();
	c.execute("""set autocommit = 0""");

	
	os.chdir('/home/semah/youpi/image');
	k = glob.glob('*.fits');

	while k <> []:
		c.execute("""start transaction""");

		fitsfile = k.pop();

		mj = fitsfile.replace('.fits','');

		#print mj;

		test = c.execute("""select name from spica_image where name =\'%s\' """%(mj));

		if (test == 1):
		
			print 'l\'spica_image nommee '+fitsfile+' existe deja dans la base';

		elif(test == 0):
		
			print 'l\'spica_image nommee '+fitsfile+' va etre ingeree par la base';

			s=re.search('_weight.fits',fitsfile);

			if s:
				print "Attention WEIGHTMAP"
				break
			
			r = pyfits.open(fitsfile);
			h1 = r[1].header;
			
			instrname = h1['instrume'];
			telescope = h1['telescop'];
			detector = h1['detector'];
			chaname = h1['filter'];
			runame = h1['runid'];
			
			#MULTIPOLYGON CALCULATION
			poly = [];
			for i in range(1,len(r)):
				
				pix1,pix2 = r[i].header['CRPIX1'],r[i].header['CRPIX2']
				val1,val2 =  r[i].header['CRVAL1'],r[i].header['CRVAL2']
				cd11,cd12,cd21,cd22 = r[i].header['CD1_1'],r[i].header['CD1_2'],r[i].header['CD2_1'],r[i].header['CD2_2']
				nax1,nax2 = r[i].header['NAXIS1'],r[i].header['NAXIS2']
				
				x1,y1,x2,y2,x3,y3,x4,y4 = 1 - pix1, 1 - pix2, nax1 - pix1, 1 - pix2, nax1 - pix1, nax2 - pix2, 1 - pix1, nax2 - pix2
				
				ra1,dec1,ra2,dec2,ra3,dec3,ra4,dec4 = val1+cd11*x1+cd12*y1,val2+cd21*x1+cd22*y1,val1+cd11*x2+cd12*y2,val2+cd21*x2+cd22*y2,val1+cd11*x3+cd12*y3,val2+cd21*x3+cd22*y3,val1+cd11*x4+cd12*y4,val2+cd21*x4+cd22*y4
				
				p = [ra1,dec1,ra2,dec2,ra3,dec3,ra4,dec4,ra1,dec1]

				poly.append(p);
			
			testa = c.execute("""select Name from spica_run where name=\'%s\'""" %(runame));

			m = fitsfile.replace('.fits','');

			if (testa == 1):
			
				if (detector == 'MegaCam' and  telescope == 'CFHT 3.6m' and instrname == 'MegaPrime'):
					print m, 'MegaCam';
						
					c.execute("""select id from spica_run where instrument_id = 2 and Name =\'%s\'  """ %(runame));

					rows = c.fetchone();
					print rows;

					c.execute("""select id from spica_channel where instrument_id = 2 and Name =\'%s\'  """ %(chaname));

					row = c.fetchone();
					print row

					c.execute("""insert into spica_image set run_id = \'%s\',calibrationkit_id = 1,instrument_id = 2, channel_id = \'%s\',Name = \'%s\' """ %(rows[0],row[0],m));
					
		
		
				elif (detector == 'WIRCam' and telescope == 'CFHT 3.6m' and instrname == 'WIRCam'):
					print m,'WIRCam';
					

					c.execute("""select id from spica_run where instrument_id = 3 and Name = \'%s\'  """ %(runame));

					rows = c.fetchone();
					print rows
					
					c.execute("""select id from spica_channel where instrument_id = 3 and Name = \'%s\'  """ %(chaname));

					row = c.fetchone();
					print row

					c.execute("""insert into spica_image set run_id = \'%s\',calibrationkit_id = 2,instrument_id = 3,channel_id = \'%s\',Name = \'%s\' """ %(rows[0],row[0],m));

			connectionObject.commit();
	connectionObject.close();
else:
        print 'not connected to database';


"""
pour megacam


,SkyFootPrint = GeomFromText("MultiPolygon(((%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s)))")


,poly[0][0],poly[0][1],poly[0][2],poly[0][3],poly[0][4],poly[0][5],poly[0][6],poly[0][7],poly[0][8],poly[0][9],poly[1][0],poly[1][1],poly[1][2],poly[1][3],poly[1][4],poly[1][5],poly[1][6],poly[1][7],poly[1][8],poly[1][9],poly[2][0],poly[2][1],poly[2][2],poly[2][3],poly[2][4],poly[2][5],poly[2][6],poly[2][7],poly[2][8],poly[2][9],poly[3][0],poly[3][1],poly[3][2],poly[3][3],poly[3][4],poly[3][5],poly[3][6],poly[3][7],poly[3][8],poly[3][9],poly[4][0],poly[4][1],poly[4][2],poly[4][3],poly[4][4],poly[4][5],poly[4][6],poly[4][7],poly[4][8],poly[4][9],poly[5][0],poly[5][1],poly[5][2],poly[5][3],poly[5][4],poly[5][5],poly[5][6],poly[5][7],poly[5][8],poly[5][9],poly[6][0],poly[6][1],poly[6][2],poly[6][3],poly[6][4],poly[6][5],poly[6][6],poly[6][7],poly[6][8],poly[6][9],poly[7][0],poly[7][1],poly[7][2],poly[7][3],poly[7][4],poly[7][5],poly[7][6],poly[7][7],poly[7][8],poly[7][9],poly[8][0],poly[8][1],poly[8][2],poly[8][3],poly[8][4],poly[8][5],poly[8][6],poly[8][7],poly[8][8],poly[8][9],poly[9][0],poly[9][1],poly[9][2],poly[9][3],poly[9][4],poly[9][5],poly[9][6],poly[9][7],poly[9][8],poly[9][9],poly[10][0],poly[10][1],poly[10][2],poly[10][3],poly[10][4],poly[10][5],poly[10][6],poly[10][7],poly[10][8],poly[10][9],poly[11][0],poly[11][1],poly[11][2],poly[11][3],poly[11][4],poly[11][5],poly[11][6],poly[11][7],poly[11][8],poly[11][9],poly[12][0],poly[12][1],poly[12][2],poly[12][3],poly[12][4],poly[12][5],poly[12][6],poly[12][7],poly[12][8],poly[12][9],poly[13][0],poly[13][1],poly[13][2],poly[13][3],poly[13][4],poly[13][5],poly[13][6],poly[13][7],poly[13][8],poly[13][9],poly[14][0],poly[14][1],poly[14][2],poly[14][3],poly[14][4],poly[14][5],poly[14][6],poly[14][7],poly[14][8],poly[14][9],poly[15][0],poly[15][1],poly[15][2],poly[15][3],poly[15][4],poly[15][5],poly[15][6],poly[15][7],poly[15][8],poly[15][9],poly[16][0],poly[16][1],poly[16][2],poly[16][3],poly[16][4],poly[16][5],poly[16][6],poly[16][7],poly[16][8],poly[16][9],poly[17][0],poly[17][1],poly[17][2],poly[17][3],poly[17][4],poly[17][5],poly[17][6],poly[17][7],poly[17][8],poly[17][9],poly[18][0],poly[18][1],poly[18][2],poly[18][3],poly[18][4],poly[18][5],poly[18][6],poly[18][7],poly[18][8],poly[18][9],poly[19][0],poly[19][1],poly[19][2],poly[19][3],poly[19][4],poly[19][5],poly[19][6],poly[19][7],poly[19][8],poly[19][9],poly[20][0],poly[20][1],poly[20][2],poly[20][3],poly[20][4],poly[20][5],poly[20][6],poly[20][7],poly[20][8],poly[20][9],poly[21][0],poly[21][1],poly[21][2],poly[21][3],poly[21][4],poly[21][5],poly[21][6],poly[21][7],poly[21][8],poly[21][9],poly[22][0],poly[22][1],poly[22][2],poly[22][3],poly[22][4],poly[22][5],poly[22][6],poly[22][7],poly[22][8],poly[22][9],poly[23][0],poly[23][1],poly[23][2],poly[23][3],poly[23][4],poly[23][5],poly[23][6],poly[23][7],poly[23][8],poly[23][9],poly[24][0],poly[24][1],poly[24][2],poly[24][3],poly[24][4],poly[24][5],poly[24][6],poly[24][7],poly[24][8],poly[24][9],poly[25][0],poly[25][1],poly[25][2],poly[25][3],poly[25][4],poly[25][5],poly[25][6],poly[25][7],poly[25][8],poly[25][9],poly[26][0],poly[26][1],poly[26][2],poly[26][3],poly[26][4],poly[26][5],poly[26][6],poly[26][7],poly[26][8],poly[26][9],poly[27][0],poly[27][1],poly[27][2],poly[27][3],poly[27][4],poly[27][5],poly[27][6],poly[27][7],poly[27][8],poly[27][9],poly[28][0],poly[28][1],poly[28][2],poly[28][3],poly[28][4],poly[28][5],poly[28][6],poly[28][7],poly[28][8],poly[28][9],poly[29][0],poly[29][1],poly[29][2],poly[29][3],poly[29][4],poly[29][5],poly[29][6],poly[29][7],poly[29][8],poly[29][9],poly[30][0],poly[30][1],poly[30][2],poly[30][3],poly[30][4],poly[30][5],poly[30][6],poly[30][7],poly[30][8],poly[30][9],poly[31][0],poly[31][1],poly[31][2],poly[31][3],poly[31][4],poly[31][5],poly[31][6],poly[31][7],poly[31][8],poly[31][9],poly[32][0],poly[32][1],poly[32][2],poly[32][3],poly[32][4],poly[32][5],poly[32][6],poly[32][7],poly[32][8],poly[32][9],poly[33][0],poly[33][1],poly[33][2],poly[33][3],poly[33][4],poly[33][5],poly[33][6],poly[33][7],poly[33][8],poly[33][9],poly[34][0],poly[34][1],poly[34][2],poly[34][3],poly[34][4],poly[34][5],poly[34][6],poly[34][7],poly[34][8],poly[34][9],poly[35][0],poly[35][1],poly[35][2],poly[35][3],poly[35][4],poly[35][5],poly[35][6],poly[35][7],poly[35][8],poly[35][9]"""


"""
pour wircam

,SkyFootPrint = GeomFromText("MultiPolygon(((%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s),(%s %s ,%s %s,%s %s,%s %s,%s %s)))") 


,poly[0][0],poly[0][1],poly[0][2],poly[0][3],poly[0][4],poly[0][5],poly[0][6],poly[0][7],poly[0][8],poly[0][9],poly[1][0],poly[1][1],poly[1][2],poly[1][3],poly[1][4],poly[1][5],poly[1][6],poly[1][7],poly[1][8],poly[1][9],poly[2][0],poly[2][1],poly[2][2],poly[2][3],poly[2][4],poly[2][5],poly[2][6],poly[2][7],poly[2][8],poly[2][9],poly[3][0],poly[3][1],poly[3][2],poly[3][3],poly[3][4],poly[3][5],poly[3][6],poly[3][7],poly[3][8],poly[3][9] """