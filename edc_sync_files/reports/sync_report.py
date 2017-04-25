import pandas as pd

from django.db import connection

from edc_sync.models import IncomingTransaction
from ..models import UploadTransactionFile
from django.db.models.aggregates import Count


class SyncReport:
    """Generates statistics for transactions.
    """
    def __init__(self):
        self.data = {}

    def report_data(self):
        qs_pending = IncomingTransaction.objects.values('producer').filter(
            is_consumed=False).annotate(Count('is_consumed')).order_by('producer')
        for item in qs_pending:
            producer_name = item.get('producer')
            self.data.update({producer_name: {
                'total_not_consumed': qs_pending.filter(producer=producer_name).count(),
                'upload_transaction_file': UploadTransactionFile.objects.filter(
                    producer=producer_name).order_by('-created').last().file_name}})


class SyncReportDetail:

    def __init__(self, producer=None):
        self.all_machines = False
        self.producer = producer
        self.report_data = []
        self.transactions_files = []
        sql_query = 'SELECT * FROM edc_sync_incomingtransaction'
        df = pd.read_sql(
            sql_query, con=connection, columns=['is_consumed', 'producer'])
        for tx_file in UploadTransactionFile.objects.filter(
                producer=producer):
            self.transactions_files.append(tx_file)
            data = self.update_report_data(
                df, batch_id=tx_file.batch_id, producer=tx_file.producer,
                file_name=tx_file.file_name)
            self.report_data.append([data, tx_file])

    def update_report_data(self, df, batch_id=None, producer=None, file_name=None):
        """Build a statistics based on a producer.
        """
        col_data = {}
        total = len(
            df[(df.is_consumed == 1) &
               (df.producer == producer) & (df.batch_id == batch_id)])

        total_not_consumed = len(df[
            (df.is_consumed == 0) &
            (df.producer == producer) & (df.batch_id == batch_id)])

        try:
            self.upload_transaction_file = UploadTransactionFile.objects.get(
                producer=producer, batch_id=batch_id)
        except UploadTransactionFile.DoesNotExist:
            pass
        except UploadTransactionFile.MultipleObjectsReturned:
            self.upload_transaction_file = UploadTransactionFile.objects.filter(
                producer=producer, batch_id=batch_id).last()
        else:
            timestamp = self.upload_transaction_file.file_name.split('.')[0]
            timestamp = timestamp[-6:]
            time = timestamp[:2] + ':' + timestamp[2:4]
            col_data.update({
                'label': time,
                'total_consumed': total,
                'total_not_consumed': total_not_consumed})
        return col_data
