import sys

from django.core.management.base import BaseCommand

from ...event_handlers import TransactionFileEventHandler
from ...observer import Observer


class Command(BaseCommand):
    help = 'Start watchdog observer'

    def handle(self, *args, **options):

        observer = Observer()
        observer.start(event_handler_class=TransactionFileEventHandler)

        sys.stdout.write('Upload folder: {}\n'.format(
            observer.event_handler.destination_folder))
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
