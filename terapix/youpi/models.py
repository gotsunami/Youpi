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

from django.db import models
from django.contrib.gis.db import models
from django.contrib.auth.models import User, Group

GRADE_A = 'A'
GRADE_B = 'B'
GRADE_C = 'C'
GRADE_D = 'D'

GRADE_SET = (	(GRADE_A, GRADE_A),
				(GRADE_B, GRADE_B),
				(GRADE_C, GRADE_C),
				(GRADE_D, GRADE_D) )
	
class Survey(models.Model):
	name = models.CharField(max_length = 240, blank=True,help_text="Name of the survey")
	comment = models.CharField(max_length = 240, blank=True,help_text="")
	url = models.URLField(max_length = 240, blank=True,null=True,help_text="")

	def __unicode__(self):
		return self.name

class Processing_kind(models.Model):
	"""
	Name of processing
	"""
	
	# Name of configuration content
	name = models.CharField(max_length = 80, unique = True)
	# = plugin.optionLabel
	label = models.CharField(max_length = 80)
	
	class Meta:
		verbose_name = "Processing kind"

	def __unicode__(self):
		return self.name

class Instrument(models.Model):
	name = models.CharField(max_length = 240, blank=True,help_text="")
	telescope = models.CharField(max_length = 240, blank=True,null=True,help_text="name of telescope")
	url = models.URLField(max_length = 240, blank=True,null=True,help_text="")
	timezone = models.CharField(max_length = 3, blank=True,null=True,help_text="")
	altitude = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")
	nchips = models.IntegerField("Number of chips",max_length = 3,null=True,blank=True,help_text="")
	astrinstru_key = models.CharField(max_length = 255,blank=True,null=True,help_text="")
	photinstru_key = models.CharField(max_length = 255,blank=True,null=True,help_text="")
	path = models.CharField(max_length = 255,blank=True,null=True)

	def __unicode__(self):
		return self.name

class Run(models.Model):
	name = models.CharField(max_length = 80,blank=True,null=True,help_text="")
	pi = models.CharField("P.I.",max_length = 80,blank=True,null=True,help_text="")
	url = models.URLField(max_length = 240,blank=True,null=True,help_text="")
	email = models.EmailField(blank=True,null=True,help_text="")
	processrequestdate = models.DateField(null=True,blank=True,help_text="")
	datestart = models.DateField(null=True,blank=True,help_text="")
	datend = models.DateField(null=True,blank=True,help_text="")
	datedownload = models.DateField(null=True,blank=True,help_text="")
	releasedate = models.DateField(null=True,blank=True,help_text="")

	# FKs constraints
	instrument = models.ForeignKey(Instrument,db_column='instrument_id')

	def __unicode__(self):
		return self.name

class Channel(models.Model):
	name = models.CharField(max_length = 80,blank=True,null=True,help_text="name of instrument")
	wavelength = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")
	url = models.URLField(max_length = 240,blank=True,null=True,help_text="")
	wavecurve = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")
	transcurve = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")
	magoffsets = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")

	# FKs constraints
	instrument = models.ForeignKey(Instrument)

	def __unicode__(self):
		return self.name

class ImageSelections(models.Model):
	"""
	Standalone table, no foreign key constraint.
	Useful to store (serialized) data related to image selection into DB.
	"""
	
	name = models.CharField(unique = True, max_length = 80)
	# Serialized data (base64 encoding over marshal serialization)
	data = models.TextField()
	date = models.DateTimeField(auto_now_add = True)
	# Default chmod permissions (ex: 644)
	mode = models.CharField(max_length = 3)

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	group = models.ForeignKey(Group)
	
	class Meta:
		verbose_name="Image selection"

	def __unicode__(self):
		return self.name

class ConfigType(models.Model):
	"""
	Defines types for configuration files
	"""
	
	name = models.CharField(max_length = 80, unique = True)
	
	class Meta:
		verbose_name = "Configuration file type"

	def __unicode__(self):
		return self.name

