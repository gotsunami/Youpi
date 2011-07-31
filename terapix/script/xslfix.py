#!/usr/bin/env python

"""
Fixes XSL paths in XML VOTABLEs
"""

import sys, os, os.path, types, shutil
import re, stat
from optparse import OptionParser
from tempfile import mkstemp

XSL_PAT = r'<\?xml-stylesheet type="text/xsl" href=".*?"\?>'
VERBOSE = False
REAL = False

def get_default_xsl_path(tool):
    data = os.popen(tool + ' -dd|grep XSL_URL').read()[:-1]
    return re.sub(r'^.*file://', '', data)

def find_and_replace(path):
    # VOTABLE resource ID with matching XSL base name
    voIds = {'sextractor': 'sex', 'swarp': 'swarp', 'scamp': 'scamp'}
    subs = vots = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith('.xml') and root.find('/fitsin/') == -1:
                xslPath = id = xslBase = xslName = None
                fabs = os.path.join(root, f)
                if VERBOSE:
                    print "Processing %s" % fabs

                fh, abspath = mkstemp()
                nfile = open(abspath, 'w')
                d = open(fabs)
                data = d.readlines()
                # Get resource ID
                for line in data:
                    if line.find('<RESOURCE') == 0:
                        vots += 1
                        m = re.search(r'<RESOURCE ID="(.*?)"', line)
                        id = m.group(1).lower()
                        xslBase = voIds[id]
                        xslName = xslBase + '.xsl'
                        # First try to locate the default XSL file path
                        # to preserve atomicity
                        xslPath = get_default_xsl_path(xslBase)
                        if xslPath == '':
                            break

                if xslPath == '':
                    if VERBOSE:
                        print "cmd '%s' not found in PATH, skipping file" % xslBase
                    continue
                for line in data:
                    if line.find('<?xml-stylesheet') == 0:
                        line = re.sub(XSL_PAT, "<?xml-stylesheet type=\"text/xsl\" href=\"%s\"?>" % xslName, line)
                    nfile.write(line)
                d.close()
                nfile.flush()
                nfile.close()
                if REAL:
                    shutil.copy(xslPath, os.path.join(root, xslName))
                    os.remove(fabs)
                    shutil.move(abspath, fabs)
                    os.chmod(fabs, stat.S_IROTH | stat.S_IRGRP | stat.S_IRUSR)
                    subs += 1
                    if VERBOSE:
                        print "XSL substitution with %s done." % xslName

    print "VOTABLE XML files: %d, substitutions: %d" % (vots, subs)

def main():
    global VERBOSE, REAL
    parser = OptionParser(usage="Usage: %prog [options] directory", description = 'Fixes XSL paths in XML VOTables')
    parser.add_option('-v', '--verbose', 
            action = 'store_true', 
            default = VERBOSE, 
            help = 'verbose output'
    )
    parser.add_option('-r', '--real', 
            action = 'store_true', 
            default = REAL, 
            help = 'perform a real update of XML files'
    )

    (options, args) = parser.parse_args()
    if len(args) != 1: 
        parser.error('Please give a directory to look into!')
        parser.print_help()

    if not os.path.isdir(args[0]):
        print 'Error: argument must be a valid directory'
        sys.exit(1)

    VERBOSE = options.verbose
    REAL = options.real
    if not REAL:
        print "Simulation, does NOT alter data (use --real to apply changes)"
        find_and_replace(args[0])
    else:
        if raw_input("Are you sure? (y/[n])") == 'y':
            find_and_replace(args[0])
        else:
            print 'Aborted.'


if __name__ == '__main__':
    main()
