import os

from django.apps import apps as django_apps
from django.contrib.sites.models import Site
from django.utils import timezone
from django_collect_offline.models import OutgoingTransaction
from django_collect_offline.transaction import serialize
from edc_base.utils import get_utcnow

from ..models import ExportedTransactionFileHistory


class BatchAlreadyOpen(Exception):
    pass


class BatchNotOpen(Exception):
    pass


class BatchClosed(Exception):
    pass


class BatchAlreadyExported(Exception):
    pass


class HistoryAlreadyExists(Exception):
    pass


class TransactionExporterError(Exception):
    pass


class JSONDumpFileError(Exception):
    pass


class JSONDumpFile:
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
            raise JSONDumpFileError(
                f'Unable to write to file. Got \'{str(e)}\'')
        except TypeError as e:
            raise JSONDumpFileError(
                f'Unable to open/find file. path={self.path}, '
                f'filename={self.batch.filename}. Got \'{str(e)}\'')


class ExportBatch:

    def __init__(self, device_id=None, using=None, model=None,
                 history_model=None, site_code=None, **kwargs):
        edc_device_app_config = django_apps.get_app_config('edc_device')
        self.closed = False
        self.batch_id = None
        self.device_id = device_id or edc_device_app_config.device_id
        self.site_code = site_code or Site.objects.get_current()
        self.filename = None
        self.history = None
        self.history_model = history_model or ExportedTransactionFileHistory
        self.model = model or OutgoingTransaction
        self.prev_batch_id = None
        self.using = using
        self.open()

    def reload(self, batch_id):
        obj = self.model.objects.using(self.using).get(batch_id=batch_id)
        self.batch_id = obj.batch_id
        self.prev_batch_id = obj.prev_batch_id
        self.filename = f'{self.batch_id}.json'
        self.history = self.history_model.objects.using(self.using).get(
            batch_id=self.batch_id)

    def open(self):
        if self.batch_id:
            raise BatchAlreadyOpen('Batch is already open.')
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S%f")
        batch_id = f'{self.device_id}{self.site_code}{timestamp}'
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
        if self.closed:
            raise BatchClosed('Batch is already closed')
        self.closed = True
        timestamp = get_utcnow()
        self.items.update(
            is_consumed_server=True,
            consumer=remote_host,
            consumed_datetime=timestamp)
        self.history.exported_datetime = timestamp
        self.history.exported = True
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
        if self.closed:
            raise BatchClosed('Batch is closed')
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

    batch_cls = ExportBatch
    json_file_cls = JSONDumpFile
    model = OutgoingTransaction
    history_model = ExportedTransactionFileHistory

    def __init__(self, export_path=None, using=None, **kwargs):
        self.path = export_path
        self.serialize = serialize
        self.using = using

    def export_batch(self):
        """Returns a batch instance after exporting a batch of txs.
        """
        batch = self.batch_cls(
            model=self.model, history_model=self.history_model, using=self.using)
        if batch.items:
            try:
                json_file = self.json_file_cls(batch=batch, path=self.path)
                json_file.write()
            except JSONDumpFileError as e:
                raise TransactionExporterError(e)
            batch.close()
            return batch
        return None
