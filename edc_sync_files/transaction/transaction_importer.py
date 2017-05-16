import os

from django.apps import apps as django_apps
from django.db.utils import IntegrityError

from edc_sync.models import IncomingTransaction
from edc_sync.transaction_deserializer import deserialize

from ..models import ImportedTransactionFileHistory
from .file_archiver import FileArchiver
from django.core.serializers.base import DeserializationError
from edc_base.utils import get_utcnow


class TransactionImporterError(Exception):
    pass


class BatchIsEmpty(Exception):
    pass


class BatchAlreadyProcessed(Exception):
    pass


class BatchHistoryError(Exception):
    pass


class BatchError(Exception):
    pass


class BatchUnsaved(Exception):
    pass


class BatchDeserializationError(Exception):
    pass


class InvalidBatchSequence(Exception):
    pass


# def deserialize(json_text=None):
#     """Wraps django deserialize with defaults for JSON
#     and natural keys.
#     """
#     return serializers.deserialize(
#         "json", json_text,
#         ensure_ascii=True,
#         use_natural_foreign_keys=True,
#         use_natural_primary_keys=False)


class JSONFile:

    def __init__(self, name=None, path=None, archive_folder=None, **kwargs):
        self._deserialized_objects = None
        self.name = name
        self.path = path
        self.archive_folder = archive_folder
        self.deserialize = deserialize
        self.file_archiver = FileArchiver(
            src_path=self.path, archive_path=self.archive_folder)

    def read(self):
        """Returns the file contents as JSON text.
        """
        with open(os.path.join(self.path, self.name)) as f:
            json_text = f.read()
        return json_text

    def archive(self):
        self.file_archiver.archive(self.name)

    @property
    def deserialized_objects(self):
        """Returns a generator of deserialized objects.
        """
        if not self._deserialized_objects:
            json_text = self.read()
            self._deserialized_objects = self.deserialize(
                json_text=json_text)
        return self._deserialized_objects


class BatchHistory:

    def __init__(self, model=None):
        self.model = model or ImportedTransactionFileHistory

    def exists(self, batch_id=None):
        """Returns True if batch_id exists in the history.
        """
        try:
            self.model.objects.get(batch_id=batch_id)
        except self.model.DoesNotExist:
            return False
        return True

    def close(self, batch_id):
        obj = self.model.objects.get(batch_id=batch_id)
        obj.consumed = True
        obj.consumed_datetime = get_utcnow()
        obj.save()

    def update(self, filename=None, batch_id=None, prev_batch_id=None,
               producer=None, count=None):
        """Creates an history model instance.
        """
        # TODO: refactor model enforce unique batch_id
        # TODO: refactor model to not allow NULLs
        if not filename:
            raise BatchHistoryError('Invalid filename. Got None')
        if not batch_id:
            raise BatchHistoryError('Invalid batch_id. Got None')
        if not prev_batch_id:
            raise BatchHistoryError('Invalid prev_batch_id. Got None')
        if not producer:
            raise BatchHistoryError('Invalid producer. Got None')
        if self.exists(batch_id=batch_id):
            raise IntegrityError('Duplicate batch_id')
        obj = self.model(
            filename=filename,
            batch_id=batch_id,
            prev_batch_id=prev_batch_id,
            producer=producer,
            total=count)
        obj.transaction_file.name = filename
        obj.save()
        return obj


