""" TempUserStep api.
"""
from core_custom_queries_app.components.temp_user_step.models import TempUserStep


def get_all():
    """Return all TempUserStep.

    Returns:

    """
    return TempUserStep.get_all()
