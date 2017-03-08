import os

from django.core import serializers
from django.db import transaction

from edc_base.utils import get_utcnow
from edc_sync.models import OutgoingTransaction

from .transaction_messages import transaction_messages


class TransactionDumps:

    def __init__(self, path, hostname=None, using=None):
        self.path = path
        self.hostname = hostname
        self.using = using or 'default'
        self.filename = '{}_{}.json'.format(
            self.hostname, str(get_utcnow().strftime("%Y%m%d%H%M")))

    def dump_to_json(self):
        """ export outgoing transactions to a json file """
        export_to_json = False
        exported = 0

        first_unconsumed_outgoing = OutgoingTransaction.objects.using(self.using).filter(
            is_consumed_server=False).first()
        batch_id = first_unconsumed_outgoing.tx_pk

        last_consumed_outgoing = OutgoingTransaction.objects.using(self.using).filter(
            is_consumed_server=True).last()
        batch_seq = None
        if not last_consumed_outgoing:
            batch_seq = batch_id
        else:
            batch_seq = last_consumed_outgoing.batch_id

        OutgoingTransaction.objects.using(self.using).filter(
            is_consumed_server=False).update(
                batch_seq=batch_seq,
                batch_id=batch_id)

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
            message = 'No transaction to dump.'
            transaction_messages.add_message(
                'error', message, network=False, permission=False)
            export_to_json = False
        return export_to_json, exported
