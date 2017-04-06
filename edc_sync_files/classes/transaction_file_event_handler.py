import re
import logging
import time
import os
from os.path import join


from django.utils import timezone
from django.apps import apps as django_apps

from watchdog.observers import Observer
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

    patterns = ["*.json"]  # TODO add regex for filename

    def __init__(self, verbose=None):
        super(TransactionFileEventHandler, self).__init__(ignore_directories=True)
        self.verbose = verbose or True
        edc_sync_file_app = django_apps.get_app_config('edc_sync_files')
        self.destination_folder = edc_sync_file_app.destination_folder
        self.archive_folder = edc_sync_file_app.archive_folder
        self.file_queue = TransactionFileQueue()

    def process(self, event):
        self.output_to_console(
            '{} {} {} Not handled.'.format(timezone.now(), event.event_type, event.src_path))

    def on_created(self, event):
        self.process_on_added(event)

    def output_to_console(self, msg):
        if self.verbose:
            print(msg)

    def start_observer(self):
        observer = Observer()
        observer.schedule(self, path=self.destination_folder)
        observer.start()
        logging.basicConfig(filename='logs/observer-error.log', level=logging.INFO)
        logger = logging.getLogger(__name__)
        try:
            records = {'time': timezone.now(), 'status': 'running'}
            logger.info('{}'.format(records))
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        except (OSError, IOError) as err:
            records = {'time': timezone.now(), 'status': '{}'.format(str(err))}
            logger.error('{}'.format(records))
            time.sleep(1)
            observer.stop()
            self.start_observer()
        observer.join()

    def process_on_added(self, event):
        """Moves file from source_dir to the destination_dir as
        determined by :func:`folder_handler.select`."""
        filename = event.src_path.split("/")[-1]
        pattern = re.compile(self.filename_pattern)
        if pattern.match(filename):
            self.file_queue.add_new_uploaded_file(event.src_path)
            self.file_queue.process_queued_files()
            self.output_to_console('{} {} {}'.format(timezone.now(),
                                                     event.event_type, event.src_path))
        else:
            print(event.src_path)

    def statinfo(self, path, filename):
        statinfo = os.stat(join(self.destination_folder, filename))
        return {
            'path': path,
            'filename': filename,
            'size': statinfo.st_size,
        }
