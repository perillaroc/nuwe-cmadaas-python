"""Block Python socket traffic outside loopback in the Sphinx process and kernels.

Python imports this module at startup when its directory is on PYTHONPATH. The
CI runner sets NUWE_CMADAAS_OFFLINE_DOCS=1 for the entire documentation step,
so spawned ipykernel processes inherit the same audit hook.
"""

import ipaddress
import os
import sys


ENABLED = os.environ.get("NUWE_CMADAAS_OFFLINE_DOCS") == "1"


def _local_host(host):
    if host is None:
        return True
    if isinstance(host, bytes):
        host = host.decode("ascii", errors="replace")
    if host in {"localhost", "localhost."}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _audit(event, args):
    if event in {"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyname_ex"}:
        host = args[0]
    elif event in {"socket.connect", "socket.sendto"}:
        address = args[1]
        if not isinstance(address, tuple):  # Unix-domain sockets remain available.
            return
        host = address[0]
    else:
        return
    if not _local_host(host):
        raise PermissionError("External network access is blocked in offline documentation")


if ENABLED:
    sys.addaudithook(_audit)
