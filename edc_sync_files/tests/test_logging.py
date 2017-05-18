import os
import logging

from django.apps import apps as django_apps
from django.test import TestCase, tag
from tempfile import mkstemp
from watchdog.events import PatternMatchingEventHandler

from ..logging import LOGGING
from ..observer import Observer, StopTestObserver

logger = logging.getLogger('edc_sync_files')

app_config = django_apps.get_app_config('edc_sync_files')

log_filename = LOGGING.get('handlers').get('file').get('filename')


class KillEvent(PatternMatchingEventHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = app_config.destination_folder

    def created(self):
        print('created')
        raise TypeError()

    def moved(self):
        print('moved')
        raise TypeError()


@tag('log')
class TestLogging(TestCase):
    def test_observer_logs(self):
        observer = Observer()
        mkstemp(suffix='.json', dir=app_config.destination_folder)
        with self.assertLogs(logger=logger, level=logging.INFO) as cm:
            try:
                observer.start(event_handlers=[
                    KillEvent(patterns=r'^\w+\.json$')], test=True)
            except StopTestObserver:
                pass
        observer.stop()
        self.assertIsNotNone(cm.output)
        self.assertGreater(len(cm.output), 0)
        self.assertIn('edc_sync_files', cm.output[0])

    def test_observer_logfile(self):
        observer = Observer()
        mkstemp(suffix='.json', dir=app_config.destination_folder)
        try:
            observer.start(event_handlers=[
                KillEvent(patterns=r'^\w+\.json$')], test=True)
        except StopTestObserver:
            pass
        observer.stop()
        self.assertTrue(os.path.exists(app_config.log_folder))
        self.assertTrue(os.path.exists(log_filename))
