from django.test import TestCase, tag

from ..ssh_client import SSHClient, SSHClientError
from ..sftp_client import SFTPClient, SFTPClientError


@tag('connect')
class TestConnector(TestCase):

    def test_localhost_trusted(self):
        ssh_client = SSHClient(remote_host='localhost', trusted_host=True)
        with ssh_client.connect() as c:
            self.assertTrue(ssh_client.connected)
            c.close()
        self.assertFalse(ssh_client.connected)

    def test_timeout_nottrusted(self):
        ssh_client = SSHClient(remote_host='127.0.0.1',
                               trusted_host=False, timeout=1)
        try:
            with ssh_client.connect() as c:
                c.close()
        except SSHClientError as e:
            self.assertIn('SSHException', str(e))
        else:
            self.fail('SSHClientError unexpectedly not raised')

    def test_timeout_trusted(self):
        ssh_client = SSHClient(remote_host='127.0.0.0',
                               trusted_host=True, timeout=1)
        try:
            with ssh_client.connect() as c:
                c.close()
        except SSHClientError as e:
            self.assertIn('socket.timeout', str(e))
        else:
            self.fail('SSHClientError unexpectedly not raised')

    def test_timeout_not_trusted(self):
        ssh_client = SSHClient(remote_host='localhost',
                               username='thing1', timeout=1)
        try:
            with ssh_client.connect() as c:
                c.close()
        except SSHClientError as e:
            self.assertIn('SSHException', str(e))
        else:
            self.fail('SSHClientError unexpectedly not raised')

    def test_sftp_closes(self):
        ssh_client = SSHClient(remote_host='localhost',
                               trusted_host=True, timeout=1)
        with ssh_client.connect() as ssh_conn:
            sftp_client = SFTPClient(ssh_conn=ssh_conn)
            with sftp_client.connect() as sftp_conn:
                sftp_conn.close()
