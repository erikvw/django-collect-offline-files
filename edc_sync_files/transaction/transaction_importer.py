import os
import shutil

from django.apps import apps as django_apps
from django.core import serializers
from django.db.utils import IntegrityError

from edc_sync.models import IncomingTransaction

from ..models import ImportedTransactionFileHistory


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


class InvalidBatchSequence(Exception):
    pass


def archive(self, src=None, dst=None):
    shutil.move(
        os.path.join(self.path, self.name),
        self.archive_folder)


def deserialize(json_text=None):
    """Wraps django deserialize with defaults for JSON
    and natural keys.
    """
    return serializers.deserialize(
        "json", json_text,
        ensure_ascii=True,
        use_natural_foreign_keys=True,
        use_natural_primary_keys=False)


class FileArchiver:

    def __init__(self, src_path=None, dst_path=None):
        self.src_path = src_path
        self.dst_path = dst_path

    def archive(self, filename):
        shutil.move(
            os.path.join(self.src_path, filename),
            self.dst_path)


class JSONFile:

    def __init__(self, name=None, path=None, archive_folder=None, **kwargs):
        self._deserialized_objects = None
        self._json_text = None
        self.name = name
        self.path = path
        self.archive_folder = archive_folder
        self.deserialize = deserialize
        self.file_archiver = FileArchiver(
            src_path=self.path, dst_path=self.archive_folder)

    @property
    def json_text(self):
        """Reads the file contents into `json_text` then archives.
        """
        if not self._json_text:
            with open(os.path.join(self.path, self.name)) as f:
                self._json_text = f.read()
            self.file_archiver.archive(self.name)
        return self._json_text

    @property
    def deserialized_objects(self):
        """Returns a generator of deserialized objects.
        """
        if not self._deserialized_objects:
            self._deserialized_objects = self.deserialize(
                json_text=self.json_text)
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
        for deserialized_tx in deserialized_txs:
            self.peek(deserialized_tx)
            self.objects.append(deserialized_tx.object)
            break
        for deserialized_tx in deserialized_txs:
            self.objects.append(deserialized_tx.object)

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
            count=self.saved_objects)

    @property
    def saved_objects(self):
        """Returns the count of saved model instances for this batch.
        """
        return self.model.objects.filter(batch_id=self.batch_id).count()

    @property
    def count(self):
        """Returns the number of objects in the batch.
        """
        return len(self.objects)

    @property
    def objects_unsaved(self):
        """Returns True if any batch objects have not been saved.
        """
        return self.count > self.saved_objects

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


class TransactionImporter:
    """Imports transactions from a file as incoming transaction and
       archives the file.
    """

    def __init__(self, filename=None, path=None, archive_folder=None):
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
        batch.populate(
            deserialized_txs=self.json_file.deserialized_objects,
            filename=self.json_file.name)
        batch.save()
        batch.update_history()
        return batch.batch_id
