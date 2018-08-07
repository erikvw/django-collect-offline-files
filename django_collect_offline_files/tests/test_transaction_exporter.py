import os
import tempfile

from django.test.testcases import TestCase
from django.test.utils import tag
from django_collect_offline.models import OutgoingTransaction
from faker import Faker

from ..models import ExportedTransactionFileHistory
from ..transaction import TransactionExporter, TransactionExporterError
from ..transaction import TransactionExporterBatch
from ..transaction.transaction_exporter import BatchAlreadyOpen, HistoryAlreadyExists
from .models import TestModel


fake = Faker()


class TestExportBatch(TestCase):

    def setUp(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()

    def test_empty_batch(self):
        batch = TransactionExporterBatch()
        self.assertEqual(batch.count, 0)
        self.assertIsNone(batch.filename)
        self.assertIsNone(batch.batch_id)
        self.assertIsNone(batch.prev_batch_id)

    def test_nonempty_batch(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        batch = TransactionExporterBatch(using='client')
        self.assertGreater(batch.count, 0)

    def test_reopen_batch(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        batch = TransactionExporterBatch(using='client')
        self.assertRaises(BatchAlreadyOpen, batch.open)

    def test_recreate_history(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        batch = TransactionExporterBatch(using='client')
        self.assertRaises(HistoryAlreadyExists, batch.create_history)

    def test_batch_history(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        batch = TransactionExporterBatch(using='client')
        self.assertEqual(batch.history.batch_id, batch.batch_id)


@tag('exporter')
class TestTransactionExporter(TestCase):

    def setUp(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        self.export_path = os.path.join(tempfile.gettempdir(), 'export')
        if not os.path.exists(self.export_path):
            os.mkdir(self.export_path)

    def test_export(self):
        """Assert exports pending transactions.
        """
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        history = tx_exporter.export_batch()
        self.assertIsNotNone(history)
        outgoing_transactions = OutgoingTransaction.objects.using(
            'client').filter(is_consumed_server=True)
        self.assertGreater(outgoing_transactions.count(), 0)

    def test_export_none_pending(self):
        """Asserts can call export_batch even if no pending transactions exist.
        """
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        history = tx_exporter.export_batch()
        self.assertIsNotNone(history)
        history = tx_exporter.export_batch()
        self.assertIsNone(history)

    def test_export_file(self):
        """Assert exports pending transactions creates file.
        """
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        history = tx_exporter.export_batch()
        self.assertTrue(os.path.exists(os.path.join(
            tx_exporter.path, history.filename)))

    def test_bad_export_file(self):
        """Assert raises when cannot create file.
        """
        tx_exporter = TransactionExporter(
            export_path='/blahblah', using='client')
        self.assertRaises(TransactionExporterError,
                          tx_exporter.export_batch)

    def test_creates_history(self):
        """Assert exports pending transactions creates history.
        """
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        tx_exporter.export_batch()
        self.assertGreater(tx_exporter.history_model.objects.using(
            'client').all().count(), 0)

    def test_updates_history(self):
        """Assert exports pending transactions updates history.
        """
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        batch = tx_exporter.export_batch()
        self.assertIsNotNone(batch.batch_id)
        self.assertIsNotNone(batch.history.prev_batch_id)
        self.assertIsNotNone(batch.history.filename)
        self.assertIsNotNone(batch.history.device_id)
        self.assertTrue(batch.history.exported)
        self.assertIsNotNone(batch.history.exported_datetime)

    def test_matching_batch_id(self):
        """Assert assigns same batch_id to all exported transactions.
        """
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        batch = tx_exporter.export_batch()
        outgoing_transactions = OutgoingTransaction.objects.using(
            'client').filter(is_consumed_server=True, batch_id=batch.batch_id)
        for obj in outgoing_transactions:
            self.assertEqual(batch.history.batch_id, obj.batch_id)
            self.assertEqual(batch.history.prev_batch_id, obj.prev_batch_id)
            self.assertEqual(batch.history.hostname,
                             '-'.join(obj.producer.split('-')[:-1]))


@tag('exporter')
class TestTransactionExporter2(TestCase):

    def setUp(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
        self.export_path = os.path.join(tempfile.gettempdir(), 'export')
        if not os.path.exists(self.export_path):
            os.mkdir(self.export_path)

    def test_first_prev_batch_id(self):
        """Assert sets prev batch id to batch id for first export batch.
        """
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        batch = tx_exporter.export_batch()
        for obj in OutgoingTransaction.objects.using(
                'client').filter(batch_id=batch.batch_id):
            self.assertEqual(obj.batch_id, obj.prev_batch_id)

    def test_next_prev_batch_id(self):
        """Assert sets prev batch id to batch id from previous export batch.
        """
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        batch = tx_exporter.export_batch()
        batch_id = batch.batch_id
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        batch = tx_exporter.export_batch()
        for obj in OutgoingTransaction.objects.using(
                'client').filter(batch_id=batch.batch_id):
            self.assertEqual(batch_id, obj.prev_batch_id)

    def test_prev_batch_id(self):
        """Assert sets prev batch id to batch id for new tx's
        otherwise to the previous batch id.
        """
        batches = []
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        for _ in range(0, 3):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            batches.append(tx_exporter.export_batch())
        for obj in OutgoingTransaction.objects.using(
                'client').filter(batch_id=batches[0].batch_id):
            self.assertEqual(obj.batch_id, obj.prev_batch_id)
        for obj in OutgoingTransaction.objects.using(
                'client').filter(batch_id=batches[1].batch_id):
            self.assertEqual(
                batches[0].batch_id, obj.prev_batch_id)
        for obj in OutgoingTransaction.objects.using(
                'client').filter(batch_id=batches[2].batch_id):
            self.assertEqual(
                batches[1].batch_id, obj.prev_batch_id)
