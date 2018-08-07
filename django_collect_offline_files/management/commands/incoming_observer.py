import logging

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from ...file_queues import process_queue
from ...observers import IncomingTransactionsFileQueueObserver


app_config = django_apps.get_app_config('django_collect_offline_files')
logger = logging.getLogger('django_collect_offline_files')


class Command(BaseCommand):

    help = 'Start observer that imports files into the incoming transactions model.'

    file_observer_cls = IncomingTransactionsFileQueueObserver

    def add_arguments(self, parser):

        parser.add_argument(
            '--src_path',
            dest='src_path',
            default=app_config.incoming_folder,
            help=(
                f'Target path on remote host. (Default: {app_config.incoming_folder}. See app_config.)'),
        )

        parser.add_argument(
            '--dst_path',
            dest='dst_path',
            default=app_config.pending_folder,
            help=(
                f'Pending path on localhost. (Default: {app_config.archive_folder}. See app_config.)'),
        )

    def handle(self, *args, **options):
        file_observer = self.file_observer_cls(
            task_processor=process_queue, **options)
        file_observer.start()
