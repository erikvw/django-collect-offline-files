import os
import shutil
from os.path import join

from django.apps import apps as django_apps
from django.core import serializers
from django.core.files import File

from edc_sync.models import IncomingTransaction
from edc_sync_files.classes import ConsumeTransactions
from edc_sync_files.classes.transaction_messages import transaction_messages

from ..models import UploadTransactionFile
from django.core.exceptions import MultipleObjectsReturned


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
        self.not_consumed = 0
        self.ignored = 0
        self.is_uploaded = False
        self.is_usb = False
        self.upload_transaction_file = None
        self.transaction_obj = None
        self.transaction_objs = []
        self.file_transactions_pks = []

        with open(self.path) as f:
            for index, deserialized_object in enumerate(
                    self.deserialize_json_file(File(f))):
                self.file_transactions_pks.append(
                    deserialized_object.object.tx_pk)
                if index == 0:
                    self.transaction_obj = deserialized_object.object
                self.transaction_objs.append(deserialized_object.object)

    def create_incoming_transactions(self):
        """ Converts outgoing transaction into incoming transactions.
        """
        has_created = False
        for outgoing in self.transaction_objs:
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
            self.consumed = True
        self.total = self.consumed + self.not_consumed
        return has_created

    def deserialize_json_file(self, file_pointer):
        json_txt = file_pointer.read()
        decoded = serializers.deserialize(
            "json", json_txt, ensure_ascii=True, use_natural_foreign_keys=True,
            use_natural_primary_keys=False)
        return decoded

    @property
    def already_uploaded(self):
        """Check whether the file is already uploaded before uploading it.
        """
        already_uploaded = False
        try:
            UploadTransactionFile.objects.get(
                file_name=self.filename)
            already_uploaded = True
            print("File already upload. Cannot be uploaded. {}".format(
                self.filename))
        except UploadTransactionFile.DoesNotExist:
            already_uploaded = False
        return already_uploaded

    @property
    def valid(self):
        """ Check order of transaction file batch seq.
        """
        if self.transaction_obj:
            try:
                UploadTransactionFile.objects.get(
                    batch_id=self.transaction_obj.batch_seq)
                self.previous_file_available = True
            except UploadTransactionFile.DoesNotExist:
                self.previous_file_available = False
            except MultipleObjectsReturned:
                self.previous_file_available = True
            first_time = (
                self.transaction_obj.batch_seq == self.transaction_obj.batch_id)
            if first_time:
                self.previous_played_all = True
            self._valid = True if (
                self.previous_file_available and not self.already_uploaded) or (
                    first_time and not self.already_uploaded) else False
            print("File  {} is validated {}.".format(self.filename, self._valid))
        else:
            self._valid = False
        return self._valid

    def archive_file(self):
        if self.is_uploaded:
            edc_sync_file_app = django_apps.get_app_config('edc_sync_files')
            try:
                if self.is_usb:
                    source_filename = join(
                        edc_sync_file_app.usb_incoming_folder, self.filename)
                else:
                    source_filename = join(
                        edc_sync_file_app.destination_folder, self.filename)

                if os.path.exists(source_filename):
                    shutil.move(source_filename, edc_sync_file_app.archive_folder)  # archive the file
                    print("File {} archived successfully into {}.".format(
                        self.filename, edc_sync_file_app.archive_folder))
                    self.is_uploaded = False
                    self.archived = True
                else:
                    print("File {} does exists to be archived.".format(self.filename))
            except FileNotFoundError as e:
                transaction_messages.add_message(
                    'error', 'Make sure archive dir exists in media/transactions/archive Got {}'.format(str(e)))
            except Exception as e:
                print(str(e))

    def upload_file(self):
        """ Create a upload transaction file in the server.
        """
        if os.path.exists(self.path):
            with open(self.path) as transaction_file:
                file = File(transaction_file)
                file_name = file.name.replace('\\', '/').split('/')[-1]
                if self.valid:
                    self.create_incoming_transactions()
                    UploadTransactionFile.objects.create(
                        transaction_file=file,
                        batch_id=self.transaction_obj.batch_id,
                        file_name=file_name,
                        producer=self.transaction_obj.producer
                    )
                    self.is_uploaded = True
                    ConsumeTransactions(
                        self.transaction_objs, self.transaction_obj)
                    self.archive_file()
                else:
                    self.is_uploaded = False
        else:
            if self.archived and self.already_uploaded:
                print("File {} already uploaded and archived in {}".format(self.filename, self.path))
            else:
                print("File {} does not exists in {}".format(self.filename, self.path))
        return self.is_uploaded
