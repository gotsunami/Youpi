#!/usr/bin/env python

"""
Generates files from dot diagrams
"""

import os

FIGURES_DIR = 'figures'
DOTS = ('mandatory_vars', 'function_calls', 'mcd', 'codasyl', 'dependencies_tree_standalone', 'dependencies_tree_cluster')
FORMATS = ('ps', 'svg', 'png')

def main():
	for fig in DOTS:
		for of in FORMATS:
			print "%s [%s]" % (fig, of)
			file = os.path.join(FIGURES_DIR, fig)
			os.system("dot -o %s.%s -T%s %s.dot 2> genfigures.log" % (file, of, of, file))

if __name__ == '__main__':
	main()
