import logging
import os
import time

from django.apps import apps as django_apps
from django.utils import timezone

from watchdog.observers import Observer as WatchdogObserver


class Observer:

    def start(self, event_handler_class=None, path=None):
        app_config = django_apps.get_app_config('edc_sync_files')
        self.observer = WatchdogObserver()
        event_handler = event_handler_class()
        self.observer.schedule(event_handler, path=path)
        self.observer.start()
        logging.basicConfig(
            filename=os.path.join(app_config.log_folder, 'observer.log'),
            level=logging.INFO)
        logger = logging.getLogger(__name__)
        try:
            records = {'time': timezone.now(), 'status': 'running'}
            logger.info('{}'.format(records))
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        except (OSError, IOError) as err:
            records = {'time': timezone.now(), 'status': '{}'.format(str(err))}
            logger.error('{}'.format(records))
            time.sleep(1)
            self.observer.stop()
            self.start(event_handler_class=event_handler_class)
        self.observer.join()

    def stop(self):
        self.observer.stop()
