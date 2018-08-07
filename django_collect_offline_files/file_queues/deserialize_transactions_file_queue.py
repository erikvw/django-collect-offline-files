import os

from django.core.serializers.base import DeserializationError
from django_collect_offline.transaction import TransactionDeserializer
from django_collect_offline.transaction import TransactionDeserializerError

from ..transaction import TransactionImporterBatch
from .base_file_queue import BaseFileQueue
from .exceptions import TransactionsFileQueueError


class DeserializeTransactionsFileQueue(BaseFileQueue):

    batch_cls = TransactionImporterBatch
    tx_deserializer_cls = TransactionDeserializer

    def __init__(self, history_model=None, allow_self=None,
                 override_role=None, **kwargs):
        super().__init__(**kwargs)
        self.history_model = history_model
        self.allow_self = allow_self
        self.override_role = override_role

    def next_task(self, item, raise_exceptions=None, **kwargs):
        """Deserializes all transactions for this batch and
        archives the file.
        """
        filename = os.path.basename(item)
        batch = self.get_batch(filename)
        tx_deserializer = self.tx_deserializer_cls(
            allow_self=self.allow_self, override_role=self.override_role)
        try:
            tx_deserializer.deserialize_transactions(
                transactions=batch.saved_transactions)
        except (DeserializationError, TransactionDeserializerError) as e:
            raise TransactionsFileQueueError(e) from e
        else:
            batch.close()
            self.archive(filename)

    def get_batch(self, filename=None):
        """Returns a batch instance given the filename.
        """
        try:
            history = self.history_model.objects.get(filename=filename)
        except self.history_model.DoesNotExist as e:
            raise TransactionsFileQueueError(
                f'Batch history not found for \'{filename}\'.') from e
        if history.consumed:
            raise TransactionsFileQueueError(
                f'Batch closed for \'{filename}\'. Got consumed=True')
        batch = self.batch_cls()
        batch.batch_id = history.batch_id
        batch.filename = history.filename
        return batch
