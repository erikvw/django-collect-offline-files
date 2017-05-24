import os
import tempfile

from faker import Faker

from django.test.testcases import TestCase
from django.test.utils import tag

from edc_sync.transaction import deserialize

from ..transaction import TransactionExporter
from .models import TestModel

fake = Faker()


@tag('deserialize')
class TestDeserializer(TestCase):

    def setUp(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(
            export_path=tempfile.gettempdir(),
            using='client')
        history = tx_exporter.export_batch()
        self.filename = history.filename
        self.path = tx_exporter.path

    def test_deserializer(self):
        with open(os.path.join(self.path, self.filename)) as f:
            json_text = f.read()
        objects = deserialize(json_text=json_text)
        try:
            next(objects)
        except StopIteration:
            self.fail('StopIteration unexpectedly raised')
