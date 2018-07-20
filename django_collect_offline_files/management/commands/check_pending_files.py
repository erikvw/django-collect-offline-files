import os
import re
import shutil

from django.apps import apps as django_apps
from django.core.management import BaseCommand, call_command
from django.core.management.base import CommandError

from ...models import ImportedTransactionFileHistory


class Command(BaseCommand):
    """
        Run every 30 minutes to check for pending files in (incoming dir).
        Check whether the watchdog process it is running if not then start it
        and then hand over pending files to watchdog.
    """
    help = ''

    def handle(self, *args, **options):

        CommandError('this command is not in use.')
        django_collect_offline_file_app = django_apps.get_app_config('django_collect_offline_files')
        for filename in self.incoming_files():
            try:
                source_filename = os.path.join(
                    django_collect_offline_file_app.incoming_folder, filename)
                destination_filename = os.path.join(
                    django_collect_offline_file_app.pending_folder, filename)
                shutil.move(source_filename, destination_filename)
            except FileNotFoundError as e:
                print('Error occurred Got {}'.format(str(e)))
        if self.check_watchdog_process():
            pending_files = self.pending_files()
            for filename in pending_files.sort() or []:
                try:
                    source_filename = os.path.join(
                        django_collect_offline_file_app.pending_folder, filename)
                    destination_filename = os.path.join(
                        django_collect_offline_file_app.incoming_folder, filename)
                    shutil.move(source_filename, destination_filename)
                except FileNotFoundError as e:
                    print('Error occurred Got {}'.format(str(e)))

    def incoming_files(self):
        django_collect_offline_file_app = django_apps.get_app_config('django_collect_offline_files')
        files = os.listdir(django_collect_offline_file_app.incoming_folder)
        incoming_files = []
        pattern = re.compile(r'^\w+\_\d{14}\.json$')
        for filename in files:
            if pattern.match(filename):
                try:
                    ImportedTransactionFileHistory.objects.get(
                        filename=filename)
                except ImportedTransactionFileHistory.DoesNotExist:
                    incoming_files.append(filename)
        return incoming_files

    def pending_files(self):
        django_collect_offline_file_app = django_apps.get_app_config('django_collect_offline_files')
        files = os.listdir(django_collect_offline_file_app.pending_folder)
        pending_files = []
        for filename in files:
            pending_files.append(filename)
        return pending_files

    def check_watchdog_process(self):
        last_record = self.read_logs().split(':')
        if last_record[0] == 'ERROR':
            call_command('start_observer')
        return True

    def read_logs(self):
        logs = []
        with open('logs/observer-error.log', "r") as out_file:
            for line in out_file:
                logs.append(line)
        return logs[-1]
