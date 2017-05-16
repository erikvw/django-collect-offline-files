import os

from django.test import TestCase, tag

from ..transaction import FileArchiver, FileArchiverError
import tempfile


@tag('archive')
class TestFileArchiver(TestCase):

    def test_default_paths(self):
        try:
            FileArchiver()
        except FileArchiverError:
            self.fail('FileArchiverError unexpectedly raised')

    def test_custom_paths_same(self):
        src_path = tempfile.gettempdir()
        archive_path = tempfile.gettempdir()
        self.assertRaises(
            FileArchiverError, FileArchiver, src_path=src_path, archive_path=archive_path)

    def test_custom_paths_do_not_exist(self):
        src_path = tempfile.gettempdir()
        archive_path = os.path.join(tempfile.gettempdir(), 'blah1')
        self.assertRaises(
            FileArchiverError, FileArchiver, src_path=src_path, archive_path=archive_path)
        src_path = os.path.join(tempfile.gettempdir(), 'blah1')
        archive_path = tempfile.gettempdir()
        self.assertRaises(
            FileArchiverError, FileArchiver, src_path=src_path, archive_path=archive_path)

    def test_custom_paths_exist(self):
        src_path = tempfile.gettempdir()
        archive_path = os.path.join(tempfile.gettempdir(), 'blah')
        if not os.path.exists(archive_path):
            os.mkdir(archive_path)
        try:
            FileArchiver(src_path=src_path, archive_path=archive_path)
        except FileArchiverError:
            self.fail('FileArchiverError unexpectedly raises')
        os.rmdir(archive_path)

    def test_archive_file(self):
        file_archiver = FileArchiver()
        _, p = tempfile.mkstemp(dir=file_archiver.src_path)
        filename = os.path.basename(p)
        file_archiver.archive(filename)
        self.assertTrue(os.path.exists(
            os.path.join(file_archiver.archive_path, filename)))
