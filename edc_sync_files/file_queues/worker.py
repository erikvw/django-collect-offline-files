from threading import Thread

from .utils import process_queue


class Worker:

    def __init__(self, queue=None):
        self.queue = queue
        self.thread = None

    def __repr__(self):
        return f'{self.__class__.__name__}(queue={self.queue})'

    def __str__(self):
        return str(self.queue)

    def start(self):
        self.thread = Thread(
            target=process_queue, name=f'{self.queue}',
            kwargs=dict(q=self.queue, log_exceptions=True))
        self.thread.start()

    def stop(self):
        self.queue.put(None)
        self.queue.join()
        self.thread.join()
