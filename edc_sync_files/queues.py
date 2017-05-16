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

logging.basicConfig(
    filename=os.path.join(app_config.log_folder, 'observer.log'),
    level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionFileQueue(Queue):

    def __init__(self, path=None, patterns=None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.patterns = patterns or transaction_filename_pattern

    def reload(self):
        combined = "(" + ")|(".join(self.patterns) + ")"
        for filename in os.listdir(self.path):
            if re.match(combined, filename):
                self.put(filename)

    def next_task(self):
        filename = self.get()
        tx_importer = TransactionImporter(filename=filename, path=self.path)
        try:
            batch = tx_importer.import_batch()
        except TransactionImporterError as e:
            logger.error(e)
        else:
            batch_queue.put(batch.batch_id)
            self.task_done()


class BatchQueue(Queue):

    def __init__(self, model=None, **kwargs):
        super().__init__(**kwargs)
        self.model = model

    def reload(self):
        for obj in self.model.objects.filter(consumed=False).order_by('created'):
            self.put(obj.batch_id)

    def next_task(self):
        batch_id = self.get()
        batch = Batch()
        batch.batch_id = batch_id
        tx_deserializer = TransactionDeserializer()
        try:
            tx_deserializer.deserialize_transactions(
                transactions=batch.saved_transactions)
        except TransactionDeserializerError as e:
            logger.error(e)
        else:
            batch.close()
            self.task_done()


batch_queue = BatchQueue(model=ImportedTransactionFileHistory)
tx_file_queue = TransactionFileQueue(path=app_config.destination_folder)
