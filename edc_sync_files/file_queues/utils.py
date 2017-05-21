import logging
import sys

from django.core.management.color import color_style

from .exceptions import TransactionsFileQueueError

logger = logging.getLogger('edc_sync_files')
style = color_style()


def process_queue(q=None, log_exceptions=None):
    while True:
        item = q.get()
        if item is None:
            q.task_done()
            logger.info(f'{q}: exiting process queue.')
            break
        try:
            q.next_task(item)
        except TransactionsFileQueueError as e:
            if log_exceptions:
                logger.exception(e)
                sys.stdout.write(style.ERROR(f'{q}. {e}\n'))
            else:
                raise TransactionsFileQueueError(
                    f'{q}. An error occurred processing a queue task. Got {e}.') from e
        q.task_done()
