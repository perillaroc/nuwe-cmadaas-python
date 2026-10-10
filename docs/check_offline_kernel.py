"""Prove that the Sphinx environment also guards an actual Jupyter kernel."""

import os
from pathlib import Path
import sys

from jupyter_client import KernelManager


GUARD_DIR = Path(__file__).resolve().parent / "_network_guard"
PROBE = """
import socket
import sitecustomize
import sys

assert sitecustomize.ENABLED
assert sitecustomize.__file__.startswith(GUARD_DIR)
assert sys.version_info[:2] == EXPECTED_VERSION

with socket.socket() as server:
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    with socket.create_connection(server.getsockname(), timeout=2) as client:
        with server.accept()[0] as peer:
            client.sendall(b"local")
            assert peer.recv(5) == b"local"

for action in (
    lambda: socket.getaddrinfo("example.com", 80),
    lambda: socket.create_connection(("192.0.2.1", 80), timeout=1),
):
    try:
        action()
    except PermissionError:
        pass
    else:
        raise AssertionError("An external socket operation was allowed")
with socket.socket() as client:
    try:
        client.connect_ex(("192.0.2.1", 80))
    except PermissionError:
        pass
    else:
        raise AssertionError("An external connect_ex was allowed")
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
    try:
        client.sendto(b"x", ("192.0.2.1", 80))
    except PermissionError:
        pass
    else:
        raise AssertionError("An external UDP send was allowed")
print("kernel loopback allowed; external DNS, TCP and UDP blocked")
"""


def main():
    import sitecustomize

    if os.environ.get("NUWE_CMADAAS_OFFLINE_DOCS") != "1" or not sitecustomize.ENABLED:
        raise SystemExit("Set NUWE_CMADAAS_OFFLINE_DOCS=1 and prepend docs/_network_guard to PYTHONPATH")
    if Path(sitecustomize.__file__).resolve() != GUARD_DIR / "sitecustomize.py":
        raise SystemExit("The documentation socket guard is not on PYTHONPATH")

    manager = KernelManager(kernel_name="python3")
    manager.start_kernel()
    client = manager.client()
    client.start_channels()
    try:
        client.wait_for_ready(timeout=30)
        context = f"GUARD_DIR = {str(GUARD_DIR)!r}\nEXPECTED_VERSION = {sys.version_info[:2]!r}\n"
        msg_id = client.execute(context + PROBE)
        while True:
            reply = client.get_shell_msg(timeout=30)
            if reply.get("parent_header", {}).get("msg_id") != msg_id:
                continue
            if reply["content"]["status"] != "ok":
                raise RuntimeError(reply["content"].get("evalue", reply["content"]))
            break
        while True:
            message = client.get_iopub_msg(timeout=30)
            if message.get("parent_header", {}).get("msg_id") != msg_id:
                continue
            if message["msg_type"] == "stream":
                print(message["content"]["text"], end="")
            if message["msg_type"] == "status" and message["content"]["execution_state"] == "idle":
                break
    finally:
        client.stop_channels()
        manager.shutdown_kernel(now=True)


if __name__ == "__main__":
    sys.exit(main())
