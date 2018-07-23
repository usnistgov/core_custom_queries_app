""" TempChoiceListFile model
"""
from django_mongoengine import Document, fields

from core_custom_queries_app.components.temp_bucket_id_files.models import TempBucketIdFiles


class TempChoiceListFile(Document):
    """
    Model which associate a specific choice the list of files
    """
    choice = fields.StringField()
    list_buckets = fields.ListField(fields.ReferenceField(TempBucketIdFiles, blank=True), blank=True)

    @staticmethod
    def get_all():
        """Return all TempChoiceListFile.

        Returns:

        """
        return TempChoiceListFile.objects().all()

    def delete_database(self):
        """
        Delete function

        Delete each part of the choice and the associated files.
        """
        for bucket in self.list_buckets:
            try:
                bucket_obj = TempBucketIdFiles.objects.get(id=bucket.id)
                bucket_obj.delete_database()
            except:
                pass

        self.delete()
