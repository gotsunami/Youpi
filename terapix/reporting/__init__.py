import string, types

class ReportFormat(object):
	"""
	Available report formats
	"""
	CSV, PDF, HTML, LATEX, PS, TARBALL = ('CSV', 'PDF', 'HTML', 'LaTeX', 'Postscript', 'Tarball',)

	@staticmethod
	def formats():
		return map(lambda x: {'name': x[0], 'ext': x[1]}, (
			(ReportFormat.CSV, 'csv'),
			(ReportFormat.HTML,'html'),
			(ReportFormat.LATEX, 'tex'),
			(ReportFormat.PS, 'ps'),
			(ReportFormat.PDF, 'pdf'),
			(ReportFormat.TARBALL, 'tar.gz'),
		))

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

