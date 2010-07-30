from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
	AddField('Plugin_swarp', 'useAutoQFITSWeights', models.NullBooleanField, null=True),
	DeleteField('Plugin_swarp', 'useQFITSWeights')
]
