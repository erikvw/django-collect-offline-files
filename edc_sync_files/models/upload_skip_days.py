from django.utils import timezone

from django.db import models

from edc_base.model.models import BaseUuidModel

from .upload_transaction_file import UploadTransactionFile


class UploadSkipDays(BaseUuidModel):

    skip_date = models.DateField(default=timezone.now())

    skip_until_date = models.DateField(null=True,
                                       blank=True,
                                       help_text=(
                                           'System will assume all days are '
                                           'skip days until this date.'))

    identifier = models.CharField(max_length=50)

    objects = models.Manager()

    def save(self, *args, **kwargs):
        if self.today_upload_exists():
            raise TypeError(
                'An upload file for \'{0}\' from \'{1}\' already exists.'
                ' So cannot create it as a skip date'.format(
                    self.skip_date, self.identifier))

        if self.today_within_skip_untill():
            raise TypeError('Cannot create a skip day for this date \'{}\'. '
                            'This date is covered by a skip until date of '
                            '\'{}\' for \'{}\'.'.format(self.skip_date,
                                                        self.skip_until_date,
                                                        self.identifier))

        """A skip day is only valid if there was an upload the previous day or
         if the previous day was also a skip day, unless if this is the first
         skip day/upload record.
         """
        if (not self.is_previous_day_file_uploaded()
                and not self.skip_previous_day()
                and not self.first_skip_day_or_upload()):
            raise TypeError('Missing Upload file for the previous day from'
                            ' \'{0}\'. Previous day is not set as a SKIP date.'
                            ' Therefore \'{1}\' is not a valid skip date.'.format(
                                self.identifier, self.skip_date))

        super(UploadSkipDays, self).save(*args, **kwargs)

    def today_upload_exists(self):
        if UploadTransactionFile.objects.filter(
                file_date=self.skip_date,
                identifier__iexact=self.identifier).exists():
            return True
        return False

    def is_previous_day_file_uploaded(self):
        yesterday = self.skip_date - timedelta(1)
        if UploadTransactionFile.objects.filter(
                file_date=yesterday,
                identifier__iexact=self.identifier).exists():
            return True
        return False

    def skip_previous_day(self):
        yesterday = self.skip_date - timedelta(1)
        if (self.__class__.objects.filter(
            skip_date=yesterday, identifier__iexact=self.identifier).exists()
                or self.__class__.objects.filter(
                    skip_until_date=yesterday,
                    identifier__iexact=self.identifier).exists()):
            return True
        return False

    def first_skip_day_or_upload(self):
        """This is the first upload or skip day record."""
        if (self.__class__.objects.all().count() == 0
                and UploadTransactionFile.objects.all().count() == 0):
            return True
        return False

    def today_within_skip_untill(self):
        if self.__class__.objects.filter(
                skip_until_date__gt=self.skip_date,
                identifier__iexact=self.identifier).exists():
            return True
        return False

    class Meta:
        app_label = 'edc_sync_files'
        ordering = ('-created', )
        unique_together = ('skip_date', 'identifier')
