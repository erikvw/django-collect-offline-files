import queue as q

from django.apps import apps as django_apps

from .transaction_loads import TransactionLoads


class TransactionFileQueue(object):

    """ Queue uploaded transaction file so that they can be played one after the other.
        1. queue = TransactionFileQueue()
        2. queue.add_new_uploaded_file(...) added by event handler possibly.
        3. queue.process_queued_files()
    """

    def __init__(self, transation_file=None):
        self.transation_file = transation_file
        self.queued_files = q.Queue()
        self.edc_sync_file_app = django_apps.get_app_config('edc_sync_files')

    def add_new_uploaded_file(self, path):
        """ Fetch the file from watchdog and add it into queue.
        """
        self.queued_files.put(TransactionLoads(path=path))

    def process_queued_files(self):
        """ Create incoming transactions and apply transactions.
        """
        while not self.queued_files.empty():
            transation_file = self.queued_files.get()
            transation_file.upload_file()
