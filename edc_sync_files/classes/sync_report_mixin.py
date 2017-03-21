from edc_sync.models import IncomingTransaction
from ..models import UploadTransactionFile


class SyncReportMixin:
    """Generates statistics for transactions for a particular machine.
    """
    def __init__(self, producer=None, filename=None,
                 report_date=None, all_machines=False):

        self.producer = producer
        self.filename = filename
        self.report_date = report_date
        self.total_consumed = 0
        self.total_not_consumed = 0
        self.upload_transaction_file = None
        self.report_data = []

        if not all_machines:
            self.machine_report()
        else:
            for producer in self.producers():
                self.producer = producer
                row_data = {
                    'total_consumed': self.total_consumed,
                    'total_not_consumed': self.not_consumed,
                    'upload_transaction_file': self.upload_transaction_file}
                self.report_data.append(row_data)

    def producers(self):
        """Returns a list of producers based on synced files.
        """
        producers = []
        # FIXME use group by
        for upload_transaction_file in UploadTransactionFile.objects.all():
            if upload_transaction_file.producer not in producers:
                producers.append(upload_transaction_file.producer)
        return producers

    def machine_report(self):
        """Build a statistics based on a producers.
        """
        self.total_consumed = IncomingTransaction.objects.filter(
            producer=self.producer, is_consumed=True).count()

        self.not_consumed = IncomingTransaction.objects.filter(
            producer=self.producer, is_consumed=False).count()

        self.upload_transaction_file = UploadTransactionFile.objects.filter(
            producer=self.producer).last()
