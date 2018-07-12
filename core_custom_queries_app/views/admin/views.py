"""
Describe all the view admin-only
"""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import formset_factory
from django.shortcuts import redirect
from django.urls import reverse

from core_custom_queries_app.components.dyn_query import api as dyn_query_api
from core_custom_queries_app.components.dyn_query.models import DynQuery
from core_custom_queries_app.components.dyn_query_step import api as dyn_query_step_api
from core_custom_queries_app.components.dyn_query_step.models import DynQueryStep
from core_custom_queries_app.views.admin.forms import Query, QueryPieceForm
from core_main_app.commons.exceptions import DoesNotExist, ModelError
from core_main_app.components.template import api as template_api
from core_main_app.components.template_version_manager import api as template_version_manager_api
from core_main_app.utils.rendering import admin_render


@staff_member_required
def queries_list(request):
    """
    View list of queries defined by the administrator.
    Used by the admin.
    Create a form where all the queries are listed.

    Args:
        request:

    Returns:

    """
    queries = dyn_query_api.get_all()

    query_list = []
    for query in queries:
        query_dict = dict()
        query_dict['id'] = query.pk
        query_dict['name'] = query.name
        try:
            template = template_api.get(query.schema)
            template_version_manager = template_version_manager_api.get_by_version_id(str(template.id))
            query_dict['schema'] = template_version_manager.title
            if template_version_manager.is_disabled:
                query_dict['schema'] += '-deleted'
        except Exception, e:
            query_dict['schema'] = 'Template deleted from the database.'

        query_dict['group'] = query.group

        query_list.append(query_dict)

    queries = query_list

    assets = {
        "css": ['core_custom_queries_app/admin/css/queries_list.css'],
    }

    return admin_render(request,
                        "core_custom_queries_app/admin/queries_list.html",
                        assets=assets,
                        context={"queries": queries})


@staff_member_required
def query_builder(request):
    """
    Create a query. Only used by an administrators.
    A query is composed by a common part (DynQuery) and at least one step (DynQueryStep).
    If the query has been validated  the query is saved into the database.
    A new query can not have the same name as another into the database.
    If not, the query is sent to the user for modification.

    Args:
        request:

    Returns:

    """
    if request.method == 'POST':
        # Take the data from the forms
        form = Query(request.POST, auto_id=True)
        number_forms = int(request.POST['form-TOTAL_FORMS'])
        query_piece_form = formset_factory(QueryPieceForm, extra=number_forms)
        formset = query_piece_form(request.POST, request.FILES)

        # Validate the forms
        if form.is_valid():
            if formset.is_valid():
                try:
                    # Create the query
                    data = form.cleaned_data
                    query = DynQuery(name=data["name"], group=data["group"], schema=data["schema"],
                                     is_limited=data["is_limited"], number_records=data["number_records"])

                    # Create the query steps
                    list_query_steps = []
                    for fs in formset:
                        data = fs.cleaned_data
                        step = DynQueryStep(name=data["name"], xpath=data["xpath"], output_field=data["output_field"],
                                            target= data["target"], value=data["value"], data_type=data["data_type"],
                                            restriction=data["restriction"], data_min_range=data["data_min_range"],
                                            data_max_range=data["data_max_range"], data_infinity=data["data_infinity"],
                                            date_range=data["date_range"])
                        list_query_steps.append(step)
                        try:
                            dyn_query_step_api.upsert(step)
                        except Exception, e:
                            for step in query.steps:
                                dyn_query_step_api.delete(step)
                            messages.add_message(request, messages.ERROR, e.message)
                            break

                    # Add the steps to the query
                    query["steps"] = list_query_steps
                    try:
                        dyn_query_api.upsert(query)
                    except Exception, e:
                        for step in query.steps:
                            dyn_query_step_api.delete(step)
                        messages.add_message(request, messages.ERROR, e.message)

                    messages.add_message(request, messages.SUCCESS, 'Query saved.')
                    return redirect(reverse("admin:core_custom_queries_app_queries"))

                except Exception as e:
                    messages.add_message(request, messages.ERROR, e.message)
    else:
        # Create an empty form to create a query
        form = Query()
        query_piece_form = formset_factory(QueryPieceForm)
        formset = query_piece_form()

    context = {'form': form,
               'formset': formset,
               'query_piece_form': query_piece_form}

    assets = {
        "js": [
            {
                "path": 'core_custom_queries_app/admin/js/custom_queries.js',
                "is_raw": False
            },
        ],
    }

    return admin_render(request,
                        'core_custom_queries_app/admin/query_builder.html',
                        assets=assets,
                        context=context)


