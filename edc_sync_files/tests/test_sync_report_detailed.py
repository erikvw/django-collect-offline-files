import os
from time import sleep

from django.test import TestCase, tag
from django.conf import settings
from faker import Faker
from edc_example.models import TestModel

from edc_sync_files.classes import TransactionDumps, TransactionLoads

from ..classes import SyncReport


@tag('TestSyncReportDetailed')
class TestSyncReportDetailed(TestCase):

    def setUp(self):
        self.fake = Faker()

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
        # OutgoingTransaction
        report_filters = {
            'producer': 'tsetsiba-client'}
        sync_report = SyncReport(
           report_filters=report_filters, all_machines=False)

        self.assertEqual(sync_report.upload_transaction_files().count(), 1)
        self.assertEqual(sync_report.not_consumed, 0)
        self.assertEqual(sync_report.total_consumed, 4)
        self.assertTrue(sync_report.upload_transaction_file)

    @tag('test_uploaded_files_detailed')
    def test_uploaded_files_detailed(self):
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
        # OutgoingTransaction
        report_filters = {
            'producer': 'tsetsiba-client'}
        sync_report = SyncReport(
           report_filters=report_filters, all_machines=False, detailed=True)

        self.assertEqual(sync_report.upload_transaction_files().count(), 1)
        self.assertEqual(sync_report.not_consumed, 0)
        self.assertEqual(sync_report.total_consumed, 4)
        self.assertTrue(sync_report.upload_transaction_file)
        self.assertEqual(
            sync_report.report_data[0].get('total_consumed'), 4)
        self.assertEqual(
            sync_report.report_data[0].get('total_not_consumed'), 0)

    @tag('test_uploaded_files_detailed1')
    def test_uploaded_files_detailed1(self):
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

        name = self.fake.name()
        TestModel.objects.using('client').create(f1=name)
        TestModel.objects.using('client').create(f1=self.fake.name())
        sleep(1)
        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps1 = TransactionDumps(path, using='client', hostname="010")

        transaction_file_path = os.path.join(
            tx_dumps1.path, tx_dumps1.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        # OutgoingTransaction
        report_filters = {
            'producer': 'tsetsiba-client'}
        sync_report = SyncReport(
           report_filters=report_filters, all_machines=False, detailed=True)

        self.assertEqual(sync_report.upload_transaction_files().count(), 2)
        self.assertEqual(sync_report.not_consumed, 0)
        self.assertEqual(sync_report.total_consumed, 4)
        self.assertTrue(sync_report.upload_transaction_file)
        for i in range(2):
            self.assertEqual(
                sync_report.report_data[i].get('total_consumed'), 4)
            self.assertEqual(
                sync_report.report_data[i].get('total_not_consumed'), 0)
