import sys

from django.apps import AppConfig as DjangoAppConfig
from django.core.management.color import color_style


style = color_style()


class AppConfig(DjangoAppConfig):

    name = 'edc_sync_files'
    verbose_name = 'File Synchronization'
    user = None
    host = None
    password = None
    source_folder = None
    destination_folder = None
    archive_folder = None
    role = None

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        if not self.role:
            sys.stdout.write(style.NOTICE(
                ' Warning: Project uses \'edc_sync_files\' but has not defined a role for this'
                'app instance. See AppConfig.\n'))
