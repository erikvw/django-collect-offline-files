from django.db import models
from edc_base.model_managers import HistoricalRecords
from edc_base.model_mixins import BaseUuidModel
from uuid import uuid4


class TestModelManager(models.Manager):

    def get_by_natural_key(self, f1):
        return self.get(f1=f1)


class TestModel(BaseUuidModel):

    f1 = models.CharField(max_length=10, unique=True)

    f2 = models.CharField(max_length=10, null=True)

    f3 = models.CharField(max_length=10, default=uuid4())

    objects = TestModelManager()

    history = HistoricalRecords()

    def natural_key(self):
        return (self.f1, )
