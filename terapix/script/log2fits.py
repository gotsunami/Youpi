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

import pyfits
import re
import glob
import os,sys
from math import *
from DBGeneric import *
sys.path.insert(0, '..')
from settings import *


db = DB(host = DATABASE_HOST,
                user = DATABASE_USER,
                passwd = DATABASE_PASSWORD,
                db = DATABASE_NAME)

g = DBGeneric(db.con)

os.chdir('/home/nis/semah/FITSTABLE')
k = glob.glob('*.log')
while k <> 0:
        log = k.pop()
        file = open(log)
        rawstr = r"""(.*)\s\|\s(\d{2}\D).*\|\s(\D\d{2}).*\|(.*)\|(.*)\|\s(\D)\s\|(.*)\|(.*)\|(\D)\s.\s(\D)(.*)\|"""
        compil_obj = re.compile(rawstr)
        lignes = file.readlines()
        for i in lignes:
                match_obj = compil_obj.search(i)
                if match_obj:
                        all_groups = match_obj.groups()
                        for j in all_groups:
                        #       print all_groups[8]+"\n",all_groups[9]
                                name = all_groups[0]+"p"
                                instrument = "MegaPrime"
                                channel = all_groups[5]
                                run = all_groups[1]+all_groups[2]
                                qsostatus = all_groups[9]
                                fitstable = log
                                is_phot = all_groups[8]

                                if qsostatus == "V":
                                        qsostatus = "VALIDATED"
                                elif qsostatus == "O":
                                        qsostatus = "OBSERVED"
                                else:
                                        print qsostatus

                                if is_phot == "P":
                                        is_phot = "1"
                                elif is_phot == "A":
                                        is_phot = "0"
                                else:
                                        print is_phot

                                g.begin()
                                g.setTableName('youpi_fitstables')

                                try:
                                        g.insert(       name = name,
                                                                instrument = instrument,
                                                                run = run,
                                                                channel = channel,
                                                                qsostatus = qsostatus,
                                                                is_phot = is_phot,
                                                                fitstable = log)

                                except Exception, e:
                                        code = e[0]
                                        if code != 1062:
                                                g.con.rollback()
                                                print "Error:", e
                                                print name, run, instrument, channel, qso
                                                sys.exit(1)
