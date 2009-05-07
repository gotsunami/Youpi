from django.contrib import admin
from terapix.youpi.models import *

class InstrumentAdmin(admin.ModelAdmin):
	list_display = ('name','telescope')

class RunAdmin(admin.ModelAdmin):
	list_display = ('name','instrument')

class ChannelAdmin(admin.ModelAdmin):
	list_display = ('name','instrument')

admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(Run, RunAdmin)
admin.site.register(Channel, ChannelAdmin)

