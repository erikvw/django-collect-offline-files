from edc_base.utils import get_utcnow

from ..ssh_client import SSHClient, SSHClientError
from ..sftp_client import SFTPClient, SFTPClientError
from .file_archiver import FileArchiver


class TransactionFileSenderError(Exception):
    pass


class TransactionFileSender:

    def __init__(self, remote_host=None, username=None, src_path=None, dst_tmp=None,
                 dst_path=None, archive_path=None, history_model=None, using=None,
                 update_history_model=None, **kwargs):
        self.using = using
        self.update_history_model = (
            True if update_history_model is None else update_history_model)
        self.file_archiver = FileArchiver(
            src_path=src_path, dst_path=archive_path)
        self.history_model = history_model
        self.ssh_client = SSHClient(
            username=username, remote_host=remote_host, **kwargs)
        self.sftp_client = SFTPClient(
            src_path=src_path, dst_tmp=dst_tmp, dst_path=dst_path, **kwargs)

    def send(self, filenames=None):
        """Sends the file to the remote host and archives
        the sent file locally.
        """
        try:
            with self.ssh_client.connect() as ssh_conn:
                with self.sftp_client.connect(ssh_conn) as sftp_conn:
                    for filename in filenames:
                        sftp_conn.copy(filename=filename)
                        self.archive(filename=filename)
                        if self.update_history_model:
                            self.update_history(filename=filename)
        except SSHClientError as e:
            raise TransactionFileSenderError(e) from e
        except SFTPClientError as e:
            raise TransactionFileSenderError(e) from e
        return filenames

    def update_history(self, filename=None):
        try:
            obj = self.history_model.objects.using(
                self.using).get(filename=filename)
        except self.history_model.DoesNotExist as e:
            raise TransactionFileSenderError(
                f'History does not exist for file \'{filename}\'. Got {e}') from e
        else:
            obj.sent = True
            obj.sent_datetime = get_utcnow()
            obj.save()

    def archive(self, filename):
        self.file_archiver.archive(filename=filename)
