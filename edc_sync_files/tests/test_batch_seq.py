import os

from django.conf import settings
from django.test.testcases import TestCase
from django.test.utils import tag

from faker import Faker

from edc_example.models import TestModel
from edc_sync.models import OutgoingTransaction

from ..classes.batch_identifier import batch_identifier
from ..classes import TransactionFile


@tag('TestTransactionOrder')
class TestBatchSeq(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.faker = Faker()

    def test_file_identifier_first_time(self):
        #  Create transactions
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())

        batch_seq, batch_id = batch_identifier(using='client')
        self.assertTrue(batch_id)

        outgoing_transactions = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False)
        # Dump transaction
        outgoing_path = os.path.join(settings.MEDIA_ROOT, 'transactions', 'outgoing')
        transaction_file = TransactionFile(outgoing_path, hostname='010')

        transaction_file.export_to_json(
            transactions=outgoing_transactions, hostname='010',
            using='client', batch_id=batch_id, batch_seq=batch_seq)

        outgoing = OutgoingTransaction.objects.using('client').filter(
            batch_seq=batch_id, batch_id=batch_id, is_consumed_server=True).first()

        self.assertEqual(
            outgoing.batch_seq,
            outgoing.batch_id)

    @tag('test_file_identifier_with_synced_tx')
    def test_file_identifier_with_synced_tx(self):
        #  Create transactions
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())

        batch_seq, batch_id = batch_identifier(using='client')
        self.assertEqual(batch_id, batch_seq)

        outgoing_transactions = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False)
        # Dump transaction
        outgoing_path = os.path.join(settings.MEDIA_ROOT, 'transactions', 'outgoing')
        transaction_file = TransactionFile(outgoing_path, hostname='010')

        transaction_file.export_to_json(
            transactions=outgoing_transactions, hostname='010',
            using='client', batch_id=batch_id, batch_seq=batch_seq)

        # Create another transactions
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())

        new_batch_seq, new_batch_id = batch_identifier(using='client')
        self.assertEqual(new_batch_seq, str(batch_id))  # Be equal to previous batch id since it is carried forward.
        self.assertNotEqual(new_batch_id, str(batch_id))  # Not equal coz new one is generated.

    @tag('test_file_identifier_with_synced_tx1')
    def test_file_identifier_with_synced_tx1(self):
        #  Create transactions
        TestModel.objects.using('client').create(f1='erik')
        TestModel.objects.using('client').create(f1='setsiba')

        batch_seq, batch_id = batch_identifier(using='client')
        self.assertEqual(batch_id, batch_seq)

        outgoing_transactions = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False)
        # Dump transaction
        outgoing_path = os.path.join(settings.MEDIA_ROOT, 'transactions', 'outgoing')
        transaction_file = TransactionFile(outgoing_path, hostname='010')

        transaction_file.export_to_json(
            transactions=outgoing_transactions, hostname='010',
            using='client', batch_id=batch_id, batch_seq=batch_seq)

        # Create another transactions
        TestModel.objects.using('client').create(f1='erik1')
        TestModel.objects.using('client').create(f1='setsiba1')

        new_batch_seq, new_batch_id = batch_identifier(using='client')
        self.assertEqual(new_batch_seq, str(batch_id))  # Be equal to previous batch id since it is carried forward.
        self.assertNotEqual(new_batch_id, str(batch_id))  # Not equal coz new one is generated.

        outgoing_transactions = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False)

        transaction_file = TransactionFile(outgoing_path, hostname='010')
        transaction_file.export_to_json(
            transactions=outgoing_transactions, hostname='010',
            using='client', batch_id=new_batch_id, batch_seq=new_batch_id)

        outgoing_transaction_count = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False).count()
        self.assertEqual(outgoing_transaction_count, 0)

        # Create another transactions
        TestModel.objects.using('client').create(f1=self.faker.name())
        TestModel.objects.using('client').create(f1=self.faker.name())

        outgoing_transaction_count = OutgoingTransaction.objects.using('client').filter(
            is_consumed_server=False).count()
        self.assertGreater(outgoing_transaction_count, 0)

        new_batch_seq1, new_batch_id1 = batch_identifier(using='client')
        self.assertEqual(new_batch_seq1, str(new_batch_id))
        self.assertNotEqual(new_batch_seq1, new_batch_id1)
