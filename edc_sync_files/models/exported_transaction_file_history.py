import socket

from django.db import models

from edc_base.model_mixins import BaseUuidModel


class HistoryManager(models.Manager):

    def get_by_natural_key(self, filename, sent_datetime):
        return self.get(filename=filename, sent_datetime=sent_datetime)


class ExportedTransactionFileHistory(BaseUuidModel):
    """A model that keeps a history of transaction files
    sent by this host.
    """

    hostname = models.CharField(
        max_length=100,
        default=socket.gethostname,
    )

    device_id = models.CharField(
        max_length=5,
        null=True)

    batch_id = models.CharField(
        max_length=100
    )

    prev_batch_id = models.CharField(
        max_length=100
    )

    remote_path = models.CharField(
        max_length=200,
        null=True)

    archive_path = models.CharField(
        max_length=100,
        null=True)

    filename = models.CharField(
        max_length=50)

    filesize = models.FloatField(
        null=True)

    filetimestamp = models.DateTimeField(
        null=True)

    exported = models.BooleanField(
        default=False,
        blank=True)

    exported_datetime = models.DateTimeField(null=True)

    sent = models.BooleanField(
        default=False,
        blank=True)

    sent_datetime = models.DateTimeField(null=True)

    confirmation_code = models.CharField(
        max_length=50,
        null=True,
        blank=True)

    confirmation_datetime = models.DateTimeField(null=True)

    objects = HistoryManager()

    def __str__(self):
        return f'host:{self.hostname} file:{self.filename} batch:{self.batch_id} '

    def natural_key(self):
        return (self.filename, self.hostname)

    class Meta:
        ordering = ('created', )
        verbose_name = 'Sent History'
        verbose_name_plural = 'Sent History'
        unique_together = (('filename', 'hostname'),)
        indexes = [
            models.Index(fields=['created']),
            models.Index(fields=['sent_datetime'])]
