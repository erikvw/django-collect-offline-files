import os
import logging
import shutil
from django.apps import apps as django_apps
from django.test import TestCase, tag
from tempfile import mkstemp
from watchdog.events import PatternMatchingEventHandler

from ..logging import LOGGING
from ..observer import Observer, StopTestObserver
from unittest.case import skip

logger = logging.getLogger('edc_sync_files')

app_config = django_apps.get_app_config('edc_sync_files')

log_filename = LOGGING.get('handlers').get('file').get('filename')


class SrcEvent(PatternMatchingEventHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = app_config.incoming_folder

    def on_created(self, event):
        logger.info(f'src any event {event.src_path}')
        filename = os.path.basename(event.src_path)
        shutil.move(event.src_path, os.path.join(
            app_config.archive_folder, filename))


class DstEvent(PatternMatchingEventHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = app_config.archive_folder

    def on_created(self, event):
        logger.info(f'dst any event {event.src_path}')


# @tag('obs')
@skip
class TestObserver(TestCase):

    def test_observer(self):
        observer = Observer()
        mkstemp(suffix='.json', dir=app_config.incoming_folder)
        with self.assertLogs(logger=logger, level=logging.INFO) as cm:
            try:
                observer.start(event_handlers=[
                    SrcEvent(patterns=[r'^\w+\.json$']),
                    DstEvent(patterns=[r'^\w+\.json$'])], timeout=1)
            except StopTestObserver as e:
                print(f'StopTestObserver. Got {e}')
                pass
        observer.stop()
        self.assertIsNotNone(cm.output)
        self.assertGreater(len(cm.output), 0)
        self.assertIn('edc_sync_files', cm.output[0])

    def test_observer_logs(self):
        observer = Observer()
        mkstemp(suffix='.json', dir=app_config.incoming_folder)
        with self.assertLogs(logger=logger, level=logging.INFO) as cm:
            try:
                observer.start(event_handlers=[
                    SrcEvent(patterns=r'^\w+\.json$'),
                    DstEvent(patterns=r'^\w+\.json$')], timeout=1)
            except StopTestObserver:
                pass
        observer.stop()
        self.assertIsNotNone(cm.output)
        self.assertGreater(len(cm.output), 0)
        self.assertIn('edc_sync_files', cm.output[0])

    def test_observer_logfile(self):
        observer = Observer()
        mkstemp(suffix='.json', dir=app_config.incoming_folder)
        try:
            observer.start(event_handlers=[
                SrcEvent(patterns=r'^\w+\.json$'),
                DstEvent(patterns=r'^\w+\.json$')], timeout=1)
        except StopTestObserver:
            pass
        observer.stop()
        self.assertTrue(os.path.exists(app_config.log_folder))
        self.assertTrue(os.path.exists(log_filename))
