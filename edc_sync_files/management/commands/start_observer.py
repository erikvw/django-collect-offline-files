import logging
import sys
import tempfile
import time

from datetime import datetime
from watchdog.observers import Observer

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from ...event_handlers import DeserializeTransactionsFileHandler
from ...event_handlers import IncomingTransactionsFileHandler
from ...models import ImportedTransactionFileHistory


app_config = django_apps.get_app_config('edc_sync_files')
logger = logging.getLogger('edc_sync_files')
regexes = [r'^\w+\.json$']


class Command(BaseCommand):

    help = 'Start watchdog observer'

    def handle(self, *args, **options):
        incoming_tx_handler = IncomingTransactionsFileHandler(
            regexes=regexes,
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)
        deserialize_tx_handler = DeserializeTransactionsFileHandler(
            regexes=regexes,
            src_path=app_config.pending_folder,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory)
        incoming_tx_handler.queue.reload()
        deserialize_tx_handler.queue.reload()
        observer = Observer()
        observer.schedule(incoming_tx_handler, app_config.incoming_folder)
        observer.schedule(deserialize_tx_handler, app_config.pending_folder)
        observer.start()
        dt = datetime.now().strftime('%Y-%m-%d %H:%M')
        sys.stdout.write(f'\nObserver started {dt}\n')
        sys.stdout.write(f'\nclearing queues ...\n')
        self.clear_queue(incoming_tx_handler)
        self.clear_queue(deserialize_tx_handler)
        sys.stdout.write(f'done clearing queues.\n')
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
        logger.info('Observer started')
        # tempfile.mkstemp(suffix='.json', prefix='test_',
        #                 dir=app_config.incoming_folder)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info('CTRL-C pressed')
            observer.stop()
        observer.join()
        logger.info('Stopped')
        dt = datetime.now().strftime('%Y-%m-%d %H:%M')
        sys.stdout.write(f'\nStopped {dt}\n')

    def clear_queue(self, queue):
        while not queue.queue.empty():
            sys.stdout.write(
                f' * {queue.__class__.__name__} queue {queue.queue.qsize()}   \r')
            queue.queue.next_task()
        sys.stdout.write(
            f' * {queue.__class__.__name__} queue {queue.queue.qsize()}   \n')
