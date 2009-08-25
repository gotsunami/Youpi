##############################################################################
#
# Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
#                    Mathias Monnerville <monnerville@iap.fr>
#                    Gregory Semah <semah@iap.fr>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
##############################################################################

#
# Urls and patterns for Youpi
#

from django.contrib.auth.views import login
from terapix.youpi.views import logout
from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
	# Module that handles queries
	'terapix.youpi.views',
	
	# Callback functions depending on urls matches
	(r'^youpi/$', 'index'),
	(r'^youpi/ingestion/$', 'ing'),
	(r'^youpi/ingestion/ingestion2/$', 'condor_ingestion'),
	(r'^youpi/ingestion/imgCount/$', 'ingestion_img_count'),
	(r'^youpi/image/info/$', 'get_image_info'),
	(r'^youpi/img/(?P<image_name>.*?)/$', 'aff_img'),
	(r'^youpi/preIngestion/$', 'preingestion'),
	(r'^youpi/processing/$', 'processing'),
	(r'^youpi/processing/(.*?)/$', 'render_plugin'),

	# Cluster
	(r'^youpi/cluster/computeRequirementString/$', 'compute_requirement_string'),
	(r'^youpi/cluster/delCondorNodeSelection/$', 'del_condor_node_selection'),
	(r'^youpi/cluster/delCondorPolicy/$', 'del_condor_policy'),
	(r'^youpi/cluster/getCondorNodeSelections/$', 'get_condor_node_selections'),
	(r'^youpi/cluster/getCondorRequirementString/$', 'get_condor_requirement_string'),
	(r'^youpi/cluster/getCondorSelectionMembers/$', 'get_condor_selection_members'),
	(r'^youpi/cluster/getCondorPolicies/$', 'get_condor_policies'),
	(r'^youpi/cluster/getPolicyData/$', 'get_policy_data'),
	(r'^youpi/cluster/nodes/$', 'condor_hosts'),
	(r'^youpi/cluster/saveCustomReqStr/$', 'save_condor_custom_reqstr'),
	(r'^youpi/cluster/saveNodeSelection/$', 'save_condor_node_selection'),
	(r'^youpi/cluster/savePolicy/$', 'save_condor_policy'),
	(r'^youpi/cluster/softwares/$', 'condor_softs'),
	(r'^youpi/cluster/softwares/versions/$', 'softs_versions'),
	(r'^youpi/cluster/softwares/versions/refresh/$', 'query_condor_node_for_versions'),
	(r'^youpi/cluster/softwares/versions/delete/$', 'clear_softs_versions'),
	(r'^youpi/cluster/status/$', 'condor_status'),
	(r'^youpi/cluster/logs/$', 'get_condor_log_files_links'),
	(r'^youpi/cluster/log/(.*?)/(.*?)/$', 'show_condor_log_file'),

	(r'^youpi/monitoring/$', 'monitoring'),
	(r'^youpi/monitoring/live/$', 'live_monitoring'),
	(r'^youpi/monitoring/softwares/$', 'soft_version_monitoring'),
	(r'^youpi/condor/cancel/$', 'job_cancel'),
	(r'^youpi/condor/setup/$', 'condor_setup'),
	(r'^youpi/report/(.*?)/(.*?)/$', 'get_report'),
	(r'^youpi/reporting/$', 'reporting'),
	(r'^youpi/results/$', 'results'),
	(r'^youpi/results/delete/$', 'delete_processing_task'),
	(r'^youpi/results/filter/$', 'task_filter'),
	(r'^youpi/results/stats/$', 'dir_stats'),
	(r'^youpi/results/(.*?)/(.*?)/$', 'single_result'),

	(r'^youpi/tags/$', 'tags'),
	(r'^youpi/tags/fetchtags/$', 'fetch_tags'),
	(r'^youpi/tags/info/$', 'get_tag_info'),
	(r'^youpi/tags/save/$', 'save_tag'),
	(r'^youpi/tags/update/$', 'update_tag'),
	(r'^youpi/tags/delete/$', 'delete_tag'),
	(r'^youpi/tags/mark/$', 'tag_mark_images'),
	(r'^youpi/tags/unmark/$', 'tag_unmark_images'),
	(r'^youpi/tags/images/$', 'get_images_from_tags'),

	# Permissions
	(r'^youpi/permissions/get/$', 'get_permissions'),
	(r'^youpi/permissions/set/$', 'set_permissions'),
	(r'^youpi/permissions/default/$', 'get_user_default_permissions'),

	# Prefs and docs
	(r'^youpi/preferences/$', 'preferences'),
	(r'^youpi/preferences/theme/set/$', 'set_current_theme'),
	(r'^youpi/preferences/condor/loadCurrentConfig/$', 'pref_load_condor_config'),
	(r'^youpi/preferences/condor/saveCurrentConfig/$', 'pref_save_condor_config'),
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
	(r'^youpi/process/query/imgsFromIdList/$', 'processing_imgs_from_idlist_post'),
	(r'^youpi/process/query/idListPagination/$', 'get_selected_ids_from_pagination'),
	(r'^youpi/process/query/remapIds/$', 'processing_imgs_remap_ids'),
	(r'^youpi/process/db/saveSelection/$', 'processing_save_image_selection'),
	(r'^youpi/process/db/getSelections/$', 'processing_get_image_selections'),
	(r'^youpi/process/db/delSelection/$', 'processing_delete_image_selection'),
	(r'^youpi/process/checkConfigFileExists/$', 'processing_check_config_file_exists'),
	(r'^youpi/process/imgsIdsFromRelease/$', 'processing_get_imgs_ids_from_release'),

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
	(r'^youpi/cart/savedItemsStats/$', 'cart_saved_items_stats'),

	# Grading
	(r'^youpi/grading/panel/(.*?)/(.*?)/$', 'grading_panel'),
	(r'^youpi/grading/cancel/(.*?)/(.*?)/$', 'grading_cancel'),
	(r'^youpi/grading/(.*?)/(.*?)/$', 'image_grading'),

	# Auto-completion
	(r'^youpi/autocompletion/(.*?)/(.*?)/$', 'autocomplete'),

    # Admin site
    (r'^youpi/admin/', include(admin.site.urls)),

	# User authentication
    (r'^youpi/accounts/login/$', login),
    (r'^youpi/accounts/logout/$', logout),

	(r'^youpi/uploadFile/$', 'upload_file'),
	(r'^youpi/uploadFile/imageSelector/imageList/$', 'ims_get_image_list_from_file'),
	(r'^youpi/uploadFile/batch/parseContent/$', 'batch_parse_content'),
	(r'^youpi/uploadFile/batch/viewContent/(.*)/$', 'batch_view_content'),
	(r'^youpi/uploadFile/batch/viewSelection/$', 'batch_view_selection'),

	# Image selector
	(r'^youpi/ims/collection/(.*?)/$', 'ims_get_collection'),
	(r'^youpi/ims/images/(.*?)/$', 'ims_get_images'),
	(r'^youpi/ims/importSelections/$', 'ims_import_selections'),

	# Stats
	(r'^youpi/stats/ingestion/$', 'stats_ingestion'),
	(r'^youpi/stats/processing/$', 'stats_processing'),

	# Plots
	(r'^youpi/plot/sky/selections/$', 'plot_sky_selections'),

	# API documentation
    (r'^youpi/api/(.*)/$', 'browse_api')
)
