import os
import shutil


class FileArchiver:

    def __init__(self, src_path=None, dst_path=None):
        self.src_path = src_path
        self.dst_path = dst_path

    def archive(self, filename):
        shutil.move(
            os.path.join(self.src_path, filename),
            self.dst_path)
