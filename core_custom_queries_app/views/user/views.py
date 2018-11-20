"""
Describe all the views used by custom_queries
"""
from datetime import datetime

from bson import ObjectId
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.forms import formset_factory
from django.shortcuts import redirect
from django.urls import reverse_lazy
from mongoengine import ValidationError
from redis import Redis, ConnectionError

import core_main_app.utils.decorators as decorators
from core_custom_queries_app.components.dyn_query import api as dyn_query_api
from core_custom_queries_app.components.history_query import api as history_query_api
from core_custom_queries_app.components.log_file import api as log_file_api
from core_custom_queries_app.components.log_file.models import LogFile
from core_custom_queries_app.components.temp_output_file import api as temp_output_file_api
from core_custom_queries_app.components.temp_user_query import api as temp_user_query_api
from core_custom_queries_app.components.temp_user_step.models import TempUserStep
from core_custom_queries_app.models import TempUserQuery
from core_custom_queries_app.permissions import rights
from core_custom_queries_app.views.user.forms import FormChooseQuery, FormRadio, FormCheck, FormDateTime, FormResult, \
    FormHistory
from core_main_app.commons.exceptions import DoesNotExist
from core_main_app.components.template_version_manager import api as template_version_manager_api
from core_main_app.utils.file import get_file_http_response
from core_main_app.utils.rendering import render
from qdr.settings import REDIS_URL


@decorators.permission_required(content_type=rights.custom_queries_content_type,
                                permission=rights.custom_queries_access, login_url=reverse_lazy("core_main_app_login"))
