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

# vim: set ts=4
# Create your forms here.
#
from django import newforms as forms

TOPIC_CHOICES = (
	('nochoice', '-- Make a choice --'),
	('general', 'General enquiry'),
	('bug', 'Bug report'),
	('suggestion', 'Suggestion')
)

class ContactForm(forms.Form):
	topic = forms.ChoiceField(choices = TOPIC_CHOICES)
	message = forms.CharField(widget = forms.Textarea(), required = False)
	email_sender = forms.EmailField(required = False, help_text = 'This is my sender help !')
	great = forms.CharField(widget = forms.CheckboxInput())

	def clean_message(self):
		topic = self.cleaned_data.get('topic', '')
		if topic == 'nochoice':
			raise forms.ValidationError("Topix: %s" % topic)
		return topic
