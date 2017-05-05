import socket
import paramiko


from django.utils import timezone

from paramiko import AutoAddPolicy
from paramiko.ssh_exception import (
    BadHostKeyException, AuthenticationException, SSHException)


class SSHConnectMixin:

    def __init__(self, **kwargs):
        self.messages = {}

    def connect(self, host):
        """Connects the ssh instance.
        If :param:`ssh` is not provided will connect `self.ssh`.
        """
        ssh = paramiko.SSHClient()
        if self.trusted_host:
            ssh.set_missing_host_key_policy(AutoAddPolicy())
        while True:
            try:
                ssh.connect(
                    self.remote_host,
                    username=self.user,
                    timeout=5,
                    banner_timeout=5,
                    compress=True,
                )
                break
            except (socket.timeout, ConnectionRefusedError) as e:
                raise ConnectionRefusedError('ConnectionRefusedError {}. {} for {}@{}...'.format(
                    timezone.now(), str(e), self.user, self.remote_host))
            except AuthenticationException as e:
                raise AuthenticationException(
                    ' AuthenticationException Got {} for user {}@{}'.format(
                        str(e)[0:-1], self.user, self.remote_host))
            except BadHostKeyException as e:
                raise BadHostKeyException(
                    ' BadHostKeyException. Add server to known_hosts on host {}.'
                    ' Got {}.'.format(e, self.remote_host))
            except socket.gaierror:
                raise Exception(
                    'Hostname {} not known or not available'.format(
                        self.remote_host))
            except ConnectionResetError as e:
                raise ConnectionResetError(
                    ' ConnectionResetError {} for {}@{}'.format(
                        str(e), self.user, self.remote_host))
            except SSHException as e:
                raise SSHException(' SSHException {} for {}@{}'.format(
                    str(e), self.user, self.remote_host))
            except OSError as e:
                raise OSError('{} .'.format(str(e)))
        return ssh

    def reconnect(self, host):
        self.connect(host)
