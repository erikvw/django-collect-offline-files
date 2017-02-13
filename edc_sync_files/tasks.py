import sys
import os

from celery.schedules import crontab
from celery.utils.log import get_task_logger

from .celery import app
from celery.exceptions import Reject
from edc_scheduler.models import History
from datetime import datetime

logger = get_task_logger(__name__)


def edc_sync_files_app_config():
    return django_apps.get_app_config('edc_sync_files')


@app.task(bind=True, default_retry_delay=30 * 1, acks_late=True)
def send_transaction_files(self):
    try:
        pass
    finally:
        sys.stdout, sys.stderr = ("yes", "no")
