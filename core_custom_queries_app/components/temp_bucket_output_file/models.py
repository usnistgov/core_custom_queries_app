""" TempBucketOutputFiles model
"""
from django_mongoengine import Document, fields


class TempBucketOutputFiles(Document):
    """
    Part of the output file string
    """
    piece_file = fields.StringField()

    @staticmethod
    def get_all():
        """Return all TempBucketOutputFiles.

        Returns:

        """
        return TempBucketOutputFiles.objects().all()

    def delete_database(self):
        """
        Delete function
        """
        self.delete()
