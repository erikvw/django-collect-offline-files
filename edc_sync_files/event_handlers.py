import os

from django.apps import apps as django_apps
from watchdog.events import PatternMatchingEventHandler

from .patterns import transaction_filename_pattern
from .queues import batch_queue, tx_file_queue


class EventHandlerError(Exception):
    pass


class TransactionFileEventHandler(PatternMatchingEventHandler):

    def __init__(self, patterns=None, archive_path=None, verbose=None):
        app_config = django_apps.get_app_config('edc_sync_files')
        patterns = patterns or transaction_filename_pattern
        super().__init__(patterns=patterns, ignore_directories=True)
        self.verbose = verbose
        self.archive_path = archive_path or app_config.archive_folder

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

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event, **kwargs):
        """Processes tasks in batch_queue.
        """
        while not batch_queue.empty():
            batch_queue.next_task()
