import os

from django.utils import timezone
from queue import Queue
from watchdog.events import PatternMatchingEventHandler

from edc_sync.transaction_deserializer import TransactionDeserializer

from .patterns import transaction_filename_pattern
from .transaction import TransactionImporter
from edc_sync_files.transaction.transaction_exporter import Batch


class EventHandlerError(Exception):
    pass


batch_queue = Queue()
file_queue = Queue()


class TransactionFileEventHandler(PatternMatchingEventHandler):

    def __init__(self, patterns=None, verbose=None):
        patterns = patterns or transaction_filename_pattern
        super().__init__(patterns=patterns, ignore_directories=True)
        self.verbose = verbose

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event, **kwargs):
        if self.verbose:
            print('{} {} {}'.format(
                timezone.now(), event.event_type, event.src_path))
        file_queue.put(event.src_path)
        while not file_queue.empty():
            path = file_queue.get()
            tx_importer = TransactionImporter(filename=os.path.basename(path))
            batch = tx_importer.import_batch()
            file_queue.task_done()
            batch_queue.put(batch.batch_id)


class TransactionBatchEventHandler(PatternMatchingEventHandler):

    """Monitors the archive folder and processes on created.
    """

    def __init__(self, patterns=None, verbose=None):
        patterns = patterns or transaction_filename_pattern
        super().__init__(patterns=patterns, ignore_directories=True)
        self.verbose = verbose

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event, **kwargs):
        if self.verbose:
            print('{} {} {}'.format(
                timezone.now(), event.event_type, event.src_path))
        while not batch_queue.empty():
            batch_id = batch_queue.get()
            batch = Batch(batch_id=batch_id)
            tx_deserializer = TransactionDeserializer(batch_id=batch_id)
            tx_deserializer.deserialize_transactions(
                transactions=batch.saved_transactions)
            batch_queue.task_done()
