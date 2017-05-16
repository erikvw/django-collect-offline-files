import os

from faker import Faker
from django.apps import apps as django_apps
from django.test.testcases import TestCase
from django.test.utils import tag

from edc_sync.models import OutgoingTransaction

from ..event_handlers import TransactionFileEventHandler
from ..models import ImportedTransactionFileHistory, ExportedTransactionFileHistory
from ..transaction import TransactionExporter
from ..queues import tx_file_queue, batch_queue
from .models import TestModel

fake = Faker()


class Event:
    def __init__(self, filename=None):
        self.event_type = 'created'
        self.src_path = os.path.join(django_apps.get_app_config(
            'edc_sync_files').destination_folder, filename)


@tag('event')
class TestFileEventHandler(TestCase):

    multi_db = True

    def setUp(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
        while not batch_queue.empty():
            batch_queue.get()

    def test_create(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(using='client')
        history = tx_exporter.export_batch()
        event_handler = TransactionFileEventHandler()
        event_handler.process(
            Event(filename=history.filename),
            check_device=False,
            check_hostname=False,
            verbose=False)
        self.assertTrue(tx_file_queue.all_tasks_done)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 1)
        self.assertFalse(batch_queue.empty())
        self.assertEqual(batch_queue.qsize(), 1)

    def test_create_many(self):
        filenames = []
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            self.assertEqual(TestModel.objects.all().count(), 0)
            tx_exporter = TransactionExporter(using='client')
            history = tx_exporter.export_batch()
            filenames.append(history.filename)
        event_handler = TransactionFileEventHandler()
        for filename in filenames:
            event_handler.process(
                Event(filename=filename),
                check_device=False,
                check_hostname=False,
                verbose=False)
            self.assertTrue(tx_file_queue.all_tasks_done)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 5)
        self.assertFalse(batch_queue.empty())
        self.assertEqual(batch_queue.qsize(), 5)

    def test_create_and_delete(self):
        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(using='client')
        history = tx_exporter.export_batch()
        event_handler = TransactionFileEventHandler()
        event_handler.process(
            Event(filename=history.filename),
            check_device=False,
            check_hostname=False,
            verbose=False)
        self.assertTrue(tx_file_queue.all_tasks_done)
        self.assertFalse(batch_queue.empty())
        self.assertEqual(batch_queue.qsize(), 1)

    def test_batch_queue(self):
        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(using='client')
        history = tx_exporter.export_batch()
        event_handler = TransactionFileEventHandler()
        event_handler.process(
            Event(filename=history.filename),
            check_device=False,
            check_hostname=False,
            verbose=False)
        self.assertTrue(tx_file_queue.all_tasks_done)
        self.assertFalse(batch_queue.empty())
        batch_id = batch_queue.get()
        self.assertIsNotNone(batch_id)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.filter(batch_id=batch_id).count(), 1)