class ConfigFile(models.Model):
	"""
	Useful to store (serialized) data related to configuration files to use for processing
	"""
	
	# Name of configuration content
	name = models.CharField(max_length = 80)
	# Config file full content (clear text)
	content = models.TextField()
	# Serialized data (base64 encoding over marshal serialization)
	data = models.TextField(null=True)
	date = models.DateTimeField(auto_now_add = True)
	# Default chmod permissions (ex: 644)
	mode = models.CharField(max_length = 3)

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	group = models.ForeignKey(Group)
	kind = models.ForeignKey(Processing_kind, db_column = 'kind_id')
	type = models.ForeignKey(ConfigType)
	
	class Meta:
		unique_together = ('name', 'kind', 'type')
		verbose_name = "Configuration file"

	def __unicode__(self):
		return self.name

class MiscData(models.Model):
	"""
	Standalone table, no foreign key constraint.
	Useful to store (serialized) misc data based a unique key.
	Example: can be used to store lists of paths to flats and masks (2 different keys)
	"""
	
	key = models.CharField(max_length = 80)
	# Serialized data (base64 encoding over marshal serialization)
	data = models.TextField()
	date = models.DateTimeField(auto_now_add = True)
	# Default chmod permissions (ex: 644)
	mode = models.CharField(max_length = 3)

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	group = models.ForeignKey(Group)

	class Meta:
		unique_together = ('key', 'user')
		verbose_name="Miscallenous data"

class CartItem(models.Model):
	"""
	Standalone table, no foreign key constraint.
	Useful to store (serialized) data related to processing cart items
	"""
	
	# Name of configuration content
	name = models.CharField(max_length = 80, unique = True)
	date = models.DateTimeField(auto_now_add = True)
	# Serialized data (base64 encoding over marshal serialization)
	data = models.TextField()
	# Default chmod permissions (ex: 644)
	mode = models.CharField(max_length = 3)

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	group = models.ForeignKey(Group)
	kind = models.ForeignKey(Processing_kind, db_column = 'kind_id')
	
	class Meta:
		verbose_name="Saved item of processing cart"

	def __unicode__(self):
		return self.name

class Image(models.Model):
	name = models.CharField(max_length = 255, help_text="name of image")
	#
	# http://dev.mysql.com/doc/refman/5.0/en/innodb-restrictions.html:
	# InnoDB tables do not support spatial data types before MySQL 5.0.16. As of 5.0.16,
	# InnoDB supports spatial data types, but not indexes on them.
	#
	# ... so spatial indexes are not created (forced with spatial_index = False)
	#
	skyfootprint = models.MultiPolygonField(spatial_index = False)
	centerfield = models.PointField(spatial_index = False)
	objects = models.GeoManager()
	path = models.CharField(max_length = 255,blank=True,null=True,help_text="path of image")
	alpha = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text= " Right ascension of field center [deg]")
	delta = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text= " Declination of field center [deg]")
	astromaccuracy = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")
	equinox = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="equinox of celestial coordinate system")
	object = models.CharField(max_length = 80,blank=True,null=True,help_text="name of observed object")
	dateobs = models.DateTimeField(null=True,blank=True,help_text="date of the observation")
	exptime = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Exposure time")
	photc_header = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")
	photc_custom = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")
	photk = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text= "Extinction coefficient")
	airmass = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")
	absorption = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Skyprobe value")
	checksum = models.CharField(max_length = 80,blank=True,null=True,help_text="")
	gain = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text=" Average conversion factor [e-/ADU]")
	ingestion_date = models.DateTimeField(help_text = 'Ingestion date and time')
	flat = models.CharField(max_length = 200,blank=True,null=True,help_text="associated flat image")
	mask = models.CharField(max_length = 200,blank=True,null=True,help_text="associated mask image")
	reg = models.CharField(max_length = 200,blank=True,null=True,help_text="associated region (polygon) image")
	is_validated = models.NullBooleanField('Validation status', default=False)

	# FKs constraints
	channel = models.ForeignKey(Channel, db_column='channel_id')
	ingestion = models.ForeignKey('Ingestion',db_column='ingestion_id')
	instrument = models.ForeignKey(Instrument, db_column = 'instrument_id')
	
	class Meta:
		unique_together = ('name', 'checksum')
		verbose_name = "Ingested image"
		verbose_name_plural = "Ingested images"


	def __unicode__(self):
		return self.name

