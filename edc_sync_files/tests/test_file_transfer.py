import os
import json

from django.conf import settings
from django.test.testcases import TestCase

from edc_sync_files.file_transfer import FileTransfer, FileConnector
from edc_sync_files.constants import LOCALHOST, REMOTE
from edc_sync_files.models import History


class TestFileTransfer(TestCase):

    def setUp(self):
        self.transfer = FileTransfer(device_ip='127.0.0.1')
        self.source_folder = os.path.join(settings.BASE_DIR, "tests", "media", "source_folder")
        self.destination_folder = os.path.join(settings.BASE_DIR, "tests", "media", "destination_folder")

    def test_connect_to_localhost(self):
        """Assert  Connection to localhost """
        self.assertTrue(self.transfer.connect_to_device(LOCALHOST))

    def test_connect_to_remote_device(self):
        """ Assert Connection to remote machine """
        self.assertTrue(self.transfer.connect_to_device(REMOTE))

    def test_media_files(self):
        """ Connect to remote device then return filenames within source dir """
        transfer = FileTransfer(
            user='tsetsiba', device_ip='127.0.0.1', source_folder=self.source_folder, destination_folder=self.destination_folder)
        self.assertEqual(len(transfer.media_file_attributes()), 3)

    def test_copy_media_file(self):
        """ Connect to remote device then return filenames within source dir """
        transfer = FileTransfer(
            filename='media_a.png',
            user='tsetsiba', device_ip='127.0.0.1', source_folder=self.source_folder, destination_folder=self.destination_folder)
        transfer.copy_media_file()
        self.assertEqual(History.objects.all().count(), 1)

    def test_count_on_media_transfer(self):
        """ Assert how many media files to send base on history table."""
        sent_media = ['media_a', 'media_b']
        localhost_media_files = ['media_a', 'media_b', 'media_c', 'media_d']
        media_to_transfer = []
        for filename in localhost_media_files:
            if filename in sent_media:
                continue
            media_to_transfer.append(filename)
        self.assertEqual(len(media_to_transfer), 2)
        for f in ['media_c', 'media_d']:
            self.assertIn(f, media_to_transfer)

        sent_media = ['media_a', 'media_b', 'media_c']
        localhost_media_files = ['media_a', 'media_b', 'media_c', 'media_d']
        media_to_transfer = []
        for filename in localhost_media_files:
            if filename in sent_media:
                continue
            media_to_transfer.append(filename)
        self.assertEqual(len(media_to_transfer), 1)

        for f in ['media_d']:
            self.assertIn(f, media_to_transfer)
