#!/usr/bin/env python

import sys, re, types

def debug(msg):
	print msg

class InstrumentConfig(object):
	"""
	Provides several facilities for dealing with Youpi instrument 
	configuration files (terapix/lib/itt/*.conf)
	"""
	# Required Youpi keywords
	required_kw = 'YRUN YINSTRUMENT YTELESCOP YDETECTOR YOBJECT ' + \
		'YAIRMASS YEXPTIME YDATEOBS YEQUINOX YFILTER YFLAT YMASK ' + \
		'YRA YDEC'
	SEP = ';'

	def __init__(self, filename):
		"""
		Sets instrument config filename to work on.
		"""
		if type(filename) != types.StringType:
			raise TypeError, "filename must be a string"
		self.__filename = filename

	@property
	def filename(self):
		return self.__filename

	def parse(self):
		conf = open(self.__filename, 'r')
		content = conf.readlines()
		conf.close()
		# Removing trailing \n
		content = [li[:-1] for li in content]
		# Removing comments and empty lines
		content = [li for li in content if len(li) and not li.startswith('#')]

		# Build a list from the static value
		required_kw = self.required_kw.split(' ')

		# Table of mappings
		map = {'+COPY': []}
		for line in content:
			#
			# Sanity checks
			#
			if line.find(self.SEP) == -1:
				# Is is a +KEYWORD line?
				li= line.strip()
				if re.match('^\+\w+$', li):
					map['+COPY'].append(li[1:])
					continue
				else:
					raise ValueError, "Field separator must be a semi-colon. No separator found. The line does not match +KEYWORD either.\nPlease check the line:\n%s" % line
			data = line.split(self.SEP)
			if len(data) > 3:
				raise ValueError, "Too many fields for this line (max is 3): %s" % line
			# Stripping content
			data = [col.strip() for col in data]
			# Converting keywords (not starting by double quote) to uppercase
			for k in range(len(data)):
				if not data[k].startswith('"'):
					data[k] = data[k].upper()

			# First column must be either a required keyword or an empty value (in this case
			# second column must start with a '+'
			if data[0] not in required_kw and len(data[0]):
				raise ValueError, "Error: '%s' is not among authorized keywords. Check line: %s" % (data[0], line)
			
			values = {'SRC': data[1]}
			# Check for optional 3rd column
			if len(data) == 3: values['MAP'] = data[2]
			# Add entry
			map[data[0]] = values

		return map


def main():
	if len(sys.argv) != 2:
		debug('Missing arg 1: conf file')
		sys.exit(1)
	c = InstrumentConfig(sys.argv[1])
	print c.parse()

if __name__ == '__main__':
	main()
