from django.apps import apps as django_apps

from edc_base.utils import get_utcnow

from ..ssh_client import SSHClient, SSHClientError
from ..sftp_client import SFTPClient, SFTPClientError
from .file_archiver import FileArchiver


class TransactionFileSenderError(Exception):
    pass


class TransactionFileSender:

    def __init__(self, history_model=None, using=None, update_history_model=None, **kwargs):
        app_config = django_apps.get_app_config('edc_sync_files')
        self.using = using
        self.update_history_model = True if update_history_model is None else update_history_model
        kwargs.update(remote_host=kwargs.get(
            'remote_host', app_config.remote_host))
        kwargs.update(src_path=kwargs.get(
            'src_path', app_config.source_folder))
        kwargs.update(dst_path=kwargs.get(
            'dst_path', app_config.destination_folder))
        kwargs.update(dst_tmp_path=kwargs.get(
            'dst_tmp_path', app_config.destination_tmp_folder))
        self.file_archiver = FileArchiver(**kwargs)
        self.history_model = history_model
        self.ssh_client = SSHClient(**kwargs)
        self.sftp_client = SFTPClient(**kwargs)
        self.src_path = self.sftp_client.src_path
        self.dst_path = self.sftp_client.dst_path

    def send(self, filenames=None):
        try:
            with self.ssh_client.connect() as ssh_conn:
                with self.sftp_client.connect(ssh_conn) as sftp_conn:
                    for filename in filenames:
                        sftp_conn.copy(filename=filename)
                        self.file_archiver.archive(filename=filename)
                        if self.update_history_model:
                            self.update_history(filename=filename)
        except SSHClientError as e:
            raise TransactionFileSenderError(f'SSHClientError. Got {e}')
        except SFTPClientError as e:
            raise TransactionFileSenderError(f'SFTPClientError. Got {e}')
        return filenames

    def update_history(self, filename=None):
        try:
            obj = self.history_model.objects.using(
                self.using).get(filename=filename)
        except self.history_model.DoesNotExist as e:
            raise TransactionFileSenderError(
                f'History does not exist for file \'{filename}\'. Got {e}')
        else:
            obj.sent = True
            obj.sent_datetime = get_utcnow()
            obj.save()
