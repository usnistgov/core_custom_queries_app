"""
Celery tasks.
"""
from datetime import datetime

from celery.schedules import crontab
from celery.task import periodic_task
from redis import Redis, ConnectionError

from core_custom_queries_app.components.history_query import api as history_query_api
from core_custom_queries_app.components.log_file import api as log_file_api
from core_custom_queries_app.components.log_file.models import LogFile
from core_custom_queries_app.components.query_to_treat import api as query_to_treat_api
from core_custom_queries_app.components.temp_bucket_id_files import api as temp_bucket_id_files_api
from core_custom_queries_app.components.temp_bucket_output_file import api as temp_bucket_output_file_api
from core_custom_queries_app.components.temp_choice_list_file import api as temp_choice_list_file_api
from core_custom_queries_app.components.temp_output_file import api as temp_output_file_api
from core_custom_queries_app.components.temp_user_query import api as temp_user_query_api
from core_custom_queries_app.components.temp_user_step import api as temp_user_step_api
from core_custom_queries_app.utils import flat_list
from core_main_app.commons.exceptions import DoesNotExist
from qdr.settings import REDIS_URL


@periodic_task(run_every=crontab(minute=0, hour=0))
def clean_mongo_db():
    """
    Clean the database.
    :return:
    """

    # Clean the database of ended temporary query if they are ended before 7 days ago.
    datetime_now = datetime.now()
    history_queries = history_query_api.get_all()
    for history_query in history_queries:
        try:
            user_query = temp_user_query_api.get_by_id(history_query.query_id)
            if (datetime_now - user_query.last_modified).total_seconds() > (60 * 60 * 24 * 7):
                try:
                    history_query.delete_database()
                except:
                    pass
        except:
            pass

    # Delete orphan HistoryQuery
    all_history_id_to_keep = temp_user_query_api.get_all().values_list('history')
    histories_to_delete = history_query_api.get_all().filter(id__nin=all_history_id_to_keep)
    for history_to_delete in histories_to_delete:
        history_to_delete.delete_database()

    # Delete orphan TempUserQuery
    all_temp_user_query_to_keep = history_query_api.get_all().values_list('query_id')
    all_temp_user_query_to_delete = temp_user_query_api.get_all().filter(id__nin=all_temp_user_query_to_keep)
    for query_to_delete in all_temp_user_query_to_delete:
        query_to_delete.delete_database()

    # Delete orphan TempOutputFile
    temp_output_files_id_to_keep = list()
    all_temp_user_queries = temp_user_query_api.get_all()
    for temp_user_query in all_temp_user_queries:
        if temp_user_query.str_id_file_json != "":
            temp_output_files_id_to_keep.append(temp_user_query.str_id_file_json)
        if temp_user_query.str_id_file_xml != "":
            temp_output_files_id_to_keep.append(temp_user_query.str_id_file_xml)
        if temp_user_query.str_id_file_csv != "":
            temp_output_files_id_to_keep.append(temp_user_query.str_id_file_csv)
    temp_output_files_to_delete = temp_output_file_api.get_all().filter(
        id__nin=temp_output_files_id_to_keep
    )
    for temp_output_file_to_delete in temp_output_files_to_delete:
        temp_output_file_to_delete.delete_database()

    # Delete orphan TempBucketOutputFiles
    temp_bucket_output_files_id_to_keep = list()
    all_files_temp_bucket_output_files_to_keep = temp_output_file_api.get_all().values_list('file')
    all_files_temp_bucket_output_files_to_keep = flat_list(all_files_temp_bucket_output_files_to_keep)
    for id_file in all_files_temp_bucket_output_files_to_keep:
        temp_bucket_output_files_id_to_keep.append(id_file.id)
    temp_bucket_output_files_to_delete = temp_bucket_output_file_api.get_all().filter(
        id__nin=temp_bucket_output_files_id_to_keep)
    for temp_bucket_output_file_to_delete in temp_bucket_output_files_to_delete:
        temp_bucket_output_file_to_delete.delete_database()

    # Delete orphan TempUserStep
    all_temp_user_step_id_to_keep = list()
    all_temp_user_step_to_keep = temp_user_query_api.get_all().values_list('list_steps')
    all_temp_user_step_to_keep = flat_list(all_temp_user_step_to_keep)
    for temp_user_step_to_keep in all_temp_user_step_to_keep:
        all_temp_user_step_id_to_keep.append(temp_user_step_to_keep.id)
    all_temp_user_steps_to_delete = temp_user_step_api.get_all().filter(id__nin=all_temp_user_step_id_to_keep)
    for step_to_delete in all_temp_user_steps_to_delete:
        step_to_delete.delete_database()

    # Delete orphan TempChoiceListFile
    all_temp_choice_list_file_id_to_keep = list()
    all_temp_choice_list_file_to_keep = temp_user_step_api.get_all().values_list('list_choices_id_file')
    all_temp_choice_list_file_to_keep = flat_list(all_temp_choice_list_file_to_keep)
    for temp_choice_list_file_to_keep in all_temp_choice_list_file_to_keep:
        all_temp_choice_list_file_id_to_keep.append(temp_choice_list_file_to_keep.id)
    all_temp_choice_list_file_to_delete = \
        temp_choice_list_file_api.get_all().filter(id__nin=all_temp_choice_list_file_id_to_keep)
    for temp_choice_list_file_to_delete in all_temp_choice_list_file_to_delete:
        temp_choice_list_file_to_delete.delete_database()

    # Delete orphan TempBucketIdFiles
    all_temp_bucket_id_files = list()
    all_temp_bucket_id_files_to_keep = temp_bucket_id_files_api.get_all().values_list('list_files')
    all_temp_bucket_id_files_to_keep = flat_list(all_temp_bucket_id_files_to_keep)
    for temp_bucket_id_files_to_keep in all_temp_bucket_id_files_to_keep:
        all_temp_bucket_id_files.append(temp_bucket_id_files_to_keep)
    all_temp_bucket_id_files_to_delete = temp_bucket_id_files_api.get_all().filter(id__nin=all_temp_bucket_id_files)
    for temp_bucket_id_files_to_delete in all_temp_bucket_id_files_to_delete:
        temp_bucket_id_files_to_delete.delete_database()


