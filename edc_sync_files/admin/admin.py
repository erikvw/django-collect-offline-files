from django.apps import apps as django_apps
from django.contrib import admin
from django.contrib.admin.sites import AdminSite

from edc_sync_files.models import History

edc_sync_files_app = django_apps.get_app_config('edc_sync_files')


class EdcSyncAdminSite(AdminSite):
    site_header = edc_sync_files_app.verbose_name
    site_title = edc_sync_files_app.verbose_name
    index_title = edc_sync_files_app.verbose_name + ' ' + 'Admin'
    site_url = '/edc-sync-files/'

edc_sync_files_admin = EdcSyncAdminSite(name='edc_sync_files_admin')


@admin.register(History, site=edc_sync_files_admin)
class HistoryAdmin (admin.ModelAdmin):

    ordering = ('-created', )

    list_display = (
        'filename', 'hostname', 'created', )

    list_filter = (
        'hostname', )

    search_fields = ('filename',)
