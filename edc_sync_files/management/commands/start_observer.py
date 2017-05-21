import logging
import sys
import time

from datetime import datetime
from django.apps import apps as django_apps
from django.core.management.base import BaseCommand
from watchdog.observers import Observer

from ...file_queues import Worker, FileQueueHandler
from ...file_queues import IncomingTransactionsFileQueue, DeserializeTransactionsFileQueue
from ...models import ImportedTransactionFileHistory


app_config = django_apps.get_app_config('edc_sync_files')
logger = logging.getLogger('edc_sync_files')


class Command(BaseCommand):

    help = 'Start TransactionFileObserver'

    def add_arguments(self, parser):
        parser.add_argument(
            '--allow_any_role',
            action='store_true',
            dest='allow_any_role',
            default=False,
            help='Allow a device of any role to deserialize transactions',
        )

    def handle(self, *args, **options):

        allow_any_role = options['allow_any_role']

        regexes = [r'\w+\.json$']

        # queues
        incoming_tx_queue = IncomingTransactionsFileQueue(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)
        incoming_tx_queue.reload(regexes=regexes)

        deserialize_tx_queue = DeserializeTransactionsFileQueue(
            src_path=app_config.pending_folder,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory,
            allow_any_role=allow_any_role)
        deserialize_tx_queue.reload(regexes=regexes)

        # workers
        incoming_tx_worker = Worker(queue=incoming_tx_queue)
        incoming_tx_worker.start()
        sys.stdout.write(f'\nStarted worker for {incoming_tx_worker}\n')

        deserialize_tx_worker = Worker(queue=deserialize_tx_queue)
        deserialize_tx_worker.start()
        sys.stdout.write(f'Started worker for {deserialize_tx_worker}\n')

        # file queue handlers
        incoming_tx_handler = FileQueueHandler(
            regexes=regexes, queue=incoming_tx_queue)

        deserialize_tx_handler = FileQueueHandler(
            regexes=regexes, queue=deserialize_tx_queue)

        # watchdog observer
        observer = Observer()
        sys.stdout.write(f'\n{observer}\n')

        watch = observer.schedule(incoming_tx_handler,
                                  incoming_tx_queue.src_path)
        sys.stdout.write(f'{watch.__class__.__name__} {watch.path}\n')
        watch = observer.schedule(deserialize_tx_handler,
                                  deserialize_tx_queue.src_path)
        sys.stdout.write(f'{watch.__class__.__name__} {watch.path}\n')
        observer.start()

        dt = datetime.now().strftime('%Y-%m-%d %H:%M')
        sys.stdout.write(f'\nStarted {dt}\n')
        sys.stdout.write('\nReady. Press CTRL-C to stop.\n\n')
        logger.info(f'{observer} started')

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info('CTRL-C pressed')
            observer.stop()
        observer.join()
        incoming_tx_worker.stop()
        deserialize_tx_worker.stop()
        logger.info(f'{observer} stopped')
        dt = datetime.now().strftime('%Y-%m-%d %H:%M')
        sys.stdout.write(f'\n{observer} stopped {dt}\n')