# FIXME: refactor with query_builder
@staff_member_required
def edit_query(request, query_id):
    """
    Update or delete a query from the query selection.
    Used by the admin.
    Create a form with the query's information. The modification are saved if the form is validated.
    A confirmation pop-up is shown is the query is about to be deleted.
    Come back to the query selection if the query has been deleted.

    Args:
        request:
        query_id:

    Returns:

    """
    # Come from the form
    if request.method == 'POST':
        # Take the data from the forms
        # FIXME: using the same form as the one for a new query prevent from updating query without changing its name
        form = Query(request.POST, auto_id=True)
        number_forms = int(request.POST['form-TOTAL_FORMS'])
        query_piece_form = formset_factory(QueryPieceForm, extra=number_forms)
        formset = query_piece_form(request.POST, request.FILES)

        # Validate the forms
        if form.is_valid():
            if formset.is_valid():
                form_data = form.cleaned_data
                formset_data = formset.cleaned_data
                try:
                    query = dyn_query_api.get_by_id(query_id)
                except DoesNotExist:
                    messages.add_message(request, messages.INFO,
                                         'The query you are trying to manage does not exist anymore.')
                    return redirect(reverse("admin:core_custom_queries_app_queries"))
                except ModelError, e:
                    messages.add_message(request, messages.WARNING, e.message)
                    return redirect(reverse("admin:core_custom_queries_app_queries"))

                query.name = form_data["name"]
                query.is_limited = form_data["is_limited"]
                query.group = form_data["group"]
                query.schema = form_data["schema"]
                query.number_records = form_data["number_records"]
                dyn_query_api.upsert(query)

                # Create the query steps
                for step_data in formset_data:
                    try:
                        step = dyn_query_step_api.get_by_id(step_data["step_id"])
                    except DoesNotExist:
                        messages.add_message(request, messages.INFO,
                                             'The query you are trying to manage does not exist anymore.')
                    except ModelError, e:
                        messages.add_message(request, messages.WARNING, e.message)

                    step.name=step_data.get("name")
                    step.xpath=step_data.get("xpath")
                    step.output_field=step_data.get("output_field")
                    step.target=step_data.get("target")
                    step.value=step_data.get("value")
                    step.data_type=step_data.get("data_type")
                    step.restriction=step_data.get("restriction")
                    step.data_min_range=step_data.get("data_min_range")
                    step.data_max_range=step_data.get("data_max_range")
                    step.data_infinity=step_data.get("data_infinity")
                    step.date_range=step_data.get("date_range")
                    dyn_query_step_api.upsert(step)

                messages.add_message(request, messages.SUCCESS, 'Query updated.')
                return redirect(reverse("admin:core_custom_queries_app_queries"))

    # Come from the query selector
    else:
        try:
            query = dyn_query_api.get_by_id(query_id)
        except DoesNotExist:
            messages.add_message(request, messages.INFO, "The matching query does not exist.")
            return redirect(reverse("admin:core_custom_queries_app_queries"))
        except ModelError, e:
            messages.add_message(request, messages.WARNING, e.message)
            return redirect(reverse("admin:core_custom_queries_app_queries"))

        nb_steps = len(query.steps)

        # Load the query
        param_query = {
            'id': query.id,
            'name': query.name,
            'is_limited': query.is_limited,
            'number_records': query.number_records,
            'group': query.group,
            'schema': query.schema
        }

        form = Query(param_query)

        query_piece_form = formset_factory(QueryPieceForm, extra=nb_steps)

        # Load the query steps
        data = dict()
        data['form-TOTAL_FORMS'] = nb_steps
        data['form-INITIAL_FORMS'] = nb_steps
        data['form-MAX_NUM_FORMS'] = nb_steps
        position = 0
        for step in query.steps:
            data['form-' + str(position) + '-step_id'] = step.id
            data['form-' + str(position) + '-name'] = step["name"]
            data['form-' + str(position) + '-xpath'] = step["xpath"]
            data['form-' + str(position) + '-output_field'] = step["output_field"]
            data['form-' + str(position) + '-target'] = step["target"]
            data['form-' + str(position) + '-value'] = step["value"]
            data['form-' + str(position) + '-data_type'] = step["data_type"]
            data['form-' + str(position) + '-restriction'] = step["restriction"]
            data['form-' + str(position) + '-data_min_range'] = step["data_min_range"]
            data['form-' + str(position) + '-data_max_range'] = step["data_max_range"]
            data['form-' + str(position) + '-data_infinity'] = step["data_infinity"]
            data['form-' + str(position) + '-date_range'] = step["date_range"]
            position += 1

        formset = query_piece_form(data)

    context = {'form': form,
               'formset': formset,
               'query_piece_form': query_piece_form,
               'query_id': query_id}

    assets = {
        "js": [
            {
                "path": 'core_custom_queries_app/admin/js/custom_queries.js',
                "is_raw": False
            },
        ],
    }

    modals = ['core_custom_queries_app/admin/custom_queries/modals/delete_query.html']

    return admin_render(request,
                        'core_custom_queries_app/admin/update_query.html',
                        modals=modals,
                        assets=assets,
                        context=context)
