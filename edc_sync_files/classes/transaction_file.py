import os

from django.conf import settings
from django.core import serializers
from django.core.files import File
from django.db import transaction

from edc_base.utils import get_utcnow
from edc_sync.models import IncomingTransaction
from edc_sync.consumer import Consumer

from ..models import UploadTransactionFile
from .transaction_messages import transaction_messages


class TransactionFile:

    def __init__(self, path, hostname=None):
        self.filename = str(path).split('/')[-1]
        self.path = path
        self.archived = False
        self._valid = False
        self.is_uploaded = False
        self.previous_file_available = False
        self.hostname = hostname
        self.consumed = 0
        self.not_consumed = 0
        self.total = 0

    def deserialize_json_file(self, file_pointer):
        try:
            json_txt = file_pointer.read()
            decoded = serializers.deserialize(
                "json", json_txt, ensure_ascii=True, use_natural_foreign_keys=True,
                use_natural_primary_keys=False)
        except:
            return None
        return decoded

    def load_to_server(self):
        """ Converts outgoing transaction into incoming transactions """
        for outgoing in self.file_transactions:
            if not IncomingTransaction.objects.filter(pk=outgoing.pk).exists():
                if outgoing._meta.get_fields():
                    self.consumed += 1
                    data = outgoing.__dict__
                    del data['using']
                    del data['is_consumed_middleman']
                    del data['is_consumed_server']
                    del data['_state']
                    IncomingTransaction.objects.create(**data)
            else:
                self.not_consumed += 1
        self.total = self.consumed + self.not_consumed

    def apply_transactions(self):
        """ Apply incoming transactions for the currently uploaded file """
        file_transactions = [
            file_transaction.tx_pk for file_transaction in self.file_transactions]
        Consumer(transactions=file_transactions).consume()

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
            self.transaction_obj.batch_seq == self.transaction_obj.batch_id)

    @property
    def already_uploaded(self):
        already_uploaded = False
        try:
            UploadTransactionFile.objects.get(
                file_name=self.filename)
            already_uploaded = True
        except UploadTransactionFile.DoesNotExist:
            already_uploaded = False
        return already_uploaded

    @property
    def valid(self):
        """ check order of transaction file batch seq. """
        try:
            UploadTransactionFile.objects.get(
                tx_pk=self.transaction_obj.batch_seq)
            self.previous_file_available = True
        except UploadTransactionFile.DoesNotExist:
            self.previous_file_available = False
        self._valid = True if (
            self.previous_file_available and not self.already_uploaded) or (
                self.first_time_upload and not self.already_uploaded) else False
        return self._valid

    def upload(self):
        """ Create a upload transaction file in the server. """
        is_uploaded = False
        file_name = self.file.name.replace('\\', '/').split('/')[-1]
#         date_string = self.filename.split('_')[2]  # .split('.')[0][:8]
#         print(file_name, date_string)
        if self.valid:
            # Attempt to create incoming transactions with transaction file transactions
            self.load_to_server()
            # Finally create an upload transaction file record.
            UploadTransactionFile.objects.create(
                transaction_file=self.file,
                consume=True,
                tx_pk=self.transaction_obj.batch_id,
                file_name=file_name,
                consumed=self.consumed,
                total=self.total,
                not_consumed=self.not_consumed
            )
            is_uploaded = True
        return is_uploaded

    def export_to_json(
            self, transactions=None, hostname=None, batch_seq=None, batch_id=None, using=None):
        """ export outgoing transactions to a json file """
        filename = '{}_{}.json'.format(self.hostname, str(get_utcnow().strftime("%Y%m%d%H%M")))
        self.filename = filename
        self.path = os.path.join(self.path, filename) or os.path.join('/tmp', filename)
        export_to_json = False
        exported = 0
        if transactions:
            transactions.update(
                batch_seq=batch_seq,
                batch_id=batch_id)
            try:
                with open(self.path, 'w') as f:
                    json_txt = serializers.serialize(
                        "json", transactions,
                        ensure_ascii=True, use_natural_foreign_keys=True,
                        use_natural_primary_keys=False)
                    f.write(json_txt)
                    exported = transactions.count()
                    with transaction.atomic():
                        print("Updating")
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
