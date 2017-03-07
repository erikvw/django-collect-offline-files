from datetime import timedelta

from django.conf import settings
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import models

from edc_base.model_mixins import BaseUuidModel
from edc_sync.models import IncomingTransaction


class UploadTransactionFile(BaseUuidModel):

    transaction_file = models.FileField(
        upload_to=settings.MEDIA_ROOT)

    file_name = models.CharField(
        max_length=50,
        null=True,
        editable=False,
        unique=True)

    tx_pk = models.CharField(max_length=100,
                             null=True)

    file_date = models.DateField(null=True,
                                 editable=False)

    identifier = models.CharField(
        max_length=50,
        null=True)

    consume = models.BooleanField(default=True)

    total = models.IntegerField(
        editable=False,
        default=0)

    consumed = models.IntegerField(
        editable=False,
        default=0)

    not_consumed = models.IntegerField(
        editable=False,
        default=0,
        help_text='duplicates')

    producer = models.TextField(
        max_length=1000,
        null=True,
        editable=False,
        help_text='List of producers detected from the file.')

    objects = models.Manager()

    def save(self, *args, **kwargs):
#         if not self.id:
#             self.file_name = self.transaction_file.name.replace('\\', '/').split('/')[-1]
#             date_string = self.file_name.split('_')[2].split('.')[0][:8]
#             self.file_date = date(int(date_string[:4]),
#                                   int(date_string[4:6]),
#                                   int(date_string[6:8]))
#             self.identifier = self.file_name.split('_')[1]

#         if self.consume:
#             self.consume_transactions()
        super(UploadTransactionFile, self).save(*args, **kwargs)

    def consume_transactions(self):
        """Can only upload if there exists an upload from the previous day,
        or a valid skip day exists in its presence.
        """
#         if self.file_already_uploaded():
#             raise TypeError('File covering date of \'{0}\' for \'{1}\' is already'
#                             ' uploaded.'.format(self.file_date, self.identifier))
#
#         if(self.today_within_skip_untill() or self.today_skip_day()):
#             raise TypeError('Cannot upload file for today because it has '
#                             'been declared a skip day for \'{0}\''.format(self.identifier))
#
#         if (not self.previous_day_file_uploaded()
#                 and not self.skip_previous_day()
#                 and not self.first_upload_or_skip_day()):
#             raise TypeError('Missing Upload file from the previous day for'
#                             ' \'{0}\'. Previous day is not set as a SKIP '
#                             'date.'.format(self.identifier))
        index = 0
        self.transaction_file.open()
        producer_list = []
        for index, outgoing in enumerate(self.deserialize_json_file(self.transaction_file)):
            if not IncomingTransaction.objects.filter(pk=outgoing.object.pk).exists():
                if outgoing.object._meta.get_fields():
                    self.consumed += 1
                    data = outgoing.object.__dict__
                    del data['using']
                    del data['is_consumed_middleman']
                    del data['is_consumed_server']
                    del data['_state']

                    IncomingTransaction.objects.create(**data)
                    if outgoing.object.producer not in producer_list:
                        producer_list.append(outgoing.object.producer)
            else:
                self.not_consumed += 1
        self.total = index
        producer_list.sort()
        self.producer = ','.join(producer_list)

    def deserialize_json_file(self, file_pointer):
        try:
            json_txt = file_pointer.read()
            decoded = serializers.deserialize(
                "json", json_txt, ensure_ascii=True, use_natural_foreign_keys=True,
                use_natural_primary_keys=False)
        except:
            return None
        return decoded

    def check_for_transactions(self, transaction_file=None, exception_cls=None):
        transaction_file = transaction_file or self.transaction_file
        transaction_file.open()
        exception_cls = exception_cls or ValidationError
        if not self.deserialize_json_file(transaction_file):
            raise exception_cls(
                'File does not contain any transactions. Got {0}'.format(transaction_file.name))

    def file_already_uploaded(self):
        if self.__class__.objects.filter(
            file_date=self.file_date,
            identifier__iexact=self.identifier
        ).exists():
            return True
        return False

    def previous_day_file_uploaded(self):
        previous = self.file_date - timedelta(1)
        if self.__class__.objects.filter(
                file_date=previous,
                identifier__iexact=self.identifier).exists():
            return True
        return False

    def skip_previous_day(self):
        from .upload_skip_days import UploadSkipDays
        yesterday = self.file_date - timedelta(1)
        if (UploadSkipDays.objects.filter(
            skip_date=yesterday, identifier__iexact=self.identifier).exists()
                or UploadSkipDays.objects.filter(
                    skip_until_date=yesterday, identifier__iexact=self.identifier).exists()):
            return True
        return False

    def first_upload_or_skip_day(self):
        from .upload_skip_days import UploadSkipDays
        """This is the first upload or skip day record.
         Specific to a particular identifier.
         """
        if ((self.__class__.objects.filter(
            identifier__iexact=self.identifier).count() == 0)
                and (UploadSkipDays.objects.filter(
                    identifier__iexact=self.identifier).count() == 0)):
            return True
        return False

    def today_within_skip_untill(self):
        from .upload_skip_days import UploadSkipDays
        if (UploadSkipDays.objects.filter(
                skip_until_date__gt=self.file_date,
                identifier__iexact=self.identifier).exists()):
            return True
        return False

    def today_skip_day(self):
        from .upload_skip_days import UploadSkipDays
        if (UploadSkipDays.objects.filter(
                skip_date=self.file_date,
                identifier__iexact=self.identifier).exists()):
            return True
        return False

    class Meta:
        app_label = 'edc_sync_files'
        ordering = ('-created',)
