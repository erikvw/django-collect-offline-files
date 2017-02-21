from django.contrib import admin

from ..models import UploadTransactionFile
from ..forms import UploadTransactionFileForm


class UploadTransactionFileAdmin(admin.ModelAdmin):

    form = UploadTransactionFileForm

    date_hierarchy = 'created'

    fields = ('transaction_file',
              'consume')

    list_display = ('file_name',
                    'consumed',
                    'not_consumed',
                    'created',
                    'producer',
                    'user_created',
                    'hostname_created')

    list_filter = ('identifier',
                   'created',
                   'hostname_created')

admin.site.register(UploadTransactionFile, UploadTransactionFileAdmin)
