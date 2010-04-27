from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
	AddField('Image', 'pixelscale', models.DecimalField, null=True, max_digits=16, decimal_places=8)
]
