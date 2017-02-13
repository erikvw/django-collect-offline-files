import os

from django.conf import settings
from django.test.testcases import TestCase

from edc_sync_files.file_transfer import FileConnector, FileTransfer
from edc_sync_files.constants import LOCALHOST, REMOTE
from edc_sync_files.models import History


class TestFileTransfer(TestCase):

    def setUp(self):
        self.transfer = FileConnector(host='127.0.0.1')
        self.source_folder = os.path.join(
            settings.BASE_DIR, "tests", "media", "source_folder")
        self.destination_folder = os.path.join(
            settings.BASE_DIR, "tests", "media", "destination_folder")

    def test_connect_localhost(self):
        """Assert  Connection to localhost. """
        self.assertTrue(self.transfer.connect(LOCALHOST))

    def test_connect_remotely(self):
        """ Assert Connection to remote machine."""
        self.assertTrue(self.transfer.connect(REMOTE))

    def test_files(self):
        """ Connect to remote device then return filenames within source dir. """
        transfer = FileTransfer(
            user='tsetsiba', device_ip='127.0.0.1',
            source_folder=self.source_folder,
            destination_folder=self.destination_folder)
        self.assertEqual(len(transfer.files_dict()), 3)

    def test_copy_files(self):
        """ Connect to remote device then return filenames within source dir """
        file_connector = FileConnector()
        transfer = FileTransfer(file_connector=file_connector)
        transfer.copy_files()
        self.assertEqual(History.objects.all().count(), 1)

    def test_count_files(self):
        """ Assert how many media files to send base on history table."""
        pass
