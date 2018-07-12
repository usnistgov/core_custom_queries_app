""" Dyn Query Step Model
"""
from django_mongoengine import fields, Document
from mongoengine import errors as mongoengine_errors

from core_main_app.commons import exceptions


class DynQueryStep(Document):
    """
    Step object created by the administrator.
    """
    # Step name
    name = fields.StringField(blank=False, unique=False)
    # True if the step is not query-able, False else
    output_field = fields.BooleanField(blank=False, unique=False)
    # Relative path to the object, in dot notation
    xpath = fields.StringField(blank=False, unique=False)
    # Define the part of the node concerned by the
    target = fields.StringField(blank=False, unique=False)
    # query, could be name, attribute, or value
    value = fields.StringField(blank=True, unique=False)
    # Define the name of the attribute concerned by
    data_type = fields.StringField(blank=False, unique=False)
    # Define if the there is a restriction to the step
    restriction = fields.BooleanField(blank=True, unique=False)
    # Define the minimum range for multiple choices step
    data_min_range = fields.IntField(blank=True, unique=False)
    # Define the maximum range for multiple choices step
    data_max_range = fields.IntField(blank=True, unique=False)
    # Define the minimum range to infinity
    data_infinity = fields.BooleanField(blank=True, unique=False)      #
    # Define the number of days for date query
    date_range = fields.IntField(blank=True, unique=False)

    @staticmethod
    def get_by_id(dyn_query_step_id):
        """Return a DynQueryStep given its id.

        Args:
            dyn_query_step_id:

        Returns:

        """
        try:
            return DynQueryStep.objects.get(pk=str(dyn_query_step_id))
        except mongoengine_errors.DoesNotExist as e:
            raise exceptions.DoesNotExist(e.message)
        except Exception as ex:
            raise exceptions.ModelError(ex.message)
