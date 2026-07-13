import struct

from core.dns_manager import DNSManager


class FakeSocket:
    last_timeout = None

    def __init__(self, *args, **kwargs):
        self.sent = b""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def settimeout(self, timeout):
        FakeSocket.last_timeout = timeout

    def connect(self, address):
        assert address == ("1.1.1.1", 53)

    def send(self, packet):
        self.sent = packet

    def recv(self, size):
        # Matching transaction ID, QR=1 and RCODE=0.
        return self.sent[:2] + struct.pack("!H", 0x8180) + b"\0" * 8


def test_real_dns_probe_uses_requested_timeout(monkeypatch):
    monkeypatch.setattr("core.dns_manager.socket.socket", FakeSocket)
    latency = DNSManager.ping_dns_fast("1.1.1.1", timeout_ms=1234)
    assert latency is not None and latency >= 0
    assert FakeSocket.last_timeout == 1.234


def test_dns_probe_rejects_invalid_address():
    assert DNSManager.ping_dns_fast("999.1.1.1") is None
