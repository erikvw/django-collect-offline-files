from edc_sync.consumer import Consumer

from edc_sync.models import IncomingTransaction


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

    def consume_transactions(self):
        """ Apply incoming transactions for the currently uploaded file.
        """
        if self.is_previous_consumed:
            print("Applying transactions for {}".format(self.filename))
            Consumer(transactions=self.file_transactions_pks).consume()
        else:
            print("File {} uploaded, transactions not played.".format(self.filename))
