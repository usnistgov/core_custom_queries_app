""" TempBucketIdFiles model
"""
from django_mongoengine import Document, fields


class TempBucketIdFiles(Document):
    """
    Part of the input file
    """
    list_files = fields.ListField(blank=True)

    @staticmethod
    def get_all():
        """Return all TempBucketIdFiles.

        Returns:

        """
        return TempBucketIdFiles.objects().all()

    def delete_database(self):
        """
        Delete function
        """
        self.delete()
