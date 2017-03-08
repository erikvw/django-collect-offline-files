from edc_sync.models import OutgoingTransaction


def transaction_file_identifier(using='default'):

    first_unconsumed_outgoing = OutgoingTransaction.objects.using(using).filter(
        is_consumed_server=False).first()
    file_identifier = first_unconsumed_outgoing.tx_pk
    last_consumed_outgoing = OutgoingTransaction.objects.using(using).filter(
        is_consumed_server=True).last()

    previous_file_identifier = None
    if not last_consumed_outgoing:
        previous_file_identifier = file_identifier
    else:
        previous_file_identifier = last_consumed_outgoing.file_identifier

    return (previous_file_identifier, file_identifier)
