from datetime import datetime
import sys

from django.core.management.base import BaseCommand

from ...event_handlers import TransactionBatchEventHandler
from ...event_handlers import TransactionFileEventHandler
from ...queues import batch_queue, tx_file_queue
from ...observer import Observer


class Command(BaseCommand):

    help = 'Start watchdog observer'

    def handle(self, *args, **options):
        tx_file_queue.reload()
        batch_queue.reload()
        observer = Observer()
        observer.start(
            event_handlers=[
                TransactionFileEventHandler(),
                TransactionBatchEventHandler()])
        sys.stdout.flush()
