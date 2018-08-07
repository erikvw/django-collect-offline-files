import os

from django.test.testcases import TestCase
from django.test.utils import tag
from django_collect_offline.models import OutgoingTransaction
from faker import Faker

from ..models import ExportedTransactionFileHistory
from ..transaction import TransactionExporterBatch, JSONDumpFile
from .models import TestModel


fake = Faker()


@tag('json')
class TestJSONFile(TestCase):

    def setUp(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

    def test_file(self):
        batch = TransactionExporterBatch(using='client')
        JSONDumpFile(batch=batch, path='/tmp')

    def test_file_text(self):
        batch = TransactionExporterBatch(using='client')
        json_file = JSONDumpFile(batch=batch, path='/tmp')
        self.assertIsNotNone(json_file.json_txt)

    def test_write_file_text(self):
        batch = TransactionExporterBatch(using='client')
        json_file = JSONDumpFile(batch=batch, path='/tmp')
        json_file.write()
        self.assertTrue(os.path.exists(
            os.path.join(json_file.path, json_file.name)))
