"""Execution-only safety hook installed before application imports."""
import ipaddress
import os
import sys


def local(host):
    if host in ('localhost', b'localhost', None):
        return True
    try:
        return ipaddress.ip_address(host.decode() if isinstance(host, bytes) else host).is_loopback
    except ValueError:
        return False


def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        name = os.path.basename(os.fsdecode(args[0]))
        flags = args[2]
        if (name == '.env' or name.startswith('.env.')) and flags & os.O_ACCMODE != os.O_WRONLY:
            raise RuntimeError('Controlled verification forbids dotenv reads')
    if event in ('socket.connect', 'socket.bind'):
        address = args[1]
        if isinstance(address, tuple) and not local(address[0]):
            raise RuntimeError('Controlled verification forbids non-loopback sockets')
    if event == 'socket.getaddrinfo' and not local(args[0]):
        raise RuntimeError('Controlled verification forbids non-loopback DNS')


sys.addaudithook(guard)
