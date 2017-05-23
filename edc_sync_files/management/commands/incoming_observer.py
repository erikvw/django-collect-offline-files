import logging

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from ...observers import IncomingTransactionsFileQueueObserver
from edc_sync_files.file_queues.process_queue import process_queue


app_config = django_apps.get_app_config('edc_sync_files')
logger = logging.getLogger('edc_sync_files')


class Command(BaseCommand):

    help = 'Start observer that imports files into the incoming transactions model.'

    file_observer_cls = IncomingTransactionsFileQueueObserver

    def handle(self, *args, **options):
        file_observer = self.file_observer_cls(
            task_processor=process_queue, **options)
        file_observer.start()
