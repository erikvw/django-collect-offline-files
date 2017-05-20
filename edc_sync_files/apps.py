import os
import sys

from django.apps import AppConfig as DjangoAppConfig
from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.color import color_style


style = color_style()


class AppConfig(DjangoAppConfig):

    name = 'edc_sync_files'
    verbose_name = 'File support for data synchronization'
    user = None
    remote_host = None
    usb_volume = '/Volumes/BCPP'

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
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        for folder in [
            self.pending_folder, self.usb_incoming_folder, self.outgoing_folder,
                self.incoming_folder, self.archive_folder, self.log_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        if not self.role:
            sys.stdout.write(style.NOTICE(
                ' Warning: Project uses \'edc_sync_files\' but has '
                'not defined a role for this app instance. See AppConfig.\n'))

    @property
    def role(self):
        """Return the role of this device.

        Role is configured through edc_device.
        See edc_device.apps.AppConfig.
        """
        return django_apps.get_app_config('edc_device').role
