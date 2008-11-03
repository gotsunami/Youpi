#
# Urls and patterns for Spica2
#

from django.contrib.auth.views import login
from terapix.spica2.views import logout
from django.conf.urls.defaults import *

urlpatterns = patterns(
	# Module that handles queries
	'terapix.spica2.views',
	
	# Callback functions depending on urls matches
	(r'^spica2/$', 'index'),
	(r'^spica2/newindex/$', 'index2'),
	(r'^spica2/ingestion/$', 'ing'),
	(r'^spica2/ingestion/ingestion1/$', 'local_ingestion'),
	(r'^spica2/ingestion/ingestion2/$', 'condor_ingestion'),
	(r'^spica2/ingestion/imgCount/$', 'ingestion_img_count'),
	(r'^spica2/img/(?P<image_name>.*?)/$', 'aff_img'),
	(r'^spica2/preIngestion/$', 'preingestion'),
	(r'^spica2/processing/$', 'processing'),
	(r'^spica2/processing/(.*?)/$', 'render_plugin'),
	(r'^spica2/cluster/status/$', 'condor_status'),
	(r'^spica2/cluster/nodes/$', 'condor_hosts'),
	(r'^spica2/cluster/softwares/$', 'condor_softs'),
	(r'^spica2/cluster/softwares/versions/$', 'softs_versions'),
	(r'^spica2/cluster/softwares/versions/refresh/$', 'query_condor_node_for_versions'),
	(r'^spica2/cluster/softwares/versions/delete/$', 'clear_softs_versions'),
	(r'^spica2/monitoring/$', 'monitoring'),
	(r'^spica2/monitoring/live/$', 'live_monitoring'),
	(r'^spica2/monitoring/softwares/$', 'soft_version_monitoring'),
	(r'^spica2/condor/cancel/$', 'job_cancel'),
	(r'^spica2/results/$', 'results'),
	(r'^spica2/results/filter/$', 'task_filter'),
	(r'^spica2/results/stats/$', 'dir_stats'),
	(r'^spica2/results/(.*?)/(.*?)/$', 'single_result'),

	# Prefs and docs
	(r'^spica2/preferences/$', 'preferences'),
	(r'^spica2/documentation/$', 'documentation'),

	# Sandbox for testing django form processing
#	(r'^spica2/sandbox/$', 'test_form'),
#	(r'^spica2/js/$', 'test_js'),

	# AJAX dynamic folder populate
	(r'^spica2/populate/(.*?)/(.*?)/(.*)/$', 'open_populate'),
	(r'^spica2/populate_generic/(.*?)/(.*?)/(.*)/$', 'open_populate_generic'),

	# Pre-ingestion
	(r'^spica2/process/preingestion/tablescount/$', 'preingestion_tables_count'),
	(r'^spica2/process/preingestion/run/$', 'preingestion_run'),
	(r'^spica2/process/preingestion/tablefields/$', 'preingestion_table_fields'),
	(r'^spica2/process/preingestion/query/$', 'preingestion_custom_query'),

	# Processing
	(r'^spica2/process/plugin/$', 'processing_plugin'),
	#(r'^spica2/process/query/imgsFromIdList/(.*)$', 'processing_imgs_from_idlist'),
	(r'^spica2/process/query/imgsFromIdList/$', 'processing_imgs_from_idlist_post'),
	(r'^spica2/process/query/remapIds/$', 'processing_imgs_remap_ids'),
	(r'^spica2/process/db/saveSelection/$', 'processing_save_image_selection'),
	(r'^spica2/process/db/getSelections/$', 'processing_get_image_selections'),
	(r'^spica2/process/db/delSelection/$', 'processing_delete_image_selection'),
	(r'^spica2/process/checkConfigFileExists/$', 'processing_check_config_file_exists'),

	# History
	(r'^spica2/history/ingestion/$', 'history_ingestion'),
	(r'^spica2/history/ingestion/report/(.*?)/$', 'show_ingestion_report'),
	(r'^spica2/history/preingestion/$', 'history_preingestion'),

	# Shopping cart related
	(r'^spica2/cart/$', 'cart_view'),
	(r'^spica2/cart/cookiecheck/$', 'cart_cookie_check'),
	(r'^spica2/cart/additem/$', 'cart_add_item'),
	(r'^spica2/cart/delitem/$', 'cart_delete_item'),
	(r'^spica2/cart/itemsCount/$', 'cart_items_count'),

	# Grading
	(r'^spica2/grading/panel/(.*?)/(.*?)/$', 'grading_panel'),
	(r'^spica2/grading/cancel/(.*?)/(.*?)/$', 'grading_cancel'),
	(r'^spica2/grading/(.*?)/(.*?)/$', 'image_grading'),

	# Auto-completion
	(r'^spica2/autocompletion/(.*?)/(.*?)/$', 'autocomplete'),

    # Uncomment this for admin
    (r'^spica2/admin/', include('django.contrib.admin.urls')),

	# User authentication
    (r'^spica2/accounts/login/$', login),
    (r'^spica2/accounts/logout/$', logout),

	(r'^spica2/uploadFile/$', 'upload_file'),
	(r'^spica2/uploadFile/batch/parseContent/$', 'batch_parse_content'),
	(r'^spica2/uploadFile/batch/viewContent/(.*)/$', 'batch_view_content'),
	(r'^spica2/uploadFile/batch/viewSelection/$', 'batch_view_selection'),

	# User profile
	(r'^spica2/profile/loadCondorNodeSelection/$', 'profile_load_condor_nodes_selection'),
	(r'^spica2/profile/saveCondorNodeSelection/$', 'profile_save_condor_nodes_selection'),

	# Plots
	(r'^spica2/plot/sky/selections/$', 'plot_sky_selections'),

	# API documentation
    (r'^spica2/api/(.*)/$', 'browse_api')
)
	
