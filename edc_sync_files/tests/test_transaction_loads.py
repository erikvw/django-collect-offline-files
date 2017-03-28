import os
from time import sleep

from faker import Faker

from django.test.testcases import TestCase
from django.test.utils import tag
from django.conf import settings

from edc_example.models import TestModel
from edc_sync_files.classes import TransactionLoads, TransactionDumps
from edc_sync.models import IncomingTransaction
from edc_sync_files.classes import SyncReport
from edc_sync_files.models import UploadTransactionFile


@tag('TestTransactionLoads')
class TestTransactionLoads(TestCase):

    def setUp(self):
        self.fake = Faker()

    @tag('test_upload_transaction_file_valid_first_timeupload1')
    def test_upload_transaction_file_valid_first_timeupload(self):

        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertTrue(new_file_to_upload.valid)

    @tag('test_upload_transaction_file_valid_first_timeupload2')
    def test_upload_transaction_file_valid_first_timeupload_delete(self):

        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertTrue(new_file_to_upload.valid)

    @tag('test_upload_transaction_file_valid2')
    def test_upload_transaction_file_valid_next_file_same(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertTrue(new_file_to_upload.valid)

        transaction_load = TransactionLoads(transaction_file_path)
        self.assertTrue(transaction_load.upload_file())

        transaction_load = TransactionLoads(transaction_file_path)
        self.assertFalse(transaction_load.upload_file())

    @tag('test_file_upload')
    def test_file_upload(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertTrue(new_file_to_upload.upload_file())

        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())
        sleep(1)
        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)
        self.assertTrue(new_file_to_upload.upload_file())

    @tag('test_file_upload_upload')
    def test_file_upload_and_play(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)

        for tx_record in new_file_to_upload.transaction_objs:
            tx_record.delete()
        self.assertTrue(new_file_to_upload.upload_file())

    @tag('test_file_upload_upload')
    def test_file_upload_and_play1(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        new_file_to_upload = TransactionLoads(path=transaction_file_path)

        for tx_record in new_file_to_upload.transaction_objs:
            tx_record.delete()
        self.assertTrue(new_file_to_upload.upload_file())

    @tag('test_file_upload_on_delete')
    def test_file_upload_on_delete(self):
        name = self.fake.name()
        TestModel.objects.using('client').create(f1=name)
        TestModel.objects.using('client').create(f1=self.fake.name())
        # Dump transaction to create records
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        model_count = TestModel.objects.filter(f1=name).count()
        self.assertEqual(model_count, 1)

        test_model = TestModel.objects.using('client').get(f1=name)
        test_model.delete()
        sleep(1)
        # Dump transaction to delete a record
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        test_model = TestModel.objects.filter(f1=name).count()
        self.assertEqual(test_model, 0)

    @tag('test_file_upload_on_delete1')
    def test_file_upload_on_delete1(self):
        name = self.fake.name()
        name1 = self.fake.name()
        TestModel.objects.using('client').create(f1=name)
        TestModel.objects.using('client').create(f1=name1)

        # Dump transaction to create records
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        model_count = TestModel.objects.filter(f1=name).count()
        self.assertEqual(model_count, 1)

        test_model = TestModel.objects.using('client').get(f1=name)
        test_model.delete()

        test_model = TestModel.objects.using('client').get(f1=name1)
        test_model.delete()
        sleep(1)
        # Dump transaction to delete a record
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        model_count = TestModel.objects.all().count()
        self.assertEqual(model_count, 0)

    @tag('test_file_upload_on_failed_play_previous')
    def test_file_upload_on_failed_play_previous(self):
        name = self.fake.name()
        name1 = self.fake.name()
        TestModel.objects.using('client').create(f1=name)
        TestModel.objects.using('client').create(f1=name1)

        # Dump transaction to create records
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        sync_report = SyncReport()
        data = sync_report.report_data[0][0]
        self.assertEqual(data.get('total_consumed'), 4)
        self.assertEqual(data.get('total_not_consumed'), 0)
        self.assertEqual(UploadTransactionFile.objects.all().count(), 1)

        inc = IncomingTransaction.objects.all().first()
        inc.is_consumed = False
        inc.save()

        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())
        sleep(1)
        # Dump transaction to delete a record
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        sync_report = SyncReport()
        data = sync_report.report_data[0][0]
        self.assertEqual(data.get('total_consumed'), 3)
        self.assertEqual(data.get('total_not_consumed'), 5)
        self.assertEqual(UploadTransactionFile.objects.all().count(), 2)

        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())
        sleep(1)
        # Dump transaction to delete a record
        path = os.path.join(settings.MEDIA_ROOT, "transactions", "outgoing")
        tx_dumps = TransactionDumps(path, using='client', hostname="010")
        self.assertTrue(tx_dumps.is_exported_to_json)

        transaction_file_path = os.path.join(tx_dumps.path, tx_dumps.filename)
        TransactionLoads(path=transaction_file_path).upload_file()

        sync_report = SyncReport()
        data = sync_report.report_data[0][0]
        self.assertEqual(data.get('total_consumed'), 3)
        self.assertEqual(data.get('total_not_consumed'), 9)
        self.assertEqual(UploadTransactionFile.objects.all().count(), 3)
