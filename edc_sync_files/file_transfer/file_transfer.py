import os.path
import collections

from hurry.filesize import size
from os import listdir

from ..models import ExportedTransactionFileHistory
from .file_connector import FileConnector


class FileTransfer:
    """Transfer a list of files to the remote host or within host.
    """

    def __init__(self, file_connector=None):
        self.file_connector = file_connector or FileConnector()
        self.ordered_files = collections.OrderedDict()

    @property
    def files(self):
        """Builds a list of filenames in the source dir (Specified in apps.py).
        """
        files = []
        for filename in listdir(self.file_connector.source_folder):
            if filename.endswith('.json'):
                files.append(filename)
        return files

    @property
    def files_dict(self):
        """ Build a list of file attrs.
        """
        file_attrs = []
        recorded_files = ExportedTransactionFileHistory.objects.filter(
            filename__in=self.files, sent=False).order_by('created')
        for history in recorded_files:
            source_filename = os.path.join(
                self.file_connector.source_folder, history.filename)
            file_attr = os.stat(source_filename)
            data = dict({
                'filename': history.filename,
                'filesize': size(file_attr.st_size),
            })
            file_attrs.append(data)
        return file_attrs

    def copy_files(self, filename=None):
        """ Copies the files from source folder to destination folder.
        """
        copied = False
        if filename:  # Use by client
            for f in self.files_dict:
                if f.get('filename') == filename:
                    copied = self.file_connector.copy(f.get('filename'))
        else:  # Use by community server to send files to central server
            for f in self.files_dict:
                filename = f.get('filename')
                copied = self.file_connector.copy(filename)
                if copied:
                    self.archive(filename)
                    # reset
                    copied = False
        return copied

    def archive(self, filename):
        """ Move file from source dir to archive dir (Specified in apps.py).
        """
        return self.file_connector.archive(filename)

    def approve_sent_file(self, filename, approval_code):
        """ Update history record after all files sent to the server.
        """
        try:
            sent_file_history = ExportedTransactionFileHistory.objects.get(
                filename=filename)
            sent_file_history.approval_code = approval_code
            sent_file_history.save()
        except ExportedTransactionFileHistory.DoesNotExist:
            pass
