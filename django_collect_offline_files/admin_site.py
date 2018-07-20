from django.apps import apps as django_apps
from django.contrib.admin.sites import AdminSite


app_config = django_apps.get_app_config('django_collect_offline_files')


class OfflineFilesAdminSite(AdminSite):
    site_header = app_config.verbose_name
    site_title = app_config.verbose_name
    index_title = app_config.verbose_name + ' ' + 'Admin'
    site_url = '/django_collect_offline_files/'


django_collect_offline_files_admin = OfflineFilesAdminSite(
    name='django_collect_offline_files_admin')
