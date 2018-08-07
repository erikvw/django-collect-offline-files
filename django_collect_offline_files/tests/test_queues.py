import logging
import os
import re
import tempfile

from django.apps import apps as django_apps
from django.test import TestCase, tag
from django_collect_offline.models import OutgoingTransaction, IncomingTransaction
from edc_device.constants import NODE_SERVER

from ..models import ImportedTransactionFileHistory, ExportedTransactionFileHistory
from ..file_queues import IncomingTransactionsFileQueue
from ..file_queues import DeserializeTransactionsFileQueue, process_queue
from ..transaction import TransactionExporter, TransactionImporter
from .models import TestModel

logger = logging.getLogger('django_collect_offline_files')


class TestQueues(TestCase):

    multi_db = True

    def setUp(self):
        self.regexes = [r'(\/\w+)+\.json$', '\w+\.json$']
        self.src_path = os.path.join(tempfile.gettempdir(), 'src')
        self.dst_path = os.path.join(tempfile.gettempdir(), 'dst')
        if not os.path.exists(self.src_path):
            os.mkdir(self.src_path)
        if not os.path.exists(self.dst_path):
            os.mkdir(self.dst_path)
        combined = re.compile("(" + ")|(".join(self.regexes) + ")", re.I)
        files = [f for f in os.listdir(
            path=self.src_path) if re.match(combined, f)]
        for f in files:
            os.remove(os.path.join(self.src_path, f))

    def make_import_tx_history(self, count=None):
        """Makes tmp files and updates imported history.
        """
        files = []
        for _ in range(0, count):
            _, p = tempfile.mkstemp(suffix='.json', dir=self.src_path)
            files.append(p)
        for index, p in enumerate(files):
            filename = os.path.basename(p)
            ImportedTransactionFileHistory.objects.create(
                batch_id=f'{index}XXXX', filename=filename, consumed=False)

    def test_incoming_tx_queue_reload_empty(self):
        q = IncomingTransactionsFileQueue(
            src_path=self.src_path,
            dst_path=self.dst_path)
        q.reload(regexes=self.regexes)
        self.assertEqual(q.qsize(), 0)

    def test_incoming_tx_queue_reload(self):
        for _ in range(0, 5):
            tempfile.mkstemp(suffix='.json', dir=self.src_path)
        q = IncomingTransactionsFileQueue(
            src_path=self.src_path,
            dst_path=self.dst_path)
        q.reload(regexes=self.regexes)
        self.assertEqual(q.qsize(), 5)

    def test_deserialize_tx_queue_reload_empty(self):
        q = DeserializeTransactionsFileQueue(
            src_path=self.src_path,
            dst_path=self.dst_path,
            history_model=ImportedTransactionFileHistory)
        q.reload(regexes=self.regexes)
        self.assertEqual(q.qsize(), 0)

    def test_deserialize_tx_queue_reload(self):
        self.make_import_tx_history(count=5)
        q = DeserializeTransactionsFileQueue(
            src_path=self.src_path,
            dst_path=self.dst_path,
            history_model=ImportedTransactionFileHistory)
        q.reload(regexes=self.regexes)
        self.assertEqual(q.qsize(), 5)

    def test_deserialize_tx_queue_task_without_tx(self):
        django_apps.app_configs['edc_device'].device_id = '98'
        django_apps.app_configs['edc_device'].device_role = NODE_SERVER
        self.make_import_tx_history(count=5)
        q = DeserializeTransactionsFileQueue(
            src_path=self.src_path,
            dst_path=self.dst_path,
            history_model=ImportedTransactionFileHistory,
            override_role=NODE_SERVER)
        q.reload(regexes=self.regexes)
        self.assertEqual(q.qsize(), 5)
        q.put(None)
        with self.assertLogs(logger=logger, level=logging.INFO) as cm:
            process_queue(queue=q)
        self.assertIn('Successfully processed', ' '.join(cm.output))
        q.join()

        self.assertEqual(q.qsize(), 0)
        self.assertEqual(q.unfinished_tasks, 0)  # there was nothing to do
        self.assertEqual(ImportedTransactionFileHistory.objects.filter(
            consumed=True).count(), 5)

    def test_deserialize_tx_queue_task_with_tx(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        ImportedTransactionFileHistory.objects.all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        IncomingTransaction.objects.all().delete()
        TestModel.objects.all().delete()
        TestModel.objects.using('client').all().delete()
        TestModel.history.all().delete()
        TestModel.history.using('client').all().delete()
        django_apps.app_configs['edc_device'].device_id = '98'
        django_apps.app_configs['edc_device'].device_role = NODE_SERVER
        TestModel.objects.using('client').create(f1='model1')

        export_path = os.path.join(tempfile.gettempdir(), 'outgoing')
        if not os.path.exists(export_path):
            os.mkdir(export_path)
        import_path = os.path.join(tempfile.gettempdir(), 'incoming')
        if not os.path.exists(import_path):
            os.mkdir(import_path)
        pending_path = os.path.join(tempfile.gettempdir(), 'pending')
        if not os.path.exists(pending_path):
            os.mkdir(pending_path)
        archive_path = os.path.join(tempfile.gettempdir(), 'archive')
        if not os.path.exists(archive_path):
            os.mkdir(archive_path)

        tx_exporter = TransactionExporter(
            export_path=export_path, using='client')
        batch = tx_exporter.export_batch()

        os.rename(
            os.path.join(export_path, batch.filename),
            os.path.join(import_path, batch.filename))
        self.assertTrue(os.path.exists(
            os.path.join(import_path, batch.filename)))

        tx_importer = TransactionImporter(import_path=import_path)
        batch = tx_importer.import_batch(filename=batch.filename)

        os.rename(
            os.path.join(import_path, batch.filename),
            os.path.join(pending_path, batch.filename))
        self.assertTrue(os.path.exists(
            os.path.join(pending_path, batch.filename)))

        q = DeserializeTransactionsFileQueue(
            src_path=pending_path,
            dst_path=archive_path,
            regexes=self.regexes,
            history_model=ImportedTransactionFileHistory,
            override_role=NODE_SERVER)

        q.put(os.path.join(pending_path, batch.filename))
        q.put(None)
        with self.assertLogs(logger=logger, level=logging.INFO) as cm:
            process_queue(queue=q)
        self.assertIn('Successfully processed', ' '.join(cm.output))
        q.join()

        self.assertEqual(q.qsize(), 0)
        self.assertEqual(q.unfinished_tasks, 0)
        self.assertEqual(
            TestModel.objects.filter(f1='model1').count(), 1)
