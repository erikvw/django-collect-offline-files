from django.contrib import admin

from ..admin_site import edc_sync_files_admin
from ..models import UploadTransactionFile


@admin.register(UploadTransactionFile, site=edc_sync_files_admin)
class UploadTransactionFileAdmin(admin.ModelAdmin):

    ordering = ('-created',)

    date_hierarchy = 'created'

    list_display = ('file_name',
                    'consumed',
                    'created',
                    'producer',
                    'user_created',
                    'hostname_created')

    list_filter = ('consumed', 'created', 'producer', 'hostname_created')

    search_fields = ('file_name', )
