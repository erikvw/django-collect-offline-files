import sys
import logging

from datetime import datetime
from watchdog.observers import Observer

logger = logging.getLogger('django_collect_offline_files')


class FileQueueObserver:

    options = {}
    queue_cls = None

    handler_cls = None
    observer_cls = Observer

    def __init__(self, task_processor=None, **options):
        self.options.update(**options)
        self.task_processor = task_processor

    def start(self):
        queue = self.queue_cls(**self.options)
        queue.reload(**self.options)

        handler = self.handler_cls(queue=queue, **self.options)

        # watchdog observer
        observer = self.observer_cls()
        sys.stdout.write(f'\n{observer}\n')

        watch = observer.schedule(handler, queue.src_path)
        sys.stdout.write(f'{watch.__class__.__name__} {watch.path}\n')
        observer.start()

        dt = datetime.now().strftime('%Y-%m-%d %H:%M')
        sys.stdout.write(f'\nStarted {dt}\n')
        sys.stdout.write('\nReady. Press CTRL-C to stop.\n\n')
        logger.info(f'{observer} started')

        try:
            self.task_processor(queue=queue, **self.options)
        except KeyboardInterrupt:
            logger.info('CTRL-C pressed')
        except Exception as e:
            logger.exception(e)
        finally:
            observer.stop()
        observer.join()
        queue.join()
        logger.info(f'{observer} stopped')
        dt = datetime.now().strftime('%Y-%m-%d %H:%M')
        sys.stdout.write(f'\n{observer} stopped {dt}\n')
