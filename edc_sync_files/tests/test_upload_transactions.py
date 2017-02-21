from datetime import date

from django.conf import settings
from django.core.files import File
from django.test import TestCase

from model_mommy import mommy


class TestUploadTransactions(TestCase):

    def setUp(self):

        mommy.make_recipe(
            'edc_sync_files.transaction',
        )

        mommy.make_recipe(
            'edc_sync_files.skip_date'
        )

    def get_transaction_file(self, transaction_path):
        path = (settings.MEDIA_ROOT + transaction_path)
        f = open(path, 'r')
        djangoFile = File(f)

        return djangoFile

    def test_file_already_uploaded(self):
        """Assert that file cannot be uploaded twice."""
        file_path = '/bcpp_otse_201702162025.json'

        with self.assertRaises(TypeError):
            mommy.make_recipe(
                'edc_sync_files.transaction',
                transaction_file=self.get_transaction_file(file_path),
                consume=True,
            )

    def test_yesterday_file_missing(self):
        """Assert file cannot be uploaded with previous file missing."""
        file_path = '/bcpp_otse_201702192025.json'

        with self.assertRaises(TypeError):
            mommy.make_recipe(
                'edc_sync_files.transaction',
                transaction_file=self.get_transaction_file(file_path),
                consume=True,
            )

    def test_skip_day_file_upload(self):
        """Assert file cannot be uploaded on a skip day."""
        file_path = '/bcpp_otse_201702172025.json'

        with self.assertRaises(TypeError):
            mommy.make_recipe(
                'edc_sync_files.transaction',
                transaction_file=self.get_transaction_file(file_path),
                consume=True,
            )

    def test_skip_untill_file_upload(self):
        mommy.make_recipe(
            'edc_sync_files.skip_date',
            skip_date=date(2017, 2, 18),
            skip_until_date=date(2017, 2, 23),
            identifier='otse',
        )

        """Assert file cannot be uploaded on a date specified in skip until."""
        file_path = '/bcpp_otse_201702212025.json'

        with self.assertRaises(TypeError):
            mommy.make_recipe(
                'edc_sync_files.transaction',
                transaction_file=self.get_transaction_file(file_path),
                consume=True,
            )
