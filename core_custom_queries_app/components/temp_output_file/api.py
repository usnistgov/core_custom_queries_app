""" TempOutputFile api
"""
from core_custom_queries_app.components.temp_output_file.models import TempOutputFile


def load_file(id_output_file):
    """ Load output file from its id

    Args:
        id_output_file:

    Returns:

    """
    return TempOutputFile.load_file(id_output_file)


def get_all():
    """Return all TempOutputFile.

    Returns:

    """
    return TempOutputFile.get_all()
