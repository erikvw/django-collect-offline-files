import logging
import sys

from django.core.management.color import color_style

logger = logging.getLogger('edc_sync_files')
style = color_style()


def process_queue(queue=None, **kwargs):
    """Loops and waits on queue calling queue's `next_task` method.

    If an exception occurs, log the error, log the exception, and break.
    """
    while True:
        item = queue.get()
        if item is None:
            queue.task_done()
            logger.info(f'{queue}: exiting process queue.')
            break
        try:
            queue.next_task(item, **kwargs)
        except Exception as e:
            queue.task_done()
            logger.error(f'{queue}: item={item}. {e}\n')
            logger.exception(e)
            sys.stdout.write(style.ERROR(f'{queue}. item={item}. {e}. Exception has been logged.\n'))
            sys.stdout.flush()
            break
        else:
            logger.info(f'{queue}: Successfully processed {item}.\n')
        queue.task_done()
