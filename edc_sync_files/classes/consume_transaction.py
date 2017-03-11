import time

from threading import Thread, Condition
from edc_sync.models import IncomingTransaction
from edc_sync.consumer import Consumer


transaction_lock = Condition()

uploaded = False
transaction_queue = False


class TrackTransactionUploading(Thread):

    def run(self):
        while True:
            transaction_lock.acquire()
            if not transaction_queue:
                transaction_lock.notify()
            transaction_lock.release()


class PlayTransactions(Thread):

    def run(self):
        while True:
            transaction_lock.acquire()
            if not uploaded:
                transaction_lock.wait()
            uploaded = Consumer().consume()
            time.sleep(5)
