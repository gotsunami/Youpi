from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
	AddField('Instrument', 'itt', models.TextField, null=True)
]
