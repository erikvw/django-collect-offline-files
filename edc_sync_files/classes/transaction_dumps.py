import re
import os
import shutil
import socket

from os.path import join

from django.apps import apps as django_apps
from django.core import serializers
from django.db import transaction
from django.utils import timezone
from django.db.utils import IntegrityError

from edc_base.utils import get_utcnow
from edc_sync.models import OutgoingTransaction

from .transaction_messages import transaction_messages
from ..constants import ERROR
from ..models import History


class TransactionDumps:

    """Dumps OutgoingTransaction(is_consumed_server=False) to into
       transaction json file.
       1. TransactionDumps(path=path_to_dump_transactions_to)
       1.1 Create history record in the server.
    """

    def __init__(self, path, hostname=None, using=None):
        self.path = path
        self.hostname = hostname or django_apps.get_app_config('edc_device').device_id
        self.using = using or 'default'
        self.filename = '{}_{}.json'.format(
            self.hostname, str(timezone.now().strftime("%Y%m%d%H%M%S")))

        self.batch_id = None
        self.batch_seq = None

        self.is_exported_to_json = self.dump_to_json()

    def update_batch_info(self):
        """Update the transaction batch information.
        """
        update_batch_info = False
        try:
            first_unconsumed_outgoing = OutgoingTransaction.objects.using(self.using).filter(
                is_consumed_server=False).first()
            self.batch_id = first_unconsumed_outgoing.tx_pk

            last_consumed_outgoing = OutgoingTransaction.objects.using(self.using).filter(
                is_consumed_server=True).last()
            self.batch_seq = None
            if not last_consumed_outgoing:
                self.batch_seq = self.batch_id
            else:
                self.batch_seq = last_consumed_outgoing.batch_id
            OutgoingTransaction.objects.using(self.using).filter(
                is_consumed_server=False).update(
                    batch_seq=self.batch_seq,
                    batch_id=self.batch_id)
            update_batch_info = True
        except AttributeError:
            transaction_messages.add_message(
                'error', 'Your machine have 0 transactions pending. No data to transfer.',
                network=False, permission=False)
            update_batch_info = False
        return update_batch_info

    def update_history(self, filesize=None, remote_path=None):
        """Creates history record when dumping.
        """
        try:
            history = History.objects.create(
                filename=self.filename,
                filesize=filesize,
                hostname=socket.gethostname(),
                remote_path=remote_path,
                batch_id=self.batch_id,
                filetimestamp=get_utcnow(),
                sent=False)
            history.save()
        except IntegrityError as e:
            try:
                new_filename = '{}_{}.json'.format(
                    self.hostname, str(timezone.now().strftime("%Y%m%d%H%M")))
                source_filename = join(self.path, self.filename)
                destination_file = join(self.path, new_filename)

                shutil.move(source_filename, new_filename)
                self.update_history()  # Create with a new name
                transaction_messages.add_message(
                    'success', 'Renamed {} to {}.'.format(source_filename, destination_file))
            except FileNotFoundError as e:
                transaction_messages.add_message(
                    'error', 'FileNotFoundError Got {}'.format(str(e)))
                transaction_messages.add_message(
                    ERROR, 'File got same name. Renamed from {} to {}'.format(
                        source_filename, destination_file))

    def dump_to_json(self):
        """Export outgoing transactions to a json file.
        """
        export_to_json = False
        exported = 0
        status = self.update_batch_info()
        if status:
            outgoing_transactions = OutgoingTransaction.objects.using(self.using).filter(
                is_consumed_server=False)
            outgoing_path = os.path.join(self.path, self.filename)
            try:
                with open(outgoing_path, 'w') as f:
                    json_txt = serializers.serialize(
                        "json", outgoing_transactions,
                        ensure_ascii=True, use_natural_foreign_keys=True,
                        use_natural_primary_keys=False)
                    f.write(json_txt)
                    exported = outgoing_transactions.count()
                    with transaction.atomic():
                        outgoing_transactions.update(
                            is_consumed_server=True,
                            consumer='/'.join(self.path.split('/')[:-1]),
                            consumed_datetime=get_utcnow())
                        export_to_json = True
                        transaction_messages.add_message(
                            'success', 'dumped transaction file successfully',
                            network=False, permission=False)
            except IOError as io_error:
                message = (
                    'Unable to create or write to file \'{}\'. '
                    'Got {}').format(self.path, str(io_error))
                transaction_messages.add_message(
                    'error', message, network=False, permission=False)
                export_to_json = False
            except TypeError:
                message = 'No pending transactions.'
                transaction_messages.add_message(
                    'error', message, network=False, permission=False)
                export_to_json = False
            if export_to_json:
                self.update_history()
        return export_to_json, exported
