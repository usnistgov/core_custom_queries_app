""" Specialized data api for Custom Queries
"""
# FIXME: access control?
from core_main_app.components.data.models import Data


# FIXME: move to core_main_app
def execute_custom_query(query, projection):
    """

    Args:
        query:
        projection:

    Returns:

    """
    return Data.execute_query(query).only(projection)


# FIXME: move to core_main_app
def get_all_by_template(template):
    """

    Args:
        template:

    Returns:

    """
    return Data.objects(template=template)
