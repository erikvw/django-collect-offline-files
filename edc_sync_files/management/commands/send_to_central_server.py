import sys

from django.core.management.base import BaseCommand
from django.apps import apps as django_apps

from edc_sync_files.classes import TransactionFileManager, TransactionDumps


class Command(BaseCommand):
    """Send transaction files to the central server.
       1. Dump transaction file
       2. Send it to the central server.
    """
    help = ''

    def handle(self, *args, **options):
        try:
            source_folder = django_apps.get_app_config('edc_sync_files').source_folder
            dump = TransactionDumps(source_folder)
            is_dumped, export = dump.dump_to_json()
            if is_dumped:
                sys.stdout.write(
                    'Transaction files: {} dumped with {}'.format(dump.filename, export))
            else:
                sys.stdout.write(
                    'Failed to dump transaction file')
            TransactionFileManager().send_files()
        except AttributeError:
            sys.stdout.write('No pending transaction files')
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
