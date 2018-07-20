import os
import tempfile

from django.apps import apps as django_apps
from django.test.testcases import TestCase
from django.test.utils import tag, override_settings
from django_collect_offline.transaction import TransactionDeserializer
from django_collect_offline.transaction import TransactionDeserializerError
from django_collect_offline.transaction import deserialize
from edc_device.constants import NODE_SERVER, CLIENT, CENTRAL_SERVER
from faker import Faker

from ..transaction import TransactionExporter
from .models import TestModel

fake = Faker()


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

    def test_tx_deserializer_not_server(self):
        """Asserts raises if not a server.
        """
        with override_settings(DEVICE_ID=None, DEVICE_ROLE=None):
            app_config = django_apps.get_app_config('edc_device')
            app_config.device_id = '15'
            app_config.device_role = CLIENT
            app_config.ready()
            self.assertRaises(TransactionDeserializerError,
                              TransactionDeserializer)

    def test_tx_deserializer_is_centralserver(self):
        """Asserts OK if is a server.
        """
        with override_settings(DEVICE_ID=None, DEVICE_ROLE=None):
            app_config = django_apps.get_app_config('edc_device')
            app_config.device_id = '99'
            app_config.device_role = CENTRAL_SERVER
            app_config.ready()
            try:
                TransactionDeserializer()
            except TransactionDeserializerError as e:
                self.fail(
                    f'TransactionDeserializerError unexpectedly raised. Got {e}')
            django_apps.app_configs['edc_device'].device_id = '98'
            try:
                TransactionDeserializer()
            except TransactionDeserializerError as e:
                self.fail(
                    f'TransactionDeserializerError unexpectedly raised. Got {e}')

    def test_tx_deserializer_override_role(self):
        """Asserts can override role if not a server by device id.
        """
        with override_settings(DEVICE_ID=None, DEVICE_ROLE=None):
            app_config = django_apps.get_app_config('edc_device')
            app_config.device_id = '15'
            app_config.device_role = CLIENT
            app_config.ready()
            try:
                TransactionDeserializer(override_role=NODE_SERVER)
            except TransactionDeserializerError as e:
                self.fail(
                    f'TransactionDeserializerError unexpectedly raised. Got {e}')
