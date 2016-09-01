from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from celery.decorators import task

from django.apps import apps as django_apps
from edc_sync_files.file_transfer import FileTransfer

logger = get_task_logger(__name__)


def edc_sync_files_app_config():
    return django_apps.get_app_config('edc_sync_files')


@periodic_task(
    run_every=(crontab(
        minute=edc_sync_files_app_config().crontab_min,
        hour=edc_sync_files_app_config().crontab_hr,
        day_of_week=edc_sync_files_app_config().crontab_day_of_week)),
    name="pull_media_from_node_server",
)
def pull_media_from_node_server():
    transfer = FileTransfer()
    logger.info("Transfering media file with celery.")
    for filename in transfer.media_filenames_to_copy():
        transfer_file = FileTransfer(filename=filename)
        transfer_file.copy_media_file()
