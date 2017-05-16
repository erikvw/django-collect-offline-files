import re
import os
import tempfile

from django.apps import apps as django_apps
from django.test import TestCase, tag

from edc_device.constants import NODE_SERVER
from edc_sync.models import OutgoingTransaction, IncomingTransaction

from ..queues import TransactionFileQueue, BatchQueue
from ..models import ImportedTransactionFileHistory
from ..transaction import TransactionExporter, TransactionImporter

from .models import TestModel


@tag('queues')
class TestQueues(TestCase):

    def setUp(self):
        self.pattern = r'^\w+\.json$'
        self.path = tempfile.gettempdir()
        files = [f for f in os.listdir(
            path=self.path) if re.match(self.pattern, f)]
        for f in files:
            os.remove(os.path.join(self.path, f))

    def test_tx_file_queue_reload_empty(self):
        q = TransactionFileQueue(path=self.path, patterns=[self.pattern])
        q.reload()
        self.assertEqual(q.qsize(), 0)

    def test_tx_file_queue_reload(self):
        for _ in range(0, 5):
            tempfile.mkstemp(suffix='.json')
        q = TransactionFileQueue(path=self.path, patterns=[self.pattern])
        q.reload()
        self.assertEqual(q.qsize(), 5)

    def test_tx_file_queue_task(self):
        for _ in range(0, 5):
            tempfile.mkstemp(suffix='.json')
        q = TransactionFileQueue(path=self.path, patterns=[self.pattern])
        q.reload()
        self.assertEqual(q.qsize(), 5)
        while not q.empty():
            q.next_task()
        self.assertEqual(q.qsize(), 0)
        self.assertEqual(q.unfinished_tasks, 5)

    def test_batch_queue_reload_empty(self):
        q = BatchQueue(model=ImportedTransactionFileHistory)
        q.reload()
        self.assertEqual(q.qsize(), 0)

    def test_batch_queue_reload(self):
        for i in range(0, 5):
            ImportedTransactionFileHistory.objects.create(
                batch_id=f'{i}XXXX', consumed=False)
        q = BatchQueue(model=ImportedTransactionFileHistory)
        q.reload()
        self.assertEqual(q.qsize(), 5)

    def test_batch_queue_task_without_tx(self):
        django_apps.app_configs['edc_device'].device_id = '98'
        django_apps.app_configs['edc_device'].device_role = NODE_SERVER
        for i in range(0, 5):
            _, p = tempfile.mkstemp(suffix='.json')
            ImportedTransactionFileHistory.objects.create(
                batch_id=f'{i}XXXX', consumed=False, filename=os.path.basename(p))
        q = BatchQueue(model=ImportedTransactionFileHistory)
        q.reload()
        self.assertEqual(q.qsize(), 5)
        while not q.empty():
            q.next_task()
        self.assertEqual(q.qsize(), 0)
        self.assertEqual(q.unfinished_tasks, 0)  # there was nothing to do
        self.assertEqual(ImportedTransactionFileHistory.objects.filter(
            consumed=True).count(), 5)

    def test_batch_queue_task_with_tx(self):
        OutgoingTransaction.objects.using('client').all().delete()
        IncomingTransaction.objects.all().delete()
        TestModel.objects.all().delete()
        TestModel.objects.using('client').all().delete()
        TestModel.history.all().delete()
        TestModel.history.using('client').all().delete()
        django_apps.app_configs['edc_device'].device_id = '98'
        django_apps.app_configs['edc_device'].device_role = NODE_SERVER
        TestModel.objects.using('client').create(f1='model1')
        tx_exporter = TransactionExporter(using='client')
        history = tx_exporter.export_batch()
        tx_importer = TransactionImporter(filename=history.filename)
        batch = tx_importer.import_batch()
        q = BatchQueue(model=ImportedTransactionFileHistory)
        q.put(batch.batch_id)
        while not q.empty():
            q.next_task()
        self.assertEqual(q.qsize(), 0)
        self.assertEqual(q.unfinished_tasks, 0)
        self.assertEqual(
            TestModel.objects.filter(f1='model1').count(), 1)
