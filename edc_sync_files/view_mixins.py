import os

from django.apps import apps as django_apps
from hurry.filesize import size

from .confirmation import BatchConfirmationCode
from .transaction import TransactionExporter
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException,\
    SSHException
# from edc_sync_files.file_transfer.file_connector import FileConnector


class TransactionFileSenderError(Exception):
    pass


class TransactionExporterViewMixin:

    batch_confirmation_cls = BatchConfirmationCode
    tx_exporter = TransactionExporter(
        path=django_apps.get_app_config(
            'edc_sync_files').source_folder)

    @property
    def batch_history_model(self):
        return self.tx_exporter.history_model

    def confirm_batch(self, batch_id=None, filename=None, code=None):
        """Update history model as "batch sent" confirmed by user.
        """
        batch_confirmation = self.batch_confirmation_cls(
            batch_id=batch_id, filename=filename, code=code,
            history_model=self.history_model)
        batch_confirmation.confirm()

    @property
    def pending_batches(self):
        """ Returns a dictionary of unsent files.
        """
        pending_batches = []
        for history in self.history_model.objects.filter(
                sent=False).order_by('created'):
            filename = os.path.join(
                self.tx_exporter.path, history.filename)
            data = dict({
                'filename': filename,
                'filesize': size(os.stat(filename).st_size),
                'batch_id': history.batch_id})
            pending_batches.append(data)
        return pending_batches

    def export_batch(self):
        """Returns response data after exporting transactions.
        """
        # FIXME: refactor this
        history = self.tx_exporter.export_batch()
        if history:
            response_data = dict(
                error=False,
                transactionFiles=self.pending_batches)
        else:
            message = 'No pending data.'
            if self.history_model.objects.filter(
                    sent=False).exists():
                message = 'Pending files found. Transfer pending files.'
            response_data = dict(messages=message, error=True)
        return response_data


class TransactionFileSenderViewMixin:

    def send_file(self, filename=None):
        """Returns response data after sending the file.
        """
        tx_file_sender = self.transaction_file_sender(filename=filename)
        try:
            tx_file_sender.send()
        except IOError as e:
            response_data = dict(
                error=True,
                messages=f'Unable to send file. Got {e}')
        else:
            response_data = dict(error=False, messages='File sent.')
        return response_data

    def recently_sent_files(self):
        batch_history_model.objects.filter(
            sent=True).order_by('-created')[:20]

    def connected(self, **kwargs):
        try:
            self.file_connector(**kwargs).connected()
        except (ConnectionRefusedError, AuthenticationException,
                BadHostKeyException, ConnectionResetError, SSHException,
                OSError)as e:
            raise TransactionFileSenderError(f'Connection error. Got {e}')
        return True
