""" TempUserQuery api
"""
from core_custom_queries_app.models import TempUserQuery


def get_by_id(temp_user_query_id):
    """Return a TempUserQuery given its id.

    Args:
        temp_user_query_id:

    Returns:

    """
    return TempUserQuery.get_by_id(temp_user_query_id)


def get_by_history_id(history_id):
    """Return a TempUserQuery given its history id.

    Args:
        history_id:

    Returns:

    """
    return TempUserQuery.get_by_history_id(history_id)


def get_all():
    """Return all TempUserQuery.

    Returns:

    """
    return TempUserQuery.get_all()
