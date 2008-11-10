#!/usr/bin/env python

"""
Looks for all .FILE_EXT files in DICT_DIR directory; parses them and 
outputs XML Docbook table content.
"""

import glob, os.path

DICT_DIR = 'data_dict'
FILE_EXT = '.dict'
SEP = ';'

STYLES = {	1 : '<varname>%s</varname>',
			4 : '<type>%s</type>',
			5 : '<code>%s</code>', }

def main():
	db_defs = glob.glob(os.path.join(DICT_DIR, '*' + FILE_EXT))
	for db_ent in db_defs:
		try:
			f = open(db_ent)
			data = f.readlines()
			f.close()
		except IOError, e:
			raise

		entries = []
		for line in data:
			if line[0] != '\n' and line[0] != '#':
				entries.append(line[:-1])

		col_count = len(entries[1].split(SEP))

		header = entries[1].split(SEP)
		thead = ''
		for name in header:
			thead += "<entry>%s</entry>" % name

		body = entries[2:]
		tbody = ''
		for row in body:
			cols = row.split(SEP)
			tbody += '<row>'
			for k in range(len(cols)):
				if k in STYLES.keys():
					pat = STYLES[k] % cols[k]
				else:
					pat = cols[k]
				tbody += "<entry>%s</entry>" % pat
			tbody += '</row>'

		xml = """
<table frame="all">
	<title>%s</title>
	<tgroup cols="%d" align="left" colsep="1">
		<thead>
			<row>%s</row>
		</thead>
		<tbody>%s</tbody>
	</tgroup>
</table>
""" % (entries[0], col_count, thead, tbody)

		try:
			name = os.path.basename(db_ent) + '.xml'
			f = open(name, 'w')
			f.write(xml)
			f.close()
			print "File %s: generated" % name
		except IOError, e:
			raise

if __name__ == '__main__':
	main()
