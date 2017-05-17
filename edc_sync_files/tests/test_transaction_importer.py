import uuid
import os
from faker import Faker

from django.db.utils import IntegrityError
from django.test.testcases import TestCase
from django.test.utils import tag

from edc_sync.models import OutgoingTransaction

from ..models import ExportedTransactionFileHistory
from ..transaction import TransactionImporter, TransactionExporter
from ..transaction.transaction_importer import (
    JSONFile, deserialize, BatchHistory, BatchHistoryError, Batch,
    BatchError, BatchIsEmpty, InvalidBatchSequence)
from .models import TestModel

fake = Faker()


class TestJSONFile(TestCase):

    def setUp(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(using='client')
        history = tx_exporter.export_batch()
        self.filename = history.filename
        self.path = tx_exporter.path

    def test_file(self):
        json_file = JSONFile(
            name=self.filename, path=self.path, archive_folder='/tmp')
        json_text = json_file.read()
        self.assertIsNotNone(json_text)

    def test_deserialize_file(self):
        json_file = JSONFile(
            name=self.filename, path=self.path, archive_folder='/tmp')
        self.assertGreater(
            len([obj for obj in json_file.deserialized_objects]), 0)

    def test_archive_file(self):
        json_file = JSONFile(
            name=self.filename, path=self.path, archive_folder='/tmp')
        json_file.file_archiver.archive(self.filename)
        path = os.path.join(json_file.path, json_file.name)
        self.assertFalse(os.path.exists(path))
        path = os.path.join(json_file.archive_folder, json_file.name)
        self.assertTrue(os.path.exists(path))


class TestDeserializer(TestCase):

    def setUp(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(using='client')
        history = tx_exporter.export_batch()
        self.filename = history.filename
        self.path = tx_exporter.path

    def test_deserializer(self):
        with open(os.path.join(self.path, self.filename)) as f:
            json_text = f.read()
        objects = deserialize(json_text=json_text)
        try:
            next(objects)
        except StopIteration:
            self.fail('StopIteration unexpectedly raised')


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


class TestBatch(TestCase):

    def test_batch_expects_objects(self):
        batch = Batch()
        self.assertRaises(BatchError, batch.populate,
                          deserialized_txs=[], filename='file')

    def test_batch_save_nothing(self):
        batch = Batch()
        self.assertRaises(BatchError, batch.save)

    def test_batch_update_history(self):
        batch = Batch()
        try:
            batch.update_history()
        except BatchIsEmpty:
            pass
        else:
            self.fail('BatchIsEmpty unexpectedly not raised')


class TestTransactionImporter(TestCase):

    def setUp(self):
        TestModel.objects.using('client').all().delete()
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()

    def test_export_and_import(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(using='client')
        history = tx_exporter.export_batch()
        tx_importer = TransactionImporter(filename=history.filename)
        batch = tx_importer.import_batch()
        self.assertIsNotNone(batch.batch_id)

    def test_export_and_import_many_in_order(self):
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            tx_exporter = TransactionExporter(using='client')
            history = tx_exporter.export_batch()
            tx_importer = TransactionImporter(filename=history.filename)
            batch = tx_importer.import_batch()
            self.assertIsNotNone(batch.batch_id)

    def test_export_and_import_many_unordered(self):
        """Assert raises error if batches imported out of sequence.
        """
        filenames = []
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            tx_exporter = TransactionExporter(using='client')
            history = tx_exporter.export_batch()
            filenames.append(history.filename)
        tx_importer = TransactionImporter(filename=filenames[3])
        self.assertRaises(InvalidBatchSequence, tx_importer.import_batch)
