""" History Query api
"""
from core_custom_queries_app.models import HistoryQuery


def get_by_id(history_query_id):
    """ Return a HistoryQuery given its id.

    Args:
        history_query_id:

    Returns:

    """
    return HistoryQuery.get_by_id(history_query_id)


def get_all_by_user_id(user_id):
    """ Return a list of HistoryQuery given their user_id.

    Args:
        user_id:

    Returns:

    """
    return HistoryQuery.get_all_by_user_id(user_id)


def get_all():
    """ Return a list of all HistoryQuery.

    Returns:

    """
    return HistoryQuery.get_all()
