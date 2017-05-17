import os

from faker import Faker
from django.test.testcases import TestCase
from django.test.utils import tag

from edc_sync.models import OutgoingTransaction

from ..event_handlers import TransactionFileEventHandler
from ..models import ImportedTransactionFileHistory, ExportedTransactionFileHistory
from ..transaction import TransactionExporter, TransactionFileSender
from ..queues import tx_file_queue, batch_queue
from .models import TestModel

fake = Faker()


class Event:
    def __init__(self, filename=None, path=None):
        self.event_type = 'created'
        self.src_path = os.path.join(path, filename)


@tag('event')
class TestFileEventHandler(TestCase):

    multi_db = True

    def setUp(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
        while not tx_file_queue.empty():
            tx_file_queue.get()
            tx_file_queue.task_done()
        while not batch_queue.empty():
            batch_queue.get()
            batch_queue.task_done()

    def test_export_send_process(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(using='client')
        batch = tx_exporter.export_batch()

        tx_file_sender = TransactionFileSender(
            history_model=tx_exporter.history_model, using='client')
        tx_file_sender.send([batch.filename])

        event_handler = TransactionFileEventHandler()
        event_handler.process(
            Event(filename=batch.filename, path=tx_file_sender.dst_path),
            check_device=False,
            check_hostname=False,
            verbose=False)
        self.assertTrue(tx_file_queue.all_tasks_done)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 1)
        self.assertFalse(batch_queue.empty())
        self.assertEqual(batch_queue.qsize(), 1)

    def test_export_send_process_many(self):
        filenames = []
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            self.assertEqual(TestModel.objects.all().count(), 0)

            tx_exporter = TransactionExporter(using='client')
            batch = tx_exporter.export_batch()
            filenames.append(batch.filename)

        tx_file_sender = TransactionFileSender(
            history_model=tx_exporter.history_model, using='client')
        tx_file_sender.send(filenames)

        event_handler = TransactionFileEventHandler()
        for filename in filenames:
            event_handler.process(
                Event(filename=filename, path=tx_file_sender.dst_path),
                check_device=False,
                check_hostname=False,
                verbose=False)
            self.assertTrue(tx_file_queue.all_tasks_done)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 5)
        self.assertFalse(batch_queue.empty())
        self.assertEqual(batch_queue.qsize(), 5)

    def test_export_send_process_with_delete(self):
        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()
        self.assertEqual(TestModel.objects.all().count(), 0)

        tx_exporter = TransactionExporter(using='client')
        batch = tx_exporter.export_batch()

        tx_file_sender = TransactionFileSender(
            history_model=tx_exporter.history_model, using='client')
        tx_file_sender.send([batch.filename])

        event_handler = TransactionFileEventHandler()
        event_handler.process(
            Event(filename=batch.filename, path=tx_file_sender.dst_path),
            check_device=False,
            check_hostname=False,
            verbose=False)
        self.assertTrue(tx_file_queue.empty())
        self.assertFalse(batch_queue.empty())
        self.assertEqual(batch_queue.qsize(), 1)

    def test_batch_queue(self):
        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(using='client')
        batch = tx_exporter.export_batch()

        tx_file_sender = TransactionFileSender(
            history_model=tx_exporter.history_model, using='client')
        tx_file_sender.send([batch.filename])

        event_handler = TransactionFileEventHandler()
        event_handler.process(
            Event(filename=batch.filename, path=tx_file_sender.dst_path),
            check_device=False,
            check_hostname=False,
            verbose=False)
        self.assertTrue(tx_file_queue.empty())
        self.assertFalse(batch_queue.empty())
        batch_id = batch_queue.get()
        self.assertIsNotNone(batch_id)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.filter(batch_id=batch_id).count(), 1)
