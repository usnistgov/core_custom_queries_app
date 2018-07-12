""" Api for DynQueryStep
"""
from core_custom_queries_app.components.dyn_query_step.models import DynQueryStep


def upsert(dyn_query_step):
    """ Save or Update DynQueryStep.

    Args:
        dyn_query_step:

    Returns:

    """
    return dyn_query_step.save()


def delete(dyn_query_step):
    """

    Args:
        dyn_query_step:

    Returns:

    """
    dyn_query_step.delete()


def get_by_id(dyn_query_step_id):
    """ Return a DynQueryStep given its id.

    Args:
        dyn_query_step_id:

    Returns:

    """
    return DynQueryStep.get_by_id(dyn_query_step_id)