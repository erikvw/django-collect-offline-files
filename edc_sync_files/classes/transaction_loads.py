import shutil
from os.path import join

from django.apps import apps as django_apps
from django.core import serializers
from django.core.files import File

from edc_sync.models import IncomingTransaction
from edc_sync.consumer import Consumer
from edc_sync_files.classes.transaction_messages import transaction_messages

from ..models import UploadTransactionFile


class TransactionLoads:
    """Uploads transaction file in the server, creates incoming transaction and
       play incoming transaction and archive transaction file.
    """

    def __init__(self, path):
        self.filename = str(path).split('/')[-1]
        self.path = path
        self.archived = False
        self._valid = False
        self.previous_file_available = False
        self.consumed = 0
        self.is_consumed = False
        self.not_consumed = 0
        self.total = 0
        self.is_uploaded = False

    def update_incoming_transactions(self):
        """ Converts outgoing transaction into incoming transactions.
        """
        has_created = False
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
        if self.consumed > 0:
            has_created = True
        self.total = self.consumed + self.not_consumed
        return has_created

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
        """Deserializes transactions file objects.
        """
        try:
            transaction_objs = []
            for _, deserialized_object in enumerate(
                    self.deserialize_json_file(File(open(self.path)))):
                transaction_objs.append(deserialized_object.object)
        except Exception as e:
            transaction_messages.add_message('error', str(e))
        return transaction_objs

    def apply_transactions(self):
        """ Apply incoming transactions for the currently uploaded file.
        """
        file_transactions = [
            str(file_transaction.tx_pk) for file_transaction in self.loaded_transactions]
        consume = Consumer(transactions=file_transactions, check_hostname=False).consume()
        return consume

    @property
    def transaction_obj(self):
        """Get the first transaction in the loaded json file.
        """
        transaction = None
        try:
            transaction = self.loaded_transactions[0]
        except IndexError as e:
            transaction_messages.add_message(
                'error', 'No records in {} file Got {}'.format(self.filename, str(e)))
        return transaction

    @property
    def already_uploaded(self):
        """Check whether the file is already uploaded before uploading it.
        """
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
        """ Check order of transaction file batch seq.
        """
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

    def archive_file(self):
        if self.is_uploaded:
            edc_sync_file_app = django_apps.get_app_config('edc_sync_files')
            try:
                destination_filename = join(
                    edc_sync_file_app.archive_folder, self.filename)
                source_filename = join(
                    self.edc_sync_file_app.destination_folder, self.filename)
                shutil.move(source_filename, destination_filename)  # archive the file
            except FileNotFoundError as e:
                transaction_messages.add_message(
                    'error', 'Make sure archive dir exists in media/transactions/archive Got {}'.format(str(e)))

    def upload_file(self):
        """ Create a upload transaction file in the server.
        """
        file = File(open(self.path))
        file_name = file.name.replace('\\', '/').split('/')[-1]
#         date_string = self.filename.split('_')[2]  # .split('.')[0][:8]
#         print(file_name, date_string)
        if self.valid:
            self.update_incoming_transactions()
            UploadTransactionFile.objects.create(
                transaction_file=file,
                consume=True,
                tx_pk=self.transaction_obj.batch_id,
                file_name=file_name,
                consumed=self.consumed,
                total=self.total,
                not_consumed=self.not_consumed
            )
            self.is_uploaded = True
        self.archive_file()
        return self.is_uploaded
