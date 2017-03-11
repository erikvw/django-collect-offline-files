from datetime import date

from django.conf import settings
from django.core.files import File
from django.test import TestCase

from model_mommy import mommy


class TestSkipDays(TestCase):

    def setUp(self):

        mommy.make_recipe(
            'edc_sync_files.transaction',
        )

    def get_transaction_file(self, transaction_path):
        path = (settings.MEDIA_ROOT + transaction_path)
        f = open(path, 'r')
        djangoFile = File(f)

        return djangoFile

    def test_file_already_uploaded(self):
        """Assert that skip day cannot be declared when file is
         already uploaded.
         """
        with self.assertRaises(TypeError):
            mommy.make_recipe(
                'edc_sync_files.skip_date',
                skip_date=date(2017, 2, 16),
                skip_until_date=date(2017, 2, 16),
                identifier='otse',
            )

    def test_yesterday_file_missing(self):
        """Assert cannot declare skip day with yesterday's file missing."""
        with self.assertRaises(TypeError):
            mommy.make_recipe(
                'edc_sync_files.skip_date',
                skip_date=date(2017, 2, 18),
                skip_until_date=date(2017, 2, 18),
                identifier='otse',
            )

    def test_today_within_skip_untill(self):

        mommy.make_recipe(
            'edc_sync_files.skip_date',
            skip_date=date(2017, 2, 17),
            skip_until_date=date(2017, 2, 24),
            identifier='otse',
        )

        """Assert cannot declare an already declared skip day."""
        with self.assertRaises(TypeError):
            mommy.make_recipe(
                'edc_sync_files.skip_date',
                skip_date=date(2017, 2, 22)
            )
