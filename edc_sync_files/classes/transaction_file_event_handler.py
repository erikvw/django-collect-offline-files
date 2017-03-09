import re
import time
import os
from os.path import join


from django.utils import timezone
from django.apps import apps as django_apps

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from .transaction_file_manager import TransactionFileManager


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

    patterns = ["*.json"]  # TODO add regex for filename

    def __init__(self, verbose=None):
        super(TransactionFileEventHandler, self).__init__(ignore_directories=True)
        self.verbose = verbose or True
        edc_sync_file_app = django_apps.get_app_config('edc_sync_files')
        self.destination_folder = edc_sync_file_app.destination_folder
        self.archive_folder = edc_sync_file_app.archive_folder
        self.file_manager = TransactionFileManager()

    def process(self, event):
        self.output_to_console(
            '{} {} {} Not handled.'.format(timezone.now(), event.event_type, event.src_path))

    def on_modified(self, event):
        self.process_on_added(event)

    def on_created(self, event):
        self.process_on_added(event)

    def output_to_console(self, msg):
        if self.verbose:
            print(msg)

    def start_observer(self):
        observer = Observer()
        observer.schedule(self, path=self.destination_folder)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def process_on_added(self, event):
        """Moves file from source_dir to the destination_dir as
        determined by :func:`folder_handler.select`."""
        filename = event.src_path.split("/")[-1]
        if len(re.findall(r'\_', filename)) == 1:
            self.file_manager.new_uploaded_file(event.src_path)
            self.file_manager.uploader.process_queued_files()
            self.output_to_console('{} {} {}'.format(timezone.now(), event.event_type, event.src_path))

    def statinfo(self, path, filename):
        statinfo = os.stat(join(self.destination_folder, filename))
        return {
            'path': path,
            'filename': filename,
            'size': statinfo.st_size,
        }
