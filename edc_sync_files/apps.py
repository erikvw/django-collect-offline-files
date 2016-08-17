import os
import sys

from django.apps import AppConfig as DjangoAppConfig
from django.conf import settings
from django.core.management.color import color_style

from edc_base.config_parser_mixin import ConfigParserMixin

style = color_style()


class AppConfig(ConfigParserMixin, DjangoAppConfig):
    name = 'edc_sync_files'
    verbose_name = 'File Synchronization'
    role = 'server'
    device_ip = 'localhost'
    source_folder = '~/edc_sync_files'
    destination_folder = None
    media_folders = []
    config_filename = 'edc_sync.ini'
    # these attrs will be overwritten with values in edc_sync.ini, see ready()
    config_attrs = {
        'edc_sync': ['user', 'password', 'device_ip', 'source_folder', 'role', 'destination_folder'],
        'corsheaders': [('cors_origin_whitelist', tuple), ('cors_origin_allow_all', bool)]
    }
    cors_origin_whitelist = None  # a tuple of host:port, host:port, ...
    cors_origin_allow_all = True

    def ready(self):
        sys.stdout.write('Loading {} ...\n'.format(self.verbose_name))
        if not self.role:
            sys.stdout.write(style.NOTICE(
                ' Warning: Project uses \'edc_sync_files\' but has not defined a role for this '
                'app instance. See AppConfig.\n'))
        self.overwrite_config_attrs_on_class(self.name)
        sys.stdout.write(' * role is {}.\n'.format(self.role.upper()))
        sys.stdout.write(' Done loading {}.\n'.format(self.verbose_name))
