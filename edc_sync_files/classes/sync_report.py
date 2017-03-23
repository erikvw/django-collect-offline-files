from edc_sync.models import IncomingTransaction
from ..models import UploadTransactionFile


class SyncReport:
    """Generates statistics for transactions.
    """

    def __init__(
            self, all_machines=None, detailed=False, report_filters=None):

        self.total_consumed = 0
        self.total_not_consumed = 0
        self.upload_transaction_file = None
        self.report_filters = report_filters or {}
        self.report_data = []
        self.all_machines = all_machines or False

        self.col_data = {}

        if not self.all_machines:
            if not detailed:
                self.update_report_data()
            else:
                for transaction_file in self.upload_transaction_files():
                    self.report_filters.update(
                        batch_id=transaction_file.batch_id)
                    self.update_report_data()
                    self.report_data.append(self.col_data)
        else:
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
            print(
                self.total_consumed, self.total_not_consumed,
                self.upload_transaction_file)

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

        self.report_filters.update()
        self.total_not_consumed = IncomingTransaction.objects.filter(
            producer=producer,
            is_consumed=False).count()

        self.upload_transaction_file = UploadTransactionFile.objects.filter(
            producer=producer).last()

        self.col_data.update({
            'total_consumed': self.total_consumed,
            'total_not_consumed': self.total_not_consumed,
            'upload_transaction_file': self.upload_transaction_file})

    def upload_transaction_files(self):
        """Returns upload transactions by producer.
        """
        return UploadTransactionFile.objects.all().order_by('-created')
