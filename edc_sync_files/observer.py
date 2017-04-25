import logging
import time

from django.utils import timezone

from watchdog.observers import Observer


class Observer:

    def start(self, event_handler_class=None):
        observer = Observer()
        event_handler = event_handler_class()
        observer.schedule(event_handler, path=event_handler.destination_folder)
        observer.start()
        logging.basicConfig(
            filename='logs/observer-error.log', level=logging.INFO)
        logger = logging.getLogger(__name__)
        try:
            records = {'time': timezone.now(), 'status': 'running'}
            logger.info('{}'.format(records))
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        except (OSError, IOError) as err:
            records = {'time': timezone.now(), 'status': '{}'.format(str(err))}
            logger.error('{}'.format(records))
            time.sleep(1)
            observer.stop()
            self.start(event_handler_class=event_handler_class)
        observer.join()
