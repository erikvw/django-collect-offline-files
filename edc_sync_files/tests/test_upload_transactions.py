import os

from django.test.testcases import TestCase
from django.test.utils import tag
from django.conf import settings
from faker import Faker
from edc_example.models import TestModel
from edc_sync_files.classes import TransactionFile
from edc_sync.models import OutgoingTransaction, IncomingTransaction

from ..classes.batch_identifier import batch_identifier
from ..models import UploadTransactionFile


@tag('TestUploadTransactions')
class TestUploadTransactions(TestCase):

    def setUp(self):
        self.fake = Faker()

    @tag('test_export_to_json_file')
    def test_export_to_json_file(self):
        # Create transactions
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        transaction_file = TransactionFile(path, hostname='010')

        outgoing_transactions = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False)

        self.assertGreater(outgoing_transactions.count(), 0)

        batch_seq, batch_id = batch_identifier(using='client')
        self.assertTrue(batch_id)
        exported_no, is_exported, _ = transaction_file.export_to_json(
            transactions=outgoing_transactions, hostname='010',
            using='client', batch_seq=batch_seq, batch_id=batch_id)
        self.assertTrue(is_exported)
        self.assertGreater(exported_no, 0)

        outgoing_transactions_count = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False).count()
        self.assertEqual(outgoing_transactions_count, 0)

    @tag('test_upload_transaction_file_valid')
    def test_upload_transaction_file_valid_first_timeupload(self):

        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())
        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        transaction_file = TransactionFile(path, hostname='010')

        outgoing_transactions = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False)
        self.assertGreater(outgoing_transactions.count(), 0)

        batch_seq, batch_id = batch_identifier(using='client')

        exported_no, is_exported, _ = transaction_file.export_to_json(
            transactions=outgoing_transactions, hostname='010',
            using='client', batch_seq=batch_seq, batch_id=batch_id)
        self.assertTrue(is_exported)
        self.assertGreater(exported_no, 0)

        new_file_to_upload = TransactionFile(path=transaction_file.path)
        self.assertTrue(new_file_to_upload.first_time_upload)
        self.assertTrue(new_file_to_upload.valid)

    @tag('test_upload_transaction_file_valid2')
    def test_upload_transaction_file_valid_next_file_same(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())
        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        transaction_file = TransactionFile(path, hostname='010')

        outgoing_transactions = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False)
        self.assertGreater(outgoing_transactions.count(), 0)

        batch_seq, batch_id = batch_identifier(using='client')

        transaction_file.export_to_json(
            transactions=outgoing_transactions, hostname='010',
            using='client', batch_seq=batch_seq, batch_id=batch_id)

        new_file_to_upload = TransactionFile(path=transaction_file.path)
        self.assertTrue(new_file_to_upload.upload())
        incoming_transaction_count = IncomingTransaction.objects.all().count()
        self.assertGreater(incoming_transaction_count, 0)

        upload_file_count = UploadTransactionFile.objects.filter(
            file_name=new_file_to_upload.filename).count()
        self.assertGreater(upload_file_count, 0)

        new_file_to_upload = TransactionFile(path=transaction_file.path)
        upload_file_count = UploadTransactionFile.objects.get(
            file_name=new_file_to_upload.filename)

        self.assertFalse(new_file_to_upload.valid)
        new_file_to_upload.upload()
        self.assertTrue(new_file_to_upload.already_uploaded)
        self.assertFalse(new_file_to_upload.valid)

    @tag('test_file_upload')
    def test_file_upload(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())
        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        transaction_file = TransactionFile(path, hostname='010')

        outgoing_transactions = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False)
        self.assertGreater(outgoing_transactions.count(), 0)

        batch_seq, batch_id = batch_identifier(using='client')

        transaction_file.export_to_json(
            transactions=outgoing_transactions, hostname='010',
            using='client', batch_seq=batch_seq, batch_id=batch_id)

        new_file_to_upload = TransactionFile(path=transaction_file.path)
        self.assertTrue(new_file_to_upload.valid)
        self.assertTrue(new_file_to_upload.upload())
