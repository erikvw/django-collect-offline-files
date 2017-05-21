import logging
import os

from ..transaction import TransactionImporter, TransactionImporterError
from .base_file_queue import BaseFileQueue
from .exceptions import TransactionsFileQueueError

logger = logging.getLogger('edc_sync_files')


class IncomingTransactionsFileQueue(BaseFileQueue):

    tx_importer_cls = TransactionImporter

    def __init__(self, src_path=None, **kwargs):
        super().__init__(src_path=src_path, **kwargs)
        self.tx_importer = self.tx_importer_cls(import_path=src_path, **kwargs)

    def next_task(self, item):
        """Calls import_batch for the next filename in the queue
        and "archives" the file.

        The archive folder is typically the folder for the deserializer queue.
        """
        filename = os.path.basename(item)
        try:
            self.tx_importer.import_batch(filename=filename)
            logger.info(f'{self}: Successfully imported {filename}.')
        except TransactionImporterError as e:
            logger.error(f'{self}: Failed to import {filename}.')
            raise TransactionsFileQueueError(e) from e
        else:
            self.archive(filename)
            logger.info(f'{self}: Successfully moved {filename} to pending.')
