import paramiko
import socket

from paramiko import AutoAddPolicy
from paramiko.ssh_exception import (
    BadHostKeyException, AuthenticationException, SSHException)
from paramiko.util import ClosingContextManager


class SSHClientError(Exception):
    pass


class SSHClient(ClosingContextManager):

    def __init__(self, remote_host=None, trusted_host=None, username=None, timeout=None,
                 banner_timeout=None, compress=None, **kwargs):
        self.banner_timeout = banner_timeout or 5
        self.compress = True if compress is None else compress
        self.remote_host = remote_host
        self.timeout = timeout or 5
        self.trusted_host = True if trusted_host is None else trusted_host
        self.username = username
        self._ssh_client = paramiko.SSHClient()

    def connect(self):
        if self.trusted_host:
            self._ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            self._ssh_client.connect(
                self.remote_host,
                username=self.username,
                timeout=self.timeout,
                banner_timeout=self.banner_timeout,
                compress=self.compress)
        except (ConnectionRefusedError) as e:
            raise SSHClientError(
                f'ConnectionRefusedError. User {self.username}@{self.remote_host}. Got {e}')
        except (socket.timeout) as e:
            raise SSHClientError(
                f'socket.timeout. Host {self.username}@{self.remote_host}. Got {e}')
        except AuthenticationException as e:
            raise SSHClientError(
                f'AuthenticationException. Host {self.username}@{self.remote_host}. Got {e}')
        except BadHostKeyException as e:
            raise SSHClientError(
                f'BadHostKeyException. Add server to known_hosts for \'{self.remote_host}\'.'
                f' Got {e}.')
        except socket.gaierror as e:
            raise SSHClientError(
                f'Socket.gaierror. Host \'{self.username}@{self.remote_host}\'. Got \'{e}\'')
        except ConnectionResetError as e:
            raise SSHClientError(
                f'ConnectionResetError. User {self.username}@{self.remote_host}. Got {e}')
        except SSHException as e:
            raise SSHClientError(
                f'SSHException. User {self.username}@{self.remote_host}. Got {e}')
        except OSError as e:
            raise SSHClientError(f'OSError. Got {e} .')
        return self

    def close(self):
        self._ssh_client.close()

    @property
    def connected(self):
        s = self._ssh_client
        try:
            return s._transport.is_active()
        except AttributeError:
            return False

    def open_sftp(self):
        return self._ssh_client.open_sftp()
