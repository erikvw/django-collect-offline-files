from django.contrib import admin

from ..admin_site import django_collect_offline_files_admin
from ..models import ImportedTransactionFileHistory


@admin.register(ImportedTransactionFileHistory, site=django_collect_offline_files_admin)
class ImportedTransactionFileHistoryAdmin(admin.ModelAdmin):

    ordering = ('-created',)

    date_hierarchy = 'created'

    list_display = ('filename',
                    'consumed',
                    'created',
                    'producer',
                    'user_created',
                    'hostname_created')

    list_filter = ('consumed', 'created', 'producer', 'hostname_created')

    search_fields = ('file_name', )
