from django.db import models

from edc_base.model_mixins import BaseUuidModel


class UploadTransactionFile(BaseUuidModel):
    """A model that keeps a history of transaction files uploaded
    to this host from a client/producer.
    """

    transaction_file = models.FileField()

    file_name = models.CharField(
        max_length=50,
        null=True,
        editable=False,
        unique=True)

    batch_id = models.CharField(
        max_length=100,
        null=True)

    file_date = models.DateField(
        null=True,
        editable=False)

    total = models.IntegerField(
        editable=False,
        default=0)

    consumed = models.IntegerField(
        editable=False,
        default=0)

    producer = models.TextField(
        max_length=1000,
        null=True,
        editable=False,
        help_text='List of producers detected from the file.')

    comment = models.CharField(
        max_length=250,
        null=True,
        blank=True)

    objects = models.Manager()

    class Meta:
        app_label = 'edc_sync_files'
        ordering = ('-created', )
