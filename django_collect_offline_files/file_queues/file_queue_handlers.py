import logging
import os

from django.core.management.color import color_style
from watchdog.events import RegexMatchingEventHandler


logger = logging.getLogger('django_collect_offline_files')
style = color_style()


class RegexFileQueueHandlerIncoming(RegexMatchingEventHandler):

    def __init__(self, queue=None, regexes=None, **kwargs):
        super().__init__(regexes=regexes)
        self.queue = queue

    def __repr__(self, queue=None, regexes=None, **kwargs):
        return f'{self.__class__.__name__}({self.queue})'

    def __str__(self):
        return str(self.queue)

    def on_created(self, event):
        self.process(event)

    def process(self, event):
        """Put and process tasks in queue.
        """
        logger.info(f'{self}: put {event.src_path}')
        self.queue.put(os.path.basename(event.src_path))


class RegexFileQueueHandlerPending(RegexMatchingEventHandler):

    def __init__(self, queue=None, regexes=None, **kwargs):
        super().__init__(regexes=regexes)
        self.queue = queue

    def __repr__(self, queue=None, regexes=None, **kwargs):
        return f'{self.__class__.__name__}({self.queue})'

    def __str__(self):
        return str(self.queue)

    def on_created(self, event):
        self.process(event)

    def process(self, event):
        """Put and process tasks in queue.
        """
        logger.info(f'{self}: put {event.src_path}')
        self.queue.put(os.path.basename(event.src_path))
