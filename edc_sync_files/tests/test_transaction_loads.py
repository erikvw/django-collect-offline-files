import os

from faker import Faker

from django.test.testcases import TestCase
from django.test.utils import tag
from django.conf import settings

from edc_example.models import TestModel
from edc_sync_files.classes import TransactionLoads, TransactionDumps


@tag('TestTransactionLoads')
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
        self.assertTrue(tx_dumps.is_exported_to_json)

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
        self.assertTrue(tx_dumps.is_exported_to_json)

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
        self.assertTrue(tx_dumps.is_exported_to_json)

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
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        
        for tx_record in new_file_to_upload.transaction_objs:
            tx_record.delete()
        self.assertTrue(new_file_to_upload.upload_file())
