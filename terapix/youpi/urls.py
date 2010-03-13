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
	(r'^$', 'index'),
	(r'^ingestion/$', 'ing'),
	(r'^ingestion/ingestion2/$', 'condor_ingestion'),
	(r'^ingestion/imgCount/$', 'ingestion_img_count'),
	(r'^ingestion/itt/content/$', 'get_itt_content'),
	(r'^ingestion/itt/raw/(.*?)/$', 'show_raw_itt_content'),
	(r'^image/info/$', 'get_image_info'),
	(r'^image/head/(.*?)/$', 'gen_image_header'),
	(r'^img/(?P<image_name>.*?)/$', 'aff_img'),
	(r'^processing/$', 'processing'),
	(r'^processing/(.*?)/$', 'render_plugin'),

	# Cluster
	(r'^cluster/computeRequirementString/$', 'compute_requirement_string'),
	(r'^cluster/delCondorNodeSelection/$', 'del_condor_node_selection'),
	(r'^cluster/delCondorPolicy/$', 'del_condor_policy'),
	(r'^cluster/getCondorNodeSelections/$', 'get_condor_node_selections'),
	(r'^cluster/getCondorRequirementString/$', 'get_condor_requirement_string'),
	(r'^cluster/getCondorSelectionMembers/$', 'get_condor_selection_members'),
	(r'^cluster/getCondorPolicies/$', 'get_condor_policies'),
	(r'^cluster/getPolicyData/$', 'get_policy_data'),
	(r'^cluster/nodes/$', 'condor_hosts'),
	(r'^cluster/saveCustomReqStr/$', 'save_condor_custom_reqstr'),
	(r'^cluster/saveNodeSelection/$', 'save_condor_node_selection'),
	(r'^cluster/savePolicy/$', 'save_condor_policy'),
	(r'^cluster/softwares/$', 'condor_softs'),
	(r'^cluster/softwares/versions/$', 'softs_versions'),
	(r'^cluster/softwares/versions/refresh/$', 'query_condor_node_for_versions'),
	(r'^cluster/softwares/versions/delete/$', 'clear_softs_versions'),
	(r'^cluster/status/$', 'condor_status'),
	(r'^cluster/logs/$', 'get_condor_log_files_links'),
	(r'^cluster/log/(.*?)/(.*?)/$', 'show_condor_log_file'),

	(r'^monitoring/$', 'monitoring'),
	(r'^monitoring/live/$', 'live_monitoring'),
	(r'^monitoring/softwares/$', 'soft_version_monitoring'),
	(r'^condor/cancel/$', 'job_cancel'),
	(r'^condor/setup/$', 'condor_setup'),
	(r'^report/(.*?)/(.*?)/$', 'get_report'),
	(r'^reporting/$', 'reporting'),
	(r'^results/$', 'results'),
	(r'^results/delete/$', 'delete_processing_task'),
	(r'^results/filter/$', 'task_filter'),
	(r'^results/stats/$', 'dir_stats'),
	(r'^results/(.*?)/(.*?)/$', 'single_result'),

	(r'^tags/$', 'tags'),
	(r'^tags/fetchtags/$', 'fetch_tags'),
	(r'^tags/info/$', 'get_tag_info'),
	(r'^tags/save/$', 'save_tag'),
	(r'^tags/update/$', 'update_tag'),
	(r'^tags/delete/$', 'delete_tag'),
	(r'^tags/mark/$', 'tag_mark_images'),
	(r'^tags/unmark/$', 'tag_unmark_images'),
	(r'^tags/images/$', 'get_images_from_tags'),

	# Permissions
	(r'^permissions/get/$', 'get_permissions'),
	(r'^permissions/set/$', 'set_permissions'),
	(r'^permissions/default/$', 'get_user_default_permissions'),

	# Prefs and docs
	(r'^preferences/$', 'preferences'),
	(r'^preferences/theme/set/$', 'set_current_theme'),
	(r'^preferences/condor/loadCurrentConfig/$', 'pref_load_condor_config'),
	(r'^preferences/condor/saveCurrentConfig/$', 'pref_save_condor_config'),
	(r'^documentation/$', 'documentation'),

	# Sandbox for testing django form processing
