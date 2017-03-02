from .file_transfer import FileTransfer


class TransactionFileManager(object):
    """Send transaction files to the remote host.
      1. Send transactions daily report.
      2. Upload the transaction files in the central server.
      3. Play transactions automatically in the server."""

    def __init__(self, file_transfer=None):
        self.file_transfer = file_transfer or FileTransfer(archive=True)

    def send_files(self):
        self.file_transfer.copy_files()

    @property
    def sending_progress(self):
        return self.file_transfer.file_connector.progress_status
