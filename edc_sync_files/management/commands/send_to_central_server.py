import sys

from django.core.management.base import BaseCommand

from ...file_transfer import SendTransactionFile
from ...transaction import TransactionExporter


class Command(BaseCommand):
    """Send transaction files to the central server.
       1. Dump transaction file
       2. Send it to the central server.
    """
    help = ''

    def handle(self, *args, **options):
        sys.stdout.write('Exporting transactions\n')
        tx_exporter = TransactionExporter()
        if tx_exporter.exported:
            sys.stdout.write(
                f'{tx_exporter.filename} exported '
                f'with {tx_exporter.exported} transactions\n')
        else:
            sys.stdout.write('Failed to export transaction file.\n')
        if tx_exporter.exported:
            sys.stdout.write('Sending transaction files\n')
            SendTransactionFile().send_files()
