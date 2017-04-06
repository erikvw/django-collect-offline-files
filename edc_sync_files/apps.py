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
    source_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'outgoing')
    destination_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'incoming')
    destination_tmp_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'tmp')
    archive_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'archive')

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
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
