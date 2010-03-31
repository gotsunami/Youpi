from django import forms
from terapix.youpi.models import *

class AlphaField(forms.CharField):
	"""
	Custom form field for right ascension values. Detects if 
	value is in decimal or sexagesimal system, then convert the 
	value to a float (if needed)
	"""
	def clean(self, value):
		import re
		if not value: return value
		value = value.strip()
		# Is it in degrees? (float)
		try:
			value = float(value)
		except ValueError:
			if not re.match(r'^\d{2}:\d{2}:\d{2}(\.\d{3})?$', value):
				raise forms.ValidationError('The RA format is invalid.')
			else:
				# Conversion to decimal
				from terapix.lib.coordconvert import Alpha
				value = Alpha.sex_to_deg(value)
		return value

class DeltaField(forms.CharField):
	"""
	Custom form field for declination values. Detects if 
	value is in decimal or sexagesimal system, then convert the 
	value to a float (if needed)
	"""
	def clean(self, value):
		import re
		if not value: return value
		value = value.strip()
		# Is it in degrees? (float)
		try:
			value = float(value)
		except ValueError:
			if not re.match(r'^[+-]?\d{2}:\d{2}:\d{2}(\.\d{3})?$', value):
				raise forms.ValidationError('The DEC format is invalid.')
			else:
				# Conversion to decimal
				from terapix.lib.coordconvert import Delta
				value = Delta.sex_to_deg(value)
		return value

class RadiusField(forms.CharField):
	"""
	Custom form field for angular radius.
	Accepted input format are: dd[:dm] or :dm or degrees (decimal)
	Returns a value converted to degrees (dec)
	"""
	def clean(self, value):
		import re
		if not value: return value
		value = value.strip()
		# Is it in degrees? (float)
		try:
			value = float(value)
		except ValueError:
			if not re.match(r'^\d{2}:\d{2}$', value): 		# degrees:minutes
				if not re.match(r'^\d{2}$', value):			# degrees
					if not re.match(r'^:\d{2}$', value):	# minutes
						raise forms.ValidationError('The radius format is invalid.')
					else:
						value = '00' + value + ':00' # Add degrees and seconds
				else:
					value += ':00:00' # Add minutes and seconds
			else:
				value += ':00' # Add seconds
			from terapix.lib.coordconvert import Delta
			value = Delta.sex_to_deg(value)
		return value

class ReportAdvancedImageForm(forms.Form):
	insts = Instrument.objects.all().order_by('name')
	channels = Channel.objects.all().order_by('name')
	runs = Run.objects.all().order_by('name')
	tags = Tag.objects.all().order_by('name')

	inst_choices =  [(i.id, i.name) for i in insts]
	inst_choices.insert(0, (-1, ''))
	chan_choices =  [(i.id, i.name) for i in channels]
	chan_choices.insert(0, (-1, ''))
	run_choices =  [(i.id, i.name) for i in runs]
	run_choices.insert(0, (-1, ''))
	tag_choices =  [(i.id, i.name) for i in tags]
	tag_choices.insert(0, (-1, ''))
	grade_choices = list(GRADE_SET)
	grade_choices.insert(0, (-1, ''))
	columns = ('Image checksum', 'Image path', 'Date obs', 'Exptime', 'Right ascension (RA)', 'Declination (DEC)', 'Run id', 'Flat', 'Mask', 'Object', 'Airmass',
			'Tags', 'Instrument', 'Channel', 'Elongation', 'Seeing', 'Sky background', 'Grade', 'Comment')

	# Selected columns in final report
	show_column_in_report = forms.MultipleChoiceField(
		choices = [(d, d) for d in columns], 
		widget = forms.SelectMultiple(attrs = {'size': '6'}), 
		help_text = 'Select colums to display in final report', 
		initial = ('Date obs',)
	)
	# Image related
	date_obs_min = forms.DateTimeField(required = False, help_text = 'Format: YYYY-MM-DD[ HH:MM:SS]', input_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d'])
	date_obs_max = forms.DateTimeField(required = False, help_text = 'Format: YYYY-MM-DD[ HH:MM:SS]', input_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d'])
	exptime_min = forms.DecimalField(help_text = 'Format:  sec, max digits: 3 (Ex: 500.090)', required = False)
	exptime_max = forms.DecimalField(help_text = 'Format:  sec, max digits: 3 (Ex: 500.090)', required = False)
	right_ascension_RA = AlphaField(max_length=100, help_text = 'Format: hh:mm:ss[.xxx] or degrees (decimal)', required = False)
	declination_DEC = DeltaField(max_length=100, help_text = 'Format: [+|-]dd:dm:ds[.xxx] or degrees (decimal)', required = False)
	radius =RadiusField(help_text = 'Format: dd[:dm] or :dm or degrees (decimal)', required = False)
	run_id = forms.ChoiceField(choices = run_choices, required = False)
	flat = forms.CharField(max_length=100, required = False, help_text = 'Flat name (can be a regexp)')
	mask = forms.CharField(max_length=100, required = False, help_text = 'Mask name (can be a regexp)')
	object = forms.CharField(max_length=100, required = False, help_text = 'Object name (can be a regexp)')
	airmass_min = forms.DecimalField(required = False)
	airmass_max = forms.DecimalField(required = False)
	tags = forms.MultipleChoiceField(choices = tag_choices, widget = forms.SelectMultiple(attrs = {'size': '6'}), required = False)
	instruments = forms.MultipleChoiceField(choices = inst_choices, widget = forms.SelectMultiple(attrs = {'size': '6'}), required = False)
	channels = forms.MultipleChoiceField(choices = chan_choices, widget = forms.SelectMultiple(attrs = {'size': '6'}), required = False)
	# QFits related
	elongation_min = forms.DecimalField(required = False)
	elongation_max = forms.DecimalField(required = False)
	seeing_min = forms.DecimalField(help_text = 'Format:  arcsec', required = False)
	seeing_max = forms.DecimalField(help_text = 'Format:  arcsec', required = False)
	sky_background_min = forms.DecimalField(help_text = 'Format: mag.sE-2', required = False)
	sky_background_max = forms.DecimalField(help_text = 'Format: mag.sE-2', required = False)
	grades = forms.MultipleChoiceField(choices = grade_choices, required = False)
	comment = forms.CharField(max_length=100, required = False, help_text = 'Grade comment (can be a regexp)')

	def __init__(self, data = None):
		forms.Form.__init__(self, data)
		# Used to set break from templates/reports/advances-image-report-options.html
		self.brks = ('Elongation max', 'Airmass max', 'Date obs max', 'Exptime max', 'Seeing max', 
			'Radius', 'Run id', 'Sky background max', 'Mask', 'Object', 'Comment', 'Tags', 'Instruments',
			'Channels', 'Show column in report')

	def clean(self):
		"""
		Ensure that if one of ra, dec, radius is filled in, the remaining 2 fields are defined too
		"""
		cleaned_data = self.cleaned_data
		fields = ('right_ascension_RA', 'declination_DEC', 'radius')
		s = len(fields)
		for k in range(s):
			if cleaned_data.get(fields[k]):
				if not cleaned_data.get(fields[(k+1)%s]) or not cleaned_data.get(fields[(k+2)%s]):
					raise forms.ValidationError('Both right ascension, declination and radius must be filled once any of them is provided.')
		return cleaned_data
