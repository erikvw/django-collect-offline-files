import os

from django.apps import apps as django_apps
from django.test import TestCase, tag
from faker import Faker

from edc_sync.models import OutgoingTransaction

from ..action_handler import ActionHandler, ActionHandlerError
from ..constants import PENDING_FILES, EXPORT_BATCH, SEND_FILES, CONFIRM_BATCH
from ..models import ExportedTransactionFileHistory
from .models import TestModel

fake = Faker()

app_config = django_apps.get_app_config('edc_sync_files')


@tag('actions')
class TestActionHandler(TestCase):

    multi_db = True

    def setUp(self):
        ExportedTransactionFileHistory.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

    def test_invalid_action(self):
        action_handler = ActionHandler(using='client')
        self.assertRaises(
            ActionHandlerError, action_handler.action, label='blahblah')

    def test_export_batch(self):
        action_handler = ActionHandler(using='client')
        action_handler.action(label=EXPORT_BATCH)
        self.assertFalse(action_handler.data.get('errmsg'))
        self.assertGreater(
            action_handler.history_model.objects.using('client').all().count(), 0)

    def test_send_files(self):
        action_handler = ActionHandler(using='client')
        action_handler.action(label=EXPORT_BATCH)
        action_handler = ActionHandler(using='client')
        action_handler.action(label=SEND_FILES)
        self.assertFalse(action_handler.data.get('errmsg'))

    def test_send_and_archive_files(self):
        action_handler = ActionHandler(using='client')
        action_handler.action(label=EXPORT_BATCH)
        action_handler = ActionHandler(using='client')
        action_handler.action(label=SEND_FILES)
        for filename in action_handler.data.get('last_sent_files'):
            self.assertFalse(os.path.exists(
                os.path.join(app_config.source_folder, filename)))
        for filename in action_handler.data.get('last_archived_files'):
            self.assertTrue(os.path.exists(
                os.path.join(app_config.archive_folder, filename)))
        self.assertEqual(action_handler.data.get('pending_files'), [])

    def test_pending_files(self):
        for _ in range(0, 3):
            action_handler = ActionHandler(using='client')
            action_handler.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        action_handler = ActionHandler(using='client')
        action_handler.action(label=PENDING_FILES)
        self.assertEqual(len(action_handler.data.get('pending_files')), 3)

    def test_pending_count(self):
        for _ in range(0, 3):
            action_handler = ActionHandler(using='client')
            action_handler.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        action_handler = ActionHandler(using='client')
        self.assertGreater(len(action_handler.pending_filenames), 0)
        self.assertEqual(len(action_handler.pending_filenames), 3)

    def test_pending_empty_after_sends_all(self):
        for _ in range(0, 3):
            action_handler = ActionHandler(using='client')
            action_handler.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        action_handler = ActionHandler(using='client')
        self.assertEqual(len(action_handler.pending_filenames), 3)
        action_handler.action(label=SEND_FILES)
        self.assertEqual(len(action_handler.pending_filenames), 0)

    def test_confirm_batch_not_sent(self):
        for i in range(0, 3):
            action_handler = ActionHandler(using='client')
            action_handler.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        action_handler = ActionHandler(using='client')
        action_handler.action(label=CONFIRM_BATCH)
        self.assertIsNone(action_handler.data.get('confirmation_code'))

    @tag('1')
    def test_confirm_batch_sent(self):
        for i in range(0, 3):
            action_handler = ActionHandler(using='client')
            action_handler.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        for i in range(0, 3):
            action_handler = ActionHandler(using='client')
            action_handler.action(label=SEND_FILES)
        action_handler = ActionHandler(using='client')
        action_handler.action(label=CONFIRM_BATCH)
        self.assertIsNotNone(action_handler.data.get('confirmation_code'))
