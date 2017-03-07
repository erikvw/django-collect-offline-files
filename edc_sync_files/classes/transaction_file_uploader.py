import collections
import queue as q
import shutil
from os.path import join

from django.apps import apps as django_apps

from .transaction_file import TransactionFile


class TransactionFileUploader(object):

    def __init__(self, transation_file=None):
        self.transation_file = transation_file
        self.queued_files = q.Queue()
        self._processed_files = collections.OrderedDict()
        self.edc_sync_file_app = django_apps.get_app_config('edc_sync_files')

    def add_new_uploaded_file(self, path):
        self.queued_files.put(TransactionFile(path=path))

    @property
    def processed_files(self):
        return self._processed_files

    def process_queued_files(self):
        while not self.queued_files.empty():
            transation_file = self.queued_files.get()
            status = transation_file.upload()
            transation_file.archived = status
            self._processed_files.update({
                transation_file.filename: transation_file
            })
        for _, processed_file in self.processed_files.items():
            destination_filename = join(
                self.edc_sync_file_app.archive_folder, processed_file.filename)
            source_filename = join(
                self.edc_sync_file_app.destination_folder, processed_file.filename)
            if processed_file.is_uploaded:
                shutil.move(source_filename, destination_filename)  # archive the file
