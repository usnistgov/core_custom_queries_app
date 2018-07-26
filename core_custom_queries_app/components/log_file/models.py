""" LogFile Model
"""
from django_mongoengine import fields, Document
from mongoengine import errors as mongoengine_errors

from core_main_app.commons import exceptions


class LogFile(Document):
    """
    Error reports for administrators
    """
    application = fields.StringField(blank=False)            # Django application name concerned by the error
    code = fields.IntField(blank=True)                       # Error code
    message = fields.StringField(blank=False)                # Error message
    additionalInformation = fields.DictField(blank=True)     # Dictionary of additional information
    timestamp = fields.DateTimeField(blank=True)             # Error creation date

    @staticmethod
    def get_by_id(log_file_id):
        """Return a LogFile given its id.

        Args:
            log_file_id:

        Returns:

        """
        try:
            return LogFile.objects.get(pk=str(log_file_id))
        except mongoengine_errors.DoesNotExist as e:
            raise exceptions.DoesNotExist(e.message)
        except Exception as ex:
            raise exceptions.ModelError(ex.message)

    @staticmethod
    def get_all():
        """Return all LogFiles.

        Returns:

        """
        return LogFile.objects().all()

    def delete_database(self):
        """
        Delete function
        """
        self.delete()
