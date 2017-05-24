from django.apps import apps as django_apps

from ..file_queues import DeserializeTransactionsFileQueue
from ..file_queues import IncomingTransactionsFileQueue
from ..models import ImportedTransactionFileHistory
from .file_queue_observer import FileQueueObserver

app_config = django_apps.get_app_config('edc_sync_files')


class IncomingTransactionsFileQueueObserver(FileQueueObserver):

    queue_cls = IncomingTransactionsFileQueue
    options = dict(
        regexes=[r'(\/\w+)+\.json$', '\w+\.json$'],
        src_path=app_config.incoming_folder,
        dst_path=app_config.pending_folder)


class DeserializeTransactionsFileQueueObserver(FileQueueObserver):

    queue_cls = DeserializeTransactionsFileQueue
    options = dict(
        regexes=[r'(\/\w+)+\.json$', '\w+\.json$'],
        src_path=app_config.pending_folder,
        dst_path=app_config.archive_folder,
        history_model=ImportedTransactionFileHistory)
