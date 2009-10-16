from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
	AddField('Image', 'is_validated', models.NullBooleanField, null=True, initial=True),
	DeleteField('Image', 'QSOstatus'),
	AddField('Ingestion', 'is_validated', models.NullBooleanField, null=True, initial=True),
	DeleteField('Ingestion', 'check_QSO_status')
]
