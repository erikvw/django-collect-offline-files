import os
import tempfile
import logging

from django.test import TestCase, tag

from ..ssh_client import SSHClient, SSHClientError
from ..sftp_client import SFTPClient, SFTPClientError, logger


class TestConnector(TestCase):

    def test_localhost_trusted(self):
        ssh_client = SSHClient(remote_host='localhost', trusted_host=True)
        with ssh_client.connect() as c:
            self.assertTrue(ssh_client.connected)
            c.close()
        self.assertFalse(ssh_client.connected)

    def test_username(self):
        remote_host = '127.0.0.1'
        options = dict(remote_host=remote_host,
                       trusted_host=False,
                       username='bob',
                       timeout=1)
        trusted_host = True
        options.update(trusted_host=trusted_host)
        ssh_client = SSHClient(**options)
        try:
            with ssh_client.connect() as c:
                c.close()
        except SSHClientError as e:
            self.assertEqual(
                str(e.__cause__), f'Authentication failed.')
        else:
            self.fail('SSHClientError unexpectedly not raised')
        trusted_host = False
        options.update(trusted_host=trusted_host)
        ssh_client = SSHClient(**options)
        try:
            with ssh_client.connect() as c:
                c.close()
        except SSHClientError as e:
            self.assertEqual(
                str(e.__cause__), f'Server \'{remote_host}\' not found in known_hosts')
        else:
            self.fail('SSHClientError unexpectedly not raised')

    def test_timeout_nottrusted(self):
        remote_host = '127.0.0.1'
        ssh_client = SSHClient(remote_host=remote_host,
                               trusted_host=False, timeout=1)
        try:
            with ssh_client.connect() as c:
                c.close()
        except SSHClientError as e:
            self.assertEqual(
                str(e.__cause__), f'Server \'{remote_host}\' not found in known_hosts')
        else:
            self.fail('SSHClientError unexpectedly not raised')

    def test_timeout_trusted(self):
        ssh_client = SSHClient(remote_host='127.0.0.0',
                               trusted_host=True, timeout=1)
        try:
            with ssh_client.connect() as c:
                c.close()
        except SSHClientError as e:
            self.assertEqual(str(e.__cause__), 'timed out')
        else:
            self.fail('SSHClientError unexpectedly not raised')

    def test_timeout_not_trusted(self):
        ssh_client = SSHClient(remote_host='localhost',
                               username='thing1', timeout=1)
        try:
            with ssh_client.connect() as c:
                c.close()
        except SSHClientError as e:
            self.assertEqual(str(e.__cause__), 'Authentication failed.')
        else:
            self.fail('SSHClientError unexpectedly not raised')

    def test_sftp_closes(self):
        ssh_client = SSHClient(remote_host='localhost',
                               trusted_host=True, timeout=1)
        with ssh_client.connect() as ssh_conn:
            sftp_client = SFTPClient()
            with sftp_client.connect(ssh_conn=ssh_conn) as sftp_conn:
                sftp_conn.close()

    def test_sftp_put(self):
        ssh_client = SSHClient(remote_host='localhost',
                               trusted_host=True, timeout=1)
        _, src = tempfile.mkstemp()
        dst = tempfile.mktemp()
        with ssh_client.connect() as ssh_conn:
            sftp_client = SFTPClient()
            with sftp_client.connect(ssh_conn=ssh_conn) as sftp_conn:
                sftp_conn.put(src, dst)
        self.assertTrue(os.path.exists(dst))

    def test_sftp_put_src_ioerror(self):
        ssh_client = SSHClient(remote_host='localhost',
                               trusted_host=True, timeout=1)
        src = tempfile.mktemp()
        dst = tempfile.mktemp()
        with ssh_client.connect() as ssh_conn:
            sftp_client = SFTPClient()
            with sftp_client.connect(ssh_conn=ssh_conn) as sftp_conn:
                self.assertRaises(SFTPClientError, sftp_conn.put, src, dst)
        self.assertFalse(os.path.exists(dst))

    def test_sftp_put_dst_ioerror(self):
        ssh_client = SSHClient(remote_host='localhost',
                               trusted_host=True, timeout=1)
        src = tempfile.mktemp()
        dst = f'/badfolder/{tempfile.mktemp()}'
        with ssh_client.connect() as ssh_conn:
            sftp_client = SFTPClient()
            with sftp_client.connect(ssh_conn=ssh_conn) as sftp_conn:
                self.assertRaises(SFTPClientError, sftp_conn.put, src, dst)
        self.assertFalse(os.path.exists(dst))

    def test_sftp_progress(self):
        ssh_client = SSHClient(remote_host='localhost',
                               trusted_host=True, timeout=1)
        with ssh_client.connect() as ssh_conn:
            sftp_client = SFTPClient(verbose=True)
            with sftp_client.connect(ssh_conn=ssh_conn) as sftp_conn:
                sftp_conn.update_progress(1, 100)

    @tag('connect')
    def test_sftp_put_progress(self):
        ssh_client = SSHClient(
            remote_host='localhost', trusted_host=True, timeout=1)
        _, src = tempfile.mkstemp(text=True)
        with open(src, 'w') as fd:
            fd.write('erik' * 10000)
        src_filename = os.path.basename(src)
        src_path = os.path.dirname(src)
        dst_tmp_path = f'{tempfile.gettempdir()}/tmp'
        if not os.path.exists(dst_tmp_path):
            os.mkdir(dst_tmp_path)
        dst_path = f'{tempfile.gettempdir()}/dst'
        if not os.path.exists(dst_path):
            os.mkdir(dst_path)
        with ssh_client.connect() as ssh_conn:
            sftp_client = SFTPClient(
                verbose=True,
                dst_path=dst_path,
                dst_tmp=dst_tmp_path,
                dst_tmp_path=dst_tmp_path,
                src_path=src_path)
            with sftp_client.connect(ssh_conn=ssh_conn) as sftp_conn:
                with self.assertLogs(logger=logger, level=logging.INFO) as cm:
                    sftp_conn.copy(filename=src_filename)
        self.assertTrue(os.path.exists(os.path.join(dst_path, src_filename)))
        self.assertIsNotNone(cm.output)
