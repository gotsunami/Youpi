from django.db import models
from django.contrib.gis.db import models
from django.contrib.auth.models import User

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

	class Admin:
		list_display = ('name','telescope')
		fields = (('Technical Informations', {'fields':('name','telescope','url','timezone','altitude')}),
			('Physical Informations',{'fields':('astrinstru_key','photinstru_key','nchips','path'),'classes': 'collapse'}),)

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

	class Admin:
		list_display = ('name','instrument')
		list_filter = ('instrument',)
		fields=(('Technical Informations ', {'fields':('name','instrument','pi','url','email')}),
			('Date Informations ',{'fields':('processrequestdate','datestart','datend','datedownload','releasedate'),'classes': 'collapse'}),)

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

	class Admin:
		list_display = ('name','instrument')
		list_filter = ('instrument',)
		fields = (('Technical Informations', {'fields':('instrument','name','url')}),
			('Physical Informations',{'fields':('wavelength','wavecurve','transcurve','magoffsets'),'classes': 'collapse'}),)

	def __unicode__(self):
		return self.name

class CalibrationKit(models.Model):
	name = models.CharField(max_length = 80,blank=True,null=True)
	badpixelmask = models.CharField(max_length = 512,blank=True,null=True,help_text="")
	flatfield = models.CharField(max_length = 512,blank=True,null=True,help_text="")

	class Meta:
		verbose_name = "Calibration kit"
		verbose_name_plural = "Calibration kits"

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

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	
	class Meta:
		verbose_name="Image selection"

	def __unicode__(self):
		return self.name

class ConfigFile(models.Model):
	"""
	Standalone table, no foreign key constraint.
	Useful to store (serialized) data related to configuration files to use for processing
	"""
	
	# Name of configuration content
	name = models.CharField(max_length = 80)
	# Config file full content (clear text)
	content = models.TextField()
	# Serialized data (base64 encoding over marshal serialization)
	data = models.TextField(null=True)
	date = models.DateTimeField(auto_now_add = True)

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	kind = models.ForeignKey(Processing_kind, db_column = 'kind_id')
	
	class Meta:
		unique_together = ('name', 'kind')
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

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	
	class Meta:
		unique_together = ('key', 'user')
		verbose_name="Miscallenous data"

class CartItem(models.Model):
	"""
	Standalone table, no foreign key constraint.
	Useful to store (serialized) data related to shopping cart items
	"""
	
	# Name of configuration content
	name = models.CharField(max_length = 80, unique = True)
	date = models.DateTimeField(auto_now_add = True)
	# Serialized data (base64 encoding over marshal serialization)
	data = models.TextField()

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	kind = models.ForeignKey(Processing_kind, db_column = 'kind_id')
	
	class Meta:
		verbose_name="Saved item of shopping cart"

	def __unicode__(self):
		return self.name

class Image(models.Model):
	name = models.CharField(max_length = 20,blank=True,unique = True,help_text="name of image")
	skyfootprint = models.MultiPolygonField()
	centerfield = models.PointField()
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
	# From preingestion step
	QSOstatus = models.CharField(max_length = 20,blank=True,null=True,help_text="Status from the related FITS table ")

	# FKs constraints
	channel = models.ForeignKey(Channel, db_column='channel_id')
	run = models.ForeignKey('Run', db_column='run_id')
	calibrationkit = models.ForeignKey(CalibrationKit,db_column='calibrationkit_id')
	ingestion = models.ForeignKey('Ingestion',db_column='ingestion_id')
	instrument = models.ForeignKey(Instrument, db_column = 'instrument_id')
	
	class Meta:
		verbose_name = "Ingested image"
		verbose_name_plural = "Ingested images"

	class Admin:
		pass

	def __unicode__(self):
		return self.name

class Processing_task(models.Model):
	bools = ((False, 'No'), (True, 'Yes'))
	start_date = models.DateTimeField(auto_now_add = True, help_text = 'Beginning of processing')
	end_date = models.DateTimeField(help_text = 'End of processing')
	success = models.BooleanField('QSO status', null = True, default = False, choices = bools)
	hostname = models.CharField(max_length = 255, null = True, help_text="Processing host (local or cluster node)")
	# Serialized data (base64 encoding over zlib compression)
	error_log = models.TextField(null=True)
	results_output_dir = models.CharField(max_length = 255, null = False, help_text="Output directory for results")
	title = models.CharField(max_length = 255, help_text="Processing task title")

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
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
	thumbnails = models.BooleanField('Has image thumbnails', default = False)

	# FKs constraints
	task = models.ForeignKey(Processing_task, db_column = 'task_id')
	
	class Meta:
		verbose_name = "SCAMP plugin"

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

	# FKs constraints
	task = models.ForeignKey(Processing_task, db_column = 'task_id')
	
	class Meta:
		verbose_name = "QualityFits-In plugin data"

	def __unicode__(self):
		return self.name

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
	grade = models.CharField(max_length = 1, blank = True, null = True, choices = GRADE_SET, help_text = "QualityFITS in grade")

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')
	fitsin = models.ForeignKey(Plugin_fitsin, db_column = 'fitsin_id')
	comment = models.ForeignKey(FirstQComment, db_column = 'comment_id')
	
	class Meta:
		verbose_name = "First Quality Evaluation"
		unique_together = ('user', 'fitsin')

