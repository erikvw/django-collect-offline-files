from django.conf import settings
from django.db import models

from edc_base.model_mixins import BaseUuidModel


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
        super(UploadTransactionFile, self).save(*args, **kwargs)

    class Meta:
        app_label = 'edc_sync_files'
        ordering = ('-created',)
