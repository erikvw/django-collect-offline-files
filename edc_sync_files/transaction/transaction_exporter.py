import os

from django.apps import apps as django_apps
from django.core import serializers
from django.utils import timezone

from edc_base.utils import get_utcnow
from edc_sync.models import OutgoingTransaction

from ..models import ExportedTransactionFileHistory


class BatchAlreadyOpen(Exception):
    pass


class BatchNotOpen(Exception):
    pass


class BatchAlreadyExported(Exception):
    pass


class HistoryAlreadyExists(Exception):
    pass


class TransactionExporterError(Exception):
    pass


def serialize(objects=None):
    return serializers.serialize(
        'json', objects,
        ensure_ascii=True, use_natural_foreign_keys=True,
        use_natural_primary_keys=False)


class JSONFile:
    def __init__(self, batch=None, path=None, **kwargs):
        self.batch = batch
        self.name = self.batch.filename
        self.path = path
        self.serialize = serialize
        self.json_txt = self.serialize(objects=self.batch.items)

    def write(self):
        try:
            with open(os.path.join(self.path, self.batch.filename), 'w') as f:
                f.write(self.json_txt)
        except IOError as e:
            raise TransactionExporterError(
                f'Unable to create export file. Got \'{str(e)}\'')


class Batch:

    def __init__(self, device_id=None, using=None, model=None,
                 history_model=None, **kwargs):
        edc_device_app_config = django_apps.get_app_config('edc_device')
        self.batch_id = None
        self.device_id = device_id or edc_device_app_config.device_id
        self.filename = None
        self.history = None
        self.history_model = history_model or ExportedTransactionFileHistory
        self.is_closed = False
        self.model = model or OutgoingTransaction
        self.prev_batch_id = None
        self.using = using
        self.open()

    def open(self):
        if self.batch_id:
            raise BatchAlreadyOpen('Batch is already open.')
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S%f")
        batch_id = f'{self.device_id}{timestamp}'
        history_obj = self.history_model.objects.using(self.using).last()
        if history_obj:
            prev_batch_id = history_obj.batch_id
        else:
            obj = self.model.objects.using(self.using).filter(
                is_consumed_server=True).last()
            prev_batch_id = obj.batch_id if obj else batch_id
        updated = self.model.objects.using(self.using).filter(
            is_consumed_server=False).update(
                batch_id=batch_id,
                prev_batch_id=prev_batch_id)
        if updated:
            self.batch_id = batch_id
            self.prev_batch_id = prev_batch_id
            self.filename = f'{self.batch_id}.json'
            self.create_history()

    def close(self, remote_host=None):
        timestamp = get_utcnow()
        self.items.update(
            is_consumed_server=True,
            consumer=remote_host,
            consumed_datetime=timestamp)
        self.history.sent_datetime = timestamp
        self.history.sent = True
        self.history.save()

    @property
    def items(self):
        if self.batch_id:
            return self.model.objects.using(self.using).filter(
                batch_id=self.batch_id).exclude(is_consumed_server=True)
        return None

    @property
    def count(self):
        if self.batch_id:
            return self.items.count()
        return 0

    def create_history(self):
        if self.history:
            raise HistoryAlreadyExists(
                'Failed to create history. History already exists')
        self.history = self.history_model.objects.using(self.using).create(
            filename=self.filename,
            device_id=self.device_id,
            batch_id=self.batch_id,
            prev_batch_id=self.prev_batch_id)


class TransactionExporter:

    """Export pending OutgoingTransactions to a file in JSON format
    and update the export `History` model.
    """

    def __init__(self, path=None, device_id=None, using=None, **kwargs):
        app_config = django_apps.get_app_config('edc_sync_files')
        self.batch_cls = Batch
        self.history_model = ExportedTransactionFileHistory
        self.json_file_cls = JSONFile
        self.model = OutgoingTransaction
        self.path = path or app_config.outgoing_folder
        self.serialize = serialize
        self.using = using

    def export_batch(self):
        """Returns a history model instance after exporting a batch
        of txs.
        """
        batch = self.batch_cls(
            model=self.model, history_model=self.history_model, using=self.using)
        if batch.items:
            json_file = self.json_file_cls(batch=batch, path=self.path)
            json_file.write()
            batch.close()
            return batch.history
        return None
