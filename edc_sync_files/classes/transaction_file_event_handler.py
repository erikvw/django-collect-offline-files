import re

from django.utils import timezone
from django.apps import apps as django_apps

from watchdog.events import PatternMatchingEventHandler

from .transaction_file_queue import TransactionFileQueue


class EventHandlerError(Exception):
    pass


class TransactionFileEventHandler(PatternMatchingEventHandler):

    """
       event.event_type
           'created' only for this class.
       event.is_directory
           True | False
       event.src_path
           path/to/observed/file
    """
    filename_pattern = r'^\w+\_\d{14}\.json$'

    patterns = ["*.json"]

    def __init__(self, verbose=None):
        super(TransactionFileEventHandler, self).__init__(ignore_directories=True)
        self.verbose = verbose or True
        edc_sync_file_app = django_apps.get_app_config('edc_sync_files')
        self.destination_folder = edc_sync_file_app.destination_folder
        self.archive_folder = edc_sync_file_app.archive_folder
        self.file_queue = TransactionFileQueue()

    def process(self, event):
        self.output_to_console(
            '{} {} {} Not handled.'.format(
                timezone.now(), event.event_type, event.src_path))

    def on_created(self, event):
        self.process_on_added(event)

    def output_to_console(self, msg):
        if self.verbose:
            print(msg)

    def process_on_added(self, event):
        """Moves file from source_dir to the destination_dir as
        determined by :func:`folder_handler.select`."""
        filename = event.src_path.split("/")[-1]
        pattern = re.compile(self.filename_pattern)
        if pattern.match(filename):
            self.file_queue.add_new_uploaded_file(event.src_path)
            self.file_queue.process_queued_files()
            self.output_to_console('{} {} {}'.format(
                timezone.now(), event.event_type, event.src_path))
        else:
            print(event.src_path)
