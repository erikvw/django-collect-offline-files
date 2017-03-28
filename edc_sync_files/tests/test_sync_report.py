import os
from time import sleep

from django.test import TestCase, tag
from django.conf import settings
from faker import Faker
from edc_example.models import TestModel

from edc_sync_files.classes import TransactionDumps, TransactionLoads

from ..classes import SyncReport


@tag('TestSyncReport')
class TestSyncReport(TestCase):

    def setUp(self):
        self.fake = Faker()

    @tag('test_uploaded_files')
    def test_uploaded_files(self):
        # Create transactions
        name = self.fake.name()
        TestModel.objects.using('client').create(f1=name)
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        model_count = TestModel.objects.filter(f1=name).count()
        self.assertEqual(model_count, 1)

        sync_report = SyncReport()
        data = sync_report.report_data[0][0]
        self.assertEqual(data.get('total_not_consumed'), 0)
        self.assertEqual(data.get('total_consumed'), 4)
        self.assertTrue(data.get('upload_transaction_file'))

    @tag('test_uploaded_files1')
    def test_uploaded_files1(self):
        # Create transactions
        name = self.fake.name()
        TestModel.objects.using('client').create(f1=name)
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps_1 = TransactionDumps(path, using='client', hostname="010")

        transaction_file_path = os.path.join(
            tx_dumps_1.path, tx_dumps_1.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        model_count = TestModel.objects.filter(
            f1=name).count()
        self.assertEqual(model_count, 1)

        sync_report = SyncReport()
        data = sync_report.report_data[0][0]
        self.assertEqual(data.get('total_not_consumed'), 0)
        self.assertEqual(data.get('total_consumed'), 4)
        self.assertTrue(data.get('upload_transaction_file'))

        name = self.fake.name()
        TestModel.objects.using('client').create(f1=name)
        TestModel.objects.using('client').create(f1=self.fake.name())
        sleep(2)
        # Dump transaction
        path = os.path.join(
            settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps_2 = TransactionDumps(
            path, using='client', hostname="010")

        transaction_file_path = os.path.join(
            tx_dumps_2.path, tx_dumps_2.filename)
        TransactionLoads(
            path=transaction_file_path).upload_file()

        sync_report = SyncReport()
        data = sync_report.report_data[0][0]
        self.assertEqual(data.get('total_not_consumed'), 0)
        self.assertEqual(data.get('total_consumed'), 8)
        self.assertTrue(data.get('upload_transaction_file'))
