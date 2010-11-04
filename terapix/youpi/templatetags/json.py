
from django import template
from django.template.defaultfilters import stringfilter
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
@stringfilter
def jsonify(object):
	if isinstance(object, QuerySet):
		return mark_safe(serialize('json', object))
	if isinstance(object, str) or isinstance(object, unicode):
		return mark_safe(simplejson.dumps(eval(object)))
	return mark_safe(simplejson.dumps(object))
