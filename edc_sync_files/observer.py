import logging
import os
import time

from django.apps import apps as django_apps
from django.utils import timezone

from watchdog.observers import Observer as WatchdogObserver

app_config = django_apps.get_app_config('edc_sync_files')
logging.basicConfig(
    filename=os.path.join(app_config.log_folder, 'observer.log'),
    level=logging.INFO)
logger = logging.getLogger(__name__)


class Observer:

    def start(self, event_handlers=None):
        self.observer = WatchdogObserver()
        for event_handler in event_handlers:
            self.observer.schedule(event_handler, path=event_handler.path)
        self.observer.start()
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
            self.start(event_handlers=event_handlers)
        self.observer.join()

    def stop(self):
        self.observer.stop()
