import os
import re

from queue import Queue

from ..transaction import FileArchiver, FileArchiverError
from .exceptions import TransactionsFileQueueError


class BaseFileQueue(Queue):

    file_archiver_cls = FileArchiver

    def __init__(self, src_path=None, dst_path=None, **kwargs):
        super().__init__(maxsize=kwargs.get('maxsize', 0))
        self.src_path = src_path
        self.dst_path = dst_path
        try:
            self.file_archiver = self.file_archiver_cls(
                src_path=src_path, dst_path=dst_path, **kwargs)
        except FileArchiverError as e:
            raise TransactionsFileQueueError(e) from e

    def __repr__(self):
        return f'{self.__class__.__name__}({self.src_path}, {self.dst_path})'

    def __str__(self):
        return self.__class__.__name__

    def next_task(self, item, **kwargs):
        pass

    def reload(self, regexes=None, **kwargs):
        """Reloads /path/to/filenames into the queue
        that match the regexes.
        """
        combined = re.compile("(" + ")|(".join(regexes) + ")", re.I)
        pending_files = os.listdir(self.src_path) or []
        pending_files.sort()
        for filename in pending_files:
            if re.match(combined, filename):
                self.put(os.path.join(self.src_path, filename))

    def archive(self, filename=None):
        try:
            self.file_archiver.archive(filename)
        except FileArchiverError as e:
            raise TransactionsFileQueueError(e) from e
