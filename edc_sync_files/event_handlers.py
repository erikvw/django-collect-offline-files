import os

from django.utils import timezone
from queue import Queue
from watchdog.events import PatternMatchingEventHandler

from edc_sync.consumer import Consumer

from .transaction import TransactionImporter
from .patterns import transaction_filename_pattern


class EventHandlerError(Exception):
    pass


class TransactionFileEventHandler(PatternMatchingEventHandler):

    def __init__(self, patterns=None, verbose=None):
        patterns = patterns or transaction_filename_pattern
        super().__init__(patterns=patterns, ignore_directories=True)
        self.verbose = verbose
        self.file_queue = Queue()

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event, **kwargs):
        if self.verbose:
            print('{} {} {}'.format(
                timezone.now(), event.event_type, event.src_path))
        self.file_queue.put(event.src_path)
        while not self.file_queue.empty():
            path = self.file_queue.get()
            tx_importer = TransactionImporter(filename=os.path.basename(path))
        self.consumed = Consumer(
            transactions=tx_importer.tx_pks, **kwargs).consume()
