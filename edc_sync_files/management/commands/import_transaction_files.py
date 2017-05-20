import os
import re
import sys

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from ...patterns import transaction_filename_pattern
from ...transaction import TransactionImporter


class Command(BaseCommand):
    """Import pending transactions files.
    """
    help = 'Import transaction files'

    def handle(self, *args, **options):
        app_config = django_apps.get_app_config('edc_sync_files')
        incoming_folder = app_config.incoming_folder
        pending_files = os.listdir(incoming_folder) or []
        if pending_files:
            pending_files.sort()
            for filename in pending_files:
                if re.match(transaction_filename_pattern, filename):
                    sys.stdout.write('Importing: {}\r'.format(filename))
                    tx_importer = TransactionImporter(
                        import_path=app_config.incoming_folder)
                    tx_importer.import_batch(filename=filename)
                    sys.stdout.write('Importing: {}. Done.\n'.format(filename))
        else:
            sys.stdout.write('No transaction files to import')
