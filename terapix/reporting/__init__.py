import string, types

class ReportFormat(object):
	"""
	Available report formats
	"""
	CSV, PDF, TXT, HTML = ('CSV', 'PDF', 'TXT', 'HTML')
	@staticmethod
	def formats():
		return (ReportFormat.CSV, ReportFormat.PDF, ReportFormat.TXT, ReportFormat.HTML)

def get_report_data(reports, id):
	"""
	Get global report given a report id
	@param id report id
	@param reports dictionary describing reports
	@returns report as a dictionary
	"""
	if type(reports) != types.ListType:
		raise TypeError, "Reports must be a list"
	if type(id) != types.StringType and type(id) != types.UnicodeType:
		raise TypeError, "Report id must be a string"
	for r in reports:
		if r['id'] == id:
			return r
	return None