def choose_query(request):
    """
    Select a query from the one into the database to be able to use it.
    Used by the user.
    If there is no query into the database, an error message is shown to the user.
    If no query has been selected, an error message is shown to the user.
    Send to the query_step if a query has been selected.
    If history queries are available, they are show with the following option:
    _History deletion
    _History recovery

    Args:
        request:

    Returns:

    """
    formset = None
    formset_history = None
    history_queries = None
    # Come back from the form with the query selected
    if request.method == 'POST':
        # Get the forms variable
        query_id = request.POST.get('query', None)
        to_recover = request.POST.get('to_recover', None)
        number_forms = request.POST.get('form-TOTAL_FORMS', None)

        # if a variable is none, come back with an error message
        if query_id is None and to_recover is None and number_forms is None:
            messages.add_message(request, messages.INFO, "You have to select a query.")
        else:
            if query_id is not None:
                return redirect(reverse("core_custom_queries_app_steps", kwargs={'query_id': query_id}))
            # History selected
            elif to_recover is not None and to_recover != '':
                return redirect(reverse("core_custom_queries_app_recover_steps", kwargs={'history_id': to_recover}))
            # Delete history query
            else:
                number_forms = int(number_forms)
                formset_history = formset_factory(FormHistory, extra=number_forms,
                                                  can_delete=True)
                formset = formset_history(request.POST, request.FILES)
                if formset.is_valid():
                    if len(formset.deleted_forms) == 0:
                        messages.add_message(request, messages.ERROR,
                                             "Please select a query first.")
                    for form in formset.deleted_forms:
                        data = form.cleaned_data
                        if 'DELETE' in data:
                            id_history = ObjectId(data['id_history'])
                            history = history_query_api.get_by_id(id_history)
                            temp_query_id = history.query_id
                            query = temp_user_query_api.get_by_id(temp_query_id)
                            query.delete_database()
                    messages.add_message(request, messages.SUCCESS,
                                         "Queries successfully deleted.")

    # Create the query form from the ones into the database
    id_list = list()
    # Get the available templates
    available_template_version_managers = template_version_manager_api.get_active_global_version_manager()
    for available_template_version_manager in available_template_version_managers:
        for available_template_id in available_template_version_manager.versions:
            id_list.append(str(available_template_id))

    # Get the queries available for the current user
    if request.user.is_staff:
        # FIXME: call specialized api
        queries = dyn_query_api.get_all().filter(schema__in=id_list).values_list('pk', 'name')
    else:
        # FIXME: call specialized api
        queries = dyn_query_api.get_all().filter(schema__in=id_list).filter(group='user').values_list('pk', 'name')

    number_queries = len(queries)

    form = None
    if number_queries != 0:
        form = FormChooseQuery(query=queries)
    else:
        # If no query available, set an error message
        message = "No query available."
        messages.add_message(request, messages.ERROR, message)

    try:
        # If histories exist load them
        history_queries = history_query_api.get_all_by_user_id(str(request.user.id))
        number_history = len(history_queries)
    except Exception:
        number_history = 0

    if number_history > 0:
        # Create the formset with the histories values
        formset_history = formset_factory(FormHistory, extra=number_history, can_delete=True)
        data = dict()
        data['form-TOTAL_FORMS'] = number_history
        data['form-INITIAL_FORMS'] = number_history
        data['form-MAX_NUM_FORMS'] = number_history
        position = 0
        for history_query in history_queries:
            try:
                query_id = str(history_query.query_id)
                data['form-' + str(position) + '-id_history'] = str(history_query.id)
                query = temp_user_query_api.get_by_id(query_id)
                data['form-' + str(position) + '-query_name'] = query.query.name
                data['form-' + str(position) + '-query_last_modified'] = query.last_modified

                h_message = history_query.message
                if h_message == "Pending.":
                    redis_server = Redis.from_url(REDIS_URL)
                    try:
                        if redis_server.exists("current_id"):
                            current_id = redis_server.get("current_id")
                            if current_id == query_id:
                                h_message = "Pending: The file creation will begin shortly."

                        if redis_server.exists("list_ids"):
                            list_id = redis_server.lrange('list_ids', 0, -1)
                            try:
                                position_id = list_id.index(query_id) + 1
                                h_message = "Pending - Waiting list: " + str(position_id) + "/" + str(len(list_id))
                            except ValueError:
                                pass

                    except ConnectionError, e:
                        log_file = LogFile(application="Custom Queries",
                                           message="Redis not reachable, is it running?",
                                           additionalInformation={'message': e.message},
                                           timestamp=datetime.now())
                        log_file_api.upsert(log_file)

                data['form-' + str(position) + '-query_message'] = h_message
                data['form-' + str(position) + '-status'] = history_query.status
                data['form-' + str(position) + '-DELETE'] = ''
                position += 1
            except DoesNotExist:
                pass
        formset = formset_history(data)

    context = {'number_queries': number_queries,
               'number_history': number_history,
               'form': form,
               'formset': formset,
               'formset_history': formset_history}

    assets = {
        "js": [
            {
                "path": 'core_custom_queries_app/user/js/custom_queries.js',
                "is_raw": False
            },
        ],
    }

    return render(request,
                  'core_custom_queries_app/user/select_query.html',
                  assets=assets,
                  context=context)


@decorators.permission_required(content_type=rights.custom_queries_content_type,
                                permission=rights.custom_queries_access, login_url=reverse_lazy("core_main_app_login"))
