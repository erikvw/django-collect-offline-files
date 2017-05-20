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
# from ...patterns import transaction_filename_regexes


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
        sys.stdout.write(f'\nStarted {dt}\n')
        while not incoming_tx_handler.queue.empty():
            sys.stdout.write(
                f' * file queue {incoming_tx_handler.queue.qsize()}   \r')
            incoming_tx_handler.queue.next_task()
        sys.stdout.write(
            f' * file queue {incoming_tx_handler.queue.qsize()}   \n')
        sys.stdout.write(
            f' * batch queue {incoming_tx_handler.queue.qsize()}   \n')
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
        logger.info('Started')
        tempfile.mkstemp(suffix='.json', prefix='test_',
                         dir=app_config.incoming_folder)
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
