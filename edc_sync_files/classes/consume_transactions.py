from edc_sync.consumer import Consumer

from edc_sync.models import IncomingTransaction
from edc_sync_files.classes.transaction_messages import transaction_messages
from edc_sync_files.models.upload_transaction_file import UploadTransactionFile


class ConsumeTransactions:
    """Consumes transactions for a transaction file.
    """

    def __init__(self, file_transactions_pks, transaction_obj, file_name):
        self.file_transactions_pks = file_transactions_pks
        self.transaction_obj = transaction_obj
        self.file_name = file_name

    @property
    def is_previous_consumed(self):
        not_consumed = 0
        if self.transaction_obj:
            not_consumed = IncomingTransaction.objects.filter(
                is_consumed=False,
                is_ignored=False,
                batch_id=self.transaction_obj.batch_seq).count()
        return True if not not_consumed else False

    def update_transaction_file(
            self, not_consumed=None, total=None, is_played=False):
        try:
            upload_transaction_file = UploadTransactionFile.objects.get(
                file_name=self.file_name)
            upload_transaction_file.total = total
            upload_transaction_file.comment = transaction_messages.last_error_message()
            upload_transaction_file.save()
        except UploadTransactionFile.DoesNotExist:
            pass

    def consume_transactions(self):
        """ Apply incoming transactions for the currently uploaded file.
        """
        if self.is_previous_consumed:
            print("Applying transactions for {}".format(self.filename))
            Consumer(transactions=self.file_transactions_pks).consume()
        else:
            print("File {} uploaded, transactions not played.".format(self.filename))
