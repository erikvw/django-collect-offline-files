import queue as q

from .transaction_loads import TransactionLoads


class TransactionFileQueue(object):

    """ Queue files and upload each file sequencely.
        1. queue = TransactionFileQueue()
        2. queue.add_new_uploaded_file(...) added by event handler possibly.
        3. queue.process_queued_files()
    """

    def __init__(self):
        self.queued_files = q.Queue()

    def add_new_uploaded_file(self, path):
        """ Fetch the file from watchdog and add it into queue.
        """
        self.queued_files.put(TransactionLoads(path=path))

    def process_queued_files(self):
        """ Create incoming transactions and apply transactions.
        """
        while not self.queued_files.empty():
            transation_loads = self.queued_files.get()
            transation_loads.upload_file()
