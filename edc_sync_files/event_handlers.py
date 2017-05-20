import os

from watchdog.events import RegexMatchingEventHandler

from .queues import IncomingTransactionsFileQueue, DeserializeTransactionsFileQueue


class EventHandlerError(Exception):
    pass


class Base(RegexMatchingEventHandler):

    def __init__(self, regexes=None, **kwargs):
        super().__init__(
            **{k: v for k, v in kwargs.items() if k in [
                'ignore_regexes', 'ignore_directories', 'case_sensitive']})


class BaseFileHandler(Base):

    queue_cls = None

    def __init__(self, regexes=None, src_path=None, dst_path=None, **kwargs):
        super().__init__(regexes=regexes, **kwargs)
        regexes = regexes
        self.src_path = src_path
        self.dst_path = dst_path
        self.queue = self.queue_cls(
            regexes=regexes, src_path=src_path, dst_path=dst_path, **kwargs)

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event):
        """Put and process tasks in queue.
        """
        self.queue.put(os.path.basename(event.src_path))
        while not self.queue.empty():
            self.queue.next_task()


class IncomingTransactionsFileHandler(BaseFileHandler):

    queue_cls = IncomingTransactionsFileQueue


class DeserializeTransactionsFileHandler(BaseFileHandler):

    queue_cls = DeserializeTransactionsFileQueue