class Processing_task(models.Model):
	bools = ((False, 'No'), (True, 'Yes'))
	start_date = models.DateTimeField(auto_now_add = True, help_text = 'Beginning of processing')
	end_date = models.DateTimeField(help_text = 'End of processing')
	success = models.NullBooleanField('QSO status', null = True, default = False, choices = bools)
	hostname = models.CharField(max_length = 255, null = True, help_text="Processing host (local or cluster node)")
	# Serialized data (base64 encoding over zlib compression)
	error_log = models.TextField(null=True)
	results_output_dir = models.CharField(max_length = 255, null = False, help_text="Output directory for results")
	title = models.CharField(max_length = 255, help_text="Processing task title")
	clusterId = models.CharField(max_length = 255, help_text="Condor Job Cluster Id", null = True)
	# Default chmod permissions (ex: 644)
	mode = models.CharField(max_length = 3)

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	group = models.ForeignKey(Group)
	kind = models.ForeignKey(Processing_kind, db_column = 'kind_id')
	
	class Meta:
		verbose_name = "Processing task"

	def __unicode__(self):
		return "Task #%d [%s] on %s" % (self.id, self.end_date-self.start_date, self.hostname)

class Plugin_scamp(models.Model):
	# Serialized data (base64 encoding over zlib compression)
	config = models.TextField(null = True)
	# Results log
	log = models.TextField(null = True)
	ldac_files = models.TextField(null = True)
	www = models.CharField(max_length = 255, blank = True, null = True, help_text = "HTTP URL to Scamp output HTML data")
	thumbnails = models.NullBooleanField('Has image thumbnails', default = False)
	aheadPath = models.CharField(max_length = 255, null = True, help_text = "Path to .ahead files")

	# FKs constraints
	task = models.ForeignKey(Processing_task, db_column = 'task_id')
	
	class Meta:
		verbose_name = "SCAMP plugin"

	def __unicode__(self):
		return self.name

class Plugin_swarp(models.Model):
	# Serialized data (base64 encoding over zlib compression)
	config = models.TextField(null = True)
	# Results log
	log = models.TextField(null = True)
	www = models.CharField(max_length = 255, blank = True, null = True, help_text = "HTTP URL to Swarp output HTML data")
	thumbnails = models.NullBooleanField('Has image thumbnails', default = False)
	weightPath = models.CharField(max_length = 255, null = True, help_text = "Path to weight images")
	useQFITSWeights = models.NullBooleanField('True if QFITS weight maps have been used', default = False)
	headPath = models.CharField(max_length = 255, null = True, help_text = "Path to .head files")
	useHeadFiles = models.NullBooleanField('True if .head files have been used', default = False)

	# FKs constraints
	task = models.ForeignKey(Processing_task, db_column = 'task_id')
	
	class Meta:
		verbose_name = "Swarp plugin"

	def __unicode__(self):
		return self.name

