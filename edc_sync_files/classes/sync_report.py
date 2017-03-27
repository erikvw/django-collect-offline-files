from edc_sync.models import IncomingTransaction
from ..models import UploadTransactionFile


class SyncReport:
    """Generates statistics for transactions.
    """

    def __init__(
            self, detailed=False, report_filters=None):

        self.total_consumed = 0
        self.total_not_consumed = 0
        self.upload_transaction_file = None
        self.report_filters = report_filters or {}
        self.report_data = []
        self.col_data = {}

        self.create_report()

    def create_report(self):
        """Create a report for each producer.
        """
        row = []
        producers = self.producers()
        for index, producer in enumerate(producers):
            index = index + 1
            self.report_filters.update(producer=producer)
            self.update_report_data(producer)
            if len(row) == 4:
                row.append(self.col_data)
                self.report_data.append(row)
                row = []
            elif len(producers) < 4:
                row.append(self.col_data)
                if index == len(self.producers()):
                    self.report_data.append(row)

    def producers(self):
        """Returns a list of producers based on synced files.
        """
        producers = []
        for upload_transaction_file in UploadTransactionFile.objects.all():
            if upload_transaction_file.producer not in producers:
                producers.append(upload_transaction_file.producer)
        return producers

    def update_report_data(self, producer=None):
        """Build a statistics based on a producer.
        """

        self.total_consumed = IncomingTransaction.objects.filter(
            producer=producer, is_consumed=True).count()

        self.total_not_consumed = IncomingTransaction.objects.filter(
            producer=producer,
            is_consumed=False).count()

        self.upload_transaction_file = UploadTransactionFile.objects.filter(
            producer=producer).order_by('-created')[0]

        self.col_data.update({
            'total_consumed': self.total_consumed,
            'total_not_consumed': self.total_not_consumed,
            'upload_transaction_file': self.upload_transaction_file})


class SyncReportDetail(SyncReport):

    def __init__(self, producer=None):
        self.all_machines = False
        self.producer = producer
        self.report_data = []
        self.transactions_files = []
        for tx_file in UploadTransactionFile.objects.filter(
                producer=producer):
            self.transactions_files.append(tx_file)
            data = self.update_report_data(
                batch_id=tx_file.batch_id, producer=tx_file.producer,
                file_name=tx_file.file_name)
            self.report_data.append([data, tx_file])

    def update_report_data(self, batch_id=None, producer=None, file_name=None):
        """Build a statistics based on a producer.
        """
        col_data = {}
        self.total_consumed = IncomingTransaction.objects.filter(
            producer=producer, batch_id=batch_id, is_consumed=True).count()

        self.total_not_consumed = IncomingTransaction.objects.filter(
            producer=producer,
            batch_id=batch_id,
            is_consumed=False).count()
        try:
            self.upload_transaction_file = UploadTransactionFile.objects.get(
                producer=producer, batch_id=batch_id)
        except UploadTransactionFile.DoesNotExist:
            pass
        else:
            timestamp = self.upload_transaction_file.file_name.split('.')[0]
            timestamp = timestamp[-6:]
            time = timestamp[:2] + ':' + timestamp[2:4]
            col_data.update({
                'label': time,
                'total_consumed': self.total_consumed,
                'total_not_consumed': self.total_not_consumed})
        return col_data
