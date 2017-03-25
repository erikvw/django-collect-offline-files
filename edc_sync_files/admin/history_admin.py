from django.contrib import admin

from ..models import History
from ..admin_site import edc_sync_files_admin


@admin.register(History, site=edc_sync_files_admin)
class HistoryAdmin (admin.ModelAdmin):

    ordering = ('-created', )

    list_display = (
        'filename', 'hostname', 'created', )

    list_filter = (
        'hostname', )

    search_fields = ('filename',)
