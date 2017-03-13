import sys

from django.core.management.base import BaseCommand

from edc_sync_files.classes import TransactionFileEventHandler


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):

        event_handler = TransactionFileEventHandler()
        event_handler.start_observer()

        sys.stdout.write('Upload folder: {}\n'.format(event_handler.destination_folder))
        sys.stdout.write('Archive folder: {}\n'.format(event_handler.archive_folder))
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
