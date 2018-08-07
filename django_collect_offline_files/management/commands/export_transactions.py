import logging

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand, CommandError
from django_collect_offline_files import ExportedTransactionFileHistory
from django_collect_offline_files import TransactionExporter, TransactionFileSender, TransactionFileSenderError


app_config = django_apps.get_app_config('django_collect_offline_files')
logger = logging.getLogger('django_collect_offline_files')


class Command(BaseCommand):

    help = 'On localhost, export outgoing transactions to file and send to username@remote_host.'

    tx_exporter_cls = TransactionExporter
    tx_file_sender_cls = TransactionFileSender
    history_model = ExportedTransactionFileHistory

    def add_arguments(self, parser):

        parser.add_argument(
            '--user',
            dest='user',
            default=f'{app_config.user}@{app_config.remote_host}',
            help=(
                f'username@remotehost (Default: {app_config.user}@{app_config.remote_host}. See app_config.)'),
        )

        parser.add_argument(
            '--export_path',
            dest='export_path',
            default=app_config.outgoing_folder,
            help=(
                f'Export path on localhost. (Default: {app_config.outgoing_folder}. See app_config.)'),
        )

        parser.add_argument(
            '--tmp_path',
            dest='tmp_path',
            default=app_config.tmp_folder,
            help=(
                f'tmp path on remote host. (Default: {app_config.tmp_folder}. See app_config.)'),
        )

        parser.add_argument(
            '--target_path',
            dest='target_path',
            default=app_config.incoming_folder,
            help=(
                f'Target path on remote host. (Default: {app_config.incoming_folder}. See app_config.)'),
        )

        parser.add_argument(
            '--archive_path',
            dest='archive_path',
            default=app_config.archive_folder,
            help=(
                f'Archive path on localhost. (Default: {app_config.archive_folder}. See app_config.)'),
        )

        parser.add_argument(
            '--export_only',
            dest='export_only',
            default=False,
            help=(f'(Default: False)'),
        )

        parser.add_argument(
            '--send_only',
            dest='send_only',
            default=False,
            help=(f'(Default: False)'),
        )

    def handle(self, *args, **options):

        if not options.get('send_only'):
            tx_exporter = self.tx_exporter_cls(**options)
            tx_exporter.export_batch()

        if not options.get('export_only'):
            tx_file_sender = self.tx_file_sender_cls(
                history_model=self.history_model,
                username=options.get('user').split('@')[0],
                remote_host=options.get('user').split('@')[1],
                trusted_host=True,
                src_path=options.get('export_path'),
                dst_tmp=options.get('tmp_path'),
                dst_path=options.get('target_path'),
                archive_path=options.get('archive_path'))
            filenames = [
                obj.filename for obj in self.history_model.objects.filter(sent=False)]
            try:
                tx_file_sender.send(filenames=filenames)
            except TransactionFileSenderError as e:
                raise CommandError(e) from e
