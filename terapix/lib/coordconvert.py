"""
Simple module for coordinate conversions, mainly beetween 
decimal and sexagesimal systems
"""

class Alpha(object):
	"""
	Right ascension
	"""
	@staticmethod
	def deg_to_sex(alpha):
		"""
		Converts degrees to hh:mm:ss.xxx alpha coordinates
		"""
		hh = mm = ss = 0.
		if alpha >= 0. and alpha < 360.:
			hh = int(alpha/15.)
			mm = int(60.*(alpha/15.-hh))
			ss = 60.*(60.*(alpha/15.-hh)-mm)
		return "%02d:%02d:%05.2f" % (hh, mm, ss)

	@staticmethod
	def sex_to_deg(hms, sep = ':'):
		"""
		Converts hh:mm:ss.xxx alpha coordinates to degrees
		"""
		hms = hms.split(sep)
		deg = float(hms[0])*15. 	# Hours
		deg += float(hms[1])/4. 	# Minutes
		deg += float(hms[2])/240.	# Seconds
		return deg

class Delta(object):
	"""
	Declination
	"""
	@staticmethod
	def deg_to_sex(delta):
		"""
		Converts degrees to dd:dm:ds.x delta coordinates 
		"""
		sign = '+'
		if delta < 0.: sign = '-'
		delta = abs(delta)
		dd = dm = ds = 0.
		if delta >= -90. and delta <= 90.:
			dd = int(delta)
			dm = int(60.*(delta-dd))
			ds = 60.*abs(60.*(delta-dd)-dm)
		return "%c%02d:%02d:%04.1f" % (sign, dd, dm, ds)

	@staticmethod
	def sex_to_deg(dms, sep = ':'):
		"""
		Converts dd:dm:ds.xxx delta coordinates to degrees
		"""
		sign = 1.
		if dms[0] == '-': sign = -1.
		dms = dms.split(sep)
		val = float(dms[0])					# Degrees
		val += float(dms[1])*sign/60.		# Minutes
		val += float(dms[2])*sign/3600.		# Seconds
		return val
