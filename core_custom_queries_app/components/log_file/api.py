""" Log File api
"""
from core_custom_queries_app.components.log_file.models import LogFile


def upsert(log_file):
    """

    Args:
        log_file:

    Returns:

    """
    return log_file.save()


def get_by_id(log_file_id):
    """Return a LogFile given its id.

    Args:
        log_file_id:

    Returns:

    """
    return LogFile.get_by_id(log_file_id)


def get_all():
    """Return all LogFiles.

    Returns:

    """
    return LogFile.get_all()

