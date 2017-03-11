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

    def __init__(self):

        self.is_dumped_to_usb = False
        self.filename = None
        try:
            destionation_dir = join('/Volumes/BCPP', 'transactions', 'incoming')
            if os.path.exists(destionation_dir):
                source_folder = django_apps.get_app_config('edc_sync_files').source_folder
                dump = TransactionDumps(source_folder)
                self.filename = dump.filename
                shutil.copy2(join(source_folder, dump.filename), destionation_dir)
                transaction_messages.add_message(
                    'success', 'Copied {} to {}.'.format(
                        join(source_folder, dump.filename),
                        join(destionation_dir, dump.filename)))
                self.is_dumped_to_usb = True
            else:
                transaction_messages.add_message(
                    'error', 'Cannot find transactions folder in the USB.')
        except FileNotFoundError as e:
            self.is_dumped_to_usb = False
            transaction_messages.add_message(
                'error', 'Cannot find transactions folder in the USB. Got '.format(str(e)))


class TransactionLoadUsbFile:
    """Loads transaction file from the usb.
    """
    def __init__(self):

        self.is_usb_transaction_file_loaded = False
        self.already_upload = False
        try:
            source_dir = join('/Volumes/BCPP', 'transactions', 'incoming')
            if os.path.exists(source_dir):
                for file in os.listdir(source_dir):
                    if file.endswith(".json"):
                        source_file = join(source_dir, file)
                        load = TransactionLoads(path=source_file)
                        self.already_upload = load.already_uploaded
                        if load.upload_file():
                            load.apply_transactions()
                            self.is_usb_transaction_file_loaded = True
                            transaction_messages.add_message(
                                'success', 'Upload the file successfully.')
                        self.archive_file(source_file)
            else:
                transaction_messages.add_message(
                    'error', 'Cannot find transactions folder in the USB.')
        except FileNotFoundError as e:
            self.is_dumped_to_usb = False
            transaction_messages.add_message(
                'error', 'Cannot find transactions folder in the USB. Got '.format(str(e)))

    def archive_file(self, filename):
        if self.is_usb_transaction_file_loaded or self.already_upload:
            archive_folder = join('/Volumes/BCPP', 'transactions', 'incoming')
            try:
                shutil.move(filename, archive_folder)  # archive the file
            except FileNotFoundError as e:
                transaction_messages.add_message(
                    'error', 'Make sure archive dir exists in /Volumes/BCPP/transactions/archive Got {}'.format(str(e)))
            except Exception as e:
                print(str(e))
