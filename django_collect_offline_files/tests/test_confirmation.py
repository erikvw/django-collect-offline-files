import os
import tempfile

from django.test import TestCase, tag
from edc_base.utils import get_utcnow

from ..confirmation import ConfirmationCode, Confirmation
from ..transaction import TransactionExporter
from .models import TestModel


class TestConfirmation(TestCase):

    multi_db = True

    def setUp(self):
        self.using = 'client'
        TestModel.objects.using(self.using).create(f1='f1')
        export_path = os.path.join(tempfile.gettempdir(), 'export')
        if not os.path.exists(export_path):
            os.mkdir(export_path)
        tx_exporter = TransactionExporter(
            export_path=export_path, using=self.using)
        batch = self.history = tx_exporter.export_batch()
        self.history = batch.history

    def test_code(self):
        """Asserts identifier class creates a code.
        """
        confirmation_code = ConfirmationCode()
        identifier = confirmation_code.identifier
        self.assertIsNotNone(identifier)

    def test_confirmed_as_batch(self):
        """Asserts confirms a batch using batch_id.
        """
        confirmation = Confirmation(
            history_model=self.history.__class__,
            using=self.using)
        qs = confirmation.history_model.objects.using(self.using).filter(
            batch_id=self.history.batch_id,
            confirmation_code__isnull=True)
        qs.update(sent=True, sent_datetime=get_utcnow())
        code = confirmation.confirm(batch_id=self.history.batch_id)
        try:
            confirmation.history_model.objects.using(self.using).get(
                batch_id=self.history.batch_id,
                confirmation_code=code)
        except confirmation.history_model.DoesNotExist:
            self.fail(
                'tx_exporter.history_model.DoesNotExist unexpectedly does not exist')

    def test_confirm_all(self):
        """Asserts confirms all not yet confirmed.
        """
        confirmation = Confirmation(
            history_model=self.history.__class__,
            using=self.using)
        qs = confirmation.history_model.objects.using(self.using).filter(
            confirmation_code__isnull=True)
        qs.update(sent=True, sent_datetime=get_utcnow())
        code = confirmation.confirm()
        self.assertIsNotNone(code)

    def test_confirmed_from_filename(self):
        """Asserts confirms a batch using a filename.
        """
        confirmation = Confirmation(
            history_model=self.history.__class__,
            using=self.using)
        qs = confirmation.history_model.objects.using(self.using).filter(
            filename=self.history.filename,
            confirmation_code__isnull=True)
        qs.update(sent=True, sent_datetime=get_utcnow())
        code = confirmation.confirm(filename=self.history.filename)
        try:
            confirmation.history_model.objects.using(self.using).get(
                batch_id=self.history.batch_id,
                confirmation_code=code)
        except confirmation.history_model.DoesNotExist:
            self.fail(
                'tx_exporter.history_model.DoesNotExist unexpectedly does not exist')
