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
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
	# Module that handles queries
	'terapix.youpi',
	
	# Callback functions depending on urls matches
	(r'^$', 'views.index'),
	(r'^ingestion/$', 'views.ing'),
	(r'^ingestion/delete/(.*?)/$', 'cviews.condor.delete_ingestion'),
	(r'^ingestion/ingestion2/$', 'views.condor_ingestion'),
	(r'^ingestion/imgCount/$', 'views.ingestion_img_count'),
	(r'^ingestion/itt/content/$', 'views.get_itt_content'),
	(r'^ingestion/itt/raw/(.*?)/$', 'views.show_raw_itt_content'),
	(r'^ingestion/rename/(.*?)/$', 'cviews.condor.rename_ingestion'),
	(r'^image/info/$', 'views.get_image_info'),
	(r'^image/info/(.*?)/$', 'views.gen_image_header'),
	(r'^image/view/(.*?)/$', 'views.view_image'),
	(r'^processing/$', 'views.processing'),
	(r'^processing/(.*?)/$', 'views.render_plugin'),

	# Cluster
	(r'^cluster/computeRequirementString/$', 'views.compute_requirement_string'),
	(r'^cluster/delCondorNodeSelection/$', 'views.del_condor_node_selection'),
	(r'^cluster/delCondorPolicy/$', 'views.del_condor_policy'),
	(r'^cluster/getCondorNodeSelections/$', 'views.get_condor_node_selections'),
	(r'^cluster/getCondorRequirementString/$', 'views.get_condor_requirement_string'),
	(r'^cluster/getCondorSelectionMembers/$', 'views.get_condor_selection_members'),
	(r'^cluster/getCondorPolicies/$', 'views.get_condor_policies'),
	(r'^cluster/getPolicyData/$', 'views.get_policy_data'),
	(r'^cluster/nodes/$', 'views.condor_hosts'),
	(r'^cluster/saveCustomReqStr/$', 'views.save_condor_custom_reqstr'),
	(r'^cluster/saveNodeSelection/$', 'views.save_condor_node_selection'),
	(r'^cluster/savePolicy/$', 'views.save_condor_policy'),
	(r'^cluster/softwares/$', 'views.condor_softs'),
	(r'^cluster/softwares/versions/$', 'views.softs_versions'),
	(r'^cluster/softwares/versions/refresh/$', 'views.query_condor_node_for_versions'),
	(r'^cluster/softwares/versions/delete/$', 'views.clear_softs_versions'),
	(r'^cluster/status/$', 'views.condor_status'),
	(r'^cluster/logs/$', 'views.get_condor_log_files_links'),
	(r'^cluster/log/(.*?)/(.*?)/$', 'views.show_condor_log_file'),

	(r'^monitoring/$', 'views.monitoring'),
	(r'^monitoring/live/$', 'views.live_monitoring'),
	(r'^monitoring/softwares/$', 'views.soft_version_monitoring'),
	(r'^condor/cancel/$', 'views.job_cancel'),
	(r'^condor/setup/$', 'views.condor_setup'),
	(r'^results/$', 'views.results'),
	(r'^results/delete/$', 'views.delete_processing_task'),
	(r'^results/filter/$', 'views.task_filter'),
	(r'^results/stats/$', 'views.dir_stats'),
	(r'^results/(.*?)/(.*?)/$', 'views.single_result'),

	(r'^tags/$', 'views.tags'),
	(r'^tags/fetchtags/$', 'views.fetch_tags'),
	(r'^tags/info/$', 'views.get_tag_info'),
	(r'^tags/save/$', 'views.save_tag'),
	(r'^tags/update/$', 'views.update_tag'),
	(r'^tags/delete/$', 'views.delete_tag'),
	(r'^tags/mark/$', 'views.tag_mark_images'),
	(r'^tags/unmark/$', 'views.tag_unmark_images'),
	(r'^tags/images/$', 'views.get_images_from_tags'),

	# Permissions
	(r'^permissions/get/$', 'views.get_permissions'),
	(r'^permissions/set/$', 'views.set_permissions'),
	(r'^permissions/default/$', 'views.get_user_default_permissions'),

	# Prefs and docs
	(r'^preferences/$', 'views.preferences'),
	(r'^preferences/theme/set/$', 'views.set_current_theme'),
	(r'^preferences/condor/loadCurrentConfig/$', 'views.pref_load_condor_config'),
	(r'^preferences/condor/saveCurrentConfig/$', 'views.pref_save_condor_config'),
	(r'^documentation/$', 'views.documentation'),

	# Sandbox for testing django form processing
