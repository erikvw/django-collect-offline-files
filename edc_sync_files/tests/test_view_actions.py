import os

from django.test import TestCase, tag
from faker import Faker

from edc_sync.models import OutgoingTransaction

from ..constants import PENDING_FILES, EXPORT_BATCH, SEND_FILE
from ..view_actions import ViewActions, ViewActionError
from .models import TestModel

fake = Faker()


@tag('tx')
class TestViewActions(TestCase):

    multi_db = True

    def setUp(self):
        view_actions = ViewActions(using='client')
        view_actions.history_model.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.using('client').all().delete()
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())

    def test_invalid_action(self):
        view_actions = ViewActions(using='client')
        self.assertRaises(
            ViewActionError, view_actions.action, label='blahblah')

    def test_export_batch(self):
        view_actions = ViewActions(using='client')
        view_actions.action(label=EXPORT_BATCH)
        self.assertFalse(view_actions.data.get('errmsg'))
        self.assertGreater(
            view_actions.history_model.objects.using('client').all().count(), 0)

    def test_send_files(self):
        view_actions = ViewActions(using='client')
        view_actions.action(label=EXPORT_BATCH)
        view_actions = ViewActions(using='client')
        view_actions.action(label=SEND_FILE)
        self.assertFalse(view_actions.data.get('errmsg'))

    def test_send_and_archive_files(self):
        view_actions = ViewActions(using='client')
        view_actions.action(label=EXPORT_BATCH)
        view_actions = ViewActions(using='client')
        view_actions.action(label=SEND_FILE)
        self.assertFalse(os.path.exists(
            view_actions.data.get('last_sent_file')))
        self.assertTrue(os.path.exists(
            view_actions.data.get('last_archived_file')))

    def test_pending_files(self):
        for _ in range(0, 3):
            view_actions = ViewActions(using='client')
            view_actions.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        view_actions = ViewActions(using='client')
        data = view_actions.action(label=PENDING_FILES)
        self.assertEqual(len(data.get('pending_files')), 3)

    def test_pending_count(self):
        for _ in range(0, 3):
            view_actions = ViewActions(using='client')
            view_actions.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        view_actions = ViewActions(using='client')
        self.assertGreater(len(view_actions.pending_filenames), 0)
        self.assertEqual(len(view_actions.pending_filenames), 3)

    def test_pending_decreases_on_send(self):
        for i in range(0, 3):
            view_actions = ViewActions(using='client')
            view_actions.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        view_actions = ViewActions(using='client')
        for i in range(0, 3):
            self.assertEqual(len(view_actions.pending_filenames), 3 - i)
            view_actions.action(label=SEND_FILE)

    def test_pending_decreases_on_send2(self):
        for i in range(0, 3):
            view_actions = ViewActions(using='client')
            view_actions.action(label=EXPORT_BATCH)
            TestModel.objects.using('client').create(f1=fake.name())
            TestModel.objects.using('client').create(f1=fake.name())
        for i in range(0, 3):
            view_actions = ViewActions(using='client')
            self.assertEqual(len(view_actions.pending_filenames), 3 - i)
            view_actions.action(label=SEND_FILE)
