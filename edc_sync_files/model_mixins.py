from django.db import models


class TransactionFileIdentifierMixin(models.Model):

    previous_file_identifer = models.CharField(max_length=100, null=True)

    file_identifier = models.CharField(max_length=100, null=True)

    class Meta:
        abstract = True
