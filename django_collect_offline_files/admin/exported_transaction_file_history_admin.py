from django.contrib import admin

from ..admin_site import django_collect_offline_files_admin
from ..models import ExportedTransactionFileHistory


@admin.register(ExportedTransactionFileHistory, site=django_collect_offline_files_admin)
class ExportedTransactionFileHistoryAdmin (admin.ModelAdmin):

    ordering = ('-created', )

    list_display = (
        'filename', 'hostname', 'created', )

    list_filter = (
        'hostname', )

    search_fields = ('filename',)
