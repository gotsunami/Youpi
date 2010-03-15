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

	date_obs_min = forms.CharField(max_length=100, required = False)
	date_obs_max = forms.CharField(max_length=100, required = False)
	range_exptime = forms.CharField(max_length=100, help_text = 'Format:  sec', required = False)
	ra_dec = forms.CharField(max_length=100, help_text = 'Format: HH:MM:SS', required = False)
	radius = forms.CharField(max_length=100, help_text = 'Degrees', required = False)
	run_id = forms.ChoiceField(choices = run_choices, required = False)
	flat = forms.CharField(max_length=100, required = False)
	mask = forms.CharField(max_length=100, required = False)
	object = forms.CharField(max_length=100, required = False)
	tags = forms.MultipleChoiceField(choices = tag_choices, widget = forms.SelectMultiple(attrs = {'size': '6'}), required = False)
	instruments = forms.MultipleChoiceField(choices = inst_choices, widget = forms.SelectMultiple(attrs = {'size': '6'}), required = False)
	channels = forms.MultipleChoiceField(choices = chan_choices, widget = forms.SelectMultiple(attrs = {'size': '6'}), required = False)
	# QFits related
	elongation_min = forms.CharField(max_length=100, required = False)
	elongation_max = forms.CharField(max_length=100, required = False)
	airmass_min = forms.CharField(max_length=100, required = False)
	airmass_max = forms.CharField(max_length=100, required = False)
	seeing_min = forms.CharField(max_length=100, help_text = 'Format:  arcsec', required = False)
	seeing_max = forms.CharField(max_length=100, help_text = 'Format:  arcsec', required = False)
	sky_background_min = forms.CharField(max_length=100, help_text = 'Format: mag.sE-2', required = False)
	sky_background_max = forms.CharField(max_length=100, help_text = 'Format: mag.sE-2', required = False)
	grade = forms.MultipleChoiceField(choices = grade_choices, required = False)
	comment = forms.CharField(max_length=100, required = False)

	def __init__(self, data = None):
		forms.Form.__init__(self, data)
		self.brks = ('Elongation max', 'Airmass max', 'Date obs max', 'Range exptime', 'Seeing max', 
			'Radius', 'Run id', 'Sky background max', 'Mask', 'Object', 'Comment', 'Tags', 'Instruments',
			'Channels', 'Show column report')
