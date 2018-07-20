import os
import logging
import sys

from django.core.management.color import color_style

logger = logging.getLogger('django_collect_offline_files')
style = color_style()


def process_queue(queue=None, **kwargs):
    """Loops and waits on queue calling queue's `next_task` method.

    If an exception occurs, log the error, log the exception,
    and break.
    """
    while True:
        item = queue.get()
        if item is None:
            queue.task_done()
            logger.info(f'{queue}: exiting process queue.')
            break
        filename = os.path.basename(item)
        try:
            queue.next_task(item, **kwargs)
        except Exception as e:
            queue.task_done()
            logger.warn(f'{queue}: item={filename}. {e}\n')
            logger.exception(e)
            sys.stdout.write(style.ERROR(
                f'{queue}. item={filename}. {e}. Exception has been logged.\n'))
            sys.stdout.flush()
            break
        else:
            logger.info(f'{queue}: Successfully processed {filename}.\n')
        queue.task_done()
