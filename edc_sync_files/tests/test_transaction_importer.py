import os

from faker import Faker
from time import sleep

from django.conf import settings
from django.test.testcases import TestCase
from django.test.utils import tag

from edc_sync.models import OutgoingTransaction

from ..models import History
from ..transaction import TransactionImporter, TransactionExporter
from .models import TestModel
from edc_sync.consumer import Consumer

fake = Faker()


class TestTransactionImporter(TestCase):

    def setUp(self):
        super().setUp()
        TestModel.objects.using('client').all().delete()
        History.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()

    def test_export_and_import(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(using='client', device_id="010")
        tx_importer = TransactionImporter(filename=tx_exporter.filename)
        self.assertGreater(tx_importer.imported, 0)

    def test_export_and_import_and_consume(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(using='client', device_id="010")
        tx_importer = TransactionImporter(filename=tx_exporter.filename)
        consumed = Consumer(
            transactions=tx_importer.tx_pks, check_device=False,
            check_hostname=False,
            verbose=False).consume()
        self.assertGreater(consumed, 0)

    def test_export_and_import_and_consume_many(self):
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            tx_exporter = TransactionExporter(using='client', device_id="010")
            tx_importer = TransactionImporter(filename=tx_exporter.filename)
            consumed = Consumer(
                transactions=tx_importer.tx_pks, check_device=False,
                check_hostname=False,
                verbose=False).consume()
            self.assertGreater(consumed, 0)
