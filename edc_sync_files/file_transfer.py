import getpass
import os.path
import paramiko

from datetime import datetime
from django.apps import apps as django_apps

from .models import History
from .constants import REMOTE, LOCALHOST


class FileConnector(object):

    def __init__(self, localhost=None, device_sftp=None, is_archived=None, copy=None, source_folder=None,
                 destination_folder=None, archive_dir=None, filename=None, pull=None, hostname=None):
        self.is_archived = True if is_archived else False
        self._copy = True if copy else False
        self.source_folder = source_folder
        self.destination_folder = destination_folder
        self.archive_dir = archive_dir
        self.filename = filename
        self.localhost = localhost
        self.device_sftp = device_sftp
        self.pull = pull or False
        self.hostname = hostname

    def copy(self):
        """ Copy the file to remote device otherwise copies it to a local folder. Push (put) or Pull (get)."""
        if self.pull:
            local_filename = os.path.join(self.destination_folder, self.filename)
            remote_file_name = os.path.join(self.source_folder, self.filename)
            sftp_attr = self.device_sftp.get(remote_file_name, local_filename)
            self.create_history()
        else:
            local_filename = os.path.join(self.source_folder, self.filename)
            remote_file_name = os.path.join(self.destination_folder, self.filename)
            sftp_attr = self.device_sftp.put(remote_file_name, local_filename, confirm=True)
            return sftp_attr

    def move(self):
        """ Copies the files to remote device and move them to archive dir. """
        source_filename = os.path.join(self.source_folder, self.filename)
        if not self.pull:
            destination_file_name = os.path.join(self.source_folder, self.filename)
            self.device_sftp.put(source_filename, destination_file_name, confirm=True)
            if self.is_archived:
                self.archive()
            return True
        return False

    def archive(self):
        """ Move file from the current dir to new dir called archive """
        filename = os.path.join(self.source_folder, self.filename)
        stdin, stdout, stderr = self.localhost.exec_command(
            "cd {} ; mv {} {}".format(self.source_folder, filename, self.archive_dir))
        return (stdin, stdout, stderr)

    def create_history(self):
        history = History.objects.create(
            filename=self.filename,
            acknowledged=True,
            ack_datetime=datetime.today(),
            hostname=self.hostname
        )
        return history


class FileTransfer(object):
    """
        The class is responsible for transfer of different files from localhost to remote device.
    """

    def __init__(self, device_ip=None, media_folders=None, filename=None, user=None, source_folder=None, destination_folder=None, hostname=None):
        self.filename = filename
        self.device_ip = device_ip or self.edc_sync_app_config.device_ip
        self.source_folder = source_folder or self.edc_sync_app_config.source_folder
        self.user = user or self.edc_sync_app_config.user
        self.media_folders = media_folders or self.edc_sync_app_config.media_folders
        self.destination_folder = destination_folder or self.edc_sync_app_config.destination_folder
        self.hostname = hostname or self.device_hostname

    @property
    def edc_sync_app_config(self):
        return django_apps.get_app_config('edc_sync')

    def connect_to_device(self, device):
        device, username = (self.device_ip, self.user) if device == REMOTE else (LOCALHOST, getpass.getuser())
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(device, username=username, look_for_keys=True)
        except paramiko.SSHException:
            return False
        return client

    @property
    def device_hostname(self):
        device = self.connect_to_device(REMOTE)
        _, stdout, _ = device.exec_command('hostname')
        hostname = stdout.read()
        if isinstance(hostname, bytes):
            hostname = hostname.decode('utf-8')
        device.close()
        return hostname

    @property
    def device_media_filenames(self):
        device = self.connect_to_device(REMOTE)
        device_sftp = device.open_sftp()
        filenames = device_sftp.listdir(self.source_folder)
        try:
            filenames.remove('.DS_Store')
        except ValueError:
            pass
        device.close()
        device_sftp.close()
        return filenames

    def media_files_to_copy(self):
        media_file_to_copy = []
        for filename in self.device_media_filenames:
            try:
                History.objects.get(filename=filename, hostname=self.hostname)
            except History.DoesNotExist:
                media_file_to_copy.append(filename)
        return media_file_to_copy

    def copy_media_file(self):
        """ Copies the files from the remote machine into local machine """
        try:
            device = self.connect_to_device(REMOTE)
            device_sftp = device.open_sftp()
            connector = FileConnector(
                remote_device_sftp=device_sftp, pull=True, filename=self.filename, is_archived=False,
                source_folder=self.source_folder, destination_folder=self.destination_folder,
                hostname=self.hostname
            )
            connector.copy()
            device.close()
            device_sftp.close()
        except paramiko.SSHException:
            return False
        return True
