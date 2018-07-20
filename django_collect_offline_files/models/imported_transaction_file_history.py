from django.db import models

from edc_base.model_mixins import BaseUuidModel


class ImportedTransactionFileHistory(BaseUuidModel):
    """A model that tracks the history of transaction
    files imported to this host.
    """

    transaction_file = models.FileField()

    filename = models.CharField(
        max_length=50,
        null=True,
        editable=False,
        unique=True)

    batch_id = models.CharField(
        max_length=100,
        null=True)

    prev_batch_id = models.CharField(
        max_length=100,
        null=True)

    filedate = models.DateField(
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
        ordering = ('-created', )
