"""edc_sync_files URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from edc_sync_files.admin import edc_sync_files_admin


from .views import PullMediaFileView

urlpatterns = [
    url(r'^pull-media-file/$', PullMediaFileView.as_view(), name='pull-media-file'),
    url(r'^admin/', edc_sync_files_admin.urls),
]
