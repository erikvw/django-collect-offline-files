import os

from django.apps import apps as django_apps
from django.test.testcases import TestCase
from django.test.utils import tag
from django_collect_offline.models import OutgoingTransaction
from edc_device.constants import NODE_SERVER
from faker import Faker

from ..file_queues import IncomingTransactionsFileQueue
from ..file_queues import DeserializeTransactionsFileQueue, process_queue
from ..models import ImportedTransactionFileHistory, ExportedTransactionFileHistory
from ..transaction import TransactionExporter, TransactionFileSender
from .models import TestModel

app_config = django_apps.get_app_config('django_collect_offline_files')
fake = Faker()


class Event:
    def __init__(self, filename=None, src_path=None):
        self.event_type = 'created'
        self.src_path = os.path.join(src_path, filename)


class TestFileEventHandler(TestCase):

    multi_db = True

    def setUp(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
        ImportedTransactionFileHistory.objects.all().delete()

    def send(self, filenames=None, history_model=None):
        tx_file_sender = TransactionFileSender(
            src_path=app_config.outgoing_folder,
            dst_tmp=app_config.tmp_folder,
            dst_path=app_config.incoming_folder,
            archive_path=app_config.archive_folder,
            history_model=history_model,
            using='client')
        tx_file_sender.send(filenames)

    @tag('e')
    def test_export_import_and_move(self):
        """Asserts queue imports, updates history, moves the file.
        """
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

        tx_exporter = TransactionExporter(
            export_path=app_config.incoming_folder, using='client')
        batch = tx_exporter.export_batch()

        self.assertTrue(os.path.join(
            app_config.incoming_folder, batch.filename))

        src_path = app_config.incoming_folder
        queue = IncomingTransactionsFileQueue(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)

        queue.put(os.path.join(src_path, batch.filename))
        queue.put(None)
        process_queue(queue=queue)
        queue.join()

        self.assertEqual(queue.unfinished_tasks, 0)
        self.assertTrue(os.path.join(
            app_config.pending_folder, batch.filename))
        self.assertEqual(
            ImportedTransactionFileHistory.objects.filter(
                batch_id=batch.batch_id,
                consumed=False).count(), 1)

    @tag('e')
    def test_deserialize_and_archive(self):
        """Asserts queue deserializes, updates history, archives the file.
        """
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

        tx_exporter = TransactionExporter(
            export_path=app_config.incoming_folder, using='client')
        batch = tx_exporter.export_batch()

        src_path = app_config.incoming_folder
        queue = IncomingTransactionsFileQueue(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)

        queue.put(os.path.join(src_path, batch.filename))
        queue.put(None)
        process_queue(queue=queue)
        queue.join()

        queue = DeserializeTransactionsFileQueue(
            src_path=app_config.pending_folder,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory,
            override_role=NODE_SERVER)

        queue.put(os.path.join(src_path, batch.filename))
        queue.put(None)
        process_queue(queue=queue)
        queue.join()

        self.assertEqual(queue.unfinished_tasks, 0)

        self.assertTrue(os.path.join(
            app_config.archive_folder, batch.filename))

        self.assertEqual(ImportedTransactionFileHistory.objects.filter(
            batch_id=batch.batch_id,
            consumed=True).count(), 1)

    @tag('e')
    def test_export_send_process_many(self):
        """Asserts export, send, import, archive."""

        # queue
        queue = IncomingTransactionsFileQueue(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)

        # export
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

        # send
        self.send(filenames=filenames, history_model=tx_exporter.history_model)

        # add to queue
        for filename in filenames:
            queue.put(os.path.join(app_config.incoming_folder, filename))

        # import
        queue.put(None)
        process_queue(queue=queue)
        queue.join()

        # assert
        self.assertEqual(queue.unfinished_tasks, 0)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.filter(
                consumed=False).count(), 5)

    @tag('e')
    def test_export_send_process_with_delete(self):

        # queue
        queue = IncomingTransactionsFileQueue(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)

        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()
        self.assertEqual(TestModel.objects.all().count(), 0)

        tx_exporter = TransactionExporter(
            export_path=app_config.outgoing_folder,
            using='client')

        batch = tx_exporter.export_batch()

        self.send(filenames=[batch.filename],
                  history_model=tx_exporter.history_model)

        # add to queue
        queue.put(os.path.join(app_config.incoming_folder, batch.filename))

        # import
        queue.put(None)
        process_queue(queue=queue)
        queue.join()

        # assert
        self.assertEqual(queue.unfinished_tasks, 0)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.filter(
                consumed=False).count(), 1)

    @tag('e')
    def test_deserialize_tx_queue_without_delete(self):

        # create
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

        # export
        tx_exporter = TransactionExporter(
            export_path=app_config.outgoing_folder,
            using='client')
        batch = tx_exporter.export_batch()

        self.send(filenames=[batch.filename],
                  history_model=tx_exporter.history_model)

        # queues
        incoming_queue = IncomingTransactionsFileQueue(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)

        deserialize_queue = DeserializeTransactionsFileQueue(
            src_path=app_config.pending_folder,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory,
            override_role=NODE_SERVER)

        # add to incoming queue
        incoming_queue.put(os.path.join(
            app_config.incoming_folder, batch.filename))

        # import
        incoming_queue.put(None)
        process_queue(queue=incoming_queue)
        incoming_queue.join()

        # add to deserialize queue
        deserialize_queue.put(os.path.join(
            app_config.incoming_folder, batch.filename))

        # deserialize
        deserialize_queue.put(None)
        process_queue(queue=deserialize_queue)
        deserialize_queue.join()

        self.assertEqual(TestModel.objects.all().count(), 2)

    @tag('e')
    def test_deserialize_tx_queue_with_delete(self):

        # create
        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()

        # export
        tx_exporter = TransactionExporter(
            export_path=app_config.outgoing_folder,
            using='client')
        batch = tx_exporter.export_batch()

        self.send(filenames=[batch.filename],
                  history_model=tx_exporter.history_model)

        # queues
        incoming_queue = IncomingTransactionsFileQueue(
            src_path=app_config.incoming_folder,
            dst_path=app_config.pending_folder)

        deserialize_queue = DeserializeTransactionsFileQueue(
            src_path=app_config.pending_folder,
            dst_path=app_config.archive_folder,
            history_model=ImportedTransactionFileHistory,
            override_role=NODE_SERVER)

        # add to incoming queue
        incoming_queue.put(os.path.join(
            app_config.incoming_folder, batch.filename))

        # import
        incoming_queue.put(None)
        process_queue(queue=incoming_queue)
        incoming_queue.join()

        # add to deserialize queue
        deserialize_queue.put(os.path.join(
            app_config.incoming_folder, batch.filename))

        # deserialize
        deserialize_queue.put(None)
        process_queue(queue=deserialize_queue)
        deserialize_queue.join()

        self.assertEqual(TestModel.objects.all().count(), 0)
