import os
import re
import sys

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from ...transaction import TransactionLoads


class Command(BaseCommand):
    """Upload pending transactions files.
    """
    help = ''

    def handle(self, *args, **options):
        edc_sync_files_app = django_apps.get_app_config('edc_sync_files')
        pending_files = os.listdir(edc_sync_files_app.destination_folder) or []
        pending_files.sort()
        try:
            for filename in pending_files:
                if filename.endswith('.json'):
                    if len(re.findall(r'\_', filename)) == 1:
                        try:
                            sys.stdout.write(
                                'Uploading: {}\n'.format(filename))
                            file_path = os.path.join(
                                edc_sync_files_app.destination_folder, filename)
                            TransactionLoads(path=file_path).upload_file()
                        except FileNotFoundError:
                            sys.stdout.write(
                                'Failed to upload: {}\n'.format(filename))
        except AttributeError:
            sys.stdout.write('No pending transaction files')
        sys.stdout.write('\npress CTRL-C to stop.\n\n')
