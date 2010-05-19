from terapix.youpi.forms import ReportAdvancedImageForm
from youpi.cviews import manager
import string

class ReportFormat(object):
	"""
	Available report formats
	"""
	CSV, PDF, TXT, HTML = ('CSV', 'PDF', 'TXT', 'HTML')
	@staticmethod
	def formats():
		return (ReportFormat.CSV, ReportFormat.PDF, ReportFormat.TXT, ReportFormat.HTML)

# Global (non-plugin related) reports definition
selopts = """Select a processing type: <select name="kind_select">%s</select>""" % \
	string.join(map(lambda x: """<option value="%s">%s</option>""" % (x[0], x[1]), [(p.id, p.optionLabel) for p in manager.plugins]), '\n')

global_reports = [
	{	'id': 'imssavedselections',	
		'title': 'List of saved selections from the image selector', 
		'description': 'This report generates a list of all custom saved selections available in the image selector.',
		'formats': (ReportFormat.CSV, ReportFormat.TXT, ReportFormat.HTML),
	},
	{	'id': 'procresults', 
		'title': 'List of processing results', 
		'options': selopts,
		'description': 'This report generates a CSV file (plain text) with all processing results. Depending on the current state of ' + \
			'the database, it may take some time to generate.',
		'formats': (ReportFormat.CSV, ReportFormat.TXT, ReportFormat.HTML),
	},
	{	'id': 'advimgreport',	
		'title': 'Advanced image report',
		'description': 'This report generates a criteria-based list of ingested images. The result set can be exported to the image selector ' + \
			'for processing the image selection. A PDF report can be generated too.',
		'template' : 'reports/advanced-image-report-options.html',
		'context': {'form' : ReportAdvancedImageForm()},
		'formats': (ReportFormat.CSV, ReportFormat.TXT, ReportFormat.HTML),
	},
]
