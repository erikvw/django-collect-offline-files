import os
import sys

from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings


class AppConfig(DjangoAppConfig):

    name = 'django_collect_offline_files'
    verbose_name = 'File support for data synchronization'
    django_collect_offline_files_using = True
    user = settings.DJANGO_COLLECT_OFFLINE_FILES_USER
    remote_host = settings.DJANGO_COLLECT_OFFLINE_FILES_REMOTE_HOST
    usb_volume = settings.DJANGO_COLLECT_OFFLINE_FILES_USB_VOLUME

    tmp_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'tmp')

    pending_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'pending')
    usb_incoming_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'usb')
    outgoing_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'outgoing')
    incoming_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'incoming')
    archive_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'archive')
    log_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'log')

    def ready(self):
        sys.stdout.write(f'Loading {self.verbose_name} ...\n')
        self.make_required_folders()
        sys.stdout.write(f'Done loading {self.verbose_name}.\n')

    def make_required_folders(self):
        """Makes all folders declared in the config if they
        do not exist.
        """
        for folder in [
            self.pending_folder, self.usb_incoming_folder, self.outgoing_folder,
                self.incoming_folder, self.archive_folder, self.tmp_folder,
                self.log_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
