import sys

from django.apps import AppConfig as DjangoAppConfig
from django.core.management.color import color_style

from django_appconfig_ini.mixin import ConfigIniMixin

style = color_style()


class AppConfig(ConfigIniMixin, DjangoAppConfig):
    name = 'edc_sync_files'
    verbose_name = 'File Synchronization'
    device_ip = 'localhost'
    source_folder = '~/edc_sync_files'
    destination_folder = None
    media_folders = []
    config_ini_attrs = {'edc_sync_files': ['source_folder', 'destination_folder', 'media_folders', 'device_ip']}
    cors_origin_whitelist = None  # a tuple of host:port, host:port, ...
    cors_origin_allow_all = True

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        self.overwrite_config_ini_attrs_on_class(self.name)
        sys.stdout.write(' * role is {}.\n'.format(self.role.upper()))
        sys.stdout.write(' Done loading {}.\n'.format(self.verbose_name))
