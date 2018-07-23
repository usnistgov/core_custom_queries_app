""" TempBucketOutputFile api
"""
from core_custom_queries_app.components.temp_bucket_output_file.models import TempBucketOutputFiles


def get_all():
    """Return all TempBucketOutputFiles.

    Returns:

    """
    return TempBucketOutputFiles.get_all()
