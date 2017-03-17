import os
import sys

from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings
from django.core.management.color import color_style


style = color_style()


class AppConfig(DjangoAppConfig):

    name = 'edc_sync_files'
    verbose_name = 'File Synchronization'
    user = None
    host = None
    password = None
    usb_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'usb')
    source_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'outgoing')
    destination_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'incoming')
    destination_tmp_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'tmp')
    archive_folder = os.path.join(
        settings.MEDIA_ROOT, 'transactions', 'archive')
    role = None

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        if not self.role:
            sys.stdout.write(style.NOTICE(
                ' Warning: Project uses \'edc_sync_files\' but has not defined a role for this'
                'app instance. See AppConfig.\n'))
