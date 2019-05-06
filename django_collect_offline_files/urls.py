from django.conf.urls import url

from django.views.generic.base import RedirectView

from .admin_site import django_collect_offline_files_admin

app_name = "django_collect_offline_files"

urlpatterns = [
    url("admin/", django_collect_offline_files_admin.urls),
    url("", RedirectView.as_view(url="admin/")),
]
