""" Url router for the custom queries application
"""
from django.conf.urls import url

from core_custom_queries_app.views.user import views as user_views

urlpatterns = [
    url(r'^$', user_views.choose_query,
        name='core_custom_queries_app_index'),
    url(r'^query/(?P<query_id>\w+)/steps$', user_views.query_steps,
        name='core_custom_queries_app_steps'),
    url(r'^query/(?P<history_id>\w+)/steps/recover/', user_views.recover_query_steps,
        name='core_custom_queries_app_recover_steps'),
    url(r'^query/(?P<history_id>\w+)/output/', user_views.output_files,
        name='core_custom_queries_app_output'),
    url(r'^query/download/', user_views.download,
        name='core_custom_queries_app_download'),
]


