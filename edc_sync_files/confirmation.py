from django.db.models import Q

from edc_base.utils import get_utcnow
from edc_identifier.simple_identifier import SimpleIdentifier


class ConfirmationError(Exception):
    pass


class BatchConfirmationCode(SimpleIdentifier):
    random_string_length = 5
    template = 'C{device_id}{random_string}'


class BatchConfirmation:

    """A class to manage confirmation of transferred transaction files.
    """

    def __init__(self, batch_id=None, filename=None, code=None, history_model=None, using=None):
        confirmation_code = BatchConfirmationCode()
        self.history_model = history_model
        try:
            self.history = self.history_model.objects.using(using).get(
                Q(batch_id=batch_id) | Q(filename=filename))
        except self.history_model.DoesNotExist:
            self.history = self.history_model.objects.using(using).get(
                confirmation_code=code)
        if not self.history.confirmation_code:
            self.code = confirmation_code.identifier
            self.history.confirmation_code = self.code
            self.history.save()
        else:
            self.code = self.history.confirmation_code

    def confirm(self):
        """Flags the batch as confirmed by updating confirmation_datetime on
        the history model for this batch.
        """
        if self.history.confirmation_code:
            self.history.confirmation_datetime = get_utcnow()
            self.history.save()
        else:
            raise ConfirmationError()