#	(r'^sandbox/$', 'test_form'),

	# AJAX dynamic folder populate
	(r'^populate/(.*?)/(.*?)/(.*)/$', 'views.open_populate'),
	(r'^populate_generic/(.*?)/(.*?)/(.*)/$', 'views.open_populate_generic'),

	# Pre-ingestion
	(r'^process/preingestion/tablescount/$', 'views.preingestion_tables_count'),
	(r'^process/preingestion/run/$', 'views.preingestion_run'),
	(r'^process/preingestion/tablefields/$', 'views.preingestion_table_fields'),
	(r'^process/preingestion/query/$', 'views.preingestion_custom_query'),

	# Processing
	(r'^process/plugin/$', 'views.processing_plugin'),
	(r'^process/query/imgsFromIdList/$', 'views.processing_imgs_from_idlist_post'),
	(r'^process/query/idListPagination/$', 'views.get_selected_ids_from_pagination'),
	(r'^process/query/remapIds/$', 'views.processing_imgs_remap_ids'),
	(r'^process/db/saveSelection/$', 'views.processing_save_image_selection'),
	(r'^process/db/getSelections/$', 'views.processing_get_image_selections'),
	(r'^process/db/delSelection/$', 'views.processing_delete_image_selection'),
	(r'^process/checkConfigFileExists/$', 'views.processing_check_config_file_exists'),
	(r'^process/imgsIdsFromRelease/$', 'views.processing_get_imgs_ids_from_release'),

	# History
	(r'^history/ingestion/$', 'views.history_ingestion'),
	(r'^history/ingestion/report/(.*?)/$', 'views.show_ingestion_report'),
	(r'^history/preingestion/$', 'views.history_preingestion'),

	# Processing cart related
	(r'^cart/$', 'views.cart_view'),
	(r'^cart/additem/$', 'views.cart_add_item'),
	(r'^cart/additems/$', 'views.cart_add_items'),
	(r'^cart/delitem/$', 'views.cart_delete_item'),
	(r'^cart/delitems/$', 'views.cart_delete_items'),
	(r'^cart/itemsCount/$', 'views.cart_items_count'),
	(r'^cart/savedItemsStats/$', 'views.cart_saved_items_stats'),

	# Grading
	(r'^grading/panel/(.*?)/(.*?)/$', 'views.grading_panel'),
	(r'^grading/cancel/(.*?)/(.*?)/$', 'views.grading_cancel'),
	(r'^grading/(.*?)/(.*?)/$', 'views.image_grading'),

	# Auto-completion
	(r'^autocompletion/(.*?)/(.*?)/$', 'views.autocomplete'),

    # Admin site
    (r'^admin/', include(admin.site.urls)),

	# User authentication
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$', logout),

	(r'^uploadFile/$', 'views.upload_file'),
	(r'^uploadFile/imageSelector/imageList/$', 'views.ims_get_image_list_from_file'),
	(r'^uploadFile/batch/parseContent/$', 'views.batch_parse_content'),
	(r'^uploadFile/batch/viewContent/(.*)/$', 'views.batch_view_content'),
	(r'^uploadFile/batch/viewSelection/$', 'views.batch_view_selection'),

	# Image selector
	(r'^ims/collection/(.*?)/$', 'views.ims_get_collection'),
	(r'^ims/images/(.*?)/$', 'views.ims_get_images'),
	(r'^ims/importSelections/$', 'views.ims_import_selections'),

	# Stats
	(r'^stats/ingestion/$', 'views.stats_ingestion'),
	(r'^stats/processing/$', 'views.stats_processing'),

	# Plots
	(r'^plot/sky/selections/$', 'views.plot_sky_selections'),

	# API documentation
    (r'^api/(.*)/$', 'views.browse_api'),

	# Maintenance
    (r'^maintenance/$', 'views.maintenance'),

	# Reporting
	(r'^report/generating/(.*?)/(.*?)/$', 'cviews.reporting.generating_report'),
	(r'^report/(.*?)/(.*?)/(.*?)/$', 'cviews.reporting.get_report'),
	(r'^reporting/$', 'cviews.reporting.reporting'),
)

if settings.DEBUG:
	urlpatterns += patterns('terapix.youpi.views',
		(r'^test/$', 'main_test_runner'),
		(r'^test/suite/$', 'main_test_suite'),
		(r'^test/get/(.*?)/$', 'get_test'),
		(r'^ping/$', 'ping'),
	)
