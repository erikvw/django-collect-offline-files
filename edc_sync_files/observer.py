import sys
import logging
import time

from django.apps import apps as django_apps

from watchdog.observers import Observer as WatchdogObserver
from datetime import datetime

app_config = django_apps.get_app_config('edc_sync_files')

logger = logging.getLogger('edc_sync_files')
logger.info('log started')


class StopTestObserver(Exception):
    pass


class Observer:

    def start(self, event_handlers=None, timeout=None, test=None, verbose=None):
        logger.info('Started.')
        self.observer = WatchdogObserver()
        for event_handler in event_handlers:
            self.observer.schedule(event_handler, path=event_handler.path)
        self.observer.start()
        try:
            dt = datetime.now().strftime('%Y-%m-%d %H:%M')
            sys.stdout.write(f'\nStarted {dt}\n')
            sys.stdout.write('\npress CTRL-C to stop.\n\n')
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info('CTRL-C pressed')
            self.observer.stop()
        except (OSError, IOError) as e:
            logger.error(f'{e}')
            time.sleep(1)
            self.observer.stop()
        finally:
            self.observer.join(timeout=timeout)
            logger.info('Stopped.')

    def stop(self):
        self.observer.stop()