def query_steps(request, query_id):
    """
    Manage each step of the query.

    Create the query step in function of the step type. Validate the user choices and store each step to the query
    history. The last step validation store the query to the database to explore the files and get the data.

    Args:
        request:
        query_id:

    Returns:

    """
    user_query = TempUserQuery()
    user_step = TempUserStep()
    first_step = False
    previous_step = False
    next_step = False
    history_id = None

    # Validate the user step
    if request.method == 'POST':
        # Get the form's value
        user_query_id = request.POST.get('user_query', None)
        step_back = request.POST.get('step_back', None)
        history_id = request.POST.get('history_id', None)

        # Handle value transportation problems.
        if user_query is None or step_back is None or history_id is None:
            messages.add_message(request, messages.ERROR,
                                 "A problem occurred during your information's transportation."
                                 " Please do it again.")
            return redirect(reverse("custom_queries_queryChoose"))
        try:
            # Load the query
            user_query = temp_user_query_api.get_by_id(user_query_id)
        except DoesNotExist:
            # The query doesn't exist anymore.
            messages.add_message(request, messages.ERROR,
                                 "A problem occurred during your information's transportation."
                                 " Please do it again.")

            return redirect(reverse("custom_queries_queryChoose"))

        # Get the current step information
        user_step = user_query.get_current_step()
        form_type = user_step.form_type
        # If the user want to go back to the previous step
        if step_back == 'True':
            previous_step = True
        else:
            error = False
            # The step is a a single choice step
            if form_type == 'radio':
                choices = request.POST.get('choices', None)
                if choices:
                    user_step.choices.append(choices)
                else:
                    messages.add_message(request, messages.WARNING, 'You have to choose one.')
                    error = True
            # The step is a a multiple choices step
            elif form_type == 'check':
                list_choices = request.POST.getlist('choices')
                # Get the step restrictions and validate the choices against the restrictions
                min_range = user_step.step.data_min_range
                if min_range != '' and min_range:
                    min_range = int(min_range)
                    max_range = user_step.step.data_max_range
                    data_infinity = user_step.step.data_infinity
                    if max_range != '' and max_range:
                        max_range = int(max_range)
                        if max_range < len(list_choices) or len(list_choices) < min_range:
                            error = True
                            messages.add_message(request, messages.WARNING,
                                                 'You have to choose between '
                                                 + str(min_range)
                                                 + ' and ' + str(max_range)
                                                 + ' choice.')
                    else:
                        if len(list_choices) < min_range:
                            error = True
                            messages.add_message(request, messages.WARNING,
                                                 'You have to choose at least one.')
                if not error:
                    user_step.choices = list_choices
            # The step is a a date step
            else:
                time_from = request.POST['timeFrom']
                time_to = request.POST['timeTo']
                if time_from == "" or time_to == "":
                    error = True
                    messages.add_message(request, messages.WARNING, 'You have to fill both date.')
                else:
                    try:
                        time_from = datetime.strptime(time_from, "%Y-%m-%d %H:%M")
                        time_to = datetime.strptime(time_to, "%Y-%m-%d %H:%M")

                        if time_from > time_to:
                            error = True
                            messages.add_message(request, messages.WARNING,
                                                 'Date \"From\" has to be before date \"To\"')

                        date_range = user_step.step.date_range
                        if date_range and date_range != '':
                            date_range = int(date_range)
                            if (time_to - time_from).days > date_range:
                                error = True
                                messages.add_message(request, messages.WARNING,
                                                     'The maximum time range you can query in is '
                                                     + str(date_range)
                                                     + ' day(s).')
                    except Exception, e:
                        error = True
                        messages.add_message(request, messages.ERROR, e)
                if not error:
                    user_step.choices = (request.POST['timeFrom'], request.POST['timeTo'])
            if not error:
                user_step.update_choices_to_db()
                next_step = True
    # Select and load the current step
    else:
        # Initialize the query
        user_query = TempUserQuery()
        user_query.initialize_query(query_id=query_id)
        first_step = True

    try:
        # Load the current step
        if first_step is True:
            # Load the first step
            user_step = user_query.get_and_load_choices_first_step()
            user_query.save_whole_query()
        elif previous_step is True:
            # Load the previous step
            user_step = user_query.get_previous_query_able_step()
            user_query.update_current_position_into_the_db()
            user_step.transform_choices_files_list_to_dict()
        elif next_step is True:
            # Load the next step
            user_step = user_query.get_and_load_choices_next_step()
            user_query.update_current_position_into_the_db()
        else:
            # Error validation
            user_step.transform_choices_files_list_to_dict()
        history_id = user_query.save_to_history(user_id=str(request.user.id), history_id=history_id)
    except Exception, e:
        # Create the log file from the error
        log_file = LogFile(application="Custom Queries",
                           message=e.message,
                           additionalInformation={'query_name': user_query.query.name,
                                                  'step_name': user_query.list_steps[user_query.current_position].step.name,
                                                  'user_choices': user_query.get_previous_choices()},
                           timestamp=datetime.now())
        log_file_api.upsert(log_file)
        try:
            user_query.update_message("Error during query step.")
        except ValidationError:
            pass

        messages.add_message(request, messages.ERROR,
                             "An internal problem occurred, the administrator has been notified.")
        return redirect(reverse("core_custom_queries_app_index"))

    if user_step is None:
        # Go to result page
        user_query.add_query_to_waiting_line()
        user_query.update_message("Pending.")
        user_query.update_status(1)
        messages.add_message(request, messages.SUCCESS,
                             "The output file will be created soon.")
        return redirect(reverse("core_custom_queries_app_index"))
    else:
        context = _create_step_context(user_query, user_step, history_id)

        assets = {
            "js": [
                {
                    "path": 'core_custom_queries_app/user/js/custom_queries.js',
                    "is_raw": False
                },
                {
                    "path": 'core_custom_queries_app/user/js/custom_queries_step.js',
                    "is_raw": False
                },
                {
                    "path": "core_custom_queries_app/libs/bootstrap-datetimepicker/js/bootstrap-datetimepicker.js",
                    "is_raw": False
                },
            ],
            'css': ['core_custom_queries_app/libs/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css']
        }

        return render(request,
                      'core_custom_queries_app/user/query_step.html',
                      assets=assets,
                      context=context)


