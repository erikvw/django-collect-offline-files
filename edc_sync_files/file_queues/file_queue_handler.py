import logging
import os

from django.core.management.color import color_style
from watchdog.events import RegexMatchingEventHandler


logger = logging.getLogger('edc_sync_files')
style = color_style()


class FileQueueHandler(RegexMatchingEventHandler):

    def __init__(self, queue=None, regexes=None, **kwargs):
        # super().__init__(regexes=regexes)
        super().__init__()
        self.queue = queue

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
