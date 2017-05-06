import os
import shutil

from django.apps import apps as django_apps
from django.core import serializers

from edc_sync.models import IncomingTransaction

from ..models import ImportedTransactionFileHistory


class TransactionImporterError(Exception):
    pass


class BatchNotReady(Exception):
    pass


class BatchAlreadyProcessed(Exception):
    pass


class InvalidBatchSequence(Exception):
    pass


class JSONFile:

    def __init__(self, name=None, path=None, archive_folder=None):
        self.archive_folder = archive_folder
        self.name = name
        self.path = path
        deserializer = Deserializer()
        with open(os.path.join(self.path, self.name)) as f:
            json_text = f.read()
        self.deserialized_objects = deserializer.deserialize(
            json_text=json_text)

    def archive(self):
        shutil.move(
            os.path.join(self.path, self.name),
            self.archive_folder)


class Deserializer:

    def deserialize(self, json_text=None):
        """Returns a generator of deserialized objects.
        """
        deserialized_tx = serializers.deserialize(
            "json", json_text, ensure_ascii=True, use_natural_foreign_keys=True,
            use_natural_primary_keys=False)
        return deserialized_tx


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

    def update(self, filename=None, batch_id=None, producer=None, count=None):
        """Creates an history model instance.
        """
        obj = self.model(
            filename=filename,
            batch_id=batch_id,
            producer=producer,
            total=count)
        obj.transaction_file.name = filename
        obj.save()


class Batch:

    def __init__(self):
        self._verified = None
        self.objects = []
        self.batch_history = BatchHistory()

    def populate(self, deserialized_objects=None):
        """Populates the batch with unsaved model instances
        from a generator of deserialized objects.
        """
        for deserialized_object in deserialized_objects:
            self.objects.append(deserialized_object.object)
            if self.batch_history.exists(batch_id=self.batch_id):
                raise BatchAlreadyProcessed(
                    f'Batch {self.batch_id} has already been processed')
            if not self.verified:
                raise InvalidBatchSequence(
                    f'Invalid batch sequence for {self.filename}')
            break
        for deserialized_object in deserialized_objects:
            self.objects.append(deserialized_object.object)

    def save(self):
        """Saves all objects in the batch as IncomingTransactions.
        """
        saved = 0
        for deserialized_object in self.objects:
            try:
                IncomingTransaction.objects.get(pk=deserialized_object.pk)
            except IncomingTransaction.DoesNotExist:
                data = {}
                for field in IncomingTransaction._meta.get_fields():
                    try:
                        data.update({field.name: getattr(
                            deserialized_object, field.name)})
                    except AttributeError:
                        pass
                IncomingTransaction.objects.create(**data)
                saved += 1
        return saved

    @property
    def count(self):
        """Returns the number of objects in the batch.
        """
        return len(self.objects)

    @property
    def batch_id(self):
        """Returns the batch_id.
        """
        try:
            return self.objects[0].batch_id
        except IndexError:
            raise BatchNotReady('Batch not ready')

    @property
    def prev_batch_id(self):
        """Returns the previous batch_id.
        """
        try:
            return self.objects[0].prev_batch_id
        except IndexError:
            raise BatchNotReady('Batch not ready')

    @property
    def producer(self):
        try:
            return self.objects[0].producer
        except IndexError:
            raise BatchNotReady('Batch not ready')

    @property
    def verified(self):
        """Returns True if previous and current batch id imply the
        current batch is the "next" or "first" batch of the sequence.
        """
        if not self._verified:
            if self.prev_batch_id == self.batch_id:
                self._verified = True
            elif self.batch_history.exists(batch_id=self.prev_batch_id):
                self._verified = True
        return self._verified


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
        try:
            batch.populate(
                deserialized_objects=self.json_file.deserialized_objects)
        except InvalidBatchSequence as e:
            raise TransactionImporterError(str(e))
        except BatchAlreadyProcessed as e:
            raise TransactionImporterError(str(e))
        else:
            batch.save()
            batch.batch_history.update(
                filename=self.json_file.name,
                count=batch.count)
        self.json_file.archive()
        return batch
