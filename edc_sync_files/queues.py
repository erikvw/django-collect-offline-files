import re
import logging
import os

from django.apps import apps as django_apps
from queue import Queue

from edc_sync.transaction_deserializer import TransactionDeserializer
from edc_sync.transaction_deserializer import TransactionDeserializerError

from .models import ImportedTransactionFileHistory
from .transaction.transaction_importer import Batch
from .transaction import TransactionImporter, TransactionImporterError
from .patterns import transaction_filename_pattern

app_config = django_apps.get_app_config('edc_sync_files')
logger = logging.getLogger('edc_sync_files')


class TransactionFileQueue(Queue):

    def __init__(self, path=None, patterns=None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.patterns = patterns or transaction_filename_pattern

    def reload(self):
        """Reloads filenames into the queue that match the pattern.
        """
        combined = "(" + ")|(".join(self.patterns) + ")"
        for filename in os.listdir(self.path):
            if re.match(combined, filename):
                self.put(filename)

    def next_task(self):
        """Calls import_batch for the next filename in the queue.
        """
        filename = self.get()
        tx_importer = TransactionImporter(filename=filename, path=self.path)
        try:
            batch = tx_importer.import_batch()
        except TransactionImporterError as e:
            logger.error(f'TransactionImporterError. Got {e}')
        else:
            batch_queue.put(batch.batch_id)
            self.task_done()


class BatchQueue(Queue):

    def __init__(self, history_model=None, **kwargs):
        super().__init__(**kwargs)
        self.history_model = history_model

    def reload(self):
        """Reloads batch_ids not yet deserialized into the queue
        from the history model.
        """
        for obj in self.history_model.objects.filter(consumed=False).order_by('created'):
            self.put(obj.batch_id)

    def next_task(self):
        """Deserializes all transactions for this batch.
        """
        batch_id = self.get()
        batch = Batch()
        batch.batch_id = batch_id
        tx_deserializer = TransactionDeserializer()
        try:
            tx_deserializer.deserialize_transactions(
                transactions=batch.saved_transactions)
        except TransactionDeserializerError as e:
            logger.error(f'TransactionDeserializerError. Got {e}')
        else:
            batch.close()
            self.task_done()


batch_queue = BatchQueue(history_model=ImportedTransactionFileHistory)
tx_file_queue = TransactionFileQueue(path=app_config.destination_folder)
