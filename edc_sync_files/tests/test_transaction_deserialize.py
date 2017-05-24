import os
import tempfile

from faker import Faker

from django.apps import apps as django_apps
from django.test.testcases import TestCase
from django.test.utils import tag

from edc_sync.transaction import deserialize

from ..transaction import TransactionExporter
from .models import TestModel
from edc_sync.transaction.transaction_deserializer import TransactionDeserializer,\
    TransactionDeserializerError
from edc_device.constants import NODE_SERVER

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

    @tag('1')
    def test_transaction_deserializer(self):
        """Asserts raises if not a server.
        """
        django_apps.app_configs['edc_device'].device_id = '15'
        self.assertRaises(TransactionDeserializerError,
                          TransactionDeserializer)

    @tag('1')
    def test_tx_deserializer_not_server(self):
        """Asserts raises if not a server.
        """
        django_apps.app_configs['edc_device'].device_id = '15'
        self.assertRaises(TransactionDeserializerError,
                          TransactionDeserializer)

    @tag('1')
    def test_tx_deserializer_is_centralserver(self):
        """Asserts OK if is a server.
        """
        django_apps.app_configs['edc_device'].device_id = '99'
        try:
            TransactionDeserializer()
        except TransactionDeserializerError as e:
            self.fail(f'TransactionDeserializerError unexpectedly raised. Got {e}')
        django_apps.app_configs['edc_device'].device_id = '98'
        try:
            TransactionDeserializer()
        except TransactionDeserializerError as e:
            self.fail(f'TransactionDeserializerError unexpectedly raised. Got {e}')

    @tag('1')
    def test_tx_deserializer_override_role(self):
        """Asserts can override role if not a server by device id.
        """
        self.assertGreater(
            len(django_apps.app_configs['edc_device'].server_id_list), 0)
        django_apps.app_configs['edc_device'].device_id = '15'
        try:
            TransactionDeserializer(override_role=NODE_SERVER)
        except TransactionDeserializerError as e:
            self.fail(f'TransactionDeserializerError unexpectedly raised. Got {e}')