class Batch:

    def __init__(self, **kwargs):
        self._valid_sequence = None
        self.filename = None
        self.batch_id = None
        self.prev_batch_id = None
        self.producer = None
        self.objects = []
        self.batch_history = BatchHistory()
        self.model = IncomingTransaction

    def __str__(self):
        return f'Batch(batch_id={self.batch_id}, filename={self.filename})'

    def __repr__(self):
        return f'Batch(batch_id={self.batch_id}, filename={self.filename})'

    def populate(self, deserialized_txs=None, filename=None, retry=None):
        """Populates the batch with unsaved model instances
        from a generator of deserialized objects.
        """
        if not deserialized_txs:
            raise BatchError(
                'Failed to populate batch. There are no objects to add.')
        self.filename = filename
        if not self.filename:
            raise BatchError('Invalid filename. Got None')
        try:
            for deserialized_tx in deserialized_txs:
                self.peek(deserialized_tx)
                self.objects.append(deserialized_tx.object)
                break
            for deserialized_tx in deserialized_txs:
                self.objects.append(deserialized_tx.object)
        except DeserializationError as e:
            raise BatchDeserializationError(e)

    def peek(self, deserialized_tx):
        """Peeks into first tx and sets self attrs.
        """
        self.batch_id = deserialized_tx.object.batch_id
        self.prev_batch_id = deserialized_tx.object.prev_batch_id
        self.producer = deserialized_tx.object.producer
        if self.batch_history.exists(batch_id=self.batch_id):
            raise BatchAlreadyProcessed(
                f'Batch {self.batch_id} has already been processed')
        elif not self.valid_sequence:
            raise InvalidBatchSequence(
                f'Invalid batch sequence for file \'{self.filename}\'. '
                f'Got {self.batch_id}')

    def save(self):
        """Saves all model instances in the batch as model.
        """
        saved = 0
        if not self.objects:
            raise BatchError('Save failed. Batch is empty')
        for deserialized_tx in self.objects:
            try:
                self.model.objects.get(pk=deserialized_tx.pk)
            except self.model.DoesNotExist:
                data = {}
                for field in self.model._meta.get_fields():
                    try:
                        data.update({field.name: getattr(
                            deserialized_tx, field.name)})
                    except AttributeError:
                        pass
                self.model.objects.create(**data)
                saved += 1
        return saved

    def update_history(self):
        if not self.objects:
            raise BatchIsEmpty('Update history failed. Batch is empty')
        if self.objects_unsaved:
            raise BatchUnsaved(
                'Update history failed. Batch has unsaved objects')
        self.batch_history.update(
            filename=self.filename,
            batch_id=self.batch_id,
            prev_batch_id=self.prev_batch_id,
            producer=self.producer,
            count=self.saved_transactions.count())

    @property
    def saved_transactions(self):
        """Returns the count of saved model instances for this batch.
        """
        return self.model.objects.filter(batch_id=self.batch_id)

    @property
    def count(self):
        """Returns the number of objects in the batch.
        """
        return len(self.objects)

    @property
    def objects_unsaved(self):
        """Returns True if any batch objects have not been saved.
        """
        return self.count > self.saved_transactions.count()

    @property
    def valid_sequence(self):
        """Returns True if previous and current batch id imply the
        current batch is the "next" or "first" batch of the sequence.
        """
        if not self._valid_sequence:
            if self.prev_batch_id == self.batch_id:
                self._valid_sequence = True
            elif self.batch_history.exists(batch_id=self.prev_batch_id):
                self._valid_sequence = True
        return self._valid_sequence

    def close(self):
        self.batch_history.close(self.batch_id)


class TransactionImporter:
    """Imports transactions from a file as incoming transaction and
       archives the file.
    """

    def __init__(self, filename=None, path=None, archive_folder=None, **kwargs):
        app_config = django_apps.get_app_config('edc_sync_files')
        self.path = path or app_config.outgoing_folder
        self.archive_folder = archive_folder or app_config.archive_folder
        self.json_file = JSONFile(
            name=filename, path=self.path, archive_folder=self.archive_folder)
        self.batch_cls = Batch

    def import_batch(self):
        """Imports the batch of outgoing transactions into
        model IncomingTransaction.
        """
        batch = self.batch_cls()
        try:
            batch.populate(
                deserialized_txs=self.json_file.deserialized_objects,
                filename=self.json_file.name)
        except BatchDeserializationError as e:
            raise TransactionImporterError(
                f'BatchDeserializationError. \'{batch}\'. Got {e}')
        batch.save()
        batch.update_history()
        self.json_file.archive()
        return batch
