import socket
import os.path
import paramiko
import shutil
from os.path import join

from hurry.filesize import size
from os import listdir


from datetime import datetime
from django.apps import apps as django_apps


from edc_base.utils import get_utcnow

from .transaction_messages import transaction_messages
from ..models import History
from ..constants import REMOTE, LOCALHOST
from .mixins import SSHConnectMixin


class FileConnector(SSHConnectMixin):
    """Connects to the file system given (host & password) or (ssh key pair.).
       1. Copies files from source folder to destination folder in file system.
       2. Copies files from file system to remote file system.
    """

    def __init__(self, host=None, password=None, source_folder=None,
                 destination_folder=None, archive_folder=None):
        self.trusted_host = True
        edc_sync_file_app = django_apps.get_app_config('edc_sync_files')
        self.progress_status = None
        self.host = host or edc_sync_file_app.host
        self.password = password or edc_sync_file_app.password
        self.user = edc_sync_file_app.user
        self.source_folder = source_folder or edc_sync_file_app.source_folder
        self.destination_folder = destination_folder or edc_sync_file_app.destination_folder
        self.archive_folder = archive_folder or edc_sync_file_app.archive_folder

    def connected(self):
        ssh = None
        client = self.connect(REMOTE)
        if client:
            ssh = client.open_sftp()
        connected = True if ssh else False
        if connected:
            ssh.close()
        return connected

    def progress(self, sent_bytes, total_bytes):
        self.progress_status = (sent_bytes / total_bytes) * 100
        print("Progress ", self.progress_status, "%")

    def copy(self, filename):
        """ Copy file from  source folder to destination folder in the
            current filesystem or to remote file system."""
        client = self.connect(REMOTE)
        host_sftp = client.open_sftp()
        destination_file = os.path.join(self.destination_folder, filename)
        sent = True
        try:
            sent_file = host_sftp.put(
                os.path.join(self.source_folder, filename),
                destination_file, callback=self.progress, confirm=True)
        except IOError as e:
            sent = False
            transaction_messages.add_message(
                'error', 'IOError Got {} . Sending {}'.format(e, destination_file))
            return False
        received_file = host_sftp.lstat(destination_file)
        print(received_file.st_size, "received file", sent_file.st_size, "sent file")
        #  create a record on successful transfer
        if sent:
            self.create_history(filename)
        return sent

    def archive(self, filename):
        """ Move file from source_folder to archive folder """
        archived = True
        try:
            source_filename = join(self.source_folder, filename)
            destination_filename = join(self.archive_folder, filename)
            shutil.move(source_filename, destination_filename)
        except FileNotFoundError as e:
            archived = False
            transaction_messages.add_message(
                'error', 'FileNotFoundError Got {}'.format(str(e)))
        return archived

    def create_history(self, filename):
        history = History.objects.create(
            filename=filename,
            acknowledged=True,
            ack_datetime=datetime.today(),
            hostname=self.hostname
        )
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


class FileTransfer(object):
    """Transfer a list of files to the remote host or within host.
    """

    def __init__(self, file_connector=None):
        self.file_connector = file_connector or FileConnector()

    @property
    def files(self):
        files = listdir(self.file_connector.source_folder)
        try:
            files.remove('.DS_Store')
        except ValueError:
            pass
        return files

    @property
    def files_dict(self):
        file_attrs = []
        client = self.file_connector.connect(LOCALHOST)
        host = client.open_sftp()
        if host:
            for filename in self.files:
                source_filename = os.path.join(
                    self.file_connector.source_folder, filename)
                file_attr = host.lstat(source_filename)
                data = dict({
                    'filename': filename,
                    'filesize': size(file_attr.st_size),
                })
                file_attrs.append(data)
        return file_attrs

    def copy_files(self, filename):
        """ Copies the files from source folder to destination folder. """
        copied = False
        for f in self.files_dict:
            if f.get('filename') == filename:
                copied = self.file_connector.copy(f.get('filename'))
        return copied

    def archive(self, filename):
        return self.file_connector.archive(filename)

    def approve_sent_file(self, filename, approval_code):
        try:
            sent_file_history = History.objects.get(filename=filename)
            sent_file_history.approval_code = approval_code
            sent_file_history.save()
        except History.DoesNotExist:
            pass
