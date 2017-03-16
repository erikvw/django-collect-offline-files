import re
import os
import shutil

from os.path import join

from django.apps import apps as django_apps

from .transaction_dumps import TransactionDumps
from .transaction_loads import TransactionLoads
from .transaction_messages import transaction_messages


class DumpToUsb:
    """Dump transaction json file to the usb.
    """

    def __init__(self, using=None):

        self.is_dumped_to_usb = False
        self.filename = None
        self.using = using
        try:
            destionation_dir = join('/Volumes/BCPP', 'transactions', 'incoming')
            if os.path.exists(destionation_dir):
                source_folder = django_apps.get_app_config('edc_sync_files').source_folder
                dump = TransactionDumps(source_folder, using=self.using)
                self.filename = dump.filename
                shutil.copy2(join(source_folder, dump.filename), destionation_dir)
                transaction_messages.add_message(
                    'success', 'Copied {} to {}.'.format(
                        join(source_folder, dump.filename),
                        join(destionation_dir, dump.filename)))
                self.is_dumped_to_usb = True
            else:
                transaction_messages.add_message(
                    'error', 'Cannot find transactions folder in the USB. ( transactions/incoming )')
        except FileNotFoundError:
            self.is_dumped_to_usb = False


class TransactionLoadUsbFile:
    """Loads transaction file from the usb.
    """
    pattern = r'^\d{0,3}\_\d{14}\.json$'

    def __init__(self):

        self.match_filename = re.compile(self.pattern)
        self.is_usb_transaction_file_loaded = False
        self.is_archived = False
        self.already_upload = False
        self.source_dir = join(
            '/Volumes/BCPP', 'transactions', 'incoming')
        self.processed_usb_files = []
        try:
            uploaded = 0
            not_upload = 0
            self.copy_to_media()
            usb_files = os.listdir(
                django_apps.get_app_config('edc_sync_files').usb_folder)
            usb_files.sort()
            for filename in usb_files or []:
                source_file = join(
                    django_apps.get_app_config(
                        'edc_sync_files').usb_folder, filename)
                if self.match_filename.match(filename):
                    load = TransactionLoads(path=source_file)
                    load.is_usb = True
                    self.already_upload = load.already_uploaded
                    if load.upload_file():
                        uploaded = uploaded + 1
                        transaction_messages.add_message(
                            'success', 'Upload the file successfully.')
                        self.processed_usb_files.append(
                            self.file_status(load, filename))
                        self.is_usb_transaction_file_loaded = True
                        self.is_archived = True
                    else:
                        self.processed_usb_files.append(
                            self.file_status(load, filename))
                        not_upload = not_upload + 1
        except FileNotFoundError as e:
            self.is_dumped_to_usb = False
            transaction_messages.add_message(
                'error', 'Cannot find transactions folder in the USB. Got '.format(str(e)))

    def file_status(self, loader, filename):
        reason = 'Failed to upload: File already' if loader.already_uploaded else None
        reason = 'Failed to upload: Incorrect transaction file sequence.' if not loader.valid else reason
        reason = 'Uploaded successfully' if loader.valid else reason
        if not reason:
            reason = 'Failed to upload with unknown reason.'
        usb_file = dict(
            {'filename': filename,
             'reason': reason})
        return usb_file

    def copy_to_media(self):
        try:
            for filename in self.usb_files():
                filename = join(self.source_dir, filename)
                shutil.move(filename, django_apps.get_app_config('edc_sync_files').usb_folder)
        except FileNotFoundError as e:
            self.is_usb_transaction_file_loaded = False
            transaction_messages.add_message(
                'error', 'Failed to load usb transaction file. Got '.format(str(e)))

    def usb_files(self):
        usb_files = []
        if os.path.exists(self.source_dir):
            for file in os.listdir(self.source_dir):
                if file.endswith(".json"):
                    usb_files.append(file)
        else:
            transaction_messages.add_message(
                'error', 'Cannot find transactions folder in the USB.')
        try:
            usb_files.sort()
        except AttributeError:
            usb_files = []
        return usb_files or []
