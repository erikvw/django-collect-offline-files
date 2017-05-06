import os

from django.utils import timezone
from queue import Queue
from watchdog.events import PatternMatchingEventHandler

from edc_sync.consumer import Consumer

from .patterns import transaction_filename_pattern
from .transaction import TransactionImporter


class EventHandlerError(Exception):
    pass


class TransactionFileEventHandler(PatternMatchingEventHandler):

    def __init__(self, patterns=None, verbose=None):
        patterns = patterns or transaction_filename_pattern
        super().__init__(patterns=patterns, ignore_directories=True)
        self.verbose = verbose
        self.q = Queue()

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event, **kwargs):
        if self.verbose:
            print('{} {} {}'.format(
                timezone.now(), event.event_type, event.src_path))
        self.q.put(event.src_path)
        while not self.q.empty():
            path = self.q.get()
            tx_importer = TransactionImporter(filename=os.path.basename(path))
            tx_importer.import_batch()
            self.q.task_done()
        self.consumed = Consumer(
            transactions=tx_importer.tx_pks, **kwargs).consume()
