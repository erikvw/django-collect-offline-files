NETWORK = 'network'
PERMISSION = 'permission'
OTHER = 'other'
ERROR = 'error'
ACTION = 'action'
SUCCESS = 'success'


class TransactionMessages:

    """Keeps track of all messages(error, success).
       messages are displayed in the view if any error occured.
    """

    def __init__(self):
        self._messages = []

    def add_message(self, message_type, message, network=False, permission=False):
        print(message_type, " ", message)
        if message_type == ERROR:
            if network:
                self._messages.append({ERROR: {NETWORK: message}})
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

transaction_messages = TransactionMessages()