#	(r'^sandbox/$', 'test_form'),
#	(r'^js/$', 'test_js'),

	# AJAX dynamic folder populate
	(r'^populate/(.*?)/(.*?)/(.*)/$', 'open_populate'),
	(r'^populate_generic/(.*?)/(.*?)/(.*)/$', 'open_populate_generic'),

	# Pre-ingestion
	(r'^process/preingestion/tablescount/$', 'preingestion_tables_count'),
	(r'^process/preingestion/run/$', 'preingestion_run'),
	(r'^process/preingestion/tablefields/$', 'preingestion_table_fields'),
	(r'^process/preingestion/query/$', 'preingestion_custom_query'),

	# Processing
	(r'^process/plugin/$', 'processing_plugin'),
	(r'^process/query/imgsFromIdList/$', 'processing_imgs_from_idlist_post'),
	(r'^process/query/idListPagination/$', 'get_selected_ids_from_pagination'),
	(r'^process/query/remapIds/$', 'processing_imgs_remap_ids'),
	(r'^process/db/saveSelection/$', 'processing_save_image_selection'),
	(r'^process/db/getSelections/$', 'processing_get_image_selections'),
	(r'^process/db/delSelection/$', 'processing_delete_image_selection'),
	(r'^process/checkConfigFileExists/$', 'processing_check_config_file_exists'),
	(r'^process/imgsIdsFromRelease/$', 'processing_get_imgs_ids_from_release'),

	# History
	(r'^history/ingestion/$', 'history_ingestion'),
	(r'^history/ingestion/report/(.*?)/$', 'show_ingestion_report'),
	(r'^history/preingestion/$', 'history_preingestion'),

	# Processing cart related
	(r'^cart/$', 'cart_view'),
	(r'^cart/cookiecheck/$', 'cart_cookie_check'),
	(r'^cart/additem/$', 'cart_add_item'),
	(r'^cart/delitem/$', 'cart_delete_item'),
	(r'^cart/itemsCount/$', 'cart_items_count'),
	(r'^cart/savedItemsStats/$', 'cart_saved_items_stats'),

	# Grading
	(r'^grading/panel/(.*?)/(.*?)/$', 'grading_panel'),
	(r'^grading/cancel/(.*?)/(.*?)/$', 'grading_cancel'),
	(r'^grading/(.*?)/(.*?)/$', 'image_grading'),

	# Auto-completion
	(r'^autocompletion/(.*?)/(.*?)/$', 'autocomplete'),

    # Admin site
    (r'^admin/', include(admin.site.urls)),

	# User authentication
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$', logout),

	(r'^uploadFile/$', 'upload_file'),
	(r'^uploadFile/imageSelector/imageList/$', 'ims_get_image_list_from_file'),
	(r'^uploadFile/batch/parseContent/$', 'batch_parse_content'),
	(r'^uploadFile/batch/viewContent/(.*)/$', 'batch_view_content'),
	(r'^uploadFile/batch/viewSelection/$', 'batch_view_selection'),

	# Image selector
	(r'^ims/collection/(.*?)/$', 'ims_get_collection'),
	(r'^ims/images/(.*?)/$', 'ims_get_images'),
	(r'^ims/importSelections/$', 'ims_import_selections'),

	# Stats
	(r'^stats/ingestion/$', 'stats_ingestion'),
	(r'^stats/processing/$', 'stats_processing'),

	# Plots
	(r'^plot/sky/selections/$', 'plot_sky_selections'),

	# API documentation
    (r'^api/(.*)/$', 'browse_api'),

	# Maintenance
    (r'^maintenance/$', 'maintenance'),
)
