import os

from django.apps import apps as django_apps
from django.core import serializers
from django.db import transaction
from django.utils import timezone

from edc_base.utils import get_utcnow
from edc_sync.models import OutgoingTransaction

from ..models import History


class TransactionExporterError(Exception):
    pass


class TransactionExporter:

    """Export pending OutgoingTransactions to a file in JSON format
    and update the export `History` model.
    """

    def __init__(self, path=None, device_id=None, using=None):
        app_config = django_apps.get_app_config('edc_sync_files')
        edc_device_app_config = django_apps.get_app_config('edc_device')
        self.filename = None
        self.message = None
        self.exported = 0
        self.batch_id = None
        self.path = path or app_config.outgoing_folder
        device_id = device_id or edc_device_app_config.device_id
        self.using = using or 'default'
        self.outgoing_transactions = OutgoingTransaction.objects.using(
            self.using).filter(is_consumed_server=False)
        if self.outgoing_transactions.exists():
            self.filename = '{}_{}.json'.format(
                device_id, str(timezone.now().strftime("%Y%m%d%H%M%S%f")[:-3]))
            self.batch_id = str(self.outgoing_transactions.first().tx_pk)
            self.prev_batch_id = self.get_prev_batch_id()
            History.objects.using(self.using).create(
                filename=self.filename, batch_id=self.batch_id)
            self.exported = self.export_file()
        if self.exported:
            self.message = f'Success. Exported transactions to {self.filename}.'
        else:
            self.message = 'Nothing to export.'

    def export_file(self):
        """Exports all pending outgoing transactions to a json file.
        """
        exported = 0
        path = os.path.join(self.path, self.filename)
        try:
            with open(path, 'w') as f:
                json_txt = serializers.serialize(
                    'json', self.outgoing_transactions,
                    ensure_ascii=True, use_natural_foreign_keys=True,
                    use_natural_primary_keys=False)
                f.write(json_txt)
        except IOError as e:
            raise TransactionExporterError(
                f'Unable to create export file \'{path}\'. Got \'{str(e)}\'')
        else:
            with transaction.atomic():
                exported = self.outgoing_transactions.update(
                    is_consumed_server=True,
                    consumer=os.path.dirname(path),
                    consumed_datetime=get_utcnow(),
                    prev_batch_id=self.prev_batch_id,
                    batch_id=self.batch_id)
        return exported

    def get_prev_batch_id(self):
        """Returns the batch id of the last consumed tx.

        If no previously consumed txs, returns the current batch_id.
        """
        obj = OutgoingTransaction.objects.using(self.using).filter(
            is_consumed_server=True).last()
        if obj:
            prev_batch_id = obj.batch_id
        else:
            prev_batch_id = self.batch_id
        return prev_batch_id
