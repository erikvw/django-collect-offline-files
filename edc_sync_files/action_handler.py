from django.apps import apps as django_apps

from .confirmation import Confirmation, ConfirmationError
from .constants import EXPORT_BATCH, SEND_FILES, CONFIRM_BATCH, PENDING_FILES
from .transaction import TransactionExporter, TransactionExporterError
from .transaction import TransactionFileSenderError, TransactionFileSender


class ActionHandlerError(Exception):
    pass


class ActionHandler:

    def __init__(self, using=None, **kwargs):
        app_config = django_apps.get_app_config('edc_sync_files')
        self.data = {}
        self.using = using
        self.archive_path = app_config.archive_folder
        self.tx_exporter = TransactionExporter(using=self.using, **kwargs)
        self.history_model = self.tx_exporter.history_model
        self.confirmation = Confirmation(
            history_model=self.history_model, using=self.using)
        self.tx_file_sender = TransactionFileSender(
            history_model=self.history_model, using=self.using, **kwargs)
        self.sent_history = self.tx_exporter.history_model.objects.using(
            self.using).filter(sent=True).order_by('-sent_datetime')
        self.recently_sent_filenames = [
            obj.filename for obj in self.sent_history[0:20]]

    def action(self, label=None, **kwargs):
        self.data = dict(
            errmsg=None, batch_id=None,
            last_sent_files=[], last_archived_files=[],
            pending_files=[],
            confirmation_code=None)
        if label == EXPORT_BATCH:
            self._export_batch()
        elif label == SEND_FILES:
            self._send_files()
        elif label == CONFIRM_BATCH:
            self._confirm_batch()
        elif label == PENDING_FILES:
            pass
        else:
            raise ActionHandlerError(f'Invalid action. Got {label}')
        self.data.update(pending_files=self.pending_filenames)

    @property
    def pending_filenames(self):
        return [
            obj.filename for obj in self.tx_exporter.history_model.objects.using(
                self.using).filter(sent=False).order_by('-created')]

    def _export_batch(self):
        try:
            history = self.tx_exporter.export_batch()
        except TransactionExporterError as e:
            raise ActionHandlerError(e)
        else:
            if history:
                self.data.update(batch_id=history.batch_id)
                self.pending_filenames.append(history.filename)

    def _send_files(self):
        try:
            filenames = self.tx_file_sender.send(
                filenames=self.pending_filenames)
        except TransactionFileSenderError as e:
            raise ActionHandlerError(
                f'Reraised TransactionFileSenderError. Got {e}')
        else:
            self.data.update(
                last_sent_files=filenames, last_archived_files=filenames)

    def _confirm_batch(self):
        try:
            code = self.confirmation.confirm()
        except ConfirmationError as e:
            raise ActionHandlerError(
                f'Reraised ConfirmationError. Got {e}')
        self.data.update(confirmation_code=code)
