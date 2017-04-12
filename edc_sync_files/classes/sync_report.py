import pandas as pd

from django.db import connection

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

        self.report_data = self.create_report()

    def create_report(self):
        """Create a report for each producer.
        """
        sql_query = 'SELECT * FROM edc_sync_incomingtransaction'
        df = pd.read_sql(
            sql_query, con=connection, columns=['is_consumed', 'producer'])
        report_data = []
        row = []
        producers = self.producers()
        for index, producer in enumerate(producers):
            index = index + 1
            row_item = self.update_report_data(df, producer)
            if len(row) == 4:
                report_data.append(row)
                row = []
            elif len(row) < 4:
                if index == len(self.producers()):
                    row.append(row_item)
                    report_data.append(row)
                else:
                    row.append(row_item)
                print(row)
        return report_data

    def producers(self):
        """Returns a list of producers based on synced files.
        """
        producers = []
        for upload_transaction_file in UploadTransactionFile.objects.all():
            if upload_transaction_file.producer not in producers:
                producers.append(upload_transaction_file.producer)
        return producers

    def update_report_data(self, df, producer=None):
        """Build a statistics based on a producer.
        """
        row_data = {}

        total = len(df[(df.is_consumed == 1) & (df.producer == producer)])
        total_not_consumed = len(df[
            (df.is_consumed == 0) & (df.producer == producer)])

        upload_transaction_file = UploadTransactionFile.objects.filter(
            producer=producer).order_by('-created').last()

        row_data.update({
            'total_consumed': total,
            'total_not_consumed': total_not_consumed,
            'upload_transaction_file': upload_transaction_file})
        return row_data


class SyncReportDetail(SyncReport):

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