# FIXME: refactor code duplicated with query_steps
@decorators.permission_required(content_type=rights.custom_queries_content_type,
                                permission=rights.custom_queries_access, login_url=reverse_lazy("core_main_app_login"))
def recover_query_steps(request, history_id):
    """

    """
    user_step = None
    previous_step = False
    next_step = False
    history_step = False

    # Validate the user step
    if request.method == 'POST':
        # Get the form's value
        user_query_id = request.POST.get('user_query', None)
        step_back = request.POST.get('step_back', None)
        try:
            # Load the query
            user_query = temp_user_query_api.get_by_id(user_query_id)
        except DoesNotExist:
            # The query doesn't exist anymore.
            messages.add_message(request, messages.ERROR,
                                 "A problem occurred during your information's transportation."
                                 " Please do it again.")

            return redirect(reverse("core_custom_queries_app_index"))

        # Get the current step information
        user_step = user_query.get_current_step()
        form_type = user_step.form_type
        # If the user want to go back to the previous step
        if step_back == 'True':
            previous_step = True
        else:
            error = False
            # The step is a a single choice step
            if form_type == 'radio':
                choices = request.POST.get('choices', None)
                if choices:
                    user_step.choices.append(choices)
                else:
                    messages.add_message(request, messages.WARNING, 'You have to choose one.')
                    error = True
            # The step is a a multiple choices step
            elif form_type == 'check':
                list_choices = request.POST.getlist('choices')
                # Get the step restrictions and validate the choices against the restrictions
                min_range = user_step.step.data_min_range
                if min_range != '' and min_range:
                    min_range = int(min_range)
                    max_range = user_step.step.data_max_range
                    # data_infinity = user_step.step.data_infinity
                    if max_range != '' and max_range:
                        max_range = int(max_range)
                        if max_range < len(list_choices) or len(list_choices) < min_range:
                            error = True
                            messages.add_message(request, messages.WARNING,
                                                 'You have to choose between '
                                                 + str(min_range)
                                                 + ' and ' + str(max_range)
                                                 + ' choice.')
                    else:
                        if len(list_choices) < min_range:
                            error = True
                            messages.add_message(request, messages.WARNING,
                                                 'You have to choose at least one.')
                if not error:
                    user_step.choices = list_choices
            # The step is a a date step
            else:
                time_from = request.POST['timeFrom']
                time_to = request.POST['timeTo']
                if time_from == "" or time_to == "":
                    error = True
                    messages.add_message(request, messages.WARNING, 'You have to fill both date.')
                else:
                    try:
                        time_from = datetime.strptime(time_from, "%Y-%m-%d %H:%M")
                        time_to = datetime.strptime(time_to, "%Y-%m-%d %H:%M")

                        if time_from > time_to:
                            error = True
                            messages.add_message(request, messages.WARNING,
                                                 'Date From has to be before date To')

                        date_range = user_step.step.date_range
                        if date_range and date_range != '':
                            date_range = int(date_range)
                            if (time_to - time_from).days > date_range:
                                error = True
                                messages.add_message(request, messages.WARNING,
                                                     'The maximum time range you can query in is '
                                                     + str(date_range)
                                                     + ' day(s).')
                    except Exception, e:
                        error = True
                        messages.add_message(request, messages.ERROR, e)
                if not error:
                    user_step.choices = (request.POST['timeFrom'], request.POST['timeTo'])
            if not error:
                user_step.update_choices_to_db()
                next_step = True
    # Select and load the current step
    else:
        # Load history queries
        try:
            history_query = history_query_api.get_by_id(history_id)
            user_query = temp_user_query_api.get_by_id(history_query.query_id)
        except DoesNotExist:
            messages.add_message(request, messages.ERROR, "A problem occurred during the redirection.")
            return redirect(reverse("core_custom_queries_app_index"))
        history_step = True
    try:        # Load the current step
        if previous_step is True:
            # Load the previous step
            user_step = user_query.get_previous_query_able_step()
            user_query.update_current_position_into_the_db()
            user_step.transform_choices_files_list_to_dict()
            history_id = user_query.save_to_history(user_id=request.user.id, history_id=history_id)
        elif next_step is True:
            # Load the next step
            user_step = user_query.get_and_load_choices_next_step()
            user_query.update_current_position_into_the_db()
            history_id = user_query.save_to_history(user_id=request.user.id, history_id=history_id)
        elif history_step is True:
            if user_query.history.message == "Error during output file creation.":
                # An error occurred
                messages.add_message(request, messages.ERROR,
                                     "An internal problem occurred during the output file creation. "
                                     "The administrator has been noticed.")
                return redirect(reverse("core_custom_queries_app_index"))
            else:
                # Load the history query
                user_step = user_query.handle_history()
                user_step.transform_choices_files_list_to_dict()
    except Exception, e:
        # Create the log file from the error
        log_file = LogFile(application="Custom Queries",
                           message=e.message,
                           additionalInformation={'query_name': user_query.query.name,
                                                  'step_name': user_query.list_steps[
                                                      user_query.current_position].step.name,
                                                  'user_choices': user_query.get_previous_choices()},
                           timestamp=datetime.now())
        log_file_api.upsert(log_file)
        try:
            user_query.update_message("Error during query step.")
        except ValidationError:
            pass

        messages.add_message(request, messages.ERROR,
                             "An internal problem occurred, the administrator has been notified.")
        return redirect(reverse("core_custom_queries_app_index"))

    if user_step is None:
        # Go to result page
        user_query.add_query_to_waiting_line()
        user_query.update_message("Pending.")
        user_query.update_status(1)
        messages.add_message(request, messages.SUCCESS,
                             "The output file will be created soon.")
        return redirect(reverse("core_custom_queries_app_index"))
    else:
        context = _create_step_context(user_query, user_step, history_id)

        assets = {
            "js": [
                {
                    "path": 'core_custom_queries_app/user/js/custom_queries.js',
                    "is_raw": False
                },
                {
                    "path": 'core_custom_queries_app/user/js/custom_queries_step.js',
                    "is_raw": False
                },
                {
                    "path": "core_custom_queries_app/libs/bootstrap-datetimepicker/js/bootstrap-datetimepicker.js",
                    "is_raw": False
                },
            ],
            'css': ['core_custom_queries_app/libs/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css']
        }

        # for the rendering
        return render(request,
                      'core_custom_queries_app/user/query_step.html',
                      assets=assets,
                      context=context)


