""" TempBucketIdFiles
"""
from core_custom_queries_app.components.temp_bucket_id_files.models import TempBucketIdFiles


def get_all():
    """Return all TempBucketIdFiles.

    Returns:

    """
    return TempBucketIdFiles.get_all()
