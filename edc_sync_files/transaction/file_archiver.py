import os
import shutil

from django.apps import apps as django_apps


class FileArchiverError(Exception):
    pass


class FileArchiver:

    def __init__(self, src_path=None, archive_path=None, **kwargs):
        app_config = django_apps.get_app_config('edc_sync_files')
        self.src_path = src_path or app_config.source_folder
        self.archive_path = archive_path or app_config.archive_folder
        if not os.path.exists(self.src_path):
            raise FileArchiverError(
                f'Source path does not exist. Got {self.src_path}')
        if not os.path.exists(self.archive_path):
            raise FileArchiverError(
                f'Archive path does not exist. Got {self.archive_path}')
        if self.src_path == self.archive_path:
            raise FileArchiverError(
                f'Source folder same as archive folder!. Got {self.src_path}')

    def archive(self, filename):
        shutil.move(
            os.path.join(self.src_path, filename),
            os.path.join(self.archive_path, filename))
