import uuid
import os
import tempfile

from django.db.utils import IntegrityError
from django.test.testcases import TestCase
from django.test.utils import tag
from django_collect_offline.models import OutgoingTransaction
from faker import Faker

from ..models import ExportedTransactionFileHistory
from ..transaction import TransactionImporter, TransactionExporter, TransactionImporterBatch
from ..transaction import TransactionImporterError
from ..transaction.transaction_importer import (
    BatchHistory, BatchHistoryError, BatchError, BatchIsEmpty)
from .models import TestModel

fake = Faker()


class TestBatchHistory(TestCase):

    def setUp(self):
        self.filename = 'file.txt'
        self.path = '/tmp'
        batch_id = uuid.uuid4().hex
        prev_batch_id = batch_id
        self.options = dict(
            filename='file.txt',
            batch_id=batch_id,
            prev_batch_id=prev_batch_id,
            producer='erik',
            count=100)

    def test_batch_history_update_with_nulls(self):
        """Assert update does not except NULLs.
        """
        obj = BatchHistory()
        self.assertRaises(BatchHistoryError, obj.update)

    def test_batch_history_update_unique(self):
        """Assert unique constraint.
        """
        batch_history = BatchHistory()
        batch_history.update(**self.options)
        self.assertRaises(IntegrityError, batch_history.update, **self.options)

    def test_batch_history_update_unique_by_batch_id(self):
        """Assert batch id unique constraint.
        """
        batch_history = BatchHistory()
        batch_history.update(**self.options)
        self.options['filename'] = 'file2.txt'
        self.assertRaises(IntegrityError, batch_history.update, **self.options)

    def test_batch_history_update_unique_by_filename(self):
        """Assert batch id unique constraint.
        """
        batch_history = BatchHistory()
        batch_history.update(**self.options)
        self.options['batch_id'] = uuid.uuid4().hex
        self.assertRaises(IntegrityError, batch_history.update, **self.options)

    def test_batch_history_update_count(self):
        """Assert excepts zero count.
        """
        batch_history = BatchHistory()
        self.options['count'] = 0
        try:
            batch_history.update(**self.options)
        except BatchHistoryError:
            self.fail(f'BatchHistoryError unexpectedly not raised.')

    def test_batch_history_exists(self):
        """Assert finds history by batch_id.
        """
        batch_history = BatchHistory()
        batch_history.update(**self.options)
        self.assertTrue(batch_history.exists(
            batch_id=self.options.get('batch_id')))


@tag('batch')
class TestImportBatch(TestCase):

    def test_batch_expects_objects(self):
        batch = TransactionImporterBatch()
        self.assertRaises(BatchError, batch.populate,
                          deserialized_txs=[], filename='file')

    def test_batch_save_nothing(self):
        batch = TransactionImporterBatch()
        self.assertRaises(BatchError, batch.save)

    def test_batch_update_history(self):
        batch = TransactionImporterBatch()
        try:
            batch.update_history()
        except BatchIsEmpty:
            pass
        else:
            self.fail('BatchIsEmpty unexpectedly not raised')


@tag('importer')
class TestTransactionImporter(TestCase):

    def setUp(self):
        TestModel.objects.using('client').all().delete()
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        self.export_path = os.path.join(tempfile.gettempdir(), 'export')
        if not os.path.exists(self.export_path):
            os.mkdir(self.export_path)
        self.import_path = os.path.join(tempfile.gettempdir(), 'import')
        if not os.path.exists(self.import_path):
            os.mkdir(self.import_path)

    def manually_move_export2import(self, filename):
        os.rename(
            os.path.join(self.export_path, filename),
            os.path.join(self.import_path, filename))

    def test_export_and_import(self):
        """Asserts exports a file and, after manually moving,
        imports.
        """
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        batch = tx_exporter.export_batch()
        self.manually_move_export2import(batch.filename)
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        self.assertIsNotNone(batch.batch_id)

    def test_export_and_import_many_in_order(self):
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            tx_exporter = TransactionExporter(
                export_path=self.export_path,
                using='client')
            batch = tx_exporter.export_batch()
            self.manually_move_export2import(batch.filename)
            tx_importer = TransactionImporter(import_path=self.import_path)
            batch = tx_importer.import_batch(filename=batch.filename)
            self.assertIsNotNone(batch.batch_id)

    @tag('1')
    def test_export_and_import_many_unordered(self):
        """Assert raises error if batches imported out of sequence.
        """
        filenames = []
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            tx_exporter = TransactionExporter(
                export_path=self.export_path,
                using='client')
            batch = tx_exporter.export_batch()
            self.manually_move_export2import(batch.filename)
            filenames.append(batch.filename)
        tx_importer = TransactionImporter(import_path=self.import_path)

        # in order, good
        try:
            tx_importer.import_batch(filename=filenames[0])
        except TransactionImporterError:
            self.fail('TransactionImporterError unexpectedly raised')

        # out of order, bad
        self.assertRaises(
            TransactionImporterError,
            tx_importer.import_batch, filename=filenames[3])