class FinalQEval(models.Model):
	"""
	Final quality evaluation.
	"""

	custom_comment = models.CharField(max_length = 255)
	date = models.DateTimeField(auto_now_add = True)
	grade = models.CharField(max_length = 1, blank = True, null = True, choices = GRADE_SET, help_text = "QualityFITS out grade")

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
	check_fitsverify = models.BooleanField('Fitsverify status', default=False, choices = check_states)
	check_QSO_status = models.BooleanField('QSO status', default=False, choices = check_states)
	check_multiple_ingestion = models.BooleanField('Multiple ingestion status', default=False, choices = check_states)
	exit_code = models.BooleanField('Exit code status', default=False, choices = ((False, 'Failure'), (True, 'Success')))
	# Serialized data (base64 encoding over zlib compression)
	report = models.TextField(blank = True, null = True)

	# FKs constraints
	user = models.ForeignKey(User, db_column = 'user_id')

	class Meta:
		verbose_name="Ingestion"

	def __unicode__(self):
		return "Ingestion" + str(self.id)
	
class Astrophotocalibration(models.Model):
	astrefcat = models.CharField(max_length = 80,blank=True,null=True,help_text="")
	xmlpath = models.CharField(max_length = 512,blank=True,null=True,help_text="")
	flatfield = models.CharField(max_length = 512,blank=True,null=True,help_text="")
	outputzp = models.DecimalField(max_digits = 16,decimal_places = 8,null=True,blank=True,help_text="")

	class Meta:
		verbose_name = "Astrometric/Photometric Calibration"
		verbose_name_plural = "Astrometric/Photometric Calibrations"

	class Admin:
		list_display = ('astrefcat','xmlpath','flatfield','outputzp')
		list_filter = ('astrefcat','xmlpath','flatfield','outputzp',)
		fields = (('General Informations', {'fields':('astrefcat','xmlpath','flatfield','outputzp',)}),)

	def __unicode__(self):
		return self.listname
       
class Coaddition(models.Model):
	image = models.ForeignKey(Image,null=True,blank= True,db_column='image_id')
	listname = models.CharField(max_length = 20,blank=True,null=True,help_text="")

	class Meta:
		verbose_name = "Coadded Image"
		verbose_name_plural = "Coadded Images"

	def __unicode__(self):
		return self.listname
       
# class Image_has_coaddition(models.Model):
# 	image = models.ForeignKey(Image,null=True,blank= True,db_column='image_id')
# 	coaddition = models.ForeignKey(Coaddition,null=True,blank= True,db_column='coaddition_id')
# 	astrophotocalibration = models.ForeignKey(Astrophotocalibration,null=True,blank= True,db_column='astrophotocalibration_id')
# 	class Meta:
# 		unique_together = ('astrophotocalibration','image','coaddition')
# 		verbose_name ="Ingested Image involved in Coaddition"
# 		verbose_name_plural ="Ingested Images involved in Coaddition"
# 	class Admin:
# 	       pass
#                list_display = ('image','coaddition')
# 	       list_filter = ('coaddition','image')
# 	       search_fields = ('image_name','coaddition')
# 	       #fields=(('Informations generales', {'fields':('astrophotocalibration','image','coaddition')}),
# 		#)
# 	def __str__(self):
# 		return self.image

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
	is_phot = models.BooleanField('is_phot', default=False,help_text="")

	class Meta:
		unique_together = [('name', 'run', 'fitstable')]

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

class Rel_ai(models.Model):
	"""
	Astrophotocalibration-Image relation
	"""

	# FKs constraints
	astrophotocalibration = models.ForeignKey(Astrophotocalibration,null=True,blank= True,db_column='astrophotocalibration_id')
	image = models.ForeignKey(Image,null=True,blank= True,db_column='image_id')

	class Meta:
		unique_together = ('astrophotocalibration','image')
		verbose_name="Ingested Image involved in Astrometric/Photometric Calibration"
		verbose_name_plural="Ingested Images involved in Astrometric/Photometric Calibration"

	def __unicode__(self):
		return self.astrophotocalibration
       
class SiteProfile(models.Model):
	# Mandatory
	user = models.ForeignKey(User, unique = True)

	# Current user GUI style
	guistyle = models.CharField(max_length = 255, default = 'default')
	# Current user Condor's nodes selection (in shopping cart)
	# Serialized data (base64 encoding over marshal serialization)
	condornodesel = models.TextField()

class CondorNodeSel(models.Model):
	# Mandatory
	user = models.ForeignKey(User)

	label = models.CharField(max_length = 255)
	# Serialized data (base64 encoding over marshal serialization)
	nodeselection = models.TextField()
	date = models.DateTimeField(auto_now_add = True)
