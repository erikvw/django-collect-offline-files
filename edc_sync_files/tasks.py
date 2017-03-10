from __future__ import absolute_import, unicode_literals

from celery.utils.log import get_task_logger

from django.apps import apps as django_apps
from django.conf import settings

from .celery import app
from edc_sync_files.classes import TransactionDumps, TransactionFileManager

logger = get_task_logger(__name__)


def edc_sync_files_app_config():
    return django_apps.get_app_config('edc_sync_files')


@app.task(bind=True, default_retry_delay=30 * 1, acks_late=True)
def dump_and_send_central_server():
    outgoing_path = edc_sync_files_app_config.source_folder
    TransactionDumps(outgoing_path, hostname=settings.COMMUNITY)
    TransactionFileManager().send_files()


@app.task(bind=True)
def send_transactions_report():
    pass
