from faker import Faker
from time import sleep

from django.test import TestCase, tag

from ..transaction import DumpToUsb, TransactionLoadUsbFile
from .models import TestModel


class TestTransactionLoadUsbFile(TestCase):

    def setUp(self):
        self.fake = Faker()

    @tag('test_dump_to_usb')
    def test_dump_to_usb(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        usb_dump = DumpToUsb(using='client')
        self.assertTrue(usb_dump.is_dumped_to_usb)

    @tag('test_load_usb_file')
    def test_load_usb_file(self):
        TestModel.objects.using('client').create(f1=self.fake.name())
        TestModel.objects.using('client').create(f1=self.fake.name())

        # Dump transaction
        usb_dump = DumpToUsb(using='client')
        self.assertTrue(usb_dump.is_dumped_to_usb)

        load_usb_file = TransactionLoadUsbFile()
        self.assertTrue(
            load_usb_file.is_usb_transaction_file_loaded)
        self.assertTrue(
            load_usb_file.is_archived)

    @tag('test_load_usb_multiple_files')
    def test_load_usb_multiple_files(self):
        for _ in range(2):
            TestModel.objects.using('client').create(f1=self.fake.name())
            TestModel.objects.using('client').create(f1=self.fake.name())
            sleep(2)
            # Dump transaction
            usb_dump = DumpToUsb(using='client')
            self.assertTrue(usb_dump.is_dumped_to_usb)

        load_usb_file = TransactionLoadUsbFile()
        self.assertTrue(
            load_usb_file.is_usb_transaction_file_loaded)
        for tx_file in load_usb_file.processed_usb_files:
            self.assertIn('Uploaded successfully', tx_file.get('reason'))