def _create_step_context(user_query, user_step, history_id):
    """

    Args:
        user_query:
        user_step:
        history_id:

    Returns:

    """
    user_query.update_time()
    # Next step query data
    query_name = user_query.query.name
    position = user_step.viewable_position
    form_type = user_step.form_type

    # Variable use by the templates
    position_to_show = user_step.viewable_position
    nb_step_to_show = user_query.number_of_query_able_step
    user_query_id = user_query.id
    first_step = user_query.is_current_first_step()

    # Form creation
    if user_step.step.data_type == 'data':
        choices = user_step.get_choices_as_tuple()
        step_name = user_step.step.name
        data_infinity = user_step.step.data_infinity
        data_min_range = user_step.step.data_min_range
        data_max_range = user_step.step.data_max_range
        if form_type == 'radio':
            form = FormRadio(choices=choices, queryName=query_name, stepName=step_name,
                             position=position, user_query=user_query_id, data_type=form_type,
                             step_back=False, history_id=history_id)
        else:
            form = FormCheck(choices=choices, queryName=query_name, stepName=step_name,
                             position=position, user_query=user_query_id,
                             data_min_range=data_min_range, data_max_range=data_max_range,
                             data_infinity=data_infinity, data_type=form_type, step_back=False,
                             history_id=history_id)
    # Next step query date
    else:
        date_range = user_step.step.date_range
        form = FormDateTime(queryName=query_name, position=position, user_query=user_query_id,
                            date_range=date_range, data_type=form_type, step_back=False,
                            history_id=history_id)

    context = {
        'query_name': query_name,
        'position_to_show': position_to_show,
        'nb_step_to_show': nb_step_to_show,
        'first_step': first_step,
        'form': form
    }

    return context


