from django.contrib import admin

from ..models import UploadSkipDays
from ..forms import SkipDaysForm


class UploadSkipDaysAdmin(admin.ModelAdmin):

    form = SkipDaysForm

    date_hierarchy = 'created'

    list_display = ('skip_date',
                    'created',
                    'user_created',
                    'hostname_created')

    list_filter = ('identifier',
                   'created',
                   'hostname_created')

admin.site.register(UploadSkipDays, UploadSkipDaysAdmin)
