import os
import shutil

from django.apps import apps as django_apps

from edc_base.utils import get_utcnow

from .constants import EXPORT_BATCH, SEND_FILE, CONFIRM_BATCH, PENDING_FILES
from .sftp_client import SFTPClient, SFTPClientError
from .ssh_client import SSHClient, SSHClientError
from .transaction import TransactionExporter, TransactionExporterError


class ViewActionError(Exception):
    pass


class ViewActions:
    def __init__(self, using=None, remote_host=None, trusted_host=None):
        app_config = django_apps.get_app_config('edc_sync_files')
        self.action_labels = [
            EXPORT_BATCH, SEND_FILE, CONFIRM_BATCH, PENDING_FILES]
        self.archive_path = app_config.archive_folder
        self.using = using
        self.data = dict(errmsg=None, batch_id=None,
                         last_sent_file=None, last_archived_file=None)
        self.tx_exporter = TransactionExporter(using=self.using)
        self.history_model = self.tx_exporter.history_model
        self.pending_filenames = [obj.filename for obj in self.tx_exporter.history_model.objects.using(
            self.using).filter(sent=False).order_by('-created')]
        self.recently_sent_filenames = [obj.filename for obj in self.tx_exporter.history_model.objects.using(
            self.using).filter(sent=True).order_by('-sent_datetime')[0:20]]
        self.remote_host = remote_host or app_config.remote_host

    def action(self, label=None, **kwargs):
        result = None
        if label == EXPORT_BATCH:
            result = self._export_batch()
        elif label == SEND_FILE:
            result = self._send_file()
        elif label == CONFIRM_BATCH:
            result = self._send_file()
        elif label == PENDING_FILES:
            result = dict(pending_files=self.pending_filenames)
        else:
            raise ViewActionError(f'Invalid action. Got {label}')
        return result

    def _export_batch(self):
        try:
            history = self.tx_exporter.export_batch()
        except TransactionExporterError as e:
            self.data.update(errmsg=str(e))
        else:
            if history:
                self.data.update(batch_id=history.batch_id)
                self.pending_filenames.append(history.filename)

    def _send_file(self):
        filename = self.pending_filenames.pop(0)
        if filename:
            ssh_client = SSHClient(
                remote_host=self.remote_host, trusted_host=True)
            try:
                with ssh_client.connect() as ssh_conn:
                    sftp_client = SFTPClient(ssh_conn=ssh_conn)
                    with sftp_client.connect() as sftp_conn:
                        sftp_conn.copy(filename=filename)
                        src = os.path.join(sftp_client.src_path, filename)
                        dst = os.path.join(self.archive_path, filename)
                        shutil.move(src, dst)
                        self._update_history(filename=filename)
                        self.data.update(last_sent_file=src)
                        self.data.update(last_archived_file=dst)
            except (SSHClientError, SFTPClientError) as e:
                self.data.update(errmsg=str(e))
            except IndexError:
                pass

    def _update_history(self, filename=None):
        obj = self.tx_exporter.history_model.objects.using(
            self.using).get(filename=filename)
        obj.sent = True
        obj.sent_datetime = get_utcnow()
        obj.save()
