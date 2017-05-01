import os
import shutil

from django.apps import apps as django_apps
from django.core import serializers

from edc_sync.models import IncomingTransaction

from ..models import ImportedTransactionFileHistory


class TransactionImporterPathError(Exception):
    pass


class TransactionImporterDuplicateError(Exception):
    pass


class TransactionImporterSequenceError(Exception):
    pass


class TransactionImporter:
    """Imports transactions from a file as incoming transaction and
       archives the file.
    """

    def __init__(self, filename=None, path=None):
        self.message = None
        self.tx_pks = []
        app_config = django_apps.get_app_config('edc_sync_files')
        self.filename = filename
        self.imported = 0
        self.path = path or app_config.outgoing_folder
        try:
            ImportedTransactionFileHistory.objects.get(filename=self.filename)
        except ImportedTransactionFileHistory.DoesNotExist:
            self.imported, self.tx_pks = self.import_file()
        else:
            raise TransactionImporterDuplicateError(
                f'File {self.filename} has already been imported.')
        shutil.move(
            os.path.join(self.path, self.filename),
            app_config.archive_folder)

    def import_file(self):
        """Imports a file of transactions into model IncomingTransaction.
        """
        imported = 0
        with open(os.path.join(self.path, self.filename)) as f:
            json_txt = f.read()
        outgoing_transactions = self.get_outgoing_transactions(json_txt)
        tx_pks = [obj.tx_pk for obj in outgoing_transactions]
        self.verify_sequence(outgoing_transactions=outgoing_transactions)
        for outgoing_transaction in outgoing_transactions:
            try:
                IncomingTransaction.objects.get(pk=outgoing_transaction.pk)
            except IncomingTransaction.DoesNotExist:
                data = outgoing_transaction.__dict__
                data.pop('using')
                data.pop('is_consumed_middleman')
                data.pop('is_consumed_server')
                data.pop('_state')
                IncomingTransaction.objects.create(**data)
                imported += 1
        history = ImportedTransactionFileHistory(
            filename=self.filename,
            batch_id=outgoing_transactions[0].batch_id,
            producer=outgoing_transactions[0].producer,
            total=len(outgoing_transactions))
        history.transaction_file.name = self.filename
        history.save()
        return imported, tx_pks

    def get_outgoing_transactions(self, json_txt=None):
        """Returns a list of deserialized outgoing transactions.
        """
        outgoing_transactions = []
        deserialized_object = serializers.deserialize(
            "json", json_txt, ensure_ascii=True, use_natural_foreign_keys=True,
            use_natural_primary_keys=False)
        for _, obj in enumerate(deserialized_object):
            outgoing_transactions.append(obj.object)
        return outgoing_transactions

    def verify_sequence(self, outgoing_transactions=None):
        """ Check import sequence of transaction file using prev_batch_id.
        """
        if outgoing_transactions[0].prev_batch_id == outgoing_transactions[0].batch_id:
            return True
        elif ImportedTransactionFileHistory.objects.filter(
                batch_id=outgoing_transactions[0].prev_batch_id).exists():
            return True
        else:
            raise TransactionImporterSequenceError(
                f'Invalid sequence for {self.filename}')
