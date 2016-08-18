import json
import socket

from django.http.response import HttpResponse
from django.views.generic.base import TemplateView

from edc_base.views.edc_base_view_mixin import EdcBaseViewMixin
from edc_sync.edc_sync_view_mixin import EdcSyncViewMixin

from rest_framework.generics import CreateAPIView


from .file_transfer import FileTransfer
from .models import History
from .serializers import HistorySerializer


class HistoryCreateView(CreateAPIView):

    queryset = History.objects.all()
    serializer_class = HistorySerializer

    def perform_create(self, serializer):
        serializer.save(user_created=self.request.user)


# class MediaFilesAPIView(APIView):
#     """
#     A view that returns the count  of transactions.
#     """
#     renderer_classes = (JSONRenderer, )
# 
#     def get(self, request, format=None):
#         return Response(json.dumps(FileTransfer().pending_media_files()))


class PullMediaFileView(EdcBaseViewMixin, EdcSyncViewMixin, TemplateView):

    template_name = 'edc_sync/home.html'
    COMMUNITY = None
    transfer = None

    def __init__(self, *args, **kwargs):
        super(PullMediaFileView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            # edc_sync_admin=edc_sync_admin,
            project_name=self.app.verbose_name + ': ' + self.role.title(),
            cors_origin_whitelist=self.cors_origin_whitelist,
            hostname=socket.gethostname(),
            ip_address=self.ip_address,
        )
        return context

    def copy_media_file(self, host, filename):
        transfer = FileTransfer(
            device_ip=host, filename=filename
        )
        return transfer.copy_media_file()

    def get(self, request, *args, **kwargs):
        result = {}
        if request.is_ajax():
            host = request.GET.get('host')
            ip_address = host[:-5] if '8000' in host else host
            action = request.GET.get('action')
            if action == 'pull':
                filename = request.GET.get('filename')
                print("inside", ip_address)
                if self.copy_media_file(ip_address, filename):
                    result = {'filename': filename, 'host': ip_address, 'status': True}
                else:
                    result = {'filename': filename, 'host': ip_address, 'status': False}
            elif action == 'media-count':
                transfer = FileTransfer(
                    device_ip=ip_address,
                )
                result = {'mediafiles': transfer.media_files_to_copy(), 'host': host}
        return HttpResponse(json.dumps(result), content_type='application/json')
