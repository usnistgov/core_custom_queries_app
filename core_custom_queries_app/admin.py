"""
Url file used by django for admin's views.
"""
from django.contrib import admin
from django.conf.urls import url

from core_custom_queries_app.views.admin import views as admin_views
from core_custom_queries_app.views.admin import ajax as admin_ajax

admin_urls = [
    url(r'^custom_queries/list$', admin_views.queries_list,
        name='core_custom_queries_app_queries'),
    url(r'^custom_queries/query_builder$', admin_views.query_builder,
        name='core_custom_queries_app_query_builder'),
    url(r'^custom_queries/(?P<query_id>\w+)/edit$', admin_views.edit_query,
        name='core_custom_queries_app_edit_query'),
    url(r'^custom_queries/list_errors$', admin_views.list_errors,
        name='core_custom_queries_app_errors'),

    url(r'^custom_queries/delete$', admin_ajax.delete_query,
        name='core_custom_queries_app_delete_query'),
]

urls = admin.site.get_urls()
admin.site.get_urls = lambda: admin_urls + urls