@decorators.permission_required(content_type=rights.custom_queries_content_type,
                                permission=rights.custom_queries_access, login_url=reverse_lazy("core_main_app_login"))
def output_files(request, history_id):
    """ Display output files view

    Args:
        request:
        history_id:

    Returns:

    """
    try:
        user_query = temp_user_query_api.get_by_history_id(history_id)
        # Load the step from the history
        if user_query.history.status == 2:
            # If the file has been created, load the files, and render the download file
            id_file_json = user_query.str_id_file_json
            id_file_csv = user_query.str_id_file_csv
            id_file_xml = user_query.str_id_file_xml
            query_name = user_query.query.name
            preview_json = temp_output_file_api.load_file(id_file_json)[:2000]
            preview_csv = temp_output_file_api.load_file(id_file_csv)[:2000]
            if len(preview_csv) == 0:
                preview_csv = 'The file is empty.'
            preview_xml = temp_output_file_api.load_file(id_file_xml)[:2000]
            form = FormResult(
                queryName=query_name,
                preview_file_csv=preview_csv,
                preview_file_json=preview_json,
                preview_file_xml=preview_xml,
                hidden_id_file_csv=id_file_csv,
                hidden_id_file_json=id_file_json,
                hidden_id_file_xml=id_file_xml
            )
            form.fields['formats'].initial = 'id_formats_0'
            context = {'form': form,
                       'query_name': query_name}
            assets = {
                "js": [
                    {
                        "path": 'core_custom_queries_app/user/js/custom_queries.js',
                        "is_raw": False
                    },
                ],
            }

            return render(request,
                          "core_custom_queries_app/user/query_results.html",
                          assets=assets,
                          context=context)
        else:
            messages.add_message(request, messages.ERROR,
                                 "An internal problem occurred during the output file creation. "
                                 "The administrator has been noticed.")
            return redirect(reverse("core_custom_queries_app_index"))
    except Exception, e:
        messages.add_message(request, messages.ERROR,
                             e.message)
        return redirect(reverse("core_custom_queries_app_index"))


@decorators.permission_required(content_type=rights.custom_queries_content_type,
                                permission=rights.custom_queries_access, login_url=reverse_lazy("core_main_app_login"))
def download(request):
    """ Generate the output files to download it

    Args:
        request:

    Returns:

    """
    id_file_csv = request.POST.get('hidden_id_file_csv', None)
    id_file_json = request.POST.get('hidden_id_file_json', None)
    id_file_xml = request.POST.get('hidden_id_file_xml', None)
    name = request.POST.get('hidden_query_name', None)
    formats = request.POST.get('formats', None)

    try:
        if formats == 'csv':
            output_file = temp_output_file_api.load_file(id_file_csv)
            extension = ".csv"
            content_type = "application/CSV"
        elif formats == 'json':
            output_file = temp_output_file_api.load_file(id_file_json)
            extension = ".json"
            content_type = "application/json"
        else:
            output_file = temp_output_file_api.load_file(id_file_xml)
            extension = ".xml"
            content_type = "application/xml"
    except:
        messages.add_message(request,
                             messages.ERROR,
                             "An internal problem occurred, the administrator has been notified.")
        return redirect(reverse("custom_queries_queryChoose"))

    today = datetime.now()
    name += "_" + str(today.month) + \
            "_" + str(today.day) + \
            "_" + str(today.year) + \
            "_" + str(today.hour) + \
            "_" + str(today.minute) + \
            "_" + str(today.second)

    # FIXME: test with large files
    response = get_file_http_response(output_file, name, content_type, extension)

    return response
