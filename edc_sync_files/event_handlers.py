import os
import sys

from django.apps import apps as django_apps
from watchdog.events import PatternMatchingEventHandler

from .patterns import transaction_filename_pattern
from .queues import batch_queue, tx_file_queue


class EventHandlerError(Exception):
    pass


class TransactionFileEventHandler(PatternMatchingEventHandler):

    def __init__(self, patterns=None, path=None, verbose=None):
        app_config = django_apps.get_app_config('edc_sync_files')
        patterns = patterns or transaction_filename_pattern
        super().__init__(patterns=patterns, ignore_directories=True)
        self.path = path or app_config.archive_folder
        if verbose:
            sys.stdout.write(f'archive path: {self.path}\n')
            sys.stdout.flush()

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event, **kwargs):
        """Processes tasks in tx_file_queue.
        """
        tx_file_queue.put(os.path.basename(event.src_path))
        while not tx_file_queue.empty():
            tx_file_queue.next_task()


class TransactionBatchEventHandler(PatternMatchingEventHandler):

    """Monitors the archive folder and processes on created.
    """

    def __init__(self, patterns=None, path=None, verbose=None):
        app_config = django_apps.get_app_config('edc_sync_files')
        patterns = patterns or transaction_filename_pattern
        super().__init__(patterns=patterns, ignore_directories=True)
        self.verbose = verbose
        self.path = path or app_config.archive_folder
        if verbose:
            sys.stdout.write(f'archive path: {self.path}\n')
            sys.stdout.flush()

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event, **kwargs):
        """Processes tasks in batch_queue.
        """
        while not batch_queue.empty():
            batch_queue.next_task()
