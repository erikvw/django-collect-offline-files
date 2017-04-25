import socket
import os.path
import shutil

from hurry.filesize import size
from os.path import join

from django.apps import apps as django_apps

from edc_base.utils import get_utcnow

from ..constants import REMOTE
from ..models import History
from ..transaction import transaction_messages
from .ssh_connection_mixin import SSHConnectMixin


class FileConnector(SSHConnectMixin):
    """Connects to the remote machine using (ssh key pair.).
       1. Copies files from source folder to destination folder.
    """

    def __init__(self, remote_host=None, source_folder=None,
                 destination_folder=None, archive_folder=None):
        self.trusted_host = True
        app_config = django_apps.get_app_config('edc_sync_files')
        self.progress_status = None
        self.remote_host = remote_host or app_config.remote_host
        self.user = app_config.user
        self.source_folder = source_folder or app_config.source_folder
        self.destination_tmp_folder = app_config.destination_tmp_folder
        self.destination_folder = (
            destination_folder or app_config.destination_folder)
        self.archive_folder = archive_folder or app_config.archive_folder

    def connected(self):
        client = self.connect(REMOTE)
        connected = False
        if client:
            ssh = client.open_sftp()
            connected = True if ssh else False
        if connected:
            client.close()
        return connected

    def progress(self, sent_bytes, total_bytes):
        self.progress_status = (sent_bytes / total_bytes) * 100
        print("Progress ", self.progress_status, "%")

    def copy(self, filename):
        """ Copy file from  source folder to destination folder in the
            current filesystem or to remote file system."""
        client = self.connect(REMOTE)
        with client.open_sftp() as host_sftp:
            try:
                destination_tmp_file = os.path.join(
                    self.destination_tmp_folder, filename)
                destination_file = os.path.join(
                    self.destination_folder, filename)
                sent = True
                source_filename = os.path.join(self.source_folder, filename)
                try:
                    host_sftp.put(
                        source_filename,
                        destination_tmp_file,
                        callback=self.progress, confirm=True)
                    transaction_messages.add_message(
                        'success', 'File {} sent to the'
                        ' server successfully.'.format(source_filename))
                    host_sftp.rename(
                        destination_tmp_file,
                        destination_file)
                except IOError as e:
                    sent = False
                    transaction_messages.add_message(
                        'error', 'IOError Got {} . Sending {}'.format(e, destination_tmp_file))
                    return False

                if sent:
                    self.update_history(filename, sent=sent)
                    transaction_messages.add_message(
                        'success', 'History record created for {}.'.format(source_filename))
            finally:
                host_sftp.close()
                client.close()
        return sent

    def archive(self, filename):
        """ Move file from source_folder to archive folder """
        archived = True
        try:
            source_filename = join(self.source_folder, filename)
            destination_filename = join(self.archive_folder, filename)
            shutil.move(source_filename, destination_filename)
            transaction_messages.add_message(
                'success', 'Archived successfully {}.'.format(source_filename))
        except FileNotFoundError as e:
            archived = False
            transaction_messages.add_message(
                'error', 'FileNotFoundError Got {}'.format(str(e)))
        return archived

    def update_history(self, filename, sent=False):
        history = History.objects.get(filename=filename)
        history.sent = sent
        history.sent_datetime = get_utcnow()
        history.save()
        return history

    @property
    def hostname(self):
        device = self.connect(REMOTE)
        _, stdout, _ = device.exec_command('hostname')
        hostname = stdout.read()
        if isinstance(hostname, bytes):
            hostname = hostname.decode('utf-8')
        device.close()
        return hostname

    @property
    def localhost_hostname(self):
        return socket.gethostname()
