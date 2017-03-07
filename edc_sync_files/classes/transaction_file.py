import os

from django.conf import settings
from django.core import serializers
from django.core.files import File
from django.db import transaction

from edc_base.utils import get_utcnow

from ..models import UploadTransactionFile
from .transaction_messages import transaction_messages


class TransactionFile:

    def __init__(self, path, hostname=None):
        self.filename = str(path).split('/')[-1]
        self.path = path
        self.archived = False
        self._valid = False
        self.already_uploaded = False
        self.is_uploaded = False
        self.previous_file_available = False
        self.hostname = hostname

    def deserialize_json_file(self, file_pointer):
        try:
            json_txt = file_pointer.read()
            decoded = serializers.deserialize(
                "json", json_txt, ensure_ascii=True, use_natural_foreign_keys=True,
                use_natural_primary_keys=False)
        except:
            return None
        return decoded

    @property
    def file_transactions(self):
        transaction_objs = []
        for _, deserialized_object in enumerate(self.deserialize_json_file(self.file)):
            transaction_objs.append(deserialized_object.object)
        return transaction_objs

    @property
    def transaction_obj(self):
        transaction = None
        try:
            transaction = self.file_transactions[0]
        except IndexError:
            pass
        return transaction

    @property
    def file(self):
        return File(open(self.path))

    @property
    def first_time_upload(self):
        return (
            self.transaction_obj.previous_tx_pk == self.transaction_obj.current_tx_pk)

    @property
    def valid(self):
        try:
            UploadTransactionFile.objects.get(
                file_name=self.filename)
            self.already_uploaded = True
        except UploadTransactionFile.DoesNotExist:
            try:
                self.already_uploaded = False
                UploadTransactionFile.objects.get(
                    tx_pk=self.transaction_obj.previous_tx_pk)
                self.previous_file_available = True
            except UploadTransactionFile.DoesNotExist:
                self.previous_file_available = False
        self._valid = True if (
            self.previous_file_available and not self.already_uploaded) or self.first_time_upload else False
        return self._valid

    def upload(self):
        is_uploaded = False
        file_name = self.file.name.replace('\\', '/').split('/')[-1]
#         date_string = self.filename.split('_')[2]  # .split('.')[0][:8]
#         print(file_name, date_string)
        if self.valid:
            UploadTransactionFile.objects.create(
                transaction_file=self.file,
                consume=True,
                tx_pk=self.transaction_obj.current_tx_pk,
                file_name=file_name
            )
            is_uploaded = True
        return is_uploaded

    def export_to_json(
            self, transactions=None, hostname=None, previous_tx_pk=None, current_tx_pk=None, using=None):
        filename = '{}_{}.json'.format(self.hostname, str(get_utcnow().strftime("%Y%m%d%H%M")))
        self.path = os.path.join(self.path, filename) or os.path.join('/tmp', filename)
        export_to_json = False
        exported = 0
        if transactions:
            transactions.update(
                current_tx_pk=current_tx_pk, previous_tx_pk=previous_tx_pk)
            try:
                with open(self.path, 'w') as f:
                    json_txt = serializers.serialize(
                        "json", transactions,
                        ensure_ascii=True, use_natural_foreign_keys=True,
                        use_natural_primary_keys=False)
                    f.write(json_txt)
                    exported = transactions.count()
                    with transaction.atomic():
                        transactions.update(
                            is_consumed_server=True,
                            consumer='/'.join(self.path.split('/')[:-1]),
                            consumed_datetime=get_utcnow())
                export_to_json = True
            except IOError as io_error:
                message = (
                    'Unable to create or write to file \'{}\'. '
                    'Got {}').format(self.path, str(io_error))
                transaction_messages.add_message(
                    'error', message, network=False, permission=False)
                export_to_json = False
            transaction_messages.add_message(
                'success', 'dumped transaction file successfully',
                network=False, permission=False)
        return (exported, export_to_json, filename)
