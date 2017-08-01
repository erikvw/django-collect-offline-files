import os

from ..transaction import TransactionImporter, TransactionImporterError
from .base_file_queue import BaseFileQueue
from .exceptions import TransactionsFileQueueError


class IncomingTransactionsFileQueue(BaseFileQueue):

    tx_importer_cls = TransactionImporter

    def __init__(self, src_path=None, raise_exceptions=None, **kwargs):
        super().__init__(src_path=src_path, **kwargs)
        self.tx_importer = self.tx_importer_cls(import_path=src_path, **kwargs)
        self.raise_exceptions = raise_exceptions

    def next_task(self, item, **kwargs):
        """Calls import_batch for the next filename in the queue
        and "archives" the file.

        The archive folder is typically the folder for the deserializer queue.
        """
        filename = os.path.basename(item)
        try:
            self.tx_importer.import_batch(filename=filename)
        except TransactionImporterError as e:
            raise TransactionsFileQueueError(e) from e
        else:
            self.archive(filename)
