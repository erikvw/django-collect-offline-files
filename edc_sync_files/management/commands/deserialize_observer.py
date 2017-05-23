import logging

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand
from edc_device.constants import NODE_SERVER, CENTRAL_SERVER

from ...observers import DeserializeTransactionsFileQueueObserver


app_config = django_apps.get_app_config('edc_sync_files')
logger = logging.getLogger('edc_sync_files')


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

    def handle(self, *args, **options):
        file_observer = self.file_observer_cls(**options)
        file_observer.start()
