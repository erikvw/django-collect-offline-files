# import os
# import logging
# import shutil
# from django.apps import apps as django_apps
# from django.test import TestCase, tag
# from tempfile import mkstemp
# from watchdog.events import PatternMatchingEventHandler
#
# from ..logging import LOGGING
# from ..observers import TransactionFileObserver
# from unittest.case import skip
# import tempfile
#
# logger = logging.getLogger('edc_sync_files')
#
# app_config = django_apps.get_app_config('edc_sync_files')
#
# log_filename = LOGGING.get('handlers').get('file').get('filename')
#
#
# @tag('obs')
# class TestObserver(TestCase):
#
#     def setUp(self):
#         self.paths = {}
#         basedir = tempfile.gettempdir()
#         self.paths.update(incoming_path=os.path.join(basedir, 'incoming'))
#         self.paths.update(outgoing_path=os.path.join(basedir, 'outgoing'))
#         self.paths.update(pending_path=os.path.join(basedir, 'pending'))
#         self.paths.update(archive_path=os.path.join(basedir, 'archive'))
#         for p in self.paths.values():
#             if not os.path.exists(p):
#                 os.mkdir(p)
#
#     def test_observer(self):
#         observer = TransactionFileObserver(**self.paths)
#         mkstemp(suffix='.json', dir=app_config.incoming_folder)
#         with self.assertLogs(logger=logger, level=logging.INFO) as cm:
#             observer.start()
#         observer.join(timeout=1)
#         observer.stop()
#         self.assertIsNotNone(cm.output)
#         self.assertGreater(len(cm.output), 0)
#         self.assertIn('edc_sync_files', cm.output[0])
#
#     def test_observer_logs(self):
#         observer = TransactionFileObserver(**self.paths)
#         mkstemp(suffix='.json', dir=app_config.incoming_folder)
#         with self.assertLogs(logger=logger, level=logging.INFO) as cm:
#             observer.start()
#         observer.join(timeout=1)
#         observer.stop()
#         self.assertIsNotNone(cm.output)
#         self.assertGreater(len(cm.output), 0)
#         self.assertIn('edc_sync_files', cm.output[0])
#
#     def test_observer_logfile(self):
#         observer = TransactionFileObserver(**self.paths)
#         mkstemp(suffix='.json', dir=app_config.incoming_folder)
#         observer.start()
#         observer.join(timeout=1)
#         observer.stop()
#         self.assertTrue(os.path.exists(app_config.log_folder))
#         self.assertTrue(os.path.exists(log_filename))