class Plugin_sex(models.Model):
	# Serialized data (base64 encoding over zlib compression)
	config = models.TextField(null = True)
	param  = models.TextField(null = True)
	# Results log
	log = models.TextField(null = True)
	www = models.CharField(max_length = 255, blank = True, null = True, help_text = "HTTP URL to Sex output HTML data")
	thumbnails = models.NullBooleanField('Has image thumbnails', default = False)
	weightPath = models.CharField(max_length = 255, null = True, help_text = "Path to weight images")
	flagPath = models.CharField(max_length = 255, null = True, help_text = "Path to flag images")
	dualweightPath = models.CharField(max_length = 255, null = True, help_text = "Path to weight images in dual mode")
	dualImage = models.CharField(max_length = 255, null = True, help_text = "Path to dual image in dual mode")
	dualflagPath = models.CharField(max_length = 255, null = True, help_text = "Path to flag images in dual mode")
	psfPath = models.CharField(max_length = 255, null = True, help_text = "Path to psf images")
	dualMode = models.NullBooleanField('Dual Image Mode', default = False)

	# FKs constraints
	task = models.ForeignKey(Processing_task, db_column = 'task_id')
	
	class Meta:
		verbose_name = "Sex plugin"

	def __unicode__(self):
		return self.name

class Plugin_fitsin(models.Model):
	"""
	Related to QualityFITSin plugin
	"""
	
	astoffra = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text= "Offset in RA w.r.t. reference")
	astoffde = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text= "Offset in Dec w.r.t. reference")
	aststdevra = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text= "Std deviation of astrometric residuals in RA w.r.t. reference")
	aststdevde = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text= "Std deviation of astrometric residuals in Dec w.r.t. reference")
	psffwhmmin = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Minimum PSF FWHM (based on a 2D Moffat fit) [arcsec]")
	psffwhm = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Average PSF FWHM (based on a 2D Moffat fit) [arcsec]")
	psffwhmmax = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Maximum PSF FWHM (based on a 2D Moffat fit) [arcsec]")
	psfhldmin = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Minimum half-light diameter [arcsec]")
	psfhld = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Average half-light diameter [arcsec]")
	psfhldmax = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Maximum half-light diameter [arcsec]")
	psfelmin = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Minimum PSF elongation (based on a 2D Moffat fit)")
	psfel = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Average PSF elongation (based on a 2D Moffat fit)")
	psfelmax = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Maximum PSF elongation (based on a 2D Moffat fit)")
	psfchi2min = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Minimum chi2 of PSF model fit")
	psfchi2 = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Average chi2 of PSF model fit")
	psfchi2max = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Maximum chi2 of PSF model fit")
	psfresimin = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Minimum residuals of Moffat fit to PSF model")
	psfresi = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Average residuals of Moffat fit to PSF model")
	psfresimax = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Maximum residuals of Moffat fit to PSF model")
	psfasymmin = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Minimum asymmetry of PSF")
	psfasym = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Average asymmetry of PSF")
	psfasymmax = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Maximum asymmetry of PSF")
	nstarsmin = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Minimum number of point sources accepted for PSF modelling")
	nstars = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Mean number of point sources accepted for PSF modelling")
	nstarsmax = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Maximum number of point sources accepted for PSF modelling")
	bkg    = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Average background level [ADU]")
	bkgstdev = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Std deviation of the background [ADU]")
	satlev = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="Minimum saturation level [ADU]")
	prevrelgrade = models.CharField(max_length = 1, blank = True, null = True, choices = GRADE_SET, help_text = "Previous QualityFITS-in grade")
	prevrelcomment = models.CharField(max_length = 255, blank = True, null = True, help_text = "Previous QualityFITS-in comment")
	flat = models.CharField(max_length = 200,blank=True,null=True,help_text="associated flat image")
	mask = models.CharField(max_length = 200,blank=True,null=True,help_text="associated mask image")
	reg = models.CharField(max_length = 200,blank=True,null=True,help_text="associated region (polygon) image")
	# Serialized data (base64 encoding over zlib compression)
	qfconfig = models.TextField(null = True)
	# QFits results ingestion log
	qflog = models.TextField(null = True)
	www = models.CharField(max_length = 255, blank = True, null = True, help_text = "HTTP URL to QF output HTML data")
	exitIfFlatMissing = models.NullBooleanField('Exit if flat is missing', default = True)

	# FKs constraints
	task = models.ForeignKey(Processing_task, db_column = 'task_id')
	
	class Meta:
		verbose_name = "QualityFits-In plugin data"

