import os

from django.core import serializers
from django.core.files import File

from edc_sync.models import IncomingTransaction
from edc_sync.consumer import Consumer

from ..models import UploadTransactionFile


class TransactionLoads:

    def __init__(self, path):
        self.filename = str(path).split('/')[-1]
        self.path = path
        self.archived = False
        self._valid = False
        self.is_uploaded = False
        self.previous_file_available = False
        self.consumed = 0
        self.not_consumed = 0
        self.total = 0

    def load_incoming_transactions(self):
        """ Converts outgoing transaction into incoming transactions """
        for outgoing in self.loaded_transactions:
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

    def deserialize_json_file(self, file_pointer):
        try:
            json_txt = file_pointer.read()
            decoded = serializers.deserialize(
                "json", json_txt, ensure_ascii=True,
                use_natural_foreign_keys=True,
                use_natural_primary_keys=False)
        except:
            return None
        return decoded

    @property
    def loaded_transactions(self):
        transaction_objs = []
        for _, deserialized_object in enumerate(
                self.deserialize_json_file(File(open(self.path)))):
            transaction_objs.append(deserialized_object.object)
        return transaction_objs

    def apply_transactions(self):
        """ Apply incoming transactions for the currently uploaded file """
        file_transactions = [
            str(file_transaction.tx_pk) for file_transaction in self.loaded_transactions]
        consume = Consumer(transactions=file_transactions, check_hostname=False).consume()
        return consume

    @property
    def transaction_obj(self):
        transaction = None
        try:
            transaction = self.loaded_transactions[0]
        except IndexError:
            pass
        return transaction

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
        first_time = (
            self.transaction_obj.batch_seq == self.transaction_obj.batch_id)
        self._valid = True if (
            self.previous_file_available and not self.already_uploaded) or (
                first_time and not self.already_uploaded) else False
        return self._valid

    def upload_file(self):
        """ Create a upload transaction file in the server. """
        is_uploaded = False
        file = File(open(self.path))
        file_name = file.name.replace('\\', '/').split('/')[-1]
#         date_string = self.filename.split('_')[2]  # .split('.')[0][:8]
#         print(file_name, date_string)
        if self.valid:
            self.load_incoming_transactions()
            UploadTransactionFile.objects.create(
                transaction_file=file,
                consume=True,
                tx_pk=self.transaction_obj.batch_id,
                file_name=file_name,
                consumed=self.consumed,
                total=self.total,
                not_consumed=self.not_consumed
            )
            is_uploaded = True
        return is_uploaded
