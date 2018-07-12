""" Dyn Query Model
"""

from django_mongoengine import fields, Document
from mongoengine import errors as mongoengine_errors
from mongoengine.queryset.base import CASCADE

from core_custom_queries_app.components.dyn_query_step.models import DynQueryStep
from core_main_app.commons import exceptions


class DynQuery(Document):
    """
    Query object created by the administrator.
    """
    # Query name
    name = fields.StringField(blank=False, unique=True)
    # Limit the query to number_records records
    is_limited = fields.BooleanField(blank=False, default=False)
    # Records number to limit the query
    number_records = fields.IntField(blank=True)
    # Group query
    group = fields.StringField(blank=False)
    # Schema associated to the query
    # FIXME: replace by a reference field
    schema = fields.StringField(blank=False)
    # List of step links to the query
    steps = fields.ListField(fields.ReferenceField(DynQueryStep,
                                                   blank=False,
                                                   reverse_delete_rule=CASCADE))

    @staticmethod
    def get_by_id(dyn_query_id):
        """Return a DynQuery given its id.

        Args:
            dyn_query_id:

        Returns:

        """
        try:
            return DynQuery.objects.get(pk=str(dyn_query_id))
        except mongoengine_errors.DoesNotExist as e:
            raise exceptions.DoesNotExist(e.message)
        except Exception as ex:
            raise exceptions.ModelError(ex.message)

    @staticmethod
    def get_all():
        """Return all DynQueries.

        Returns:

        """
        return DynQuery.objects().all()
