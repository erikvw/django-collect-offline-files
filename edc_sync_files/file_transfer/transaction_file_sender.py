# from .file_connector import FileConnector
#
#
# class TransactionFileSender:
#     """Send transaction files.
#     """
#
#     def __init__(self, filename=None, **kwargs):
#         self.file_connector = FileConnector(**kwargs)
#         self.filename = filename
#         self.progress = self.file_connector.progress_status
#
#     def send(self):
#         sent = self.file_connector.copy(self.filename)
#         archived = False
#         if sent:
#             archived = self.file_connector.archive(self.filename)
#         return (sent, archived)
