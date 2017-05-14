import os

from paramiko.util import ClosingContextManager

from django.apps import apps as django_apps


class SFTPClientError(Exception):
    pass


class SFTPClient(ClosingContextManager):

    """Wraps open_sftp with folder defaults for copy (and archive).

    Copy is three steps, put, rename, then archive locally.
    """

    def __init__(self, ssh_conn=None, dst_path=None, dst_tmp_path=None, src_path=None):
        app_config = django_apps.get_app_config('edc_sync_files')
        self.src_path = src_path or app_config.source_folder
        self.dst_path = dst_path or app_config.destination_folder
        self.dst_tmp_path = dst_tmp_path or app_config.destination_tmp_folder
        self.ssh_conn = ssh_conn
        self.sftp = None

    def connect(self):
        self.sftp = self.ssh_conn.open_sftp()
        return self

    def close(self):
        self.sftp.close()

    def copy(self, filename=None):
        """Put on destination as a temp file, rename on the destination.
        """
        dst_tmp = os.path.join(self.dst_tmp_path, filename)
        dst_final = os.path.join(self.dst_path, filename)
        src = os.path.join(self.src_path, filename)
        if not os.path.exists():
            raise SFTPClientError(f'Source file does not exist. Got \'{src}\'')
        try:
            self.sftp.put(
                src, dst_tmp, callback=self.progress, confirm=True)
        except IOError as e:
            raise SFTPClientError(
                f'IOError. Failed to copy {dst_tmp}. Got {e}')
        try:
            self.sftp.rename(dst_tmp, dst_final)
        except IOError as e:
            raise SFTPClientError(
                f'IOError. Failed to rename {dst_tmp}. Got {e}')
        return True
