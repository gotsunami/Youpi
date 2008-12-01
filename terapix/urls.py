#
# Urls and patterns for Youpi
#

from django.contrib.auth.views import login
from terapix.youpi.views import logout
from django.conf.urls.defaults import *

urlpatterns = patterns(
	# Module that handles queries
	'terapix.youpi.views',
	
	# Callback functions depending on urls matches
	(r'^youpi/$', 'index'),
	(r'^youpi/newindex/$', 'index2'),
	(r'^youpi/ingestion/$', 'ing'),
	(r'^youpi/ingestion/ingestion1/$', 'local_ingestion'),
	(r'^youpi/ingestion/ingestion2/$', 'condor_ingestion'),
	(r'^youpi/ingestion/imgCount/$', 'ingestion_img_count'),
	(r'^youpi/img/(?P<image_name>.*?)/$', 'aff_img'),
	(r'^youpi/preIngestion/$', 'preingestion'),
	(r'^youpi/processing/$', 'processing'),
	(r'^youpi/processing/(.*?)/$', 'render_plugin'),
	(r'^youpi/cluster/status/$', 'condor_status'),
	(r'^youpi/cluster/nodes/$', 'condor_hosts'),
	(r'^youpi/cluster/softwares/$', 'condor_softs'),
	(r'^youpi/cluster/softwares/versions/$', 'softs_versions'),
	(r'^youpi/cluster/softwares/versions/refresh/$', 'query_condor_node_for_versions'),
	(r'^youpi/cluster/softwares/versions/delete/$', 'clear_softs_versions'),
	(r'^youpi/monitoring/$', 'monitoring'),
	(r'^youpi/monitoring/live/$', 'live_monitoring'),
	(r'^youpi/monitoring/softwares/$', 'soft_version_monitoring'),
	(r'^youpi/condor/cancel/$', 'job_cancel'),
	(r'^youpi/condor/setup/$', 'condor_setup'),
	(r'^youpi/results/$', 'results'),
	(r'^youpi/results/filter/$', 'task_filter'),
	(r'^youpi/results/stats/$', 'dir_stats'),
	(r'^youpi/results/(.*?)/(.*?)/$', 'single_result'),

	# Prefs and docs
	(r'^youpi/preferences/$', 'preferences'),
	(r'^youpi/preferences/theme/set/$', 'set_current_theme'),
	(r'^youpi/documentation/$', 'documentation'),

	# Sandbox for testing django form processing
#	(r'^youpi/sandbox/$', 'test_form'),
#	(r'^youpi/js/$', 'test_js'),

	# AJAX dynamic folder populate
	(r'^youpi/populate/(.*?)/(.*?)/(.*)/$', 'open_populate'),
	(r'^youpi/populate_generic/(.*?)/(.*?)/(.*)/$', 'open_populate_generic'),

	# Pre-ingestion
	(r'^youpi/process/preingestion/tablescount/$', 'preingestion_tables_count'),
	(r'^youpi/process/preingestion/run/$', 'preingestion_run'),
	(r'^youpi/process/preingestion/tablefields/$', 'preingestion_table_fields'),
	(r'^youpi/process/preingestion/query/$', 'preingestion_custom_query'),

	# Processing
	(r'^youpi/process/plugin/$', 'processing_plugin'),
	#(r'^youpi/process/query/imgsFromIdList/(.*)$', 'processing_imgs_from_idlist'),
	(r'^youpi/process/query/imgsFromIdList/$', 'processing_imgs_from_idlist_post'),
	(r'^youpi/process/query/remapIds/$', 'processing_imgs_remap_ids'),
	(r'^youpi/process/db/saveSelection/$', 'processing_save_image_selection'),
	(r'^youpi/process/db/getSelections/$', 'processing_get_image_selections'),
	(r'^youpi/process/db/delSelection/$', 'processing_delete_image_selection'),
	(r'^youpi/process/checkConfigFileExists/$', 'processing_check_config_file_exists'),

	# History
	(r'^youpi/history/ingestion/$', 'history_ingestion'),
	(r'^youpi/history/ingestion/report/(.*?)/$', 'show_ingestion_report'),
	(r'^youpi/history/preingestion/$', 'history_preingestion'),

	# Shopping cart related
	(r'^youpi/cart/$', 'cart_view'),
	(r'^youpi/cart/cookiecheck/$', 'cart_cookie_check'),
	(r'^youpi/cart/additem/$', 'cart_add_item'),
	(r'^youpi/cart/delitem/$', 'cart_delete_item'),
	(r'^youpi/cart/itemsCount/$', 'cart_items_count'),

	# Grading
	(r'^youpi/grading/panel/(.*?)/(.*?)/$', 'grading_panel'),
	(r'^youpi/grading/cancel/(.*?)/(.*?)/$', 'grading_cancel'),
	(r'^youpi/grading/(.*?)/(.*?)/$', 'image_grading'),

	# Auto-completion
	(r'^youpi/autocompletion/(.*?)/(.*?)/$', 'autocomplete'),

    # Uncomment this for admin
    (r'^youpi/admin/', include('django.contrib.admin.urls')),

	# User authentication
    (r'^youpi/accounts/login/$', login),
    (r'^youpi/accounts/logout/$', logout),

	(r'^youpi/uploadFile/$', 'upload_file'),
	(r'^youpi/uploadFile/batch/parseContent/$', 'batch_parse_content'),
	(r'^youpi/uploadFile/batch/viewContent/(.*)/$', 'batch_view_content'),
	(r'^youpi/uploadFile/batch/viewSelection/$', 'batch_view_selection'),

	(r'^youpi/profile/delCondorNodeSelection/$', 'del_condor_node_selection'),
	(r'^youpi/profile/getCondorNodeSelections/$', 'get_condor_node_selections'),
	(r'^youpi/profile/getCondorSelectionMembers/$', 'get_condor_selection_members'),
	(r'^youpi/profile/saveCondorNodeSelection/$', 'save_condor_node_selection'),

	# Plots
	(r'^youpi/plot/sky/selections/$', 'plot_sky_selections'),

	# API documentation
    (r'^youpi/api/(.*)/$', 'browse_api')
)
