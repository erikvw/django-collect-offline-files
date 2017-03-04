from __future__ import absolute_import, unicode_literals

from celery.schedules import crontab
from celery.utils.log import get_task_logger

from .celery import app
from celery.exceptions import Reject

logger = get_task_logger(__name__)


def edc_sync_files_app_config():
    return django_apps.get_app_config('edc_sync_files')


@app.task(bind=True, default_retry_delay=30 * 1, acks_late=True)
def upload_transaction_files():
    pass


@app.task(bind=True)
def send_transaction_report():
    pass
