from edc_sync.models import OutgoingTransaction


def batch_identifier(using='default'):

    first_unconsumed_outgoing = OutgoingTransaction.objects.using(using).filter(
        is_consumed_server=False).first()
    batch_id = first_unconsumed_outgoing.tx_pk
    last_consumed_outgoing = OutgoingTransaction.objects.using(using).filter(
        is_consumed_server=True).last()

    batch_seq = None
    if not last_consumed_outgoing:
        batch_seq = batch_id
    else:
        batch_seq = last_consumed_outgoing.batch_id

    return batch_seq, batch_id
