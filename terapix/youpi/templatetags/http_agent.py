
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def check_firefox(agent):
	import re
	return re.search(r'Firefox\/\d\.\d{1,}', agent)
