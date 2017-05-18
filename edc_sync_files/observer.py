import logging
import time

from django.apps import apps as django_apps

from watchdog.observers import Observer as WatchdogObserver
from tempfile import mkstemp
from datetime import datetime
import sys

app_config = django_apps.get_app_config('edc_sync_files')

logger = logging.getLogger('edc_sync_files')
logger.info('log started')


class StopTestObserver(Exception):
    pass


class ObserverError(Exception):
    pass


class Observer:

    def start(self, event_handlers=None, timeout=None, test=None, verbose=None):
        self.observer = WatchdogObserver()
        for event_handler in event_handlers:
            self.observer.schedule(event_handler, path=event_handler.path)
        self.observer.start()
        try:
            if not test:
                dt = datetime.now().strftime('%Y-%m-%d %H:%M')
                sys.stdout.write(f'\nStarted {dt}\n')
                sys.stdout.write('\npress CTRL-C to stop.\n\n')
            logger.info('running')
            while True:
                time.sleep(1)
                if test:
                    mkstemp(suffix='.json', dir=event_handler.path)
                    time.sleep(1)
                    logger.info('StopTestObserver')
                    raise StopTestObserver()
        except KeyboardInterrupt:
            self.observer.stop()
        except (OSError, IOError) as e:
            logger.error(f'{e}')
            time.sleep(1)
            self.observer.stop()
            # self.start(event_handlers=event_handlers, timeout=timeout)
            raise ObserverError(e)
        else:
            self.observer.join(timeout=timeout)

    def stop(self):
        self.observer.stop()