@periodic_task(run_every=crontab(minute='*'))
def get_files_to_create():
    """
    Treat the queries in the waiting queue.

    Get the queries from the database and put them into the waiting list.
    If a the waiting list is empty or the worker is already run, do nothing, else, launch the worker.
    """
    redis_server = Redis.from_url(REDIS_URL)

    queries_to_treat = query_to_treat_api.get_all()

    try:
        for query_to_treat in queries_to_treat:
            Redis.rpush(redis_server, 'list_ids', str(query_to_treat.query.id))
            query_to_treat.delete_database()

        if not Redis.exists(redis_server, 'is_working'):
            Redis.set(redis_server, 'is_working', False)

        if Redis.get(redis_server, 'is_working') == 'False':
            Redis.set(redis_server, 'is_working', True)
            if Redis.exists(redis_server, 'list_ids'):
                run_worker(redis_server)
            Redis.set(redis_server, 'is_working', False)
    except ConnectionError, e:
        log_file = LogFile(application="Custom Queries",
                           message="Redis not reachable, is it running?",
                           additionalInformation={'message': e.message},
                           timestamp=datetime.now())
        log_file_api.upsert(log_file)


def run_worker(redis_server):
    """
    Worker algorithm.

    While the waiting list is not empty, treat the query in order.

    :param redis_server: Redis server instance.
    """
    try:
        while Redis.exists(redis_server, 'list_ids'):
            current_id = Redis.lpop(redis_server, 'list_ids')
            redis_server.set('current_id', current_id)
            try:
                query = temp_user_query_api.get_by_id(current_id)
                query.create_outputs_file()
            except DoesNotExist:
                pass
            redis_server.set('current_id', "None")
    except ConnectionError, e:
        log_file = LogFile(application="Custom Queries",
                           message="Redis not reachable, is it running?",
                           additionalInformation={'message': e.message},
                           timestamp=datetime.now())
        log_file_api.upsert(log_file)
