import os

from faker import Faker
from django.apps import apps as django_apps
from django.test.testcases import TestCase
from django.test.utils import tag

from edc_sync.models import OutgoingTransaction

from ..models import ImportedTransactionFileHistory, ExportedTransactionFileHistory
from ..transaction import TransactionExporter, TransactionFileSender
from .models import TestModel

app_config = django_apps.get_app_config('edc_sync_files')
fake = Faker()


class Event:
    def __init__(self, filename=None, src_path=None):
        self.event_type = 'created'
        self.src_path = os.path.join(src_path, filename)


@tag('event')
class TestFileEventHandler(TestCase):

    multi_db = True

    def setUp(self):
        self.regexes = [r'^\w+\.json$']
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
#         while not incoming_tx_queue.empty():
#             incoming_tx_queue.get()
#             incoming_tx_queue.task_done()
#         while not deserialize_tx_queue.empty():
#             deserialize_tx_queue.get()
#             deserialize_tx_queue.task_done()

    def test_export_send_process(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(
            export_path=app_config.outgoing_folder,
            using='client')
        batch = tx_exporter.export_batch()

        tx_file_sender = TransactionFileSender(
            src_path=app_config.outgoing_folder,
            dst_path=app_config.incoming_folder,
            archive_path=app_config.archive_folder,
            history_model=tx_exporter.history_model,
            using='client')
        tx_file_sender.send([batch.filename])

        src_path = app_config.incoming_folder
        incoming_tx_handler = IncomingTransactionsFileHandler(
            regexes=self.regexes,
            src_path=src_path,
            dst_path=app_config.pending_folder)
        incoming_tx_handler.process(
            Event(filename=batch.filename, src_path=src_path))
        self.assertTrue(incoming_tx_handler.queue.all_tasks_done)

        src_path = app_config.pending_folder
        deserialize_tx_handler = DeserializeTransactionsFileHandler(
            regexes=self.regexes,
            src_path=src_path,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory,
            allow_any_role=True)
        deserialize_tx_handler.process(
            Event(filename=batch.filename, src_path=src_path))
        self.assertTrue(deserialize_tx_handler.queue.all_tasks_done)

        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 1)
        self.assertTrue(deserialize_tx_handler.queue.empty())
        self.assertEqual(deserialize_tx_handler.queue.qsize(), 0)

    def test_export_send_process_many(self):
        filenames = []
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            self.assertEqual(TestModel.objects.all().count(), 0)

            tx_exporter = TransactionExporter(
                export_path=app_config.outgoing_folder,
                using='client')
            batch = tx_exporter.export_batch()
            filenames.append(batch.filename)

        tx_file_sender = TransactionFileSender(
            src_path=app_config.outgoing_folder,
            dst_path=app_config.incoming_folder,
            archive_path=app_config.archive_folder,
            history_model=tx_exporter.history_model,
            using='client')
        tx_file_sender.send(filenames)

        incoming_tx_handler = IncomingTransactionsFileHandler(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)
        for filename in filenames:
            incoming_tx_handler.process(
                Event(filename=filename, src_path=app_config.incoming_folder))
            self.assertTrue(incoming_tx_handler.queue.all_tasks_done)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 5)

    def test_export_send_process_with_delete(self):
        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()
        self.assertEqual(TestModel.objects.all().count(), 0)

        tx_exporter = TransactionExporter(
            export_path=app_config.outgoing_folder,
            using='client')

        batch = tx_exporter.export_batch()

        tx_file_sender = TransactionFileSender(
            src_path=app_config.outgoing_folder,
            dst_path=app_config.incoming_folder,
            archive_path=app_config.archive_folder,
            history_model=tx_exporter.history_model,
            using='client')
        tx_file_sender.send([batch.filename])

        incoming_tx_handler = IncomingTransactionsFileHandler(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)
        incoming_tx_handler.process(
            Event(filename=batch.filename, src_path=app_config.incoming_folder))
        self.assertTrue(incoming_tx_handler.queue.empty())
        self.assertEqual(incoming_tx_handler.queue.qsize(), 0)
        self.assertEqual(TestModel.objects.all().count(), 0)

    def test_deserialize_tx_queue_with_delete(self):
        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(
            export_path=app_config.outgoing_folder,
            using='client')
        batch = tx_exporter.export_batch()

        tx_file_sender = TransactionFileSender(
            src_path=app_config.outgoing_folder,
            dst_path=app_config.incoming_folder,
            archive_path=app_config.archive_folder,
            history_model=tx_exporter.history_model,
            using='client')
        tx_file_sender.send([batch.filename])

        incoming_tx_handler = IncomingTransactionsFileHandler(
            regexes=self.regexes,
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)
        incoming_tx_handler.process(
            Event(filename=batch.filename, src_path=app_config.incoming_folder))
        self.assertTrue(incoming_tx_handler.queue.empty())

        deserialize_tx_handler = DeserializeTransactionsFileHandler(
            regexes=self.regexes,
            src_path=app_config.pending_folder,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory,
            allow_any_role=True)
        deserialize_tx_handler.process(
            Event(filename=batch.filename, src_path=app_config.pending_folder))
        self.assertEqual(TestModel.objects.all().count(), 0)

    def test_deserialize_tx_queue(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(
            export_path=app_config.outgoing_folder,
            using='client')
        batch = tx_exporter.export_batch()

        tx_file_sender = TransactionFileSender(
            src_path=app_config.outgoing_folder,
            dst_path=app_config.incoming_folder,
            archive_path=app_config.archive_folder,
            history_model=tx_exporter.history_model,
            using='client')
        tx_file_sender.send([batch.filename])

        incoming_tx_handler = IncomingTransactionsFileHandler(
            regexes=self.regexes,
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)
        incoming_tx_handler.process(
            Event(filename=batch.filename, src_path=app_config.incoming_folder))
        self.assertTrue(incoming_tx_handler.queue.empty())

        deserialize_tx_handler = DeserializeTransactionsFileHandler(
            regexes=self.regexes,
            src_path=app_config.pending_folder,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory,
            allow_any_role=True)
        deserialize_tx_handler.process(
            Event(filename=batch.filename, src_path=app_config.pending_folder))
        self.assertEqual(TestModel.objects.all().count(), 2)
