import os

from faker import Faker
from django.apps import apps as django_apps
from django.test.testcases import TestCase
from django.test.utils import tag

from ..event_handlers import TransactionFileEventHandler
from ..models import ImportedTransactionFileHistory
from ..transaction import TransactionExporter
from .models import TestModel

fake = Faker()


class Event:
    def __init__(self, filename=None):
        self.event_type = 'created'
        self.src_path = os.path.join(django_apps.get_app_config(
            'edc_sync_files').destination_folder, filename)


class TestFileEventHandler(TestCase):

    def test_create(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(using='client')
        # Uploaded by watchdog
        event_handler = TransactionFileEventHandler()
        event_handler.process(
            Event(filename=tx_exporter.filename),
            check_device=False,
            check_hostname=False,
            verbose=False)
        self.assertGreater(event_handler.consumed, 0)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 1)
        self.assertEqual(TestModel.objects.all().count(), 2)

    def test_create_many(self):
        filenames = []
        for _ in range(0, 5):
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
            self.assertEqual(TestModel.objects.all().count(), 0)
            tx_exporter = TransactionExporter(using='client')
            filenames.append(tx_exporter.filename)
        # Uploaded by watchdog
        event_handler = TransactionFileEventHandler()
        for filename in filenames:
            event_handler.process(
                Event(filename=filename),
                check_device=False,
                check_hostname=False,
                verbose=False)
            self.assertGreater(event_handler.consumed, 0)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 5)
        self.assertEqual(TestModel.objects.all().count(), 10)

    def test_create_and_delete(self):
        obj1 = TestModel.objects.using('client').create(f1=fake.name())
        obj2 = TestModel.objects.using('client').create(f1=fake.name())
        obj1.delete()
        obj2.delete()
        self.assertEqual(TestModel.objects.all().count(), 0)
        tx_exporter = TransactionExporter(using='client')
        # Uploaded by watchdog
        event_handler = TransactionFileEventHandler()
        event_handler.process(
            Event(filename=tx_exporter.filename),
            check_device=False,
            check_hostname=False,
            verbose=False)
        self.assertGreater(event_handler.consumed, 0)
        self.assertEqual(
            ImportedTransactionFileHistory.objects.all().count(), 1)
        self.assertEqual(TestModel.objects.all().count(), 0)
