""" QueryToTreat api.
"""
from core_custom_queries_app.models import QueryToTreat


def get_all():
    """Return all QueryToTreat.

    Returns:

    """
    return QueryToTreat.get_all()
