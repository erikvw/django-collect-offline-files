import json
import os

from django.core.serializers.base import DeserializationError
from django.db.utils import IntegrityError
from django_collect_offline.models import IncomingTransaction
from django_collect_offline.transaction import deserialize
from edc_base.utils import get_utcnow

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


class BatchDeserializationError(Exception):
    pass


class InvalidBatchSequence(Exception):
    pass


class JSONFileError(Exception):
    pass


class JSONLoadFile:

    def __init__(self, name=None, path=None, **kwargs):
        self._deserialized_objects = None
        self.deserialize = deserialize
        self.name = name
        self.path = path

    def __str__(self):
        return os.path.join(self.path, self.name)

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name})'

    def read(self):
        """Returns the file contents as validated JSON text.
        """
        p = os.path.join(self.path, self.name)
        try:
            with open(p) as f:
                json_text = f.read()
        except FileNotFoundError as e:
            raise JSONFileError(e) from e
        try:
            json.loads(json_text)
        except (json.JSONDecodeError, TypeError) as e:
            raise JSONFileError(f'{e} Got {p}') from e
        return json_text

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
        try:
            obj = self.model.objects.get(batch_id=batch_id)
        except self.model.DoesNotExist:
            obj = self.model(
                filename=filename,
                batch_id=batch_id,
                prev_batch_id=prev_batch_id,
                producer=producer,
                total=count)
            obj.transaction_file.name = filename
            obj.save()
        return obj


class ImportBatch:

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
            raise BatchDeserializationError(e) from e
        except JSONFileError as e:
            raise BatchDeserializationError(e) from e

    def peek(self, deserialized_tx):
        """Peeks into first tx and sets self attrs or raise.
        """
        self.batch_id = deserialized_tx.object.batch_id
        self.prev_batch_id = deserialized_tx.object.prev_batch_id
        self.producer = deserialized_tx.object.producer
        if self.batch_history.exists(batch_id=self.batch_id):
            raise BatchAlreadyProcessed(
                f'Batch {self.batch_id} has already been processed')
        if self.prev_batch_id != self.batch_id:
            if not self.batch_history.exists(batch_id=self.prev_batch_id):
                raise InvalidBatchSequence(
                    f'Invalid import sequence. History does not exist for prev_batch_id. '
                    f'Got file=\'{self.filename}\', prev_batch_id='
                    f'{self.prev_batch_id}, batch_id={self.batch_id}.')

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

    def close(self):
        self.batch_history.close(self.batch_id)


class TransactionImporter:
    """Imports transactions from a file as incoming transaction.
    """
    batch_cls = ImportBatch
    json_file_cls = JSONLoadFile

    def __init__(self, import_path=None, **kwargs):
        self.path = import_path

    def import_batch(self, filename):
        """Imports the batch of outgoing transactions into
        model IncomingTransaction.
        """
        batch = self.batch_cls()
        json_file = self.json_file_cls(name=filename, path=self.path)
        try:
            deserialized_txs = json_file.deserialized_objects
        except JSONFileError as e:
            raise TransactionImporterError(e) from e
        try:
            batch.populate(
                deserialized_txs=deserialized_txs,
                filename=json_file.name)
        except (BatchDeserializationError, InvalidBatchSequence, BatchAlreadyProcessed) as e:
            raise TransactionImporterError(e) from e
        batch.save()
        batch.update_history()
        return batch
