import os

from django.test.testcases import TestCase
from django.test.utils import tag
from faker import Faker

from edc_sync.models import OutgoingTransaction

from ..models import History
from ..transaction import TransactionExporter
from .models import TestModel
from edc_sync_files.transaction.transaction_exporter import TransactionExporterError


fake = Faker()


class TestTransactionExporter(TestCase):

    def setUp(self):
        TestModel.objects.using('client').all().delete()
        History.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()

    def test_export_pending(self):
        """Assert exports pending transactions.
        """
        # Create transactions
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

        tx_exporter = TransactionExporter(using='client', device_id='010')
        self.assertTrue(tx_exporter.exported)
        self.assertEqual(History.objects.using('client').all().count(), 1)

        outgoing_transactions = OutgoingTransaction.objects.using(
            'client').filter(is_consumed_server=True)
        self.assertGreater(outgoing_transactions.count(), 0)

    def test_export_none_pending(self):
        """Asserts can instantiate even if no pending transactions exist.
        """
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        TransactionExporter(using='client', device_id='010')
        self.assertEqual(History.objects.using('client').all().count(), 1)

        # export when none pending
        tx_exporter = TransactionExporter(using='client', device_id='010')
        self.assertEqual(History.objects.using('client').all().count(), 1)
        self.assertFalse(tx_exporter.exported)

    def test_export_file(self):
        """Assert exports pending transactions creates file.
        """
        # Create transactions
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

        tx_exporter = TransactionExporter(using='client', device_id='010')
        self.assertTrue(os.path.exists(os.path.join(
            tx_exporter.path, tx_exporter.filename)))

    def test_bad_export_file(self):
        """Assert exports pending transactions creates file.
        """
        # Create transactions
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

        try:
            TransactionExporter(
                path='/blahblah', using='client', device_id='010')
            self.fail('TransactionExporterError not raised for invalid path')
        except TransactionExporterError:
            pass

    def test_updates_history(self):
        """Assert exports pending transactions updates history.
        """
        # Create transactions
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

        tx_exporter = TransactionExporter(using='client', device_id='010')
        try:
            history = History.objects.using('client').get(
                filename=tx_exporter.filename)
        except history.DoesNotExist:
            self.fail('History instance unexpectedly does not exist')
        self.assertTrue(tx_exporter.batch_id, history.batch_id)

    def test_matching_batch_id(self):
        """Assert assigns same batch_id to all exported transactions.
        """
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(using='client', device_id='010')

        outgoing_transactions = OutgoingTransaction.objects.using(
            'client').filter(is_consumed_server=True)
        for obj in outgoing_transactions:
            self.assertEqual(tx_exporter.batch_id, obj.batch_id)

    def test_matching_prev_batch_id(self):
        """Assert assigns same prev_batch_id to all exported transactions.
        """
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        TransactionExporter(using='client', device_id='010')
        outgoing_transactions = OutgoingTransaction.objects.using(
            'client').filter(is_consumed_server=True)
        for obj in outgoing_transactions:
            self.assertEqual(
                outgoing_transactions[0].prev_batch_id,
                obj.prev_batch_id)

    def test_prev_batch_id(self):
        """Assert sets prev batch id to batch id for new tx's
        otherwise to the previous batch id.
        """
        tx_exporters = []
        for _ in range(0, 3):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            tx_exporter = TransactionExporter(using='client', device_id='010')
            tx_exporters.append(tx_exporter)
        for obj in OutgoingTransaction.objects.using(
                'client').filter(batch_id=tx_exporters[0].batch_id):
            self.assertEqual(
                obj.batch_id, obj.prev_batch_id)
        for obj in OutgoingTransaction.objects.using(
                'client').filter(batch_id=tx_exporters[1].batch_id):
            self.assertEqual(
                tx_exporters[0].batch_id, obj.prev_batch_id)
        for obj in OutgoingTransaction.objects.using(
                'client').filter(batch_id=tx_exporters[2].batch_id):
            self.assertEqual(
                tx_exporters[1].batch_id, obj.prev_batch_id)

    def test_not_error_messages(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(using='client', device_id='010')
        self.assertIn('Success', tx_exporter.message)

    def test_error_messages(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        TransactionExporter(using='client', device_id='010')
        tx_exporter = TransactionExporter(using='client', device_id='010')
        self.assertIn('Nothing', tx_exporter.message)
