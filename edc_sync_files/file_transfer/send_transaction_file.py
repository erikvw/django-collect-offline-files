from django.apps import apps as django_apps

from edc_base.utils import get_utcnow

from .file_connector import FileConnector


class TransactionFileSender:
    """Send transaction files.
    """

    def __init__(self, filename=None, **kwargs):
        self.file_connector = FileConnector(**kwargs)
        self.filename = filename
        self.progress = self.file_connector.progress_status

    def send(self):
        sent = self.file_connector.copy(self.filename)
        archived = False
        if sent:
            archived = self.file_transfer.archive(self.filename)
        return (sent, archived)
