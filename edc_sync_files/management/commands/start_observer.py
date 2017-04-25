import sys

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from ...event_handlers import TransactionFileEventHandler
from ...observer import Observer


class Command(BaseCommand):
    help = 'Start watchdog observer'

    def handle(self, *args, **options):
        destination_folder = django_apps.get_app_config(
            'edc_sync_files').destination_folder
        observer = Observer()
        observer.start(
            event_handler_class=TransactionFileEventHandler,
            path=destination_folder)

        sys.stdout.write('Upload folder: {}\n'.format(
            destination_folder))
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
