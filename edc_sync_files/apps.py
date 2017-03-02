import sys

from django.apps import AppConfig as DjangoAppConfig
from django.core.management.color import color_style

from django_appconfig_ini.mixin import ConfigIniMixin

style = color_style()


class AppConfig(ConfigIniMixin, DjangoAppConfig):

    name = 'edc_sync_files'
    verbose_name = 'File Synchronization'
    user = None
    host = None
    password = None
    source_folder = None
    destination_folder = None
    archive_folder = None
    role = None

    config_filename = 'edc_sync_files.ini'
    config_ini_attrs = {'edc_sync_files': []}
    #  'host', 'password', 'source_folder', 'destination_folder']}
    cors_origin_whitelist = None  # a tuple of host:port, host:port, ...
    cors_origin_allow_all = True

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        if not self.role:
            sys.stdout.write(style.NOTICE(
                ' Warning: Project uses \'edc_sync_files\' but has not defined a role for this'
                'app instance. See AppConfig.\n'))
        self.overwrite_config_ini_attrs_on_class(self.name)
        sys.stdout.write(' * role is {}.\n'.format(self.role.upper()))
        sys.stdout.write(' Done loading {}.\n'.format(self.verbose_name))
