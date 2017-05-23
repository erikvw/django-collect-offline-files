import logging
import os

from django.core.management.color import color_style
from watchdog.events import RegexMatchingEventHandler, PatternMatchingEventHandler


logger = logging.getLogger('edc_sync_files')
style = color_style()


class FileQueueHandlerMixin:

    def __repr__(self):
        return f'{self.__class__.__name__}({self.queue})'

    def __str__(self):
        return str(self.queue)

    def on_created(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def process(self, event):
        """Put and process tasks in queue.
        """
        logger.info(f'{self}: put {event.src_path}')
        self.queue.put(os.path.basename(event.src_path))


class RegexFileQueueHandler(FileQueueHandlerMixin, RegexMatchingEventHandler):

    def __init__(self, queue=None, regexes=None, **kwargs):
        super().__init__(regexes=regexes)
        self.queue = queue


class PatternFileQueueHandler(FileQueueHandlerMixin, PatternMatchingEventHandler):

    def __init__(self, queue=None, patterns=None, **kwargs):
        super().__init__(patterns=patterns)
        self.queue = queue
