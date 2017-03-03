import getpass
import os.path
import paramiko

from hurry.filesize import size

from datetime import datetime
from django.apps import apps as django_apps

from edc_base.utils import get_utcnow
from edc_sync_files.models import History

from .constants import REMOTE, LOCALHOST


class FileConnector(object):
    """Connects to the file system given (host & password) or (ssh key pair.).
       1. Copies files from source folder to destination folder in file system.
       2. Copies files from file system to remote file system.
    """

    def __init__(self, host=None, password=None, source_folder=None,
                 destination_folder=None, archive_folder=None):
        self.progress_status = None
        self.host = host or self.edc_sync_file.host
        self.password = password or self.edc_sync_file.password
        self.user = self.edc_sync_file.user
        self.source_folder = source_folder or self.edc_sync_file.source_folder
        self.destination_folder = destination_folder or self.edc_sync_file.destination_folder
        self.archive_folder = archive_folder or self.edc_sync_file.archive_folder
        self.host_sftp = None  # 
        self.local_sftp = None  # self.connect(LOCALHOST)

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
        return client

    def progress(self, sent_bytes, total_bytes):
        self.progress_status = (sent_bytes / total_bytes) * 100
        print("Progress ", self.progress_status, "%")

    def copy(self, filename):
        """ Copy file from  source folder to destination folder in the
            current filesystem or to remote file system."""
        client = self.connect(REMOTE)
        self.host_sftp = client.open_sftp()
        temp_des = '/Users/django/source/bcpp/media/transactions/outgoing/' + filename
        destination_file = os.path.join(self.destination_folder, filename)
        sent_file = self.host_sftp.put(
            os.path.join(self.source_folder, filename),
            temp_des, callback=self.progress, confirm=True)
        #  create a record on successful transfer
        # self.create_history(filename)
        self.host_sftp.close()

    def archive(self, filename):
        """ Move file from source_folder to archive folder """
        client = self.connect(LOCALHOST)
        filename = os.path.join(self.source_folder, filename)
        stdin, stdout, stderr = client.exec_command(
            "cd {} ; mv {} {}".format(
                self.source_folder, filename, self.archive_folder))
        return (stdin, stdout, stderr)

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
        device = self.connect(LOCALHOST)
        _, stdout, _ = device.exec_command('hostname')
        hostname = stdout.read()
        if isinstance(hostname, bytes):
            hostname = hostname.decode('utf-8')
        device.close()
        return hostname

    @property
    def localhost_hostname(self):
        device = self.connect(REMOTE)
        _, stdout, _ = device.exec_command('hostname')
        hostname = stdout.read()
        if isinstance(hostname, bytes):
            hostname = hostname.decode('utf-8')
        device.close()
        return hostname


class FileTransfer(object):
    """Transfer a list of files to the remote host or within host.
    """

    def __init__(self, file_connector=None, archive=None):
        self.file_connector = file_connector or FileConnector()
        self.archive = archive or False

    @property
    def edc_sync_app_config(self):
        return django_apps.get_app_config('edc_sync_files')

    @property
    def files(self):
        client = self.file_connector.connect(LOCALHOST)
        host = client.open_sftp()
        files = []
        if host:
            files = host.listdir(self.file_connector.source_folder)
            try:
                files.remove('.DS_Store')
            except ValueError:
                pass
            host.close()
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
        """ Copies the files from the remote machine into local machine. """
        try:
            for f in self.files_dict:
                if f.get('filename') == filename:
                    self.file_connector.copy(f.get('filename'))
        except paramiko.SSHException:
            return False
        return True

    def approve_sent_file(self, filename, approval_code):
        try:
            sent_file_history = History.objects.get(filename=filename)
            sent_file_history.approval_code = approval_code
            sent_file_history.save()
        except History.DoesNotExist:
            pass
