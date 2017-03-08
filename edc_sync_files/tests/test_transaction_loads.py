import os

from django.test.testcases import TestCase
from django.test.utils import tag
from django.conf import settings
from faker import Faker
from edc_example.models import TestModel
from edc_sync_files.classes import TransactionLoads, TransactionDumps
from edc_sync.models import OutgoingTransaction, IncomingTransaction

from ..classes.batch_identifier import batch_identifier
from ..models import UploadTransactionFile


@tag('TestUploadTransactions')
class TestTransactionLoads(TestCase):

    def setUp(self):
        self.fake = Faker()

    @tag('test_upload_transaction_file_valid_first_timeupload')
    def test_upload_transaction_file_valid_first_timeupload(self):

        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        is_exported, _ = tx_dumps.dump_to_json()
        self.assertTrue(is_exported)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertTrue(new_file_to_upload.valid)

    @tag('test_upload_transaction_file_valid2')
    def test_upload_transaction_file_valid_next_file_same(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        is_exported, _ = tx_dumps.dump_to_json()
        self.assertTrue(is_exported)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertTrue(new_file_to_upload.valid)

        transaction_load = TransactionLoads(transaction_file_path)
        self.assertTrue(transaction_load.upload_file())

        transaction_load = TransactionLoads(transaction_file_path)
        self.assertFalse(transaction_load.upload_file())

    @tag('test_file_upload')
    def test_file_upload(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        is_exported, _ = tx_dumps.dump_to_json()
        self.assertTrue(is_exported)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertFalse(new_file_to_upload.upload_file())

    @tag('test_file_upload_upload')
    def test_file_upload_and_play(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        is_exported, _ = tx_dumps.dump_to_json()
        self.assertTrue(is_exported)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertTrue(new_file_to_upload.upload_file())

        for tx_record in new_file_to_upload.loaded_transactions:
            tx_record.delete()
        self.assertTrue(new_file_to_upload.apply_transactions())
