import logging

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from ...file_queues import process_queue
from ...observers import IncomingTransactionsFileQueueObserver


app_config = django_apps.get_app_config('edc_sync_files')
logger = logging.getLogger('edc_sync_files')


class Command(BaseCommand):

    help = 'Start observer that imports files into the incoming transactions model.'

    file_observer_cls = IncomingTransactionsFileQueueObserver

    def handle(self, *args, **options):
        file_observer = self.file_observer_cls(
            task_processor=process_queue, **options)
        file_observer.start()
