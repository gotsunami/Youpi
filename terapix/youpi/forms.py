from django import forms
from terapix.youpi.models import *

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

	date_obs_min = forms.DateTimeField(required = False, help_text = 'Format: YYYY-MM-DD[ HH:MM:SS]', input_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d'])
	date_obs_max = forms.DateTimeField(required = False, help_text = 'Format: YYYY-MM-DD[ HH:MM:SS]', input_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d'])
	exptime_min = forms.DecimalField(help_text = 'Format:  sec, max digits: 3 (Ex: 500.090)', required = False)
	exptime_max = forms.DecimalField(help_text = 'Format:  sec, max digits: 3 (Ex: 500.090)', required = False)
	ra_dec = forms.CharField(max_length=100, help_text = 'Format: HH:MM:SS or degrees', required = False)
	radius = forms.DecimalField(help_text = 'Degrees', required = False)
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
	sky_background_min = forms.CharField(max_length=100, help_text = 'Format: mag.sE-2', required = False)
	sky_background_max = forms.CharField(max_length=100, help_text = 'Format: mag.sE-2', required = False)
	grades = forms.MultipleChoiceField(choices = grade_choices, required = False)
	comment = forms.CharField(max_length=100, required = False, help_text = 'Grade comment (can be a regexp)')

	def __init__(self, data = None):
		forms.Form.__init__(self, data)
		self.brks = ('Elongation max', 'Airmass max', 'Date obs max', 'Exptime max', 'Seeing max', 
			'Radius', 'Run id', 'Sky background max', 'Mask', 'Object', 'Comment', 'Tags', 'Instruments',
			'Channels', 'Show column report')
