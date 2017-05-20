import os


class FileArchiverError(Exception):
    pass


class FileArchiver:

    def __init__(self, src_path=None, dst_path=None, **kwargs):
        self.src_path = src_path
        self.dst_path = dst_path
        try:
            if not os.path.exists(self.src_path):
                raise FileArchiverError(
                    f'Source path does not exist. Got {self.src_path}')
        except TypeError as e:
            raise FileArchiverError(
                f'Source path does not exist. src_path={self.src_path}. Got {e}')
        try:
            if not os.path.exists(self.dst_path):
                raise FileArchiverError(
                    f'Destination path does not exist. Got {self.dst_path}')
        except TypeError as e:
            raise FileArchiverError(
                f'Destination path does not exist. dst_path={self.dst_path}. Got {e}')
        if self.src_path == self.dst_path:
            raise FileArchiverError(
                f'Source folder same as destination folder!. Got {self.src_path}')

    def archive(self, filename):
        os.rename(
            os.path.join(self.src_path, filename),
            os.path.join(self.dst_path, filename))
