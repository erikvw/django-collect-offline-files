import sys

from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings
from django.core.management.color import color_style

from django_appconfig_ini.mixin import ConfigIniMixin

style = color_style()


class AppConfig(ConfigIniMixin, DjangoAppConfig):
    name = 'edc_sync_files'
    verbose_name = 'File Synchronization'
    role = 'server'
    device_ip = 'localhost'
    source_folder = '~/edc_sync_files'
    destination_folder = None
    media_folders = []
    #
    crontab_hr = None
    crontab_min = None
    crontab_day_of_week = None  # e.g monday if want to execute monday only or if you want monday and tuesday then monday, tuesday

    config_filename = 'edc_sync_files.ini'

    cors_origin_whitelist = None  # a tuple of host:port, host:port, ...
    cors_origin_allow_all = True

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        if not self.role:
            sys.stdout.write(style.NOTICE(
                ' Warning: Project uses \'edc_sync_files\' but has not defined a role for this'
                'app instance. See AppConfig.\n'))
        # self.overwrite_config_attrs_on_class(self.name)
        sys.stdout.write(' * role is {}.\n'.format(self.role.upper()))
        sys.stdout.write(' Done loading {}.\n'.format(self.verbose_name))
