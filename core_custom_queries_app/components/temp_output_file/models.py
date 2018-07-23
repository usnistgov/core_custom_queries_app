""" TempBucketOutputFiles model
"""
from django_mongoengine import Document, fields
from mongoengine import errors as mongoengine_errors

from core_custom_queries_app.components.temp_bucket_output_file.models import TempBucketOutputFiles
from core_main_app.commons import exceptions


class TempOutputFile(Document):
    """
    Output files
    """
    data_type = fields.StringField()  # Type of the file (cxv, json or xml)
    # FIXME: use GridFS?
    file = fields.ListField(fields.ReferenceField(TempBucketOutputFiles, blank=True), blank=True)  # List of file parts

    @staticmethod
    def get_by_id(temp_output_file_id):
        """Return a TempOutputFile given its id.

        Args:
            temp_output_file_id:

        Returns:

        """
        try:
            return TempOutputFile.objects.get(pk=str(temp_output_file_id))
        except mongoengine_errors.DoesNotExist as e:
            raise exceptions.DoesNotExist(e.message)
        except Exception as ex:
            raise exceptions.ModelError(ex.message)

    @staticmethod
    def get_all():
        """Return all TempOutputFile.

        Returns:

        """
        return TempOutputFile.objects().all()

    def delete_database(self):
        """
        Delete function

        Delete all part of the file.
        """
        for part_file in self.file:
            part_file.delete_database()
        self.delete()

    def save_file(self, str_file, type_file):
        """
        Save the current file.

        :param str_file: File content
        :param type_file: Type of file
        :return: id of the saved file
        """

        # Cut the file
        chunks_file = [str_file[x:x + 11000000] for x in xrange(0, len(str_file), 11000000)]
        self.data_type = type_file
        list_chunks = list()
        # Save each part of the file
        for chunk_file in chunks_file:
            temp_bucket_output_file = TempBucketOutputFiles()
            temp_bucket_output_file.piece_file = chunk_file
            temp_bucket_output_file.save()
            list_chunks.append(temp_bucket_output_file)
        self.file = list_chunks
        self.save()
        return str(self.id)

    @staticmethod
    def load_file(id_output_file):
        """
        Load the output file.

        :param id_output_file: File id to load.
        :return: File content
        """
        temp_output_file = TempOutputFile.get_by_id(id_output_file)

        list_output_file = []
        for chunk in temp_output_file.file:  # Load each part of the file
            list_output_file.append(chunk.piece_file)
        return "".join(list_output_file)  # Create the file
