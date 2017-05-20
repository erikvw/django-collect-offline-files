import logging
import os
import re

from django.apps import apps as django_apps
from queue import Queue

from edc_sync.transaction_deserializer import TransactionDeserializer
from edc_sync.transaction_deserializer import TransactionDeserializerError

from .transaction import TransactionImporterBatch, FileArchiver, FileArchiverError
from .transaction import TransactionImporter, TransactionImporterError

app_config = django_apps.get_app_config('edc_sync_files')
logger = logging.getLogger('edc_sync_files')


class BaseFileQueue(Queue):

    file_archiver_cls = FileArchiver

    def __init__(self, regexes=None, src_path=None, dst_path=None, **kwargs):
        super().__init__(**kwargs)
        self.regexes = regexes
        self.src_path = src_path
        self.dst_path = dst_path
        try:
            self.file_archiver = self.file_archiver_cls(
                src_path=src_path, dst_path=dst_path)
        except FileArchiverError as e:
            raise TransactionDeserializerError(e)

    def reload(self):
        """Reloads /path/to/filenames into the queue that match the regexes.
        """
        combined = "(" + ")|(".join(self.regexes) + ")"
        for filename in os.listdir(self.src_path):
            if re.match(combined, filename):
                self.put(os.path.join(self.src_path, filename))

    def archive(self, filename=None):
        self.file_archiver.archive(filename)


class IncomingTransactionsFileQueue(BaseFileQueue):

    tx_importer_cls = TransactionImporter

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tx_importer = self.tx_importer_cls(import_path=self.src_path)

    def next_task(self):
        """Calls import_batch for the next filename in the queue
        and "archives" the file.

        The archive folder is typically the folder for the deserializer queue.
        """
        filename = self.get()

        try:
            self.tx_importer.import_batch(filename=filename)
        except TransactionImporterError as e:
            logger.error(f'TransactionImporterError. Got {e}')
        else:
            self.archive(filename)
            self.task_done()


class DeserializeTransactionsFileQueue(BaseFileQueue):

    batch_cls = TransactionImporterBatch
    tx_deserializer_cls = TransactionDeserializer

    def __init__(self, history_model=None, allow_self=None, allow_any_role=None, **kwargs):
        super().__init__(**kwargs)
        self.history_model = history_model
        self.allow_self = allow_self
        self.allow_any_role = allow_any_role

    def next_task(self):
        """Deserializes all transactions for this batch and
        archives the file.
        """
        p = self.get()
        filename = os.path.basename(p)
        batch = self.get_batch(filename)
        tx_deserializer = self.tx_deserializer_cls(
            allow_self=self.allow_self,
            allow_any_role=self.allow_any_role)
        try:
            tx_deserializer.deserialize_transactions(
                transactions=batch.saved_transactions)
        except TransactionDeserializerError as e:
            logger.error(f'TransactionDeserializerError. Got {e}')
        else:
            batch.close()
            self.archive(filename)
            self.task_done()

    def get_batch(self, filename=None):
        """Returns a batch instance given the filename.
        """
        history = self.history_model.objects.get(
            filename=filename, consumed=False)
        batch = self.batch_cls()
        batch.batch_id = history.batch_id
        batch.filename = history.filename
        return batch
