""" TempChoiceListFile api.
"""
from core_custom_queries_app.components.temp_choice_list_file.models import TempChoiceListFile


def get_all():
    """Return all TempChoiceListFile.

    Returns:

    """
    return TempChoiceListFile.get_all()
