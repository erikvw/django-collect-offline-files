import re
from django.core.management.base import BaseCommand
from edc_sync_files.file_transfer import FileTransfer


class Command(BaseCommand):
    '''arguments
        ip address: ip address of the machine you want copy files from.
    '''
    args = ()
    help = 'Specify ip address.'

    def add_arguments(self, parser):
        parser.add_argument('ip', nargs='+', type=str)

    def handle(self, *args, **options):
        self.copy_file_from_host(options['ip'][0])

    def copy_file_from_host(self, ip_address):
        if self.validate_ip(ip_address):
            file_transfer = FileTransfer(device_ip=ip_address)
            print("{} media file(s) to copy.".format(len(file_transfer.media_filenames_to_copy())))
            for index, filename in enumerate(file_transfer.media_filenames_to_copy()):
                file_attr = file_transfer.media_file_attributes()[index]
                index = index + 1
                print("{}. Copying {} - {} from host: {}.".format(index, filename, file_attr.get('filesize'), ip_address))
                FileTransfer(device_ip=ip_address, filename=filename).copy_media_file()
                self.stdout.write(self.style.SUCCESS('Successfully copied, "%s"' % filename))

    def validate_ip(self, ip):
        ip_address = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)
        if ip_address:
            return ip_address.group()
        else:
            if ip:
                print("Illegal ip address.")
