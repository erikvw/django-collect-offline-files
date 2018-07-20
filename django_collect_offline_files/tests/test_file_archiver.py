import os
import tempfile

from django.apps import apps as django_apps
from django.test import TestCase, tag

from ..transaction import FileArchiver, FileArchiverError


class TestFileArchiver(TestCase):

    def test_no_parameters(self):
        self.assertRaises(FileArchiverError, FileArchiver)

    def test_custom_paths_same(self):
        src_path = tempfile.gettempdir()
        dst_path = tempfile.gettempdir()
        self.assertRaises(
            FileArchiverError, FileArchiver, src_path=src_path, dst_path=dst_path)

    def test_custom_paths_do_not_exist(self):
        src_path = tempfile.gettempdir()
        dst_path = os.path.join(tempfile.gettempdir(), 'blah1')
        self.assertRaises(
            FileArchiverError, FileArchiver, src_path=src_path, dst_path=dst_path)
        src_path = os.path.join(tempfile.gettempdir(), 'blah1')
        dst_path = tempfile.gettempdir()
        self.assertRaises(
            FileArchiverError, FileArchiver, src_path=src_path, dst_path=dst_path)

    def test_custom_paths_exist(self):
        src_path = tempfile.gettempdir()
        dst_path = os.path.join(tempfile.gettempdir(), 'blah')
        if not os.path.exists(dst_path):
            os.mkdir(dst_path)
        try:
            FileArchiver(src_path=src_path, dst_path=dst_path)
        except FileArchiverError:
            self.fail('FileArchiverError unexpectedly raises')
        os.rmdir(dst_path)

    def test_archive_file_with_app_config_folders(self):
        app_config = django_apps.get_app_config('django_collect_offline_files')
        file_archiver = FileArchiver(
            src_path=app_config.outgoing_folder,
            dst_path=app_config.archive_folder)
        _, p = tempfile.mkstemp(dir=file_archiver.src_path)
        filename = os.path.basename(p)
        file_archiver.archive(filename)
        self.assertTrue(os.path.exists(
            os.path.join(file_archiver.dst_path, filename)))
