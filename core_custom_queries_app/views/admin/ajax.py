""" AJAX views for admin custom queries
"""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest, HttpResponse
from django.urls import reverse

from core_custom_queries_app.components.dyn_query import api as dyn_query_api
from core_main_app.commons.exceptions import DoesNotExist


@staff_member_required
def delete_query(request):
    try:
        query_id = request.POST['id']
        try:
            query = dyn_query_api.get_by_id(query_id)
            dyn_query_api.delete(query)
        except DoesNotExist:
            messages.add_message(request, messages.INFO,
                                 'The query you are trying to manage does '
                                 'not exist anymore.')
            return HttpResponseBadRequest()
        messages.add_message(request, messages.SUCCESS, 'Query deleted.')
        return HttpResponse(reverse("admin:core_custom_queries_app_queries"))

    except Exception, e:
        return HttpResponseBadRequest(e.message, content_type='application/javascript')
