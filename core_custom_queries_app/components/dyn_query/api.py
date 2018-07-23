""" Api for DynQueries
"""
from core_custom_queries_app.components.dyn_query.models import DynQuery
from core_custom_queries_app.components.dyn_query_step import api as dyn_query_step_api
from core_custom_queries_app.components.temp_user_query import api as temp_user_query_api


def upsert(dyn_query):
    """ Save or Update DynQuery.

    Args:
        dyn_query:

    Returns:

    """
    return dyn_query.save()


def get_by_id(dyn_query_id):
    """ Return a DynQuery given its id.

    Args:
        dyn_query_id:

    Returns:

    """
    return DynQuery.get_by_id(dyn_query_id)


def get_all():
    """ Get all DynQueries.

    Returns:

    """
    return DynQuery.get_all()


def delete(dyn_query):
    """ Delete DynQuery.

    Args:
        dyn_query:

    Returns:

    """
    # delete linked steps
    for step in dyn_query.steps:
        dyn_query_step_api.delete(step)

    # delete linked temp user queries
    temp_queries = temp_user_query_api.get_all().filter(query=dyn_query)
    for temp_query in temp_queries:
        temp_query.delete_database()
    dyn_query.delete()
