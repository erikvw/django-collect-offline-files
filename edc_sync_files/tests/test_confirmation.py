from django.test import TestCase, tag

from edc_sync_files.transaction.transaction_exporter import TransactionExporter

from ..confirmation import BatchConfirmationCode, BatchConfirmation
from .models import TestModel


class TestConfirmation(TestCase):

    multi_db = True

    def setUp(self):
        self.using = 'client'
        TestModel.objects.using(self.using).create(f1='f1')
        tx_exporter = TransactionExporter(using=self.using)
        self.history = tx_exporter.export_batch()

    def test_code(self):
        """Asserts identifier class creates a code.
        """
        confirmation_code = BatchConfirmationCode()
        identifier = confirmation_code.identifier
        self.assertIsNotNone(identifier)

    def test_confirmation_code(self):
        """Asserts Confirmation class creates a code.
        """
        confirmation = BatchConfirmation(
            batch_id=self.history.batch_id,
            history_model=self.history.__class__,
            using=self.using)
        self.assertIsNotNone(confirmation.code)

    def test_confirmed_as_batch(self):
        """Asserts confirms a batch using batch_id.
        """
        confirmation = BatchConfirmation(
            batch_id=self.history.batch_id,
            history_model=self.history.__class__,
            using=self.using)
        confirmation.confirm()
        try:
            confirmation.history_model.objects.using(self.using).get(
                batch_id=self.history.batch_id,
                confirmation_code=confirmation.code)
        except confirmation.history_model.DoesNotExist:
            self.fail(
                'tx_exporter.history_model.DoesNotExist unexpectedly does not exist')

    def test_confirmed_as_batch_from_filename(self):
        """Asserts confirms a batch using a filename.
        """
        confirmation = BatchConfirmation(
            filename=self.history.filename,
            history_model=self.history.__class__,
            using=self.using)
        confirmation.confirm()
        try:
            confirmation.history_model.objects.using(self.using).get(
                batch_id=self.history.batch_id,
                confirmation_code=confirmation.code)
        except confirmation.history_model.DoesNotExist:
            self.fail(
                'tx_exporter.history_model.DoesNotExist unexpectedly does not exist')

    def test_confirmed_as_batch_from_code(self):
        """Asserts confirms a batch using a code.
        """
        confirmation = BatchConfirmation(
            filename=self.history.filename,
            history_model=self.history.__class__,
            using=self.using)
        code = confirmation.code
        confirmation = BatchConfirmation(
            code=code,
            history_model=self.history.__class__,
            using=self.using)
        confirmation.confirm()
        try:
            confirmation.history_model.objects.using(self.using).get(
                batch_id=self.history.batch_id,
                confirmation_code=confirmation.code)
        except confirmation.history_model.DoesNotExist:
            self.fail(
                'tx_exporter.history_model.DoesNotExist unexpectedly does not exist')
