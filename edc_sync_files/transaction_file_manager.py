from .file_transfer import FileTransfer

from edc_base.utils import get_utcnow


class TransactionFileManager(object):
    """Send transaction files to the remote host.
      1. Send transactions daily report.
      2. Upload the transaction files in the central server.
      3. Play transactions automatically in the server."""

    def __init__(self, file_transfer=None, filename=None):
        self.file_transfer = file_transfer or FileTransfer(archive=True)
        self.filename = filename
        self.approval_code = None

    def send_files(self):
        self.file_transfer.copy_files(self.filename)
        self.file_transfer.archive(self.filename)

    @property
    def sending_progress(self):
        return self.file_transfer.file_connector.progress_status

    def host_identifier(self):
        return self.file_transfer.file_connector.hostname[:4]

    def approve_transfer_files(self, files):
        approval_code = '{}{}'.format(
            self.host_identifier, str(get_utcnow().strftime("%Y%m%d%H%M")))
        for filename in files:
            self.file_transfer.approve_sent_file(filename, approval_code)
        return True
