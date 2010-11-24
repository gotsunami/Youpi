"""
Query processing results. They can be displayed and deleted.
"""

import sys, os, string, curses, os.path, types
import datetime, time
from optparse import OptionParser
from terminal import *
os.environ['DJANGO_SETTINGS_MODULE'] = 'terapix.settings'
if '..' not in sys.path:
	sys.path.insert(0, '..')

try:
	from django.db import IntegrityError
	from django.conf import settings
	#
	from terapix.youpi.models import *
except ImportError:
	print 'Please run this command from the terapix subdirectory.'
	sys.exit(1)

g_limit = 10
g_kind = g_user = None
g_delete = False
g_title_width = 30

def print_processings(tasks):
	total = tasks.count()
	fmt = '%-' + str(g_title_width) + 's %-20s %-8s %-12s %3s'
	print ('%4s ' + fmt) % ('#', 'Title', 'Start', 'Duration', 'User', 'Success')
	print '-' * (56+g_title_width)
	k = 1
	for t in tasks[:g_limit]:
		if t.success: state = 'yes'
		else: state = 'no'
		print ('%04d ' + fmt) % (k, t.title[:g_title_width-1], t.start_date, t.end_date-t.start_date, t.user, state)
		k += 1
	if total > g_limit:
		print "Filtered: latest %d results" % g_limit
	print "Total: %d" % total
	print '-' * (56+g_title_width)

def list_processings(tags=[]):
	"""
	List processing results according to parameters
	"""
	from terapix.lib.processing import find_tasks
	print_processings(find_tasks(tags, g_task_id, g_kind, g_user, g_success, g_failure))

	if g_delete and len(tasks) > 0:
		rels = Rel_it.objects.filter(task__in=tasks)
		print "Rel_it:", len(rels)
		print "Tasks:", len(tasks)
		r = raw_input('Please CONFIRM items deletion? (yes/no) ')
		if r not in ('yes',):
			print "Aborted."
			sys.exit(0)
		print "Deleting..."

		from django.db import transaction
		transaction.enter_transaction_management()
		try:
			for r in rels:
				r.delete()
			if not g_task_id:
				for t in tasks:
					proc = eval("Plugin_%s.objects.get(task=t)" % t.kind.name)
					proc.delete()
					t.delete()
			else:
				t = Processing_task.objects.get(id=g_task_id)
				t.delete()
			transaction.commit()
		except Exception, e:
			transaction.rollback()
			transaction.leave_transaction_management()
			print "Error: %s" % e
			print "Transaction rolled back"
			sys.exit(1)

def main():
	global g_limit, g_kind, g_user, g_delete, g_success, g_failure, g_task_id
	global g_title_width

	parser = OptionParser(description = 'Gets some info on processing results')
	parser.add_option('-d', '--delete', 
			default = False, 
			action = 'store_true', 
			help = 'Delete matched processings, with confirmation'
	)
	parser.add_option('-t', '--tags', 
			default = False, 
			action = 'store', 
			type = 'string',
			dest = 'tags',
			help = 'One tag or comma-separated list of tags'
	)
	parser.add_option('-l', '--limit', 
			default = False, 
			action = 'store', 
			type = 'int',
			dest = 'limit',
			help = "Max number of results returned [default: %d]" % g_limit
	)
	parser.add_option('-k', '--kind', 
			default = False, 
			action = 'store', 
			type = 'string',
			dest = 'kind',
			help = 'Processing kind name (fitsin, scamp, swarp, sex, skel, stiff)'
	)
	parser.add_option('-u', '--user', 
			default = False, 
			action = 'store', 
			type = 'string',
			dest = 'user',
			help = 'User owner'
	)
	parser.add_option('-s', '--success', 
			default = False, 
			action = 'store_true', 
			help = 'Only matches successful processings'
	)
	parser.add_option('-f', '--failure', 
			default = False, 
			action = 'store_true', 
			help = 'Only matches failed processings'
	)
	parser.add_option('-i', '--taskid', 
			default = False, 
			action = 'store', 
			type = 'int',
			dest = 'taskid',
			help = 'Queries only one task'
	)
	parser.add_option('-w', '--title-width', 
			default = False, 
			action = 'store', 
			type = 'int',
			dest = 'twidth',
			help = "Title column width [default: %d]" % g_title_width
	)
	(options, args) = parser.parse_args()
	if len(args): parser.error('takes no argument at all')

	if options.limit:
		g_limit = options.limit
	if options.twidth:
		g_title_width = options.twidth
	g_kind = options.kind
	g_user = options.user
	g_delete = options.delete
	g_success = options.success
	g_failure = options.failure
	g_task_id = options.taskid
	
	try:
		start = time.time()
		if options.tags:
			list_processings(tags=options.tags.split(','))
		else:
			list_processings()

		print "Took: %.2fs" % (time.time()-start)
	except KeyboardInterrupt:
		print "Exiting..."
		sys.exit(2)


if __name__ == '__main__':
	main()