class Plugin_fitsout(models.Model):
	"""
	 Related to QualityFITSout plugin
	"""
	
	# FKs constraints
	task = models.ForeignKey(Processing_task, db_column = 'task_id')
	
	class Meta:
		verbose_name = "QualityFits-Out plugin data"

	def __unicode__(self):
		return self.name

class FirstQComment(models.Model):
	"""
	First quality predefined comments.
	"""

	comment = models.CharField(max_length = 255, unique = True)
	
	class Meta:
		verbose_name = "First Quality Comment"

class FinalQComment(models.Model):
	"""
	Final quality predefined comments.
	"""

	comment = models.CharField(max_length = 255, unique = True)
	
	class Meta:
		verbose_name = "Final Quality Comment"
    
class FirstQEval(models.Model):
	"""
	First quality evaluation.
	"""

	custom_comment = models.CharField(max_length = 255)
	date = models.DateTimeField(auto_now_add = True)
	grade = models.CharField(max_length = 1, choices = GRADE_SET, help_text = "QualityFITS in grade")

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	fitsin = models.ForeignKey(Plugin_fitsin, db_column = 'fitsin_id')
	comment = models.ForeignKey(FirstQComment, db_column = 'comment_id')
	
	class Meta:
		verbose_name = "First Quality Evaluation"
		unique_together = ('user', 'fitsin')
		permissions = (('can_grade', "Can grade a QualityFITSed image"),)

class FinalQEval(models.Model):
	"""
	Final quality evaluation.
	"""

	custom_comment = models.CharField(max_length = 255)
	date = models.DateTimeField(auto_now_add = True)
	grade = models.CharField(max_length = 1, choices = GRADE_SET, help_text = "QualityFITS out grade")

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	fitsout = models.ForeignKey(Plugin_fitsin, db_column = 'fitsout_id')
	comment = models.ForeignKey(FinalQComment, db_column = 'comment_id')
	
	class Meta:
		verbose_name = "Final Quality Evaluation"
		unique_together = ('user', 'fitsout')

class Ingestion(models.Model):
	start_ingestion_date = models.DateTimeField(help_text = 'Beginning of ingestion')
	end_ingestion_date = models.DateTimeField(help_text = 'End of ingestion')
	email = models.EmailField(blank=True,help_text="email of the ingestion user")
	path = models.CharField(max_length = 250,blank=True,null=True,help_text="path where are stored images data")
	label = models.CharField(unique = True, max_length = 80, help_text="Unique ingestion identifier")
	check_states = ((False, 'No'), (True, 'Yes'))
	check_fitsverify = models.NullBooleanField('Fitsverify status', default=False, choices = check_states)
	is_validated = models.NullBooleanField('Validation status', default=False, choices = check_states)
	check_multiple_ingestion = models.NullBooleanField('Multiple ingestion status', default=False, choices = check_states)
	exit_code = models.NullBooleanField('Exit code status', default=False, choices = ((False, 'Failure'), (True, 'Success')))
	# Serialized data (base64 encoding over zlib compression)
	report = models.TextField(blank = True, null = True)
	# Default chmod permissions (ex: 644)
	mode = models.CharField(max_length = 3)

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	group = models.ForeignKey(Group)

	class Meta:
		verbose_name="Ingestion"

	def __unicode__(self):
		return "Ingestion" + str(self.id)
	
class Coaddition(models.Model):
	image = models.ForeignKey(Image,null=True,blank= True,db_column='image_id')
	listname = models.CharField(max_length = 20,blank=True,null=True,help_text="")

	class Meta:
		verbose_name = "Coadded Image"
		verbose_name_plural = "Coadded Images"

	def __unicode__(self):
		return self.listname
       
