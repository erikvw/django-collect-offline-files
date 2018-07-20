from django.db.models import Q

from edc_base.utils import get_utcnow
from edc_identifier.simple_identifier import SimpleIdentifier


class ConfirmationError(Exception):
    pass


class ConfirmationCode(SimpleIdentifier):
    random_string_length = 5
    template = 'C{device_id}{random_string}'


class Confirmation:

    """A class to manage confirmation of sent / transferred transaction files.
    """

    def __init__(self, history_model=None, using=None, **kwargs):
        self.history_model = history_model
        self.using = using

    def confirm(self, batch_id=None, filename=None):
        """Flags the batch as confirmed by updating
        confirmation_datetime on the history model for this batch.
        """
        if batch_id or filename:
            export_history = self.history_model.objects.using(
                self.using).filter(
                    Q(batch_id=batch_id) | Q(filename=filename),
                    sent=True, confirmation_code__isnull=True)
        else:
            export_history = self.history_model.objects.using(self.using).filter(
                sent=True, confirmation_code__isnull=True)
        if export_history.count() == 0:
            raise ConfirmationError(
                'Nothing to do. No history of sent and unconfirmed files')
        else:
            confirmation_code = ConfirmationCode()
            export_history.update(
                confirmation_code=confirmation_code.identifier,
                confirmation_datetime=get_utcnow())
        return confirmation_code.identifier
