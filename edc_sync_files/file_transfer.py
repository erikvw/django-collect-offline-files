import getpass
import os.path
import paramiko

from hurry.filesize import size

from datetime import datetime
from django.apps import apps as django_apps

from edc_sync_files.models import history
from .constants import REMOTE, LOCALHOST


class FileConnector(object):
    """Connects to the file system given (host & password) or (ssh key pair.).
       1. Copies files from source folder to destination folder in file system.
       2. Copies files from file system to remote file system.
    """

    def __init__(self, host=None, password=None, source_folder=None,
                 destination_folder=None, archive_folder=None):

        self.host = host or self.edc_sync_file.host
        self.password = password or self.edc_sync_file.password
        self.user = self.edc_sync_file.user
        self.source_folder = source_folder or self.edc_sync_file.source_folder
        self.destination_folder = destination_folder or self.edc_sync_file.destination_folder
        self.archive_folder = archive_folder or self.edc_sync_file.archive_folder
        self.host_sftp = self.connect(REMOTE)
        self.local_sftp = self.connect(LOCALHOST)

    @property
    def edc_sync_file(self):
        return django_apps.get_app_config('edc_sync_files')

    def connect(self, host):
        device, username = (
            self.host, self.user) if host == REMOTE else (
                LOCALHOST, getpass.getuser())
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(device, username=username, look_for_keys=True, timeout=30)
        client = client.open_sftp()
        return client

    def copy(self, filename):
        """ Copy file from  source folder to destination folder in the
            current filesystem or to remote file system."""
        self.host_sftp.put(
            os.path.join(self.source_folder, filename),
            os.path.join(self.destination_folder, filename))
        #  create a record on successful transfer
        self.create_history(filename)

    def archive(self, filename):
        """ Move file from source_folder to archive folder """
        filename = os.path.join(self.source_folder, filename)
        stdin, stdout, stderr = self.localhost.exec_command(
            "cd {} ; mv {} {}".format(
                self.source_folder, filename, self.archive_folder))
        return (stdin, stdout, stderr)

    def create_history(self, filename):
        history = history.objects.create(
            filename=filename,
            acknowledged=True,
            ack_datetime=datetime.today(),
            hostname=self.hostname
        )
        return history

    def close(self):
        """ Close file system connection. """
        self.host_sftp.close()
        self.local_sftp.close()

    @property
    def hostname(self):
        device = self.connect_to_device(REMOTE)
        _, stdout, _ = device.exec_command('hostname')
        hostname = stdout.read()
        if isinstance(hostname, bytes):
            hostname = hostname.decode('utf-8')
        device.close()
        return hostname


class FileTransfer(object):
    """Transfer a list of files to the remote host or within host.
    """

    def __init__(self, file_connector=None):
        self.file_connector = file_connector or FileConnector()
        self.archive = False

    @property
    def edc_sync_app_config(self):
        return django_apps.get_app_config('edc_sync_files')

    @property
    def files(self):
        host = self.file_connector.connect(LOCALHOST)
        files = []
        if host:
            files = host.listdir(self.file_connector.source_folder)
            try:
                files.remove('.DS_Store')
            except ValueError:
                pass
            host.close()
            host.close()
        return files

    def files_dict(self):
        file_attrs = []
        host = self.connect_to_device(REMOTE)
        if host:
            for filename in self.files():
                source_filename = os.path.join(self.source_folder, filename)
                file_attr = host.lstat(source_filename)
                data = dict({
                    'filename': filename,
                    'filesize': size(file_attr.st_size),
                })
                file_attrs.append(data)
        return file_attrs

    def copy_files(self):
        """ Copies the files from the remote machine into local machine. """
        try:
            for f in self.files:
                self.file_connector.copy(f.get('filename'))
                if self.archive:
                    self.file_connector.archive(f.get('filename'))
            self.file_connector.close()
        except paramiko.SSHException:
            return False
        return True
