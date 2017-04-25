import requests

from django.urls import reverse

from requests.exceptions import ConnectionError, HTTPError


from edc_sync.models import ReceiveDevice, Client

from .sync_report import SyncReport
from edc_sync_files.models.upload_transaction_file import UploadTransactionFile
from datetime import datetime


class SyncReportClient(SyncReport):
    """ Displays number of pending transactions in the client and number of
        times the machine have synced.
    """

    def __init__(self):
        self.report_data = []

        for client in Client.objects.all():
            try:
                ReceiveDevice.objects.get(
                    hostname=client.hostname,
                    received_date=datetime.today().date())
                received = True
            except ReceiveDevice.DoesNotExist:
                received = False
            try:
                url = 'http://' + client.hostname + reverse(
                    'edc_sync:transaction-count')
                r = requests.get(url, timeout=3)
                data = r.json()
                connected = True
            except (ConnectionError, Exception):
                pending = -1
                connected = False
            except HTTPError:
                pending = -1
                connected = True
            else:
                pending = data.get('outgoingtransaction_count')
            data = {'device': client.hostname,
                    'sync_times': self.synced_files(client.hostname),
                    'pending': pending,
                    'connected': connected,
                    'received': received,
                    'comment': client.comment}
            self.report_data.append(data)

    def synced_files(self, hostname):
        producer = '{}-default'.format(hostname)
        return [p for p in UploadTransactionFile.objects.filter(
            producer=producer,
            created__date=datetime.today().date()).order_by('-created')]
