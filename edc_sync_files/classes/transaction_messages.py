from ..constants import ERROR, NETWORK, TRANSACTION, PERMISSION, ACTION, SUCCESS, OTHER


class TransactionMessages:

    """Keeps track of all messages(error, success).
       messages are displayed in the view if any error occured.
    """

    def __init__(self):
        self._messages = []

    def add_message(self, message_type, message, network=False, permission=False, transaction=None):
        print(message_type, " ", message)
        if message_type == ERROR:
            if network:
                self._messages.append({ERROR: {NETWORK: message}})
            elif transaction:
                self._messages.append({TRANSACTION: {PERMISSION: message}})
            else:
                self._messages.append({ERROR: {PERMISSION: message}})
        else:
            if network:
                self._messages.append({SUCCESS: {NETWORK: message}})
            elif permission:
                self._messages.append({SUCCESS: {PERMISSION: message}})
            else:
                self._messages.append({OTHER: {ACTION: message}})

    def messages(self):
        return self._messages

    def clear(self):
        self._messages = []

    def last_error_message(self):
        try:
            message = self.messages()[-1].get(ERROR) if len(self.messages()) else ''
        except IndexError:
            message = ''
        return str(message)

transaction_messages = TransactionMessages()
