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
    (r'^$', 'views.home'),
    (r'^image/info/$', 'views.get_image_info'),
    (r'^image/info/(.*?)/$', 'views.gen_image_header'),
    (r'^image/view/(.*?)/$', 'views.view_image'),
    (r'^processing/$', 'views.processing'),
    (r'^processing/(.*?)/$', 'views.render_plugin'),

    # Ingestion
    (r'^ingestion/$', 'cviews.ingestion.home'),
    (r'^ingestion/exists/(.*?)/$', 'cviews.ingestion.ingestion_exists'),
    (r'^ingestion/delete/(.*?)/$', 'cviews.ingestion.delete_ingestion'),
    (r'^ingestion/ingestion2/$', 'cviews.condor.condor_ingestion'),
    (r'^ingestion/imgCount/$', 'cviews.ingestion.ingestion_img_count'),
    (r'^ingestion/itt/content/$', 'cviews.ingestion.get_itt_content'),
    (r'^ingestion/itt/raw/(.*?)/$', 'cviews.ingestion.show_raw_itt_content'),
    (r'^ingestion/rename/(.*?)/$', 'cviews.ingestion.rename_ingestion'),
    (r'^populate/(.*?)/(.*?)/(.*)/$', 'cviews.ingestion.open_populate'),
    (r'^populate_generic/(.*?)/(.*?)/(.*)/$', 'cviews.ingestion.open_populate_generic'),
    (r'^history/ingestion/$', 'cviews.ingestion.history_ingestion'),
    (r'^history/ingestion/report/(.*?)/$', 'cviews.ingestion.show_ingestion_report'),
    (r'^stats/ingestion/$', 'cviews.ingestion.stats_ingestion'),
    (r'^stats/processing/$', 'cviews.ingestion.stats_processing'),

    # Cluster
    (r'^condor/setup/$', 'cviews.condor.home'),
    (r'^cluster/computeRequirementString/$', 'cviews.condor.compute_requirement_string'),
    (r'^cluster/delCondorNodeSelection/$', 'cviews.condor.del_condor_node_selection'),
    (r'^cluster/delCondorPolicy/$', 'cviews.condor.del_condor_policy'),
    (r'^cluster/getCondorNodeSelections/$', 'cviews.condor.get_condor_node_selections'),
    (r'^cluster/getCondorRequirementString/$', 'cviews.condor.get_condor_requirement_string'),
    (r'^cluster/getCondorSelectionMembers/$', 'cviews.condor.get_condor_selection_members'),
    (r'^cluster/getCondorPolicies/$', 'cviews.condor.get_condor_policies'),
    (r'^cluster/getPolicyData/$', 'cviews.condor.get_policy_data'),
    (r'^cluster/nodes/$', 'cviews.condor.condor_hosts'),
    (r'^cluster/saveCustomReqStr/$', 'cviews.condor.save_condor_custom_reqstr'),
    (r'^cluster/saveNodeSelection/$', 'cviews.condor.save_condor_node_selection'),
    (r'^cluster/savePolicy/$', 'cviews.condor.save_condor_policy'),
    (r'^cluster/softwares/$', 'cviews.condor.condor_softs'),
    (r'^cluster/softwares/versions/$', 'cviews.condor.softs_versions'),
    (r'^cluster/softwares/versions/refresh/$', 'cviews.condor.query_condor_node_for_versions'),
    (r'^cluster/softwares/versions/delete/$', 'cviews.condor.clear_softs_versions'),
    (r'^cluster/status/$', 'cviews.condor.condor_status'),
    (r'^cluster/logs/$', 'cviews.condor.get_condor_log_files_links'),
    (r'^cluster/log/(.*?)/(.*?)/$', 'cviews.condor.show_condor_log_file'),
    (r'^condor/cancel/$', 'cviews.condor.job_cancel'),
    (r'^monitoring/$', 'cviews.condor.monitoring'),
    (r'^monitoring/live/$', 'cviews.condor.live_monitoring'),
    (r'^monitoring/softwares/$', 'cviews.condor.soft_version_monitoring'),
    (r'^history/cluster/jobs/$', 'cviews.condor.history_cluster_jobs'),

    # Tags
    (r'^tags/$', 'cviews.tags.home'),
    (r'^tags/images/$', 'cviews.tags.get_images_from_tags'),
    (r'^tags/fetchtags/$', 'cviews.tags.fetch_tags'),
    (r'^tags/info/$', 'cviews.tags.get_tag_info'),
    (r'^tags/save/$', 'cviews.tags.save_tag'),
    (r'^tags/update/$', 'cviews.tags.update_tag'),
    (r'^tags/delete/$', 'cviews.tags.delete_tag'),
    (r'^tags/mark/$', 'cviews.tags.tag_mark_images'),
    (r'^tags/unmark/$', 'cviews.tags.tag_unmark_images'),

    # Results
    (r'^results/$', 'cviews.results.home'),
    (r'^results/delete/$', 'cviews.results.delete_processing_task'),
    (r'^results/filter/$', 'cviews.results.task_filter'),
    (r'^results/stats/$', 'cviews.results.dir_stats'),
    (r'^results/outputdirs/$', 'cviews.results.get_all_results_output_dir'),
    (r'^results/(.*?)/(.*?)/$', 'cviews.results.single_result'),

    # Grading
    (r'^grading/panel/(.*?)/(.*?)/$', 'cviews.results.grading_panel'),
    (r'^grading/cancel/(.*?)/(.*?)/$', 'cviews.results.grading_cancel'),
    (r'^grading/(.*?)/(.*?)/$', 'cviews.results.image_grading'),

    # Permissions
    (r'^permissions/get/$', 'cviews.perm.get_permissions'),
    (r'^permissions/set/$', 'cviews.perm.set_permissions'),
    (r'^permissions/default/$', 'cviews.perm.get_user_default_permissions'),

    # Preferences
    (r'^preferences/$', 'cviews.pref.home'),
    (r'^preferences/theme/set/$', 'cviews.pref.set_current_theme'),
    (r'^preferences/condor/loadCurrentConfig/$', 'cviews.pref.pref_load_condor_config'),
    (r'^preferences/condor/saveCurrentConfig/$', 'cviews.pref.pref_save_condor_config'),

    # Image selector
    (r'^ims/collection/(.*?)/$', 'cviews.ims.ims_get_collection'),
    (r'^ims/images/(.*?)/$', 'cviews.ims.ims_get_images'),
    (r'^ims/importSelections/$', 'cviews.ims.ims_import_selections'),
    (r'^process/query/imgsFromIdList/$', 'cviews.ims.processing_imgs_from_idlist_post'),
    (r'^process/query/idListPagination/$', 'cviews.ims.get_selected_ids_from_pagination'),
    (r'^process/query/remapIds/$', 'cviews.ims.processing_imgs_remap_ids'),
    (r'^process/db/saveSelection/$', 'cviews.ims.processing_save_image_selection'),
    (r'^process/db/getSelections/$', 'cviews.ims.processing_get_image_selections'),
    (r'^process/db/delSelection/$', 'cviews.ims.processing_delete_image_selection'),
    (r'^process/imgsIdsFromRelease/$', 'cviews.ims.processing_get_imgs_ids_from_release'),
    (r'^uploadFile/$', 'cviews.ims.upload_file'),
    (r'^uploadFile/imageSelector/imageList/$', 'cviews.ims.ims_get_image_list_from_file'),
    (r'^uploadFile/batch/parseContent/$', 'cviews.ims.batch_parse_content'),
    (r'^uploadFile/batch/viewContent/(.*)/$', 'cviews.ims.batch_view_content'),
    (r'^uploadFile/batch/viewSelection/$', 'cviews.ims.batch_view_selection'),

    # Processing cart 
    (r'^cart/$', 'cviews.processingcart.home'),
    (r'^cart/additem/$', 'cviews.processingcart.cart_add_item'),
    (r'^cart/additems/$', 'cviews.processingcart.cart_add_items'),
    (r'^cart/delitem/$', 'cviews.processingcart.cart_delete_item'),
    (r'^cart/delitems/$', 'cviews.processingcart.cart_delete_items'),
    (r'^cart/itemsCount/$', 'cviews.processingcart.cart_items_count'),
    (r'^cart/savedItemsStats/$', 'cviews.processingcart.cart_saved_items_stats'),

    # Reporting
    (r'^report/generating/(.*?)/(.*?)/$', 'cviews.reporting.generating_report'),
    (r'^report/(.*?)/(.*?)/(.*?)/$', 'cviews.reporting.get_report'),
    (r'^reporting/$', 'cviews.reporting.reporting'),

    # User authentication & admin
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$', logout),

    # Plots
    (r'^plot/sky/selections/$', 'cviews.plot.plot_sky_selections'),

    (r'^documentation/$', 'views.documentation'),
    (r'^process/plugin/$', 'views.processing_plugin'),
    (r'^process/checkConfigFileExists/$', 'views.processing_check_config_file_exists'),
    (r'^autocompletion/(.*?)/(.*?)/$', 'views.autocomplete'),
    (r'^api/(.*)/$', 'views.browse_api'),
    (r'^maintenance/$', 'views.maintenance'),
)

if settings.DEBUG:
    urlpatterns += patterns('terapix.youpi.views',
        (r'^test/$', 'main_test_runner'),
        (r'^test/suite/$', 'main_test_suite'),
        (r'^test/get/(.*?)/$', 'get_test'),
        (r'^ping/$', 'ping'),
    )
