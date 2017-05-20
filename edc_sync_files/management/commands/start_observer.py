import logging
import sys
import time

from datetime import datetime
from watchdog.observers import Observer

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from ...event_handlers import DeserializeTransactionsFileHandler
from ...event_handlers import IncomingTransactionsFileHandler
from ...models import ImportedTransactionFileHistory
from ...queues import tx_batch_queue, incoming_tx_queue


app_config = django_apps.get_app_config('edc_sync_files')
logger = logging.getLogger('edc_sync_files')
regexes = [r'^\w+\.json$']


class Command(BaseCommand):

    help = 'Start watchdog observer'

    def handle(self, *args, **options):
        tx_file_handler = IncomingTransactionsFileHandler(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder,
            regexes=regexes)
        tx_batch_handler = DeserializeTransactionsFileHandler(
            src_path=app_config.pending_folder,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory)
        incoming_tx_queue.open(
            src_path=tx_file_handler.src_path,
            dst_path=tx_file_handler.dst_path,
            regexes=regexes)
        tx_batch_queue.open(
            src_path=tx_batch_handler.src_path,
            dst_path=tx_batch_handler.dst_path,
            history_model=ImportedTransactionFileHistory)
        incoming_tx_queue.reload()
        tx_batch_queue.reload()
        observer = Observer()
        observer.schedule(tx_file_handler, tx_file_handler.src_path)
        observer.schedule(tx_batch_handler, tx_batch_handler.src_path)
        observer.start()
        dt = datetime.now().strftime('%Y-%m-%d %H:%M')
        sys.stdout.write(f'\nStarted {dt}\n')
        while not incoming_tx_queue.empty():
            sys.stdout.write(f' * file queue {incoming_tx_queue.qsize()}\r')
            incoming_tx_queue.next_task()
        sys.stdout.write(f' * file queue {incoming_tx_queue.qsize()}   \n')
        sys.stdout.write(f' * batch queue {incoming_tx_queue.qsize()}   \n')
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
        logger.info('Started')
#         mkstemp(suffix='.json', prefix='test_',
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