class Fitstables(models.Model):
    # Image name
	name = models.CharField(max_length = 80,blank=True,null=True)
	instrument =  models.CharField(max_length = 80,blank=True,null=True)
	channel =  models.CharField(max_length = 80,blank=True,null=True)
	run =  models.CharField(max_length = 80,blank=True,null=True)
	QSOstatus = models.CharField(max_length = 20,blank=True,null=True,help_text="Status from the related FITS table ")
	object = models.CharField(max_length = 20,blank=True,null=True,help_text="")
    # Complete path to file
	fitstable = models.CharField(max_length = 80,blank=True,null=True, help_text="")
	
	# Other information
	absorption = models.DecimalField(max_digits = 32,decimal_places = 16,null=True,blank=True,help_text="")
	absorption_err = models.DecimalField(max_digits = 32,decimal_places = 16,null=True,blank=True,help_text="")
	is_phot = models.NullBooleanField('is_phot', default=False,help_text="")

	class Meta:
		unique_together = [('name', 'run', 'fitstable')]

class Tag(models.Model):
	name = models.CharField(max_length = 255, blank = False, null = False, unique = True, help_text = 'Tag name')
	style = models.CharField(max_length = 255, help_text = 'Tag CSS style')
	date = models.DateTimeField(auto_now_add = True)
	comment = models.CharField(max_length = 255, help_text = 'Comment')
	# Default chmod permissions (ex: 644)
	mode = models.CharField(max_length = 3)

	# FKs constraints
	user = models.ForeignKey(User)
	group = models.ForeignKey(Group)

	class Meta:
		permissions = (('can_edit_others', "Can edit others' tags"),)

	class Meta:
		verbose_name = "Tags"

class Rel_si(models.Model):
	"""
	Survey-Instrument relation
	"""

	survey = models.ForeignKey(Survey, db_column = 'survey_id')
	instrument = models.ForeignKey(Instrument, db_column = 'instrument_id')
	
	class Meta:
		unique_together = ('survey', 'instrument')

	def __unicode__(self):
		return self.name

class Rel_ri(models.Model):
	"""
	Run-Image relation
	"""

	run = models.ForeignKey(Run, db_column = 'run_id')
	image = models.ForeignKey(Image, db_column = 'image_id')

	class Meta:
		unique_together = ('run', 'image')

	def __unicode__(self):
		return self.name

class Rel_it(models.Model):
	"""
	Image-Processing Task relation
	"""

	image = models.ForeignKey(Image, db_column = 'image_id')
	task = models.ForeignKey(Processing_task, db_column = 'task_id')

	class Meta:
		unique_together = ('image', 'task')

class Rel_us(models.Model):
	"""
	User-Survey relation
	"""

	user = models.ForeignKey(User)
	survey = models.ForeignKey(Survey)

	class Meta:
		unique_together = ('user', 'survey')

class Rel_tagi(models.Model):
	"""
	Tag-Image relation
	"""

	image = models.ForeignKey(Image)
	tag = models.ForeignKey(Tag)

	class Meta:
		unique_together = ('image', 'tag')

class SiteProfile(models.Model):

	# Current user GUI style
	guistyle = models.CharField(max_length = 255, default = 'default')
	dflt_condor_setup = models.TextField()
	# Custom Condor requirements
	custom_condor_req = models.TextField(null = True)
	# Default chmod permissions (ex: 644)
	dflt_mode = models.CharField(max_length = 3)

	# FKs
	user = models.ForeignKey(User, unique = True)
	dflt_group = models.ForeignKey(Group)

class CondorNodeSel(models.Model):
	"""
	Used to store both custom selections and custom policies
	Only custom selections content is base64 + marshal encoded.
	Custom policies are clear text content.
	"""

	# Mandatory
	user = models.ForeignKey(User)

	label = models.CharField(max_length = 255)
	nodeselection = models.TextField()
	date = models.DateTimeField(auto_now_add = True)
	is_policy = models.NullBooleanField('Selection is a custom policy', default = False)

	class Meta:
		unique_together = ('label', 'is_policy')

