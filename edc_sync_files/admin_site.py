from django.apps import apps as django_apps
from django.contrib.admin.sites import AdminSite


app_config = django_apps.get_app_config('edc_sync_files')


class EdcSyncAdminSite(AdminSite):
    site_header = app_config.verbose_name
    site_title = app_config.verbose_name
    index_title = app_config.verbose_name + ' ' + 'Admin'
    site_url = '/edc_sync/'

edc_sync_files_admin = EdcSyncAdminSite(name='edc_sync_files_admin')
