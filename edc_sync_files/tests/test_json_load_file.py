import os
import tempfile

from django.test.testcases import TestCase
from django.test.utils import tag
from faker import Faker

from ..transaction import TransactionExporter
from ..transaction.transaction_importer import JSONLoadFile, JSONFileError
from .models import TestModel

fake = Faker()


@tag('json')
class TestJSONLoadFile(TestCase):

    def setUp(self):
        TestModel.objects.using('client').create(f1=fake.name())
        TestModel.objects.using('client').create(f1=fake.name())
        tx_exporter = TransactionExporter(
            export_path=tempfile.gettempdir(),
            using='client')
        batch = tx_exporter.export_batch()
        self.filename = batch.filename
        self.path = tx_exporter.path

    def test_file(self):
        json_file = JSONLoadFile(name=self.filename, path=self.path)
        json_text = json_file.read()
        self.assertIsNotNone(json_text)

    def test_bad_json_file(self):
        _, p = tempfile.mkstemp()
        with open(p, 'w') as f:
            f.write('][][][][][sdfsdfs')
        filename = os.path.basename(p)
        path = os.path.dirname(p)
        json_file = JSONLoadFile(name=filename, path=path)
        self.assertRaises(JSONFileError, json_file.read)

    def test_deserialize_file(self):
        json_file = JSONLoadFile(name=self.filename, path=self.path)
        self.assertGreater(
            len([obj for obj in json_file.deserialized_objects]), 0)
