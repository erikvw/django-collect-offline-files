from faker import Faker
from time import sleep

from django.test.testcases import TestCase
from django.test.utils import tag

from edc_example.models import TestModel

from ..models import UploadTransactionFile
from ..transaction import TransactionDumps


@tag('testFileEventHandler')
class testFileEventHandler(TestCase):

    def setUp(self):
        self.fake = Faker()

    def test_export_to_json_file(self):
        # Create transactions
        tx = TestModel.objects.using('client').create(f1=self.fake.name())
        tx1 = TestModel.objects.using('client').create(f1=self.fake.name())

        tx.delete()
        tx1.delete()

        self.assertEqual(TestModel.objects.using(
            'client').filter(f1=tx.f1).count(), 0)
        self.assertEqual(TestModel.objects.using(
            'client').filter(f1=tx1.f1).count(), 0)

        # Dump transaction
        path = '/Users/tsetsiba/source/edc-sync-files/edc_sync_files/media/transactions/incoming'
        TransactionDumps(path, using='client', hostname="010")
        self.assertEqual(TestModel.objects.using(
            'default').filter(f1=tx.f1).count(), 1)
        self.assertEqual(TestModel.objects.using(
            'default').filter(f1=tx1.f1).count(), 1)

        # Uploaded by watchdog
        self.assertEqual(UploadTransactionFile.objects.all().count(), 1)

    def test_export_upload_multiple_files(self):
        # Create transactions
        tx = TestModel.objects.using('client').create(f1=self.fake.name())
        tx1 = TestModel.objects.using('client').create(f1=self.fake.name())
        tx.delete()
        tx1.delete()

        # Dump transaction
        path = '/Users/tsetsiba/source/edc-sync-files/edc_sync_files/media/transactions/incoming'
        TransactionDumps(path, using='client', hostname="010")
        self.assertEqual(TestModel.objects.using(
            'default').filter(f1=tx.f1).count(), 1)
        self.assertEqual(TestModel.objects.using(
            'default').filter(f1=tx1.f1).count(), 1)

        self.assertEqual(UploadTransactionFile.objects.all().count(), 1)

        # Create transactions
        tx = TestModel.objects.using('client').create(f1=self.fake.name())
        tx1 = TestModel.objects.using('client').create(f1=self.fake.name())
        tx.delete()
        tx1.delete()
        sleep(1)

        TransactionDumps(path, using='client', hostname="010")
        self.assertEqual(UploadTransactionFile.objects.all().count(), 1)
