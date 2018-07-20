import logging

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand
from edc_device.constants import NODE_SERVER, CENTRAL_SERVER

from django_collect_offline_files import process_queue
from django_collect_offline_files import DeserializeTransactionsFileQueueObserver


app_config = django_apps.get_app_config('django_collect_offline_files')
logger = logging.getLogger('django_collect_offline_files')


class Command(BaseCommand):

    help = 'Start the observer that deserializes incoming transactions.'
    file_observer_cls = DeserializeTransactionsFileQueueObserver

    def add_arguments(self, parser):
        parser.add_argument(
            '--override_role',
            dest='override_role',
            default=None,
            help=(f'Specify the device role to deserialize transactions '
                  f'({NODE_SERVER}, {CENTRAL_SERVER}). Not recommended. '),
        )

        parser.add_argument(
            '--src_path',
            dest='src_path',
            default=app_config.pending_folder,
            help=(f'Target path on remote host. (Default: {app_config.pending_folder}. See app_config.)'),
        )

        parser.add_argument(
            '--dst_path',
            dest='dst_path',
            default=app_config.archive_folder,
            help=(f'Archive path on localhost. (Default: {app_config.archive_folder}. See app_config.)'),
        )

    def handle(self, *args, **options):
        file_observer = self.file_observer_cls(
            task_processor=process_queue, **options)
        file_observer.start()
