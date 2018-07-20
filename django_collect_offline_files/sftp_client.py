import logging
import os
import sys

from paramiko.util import ClosingContextManager

logger = logging.getLogger('django_collect_offline_files')


class SFTPClientError(Exception):
    pass


class SFTPClient(ClosingContextManager):

    """Wraps open_sftp with folder defaults for copy.

    Copy is two steps; put then rename.
    """

    def __init__(self, src_path=None, dst_path=None, dst_tmp=None,
                 verbose=None, **kwargs):
        self.src_path = src_path
        self.dst_tmp = dst_tmp
        self.dst_path = dst_path
        self._sftp_client = None
        self.verbose = verbose
        self.progress = 0

    def connect(self, ssh_conn=None):
        self._sftp_client = ssh_conn.open_sftp()
        return self

    def close(self):
        self._sftp_client.close()

    def copy(self, filename=None):
        """Puts on destination as a temp file, renames on
        the destination.
        """
        dst = os.path.join(self.dst_path, filename)
        src = os.path.join(self.src_path, filename)
        dst_tmp = os.path.join(self.dst_tmp, filename)
        self.put(src=src, dst=dst_tmp,
                 callback=self.update_progress, confirm=True)
        self.rename(src=dst_tmp, dst=dst)

    def put(self, src=None, dst=None, callback=None, confirm=None):
        if not os.path.exists(src):
            raise SFTPClientError(f'Source file does not exist. Got \'{src}\'')
        self.progress = 0
        try:
            self._sftp_client.put(src, dst, callback=callback, confirm=confirm)
        except IOError as e:
            raise SFTPClientError(
                f'IOError. Failed to copy {src}.') from e
        if self.verbose:
            logger.info(f'Copied {src} to {dst}')
            sys.stdout.write('\n')

    def rename(self, src=None, dst=None):
        try:
            self._sftp_client.rename(src, dst)
        except IOError as e:
            raise SFTPClientError(
                f'IOError. Failed to rename {src} to {dst}.') from e

    def update_progress(self, sent_bytes, total_bytes):
        self.progress = (sent_bytes / total_bytes) * 100
        if self.verbose:
            sys.stdout.write(f'Progress {self.progress}% \r')
