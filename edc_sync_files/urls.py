from django.conf.urls import url

from django.views.generic.base import RedirectView

from .admin_site import edc_sync_files_admin

app_name = 'edc_sync_files'

urlpatterns = [
    url(r'^admin/', edc_sync_files_admin.urls),
    url(r'', RedirectView.as_view(url='admin/')),
]
