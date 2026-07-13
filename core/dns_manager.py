"""DNS application and real DNS-query health measurements."""

from __future__ import annotations

import logging
import os
import random
import socket
import struct
import threading
import time
from statistics import median
from typing import Optional

from .network_adapter import AdapterInfo, NetworkAdapterDetector
from .powershell import PowerShellExecutor, quote_ps_literal
from .validation import is_valid_ipv4, normalize_ipv4

logger = logging.getLogger(__name__)
DEBUG_PERF = os.environ.get("DNS_JANTEX_DEBUG_PERF", "").lower() in {"1", "true", "yes"}


class DNSManager:
    """Privileged DNS settings plus unprivileged DNS health checks."""

    _cached_adapter_name: Optional[str] = None
    _cache_lock = threading.Lock()

    @staticmethod
    def validate_dns(address: str) -> bool:
        return is_valid_ipv4(address)

    @classmethod
    def _get_iface(cls, adapter_name: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        if adapter_name:
            return adapter_name, None
        with cls._cache_lock:
            if cls._cached_adapter_name:
                return cls._cached_adapter_name, None

        adapter = NetworkAdapterDetector.get_active_adapter()
        if not adapter:
            return None, "No active network adapter found"
        with cls._cache_lock:
            cls._cached_adapter_name = adapter.name
        return adapter.name, None

    @classmethod
    def invalidate_cache(cls) -> None:
        with cls._cache_lock:
            cls._cached_adapter_name = None

    @staticmethod
    def set_dns(primary: str, secondary: str = "", adapter_name: Optional[str] = None,
                *, flush_cache: bool = False) -> tuple[bool, str]:
        """Set and verify IPv4 DNS on one adapter.

        This method is intended to run only inside the elevated helper.
        """
        started = time.perf_counter()
        try:
            primary = normalize_ipv4(primary)
            secondary = normalize_ipv4(secondary, required=False)
        except ValueError as exc:
            return False, str(exc)

        iface, error = DNSManager._get_iface(adapter_name)
        if not iface:
            return False, error or "No active network adapter found"

        servers = [primary] + ([secondary] if secondary else [])
        expected = ", ".join(quote_ps_literal(server) for server in servers)
        iface_literal = quote_ps_literal(iface)
        script = (
            f"$expected = @({expected}); "
            f"Set-DnsClientServerAddress -InterfaceAlias {iface_literal} "
            "-ServerAddresses $expected -ErrorAction Stop; "
            f"$actual = @((Get-DnsClientServerAddress -InterfaceAlias {iface_literal} "
            "-AddressFamily IPv4 -ErrorAction Stop).ServerAddresses); "
            "if ((@(Compare-Object -ReferenceObject $expected -DifferenceObject $actual)).Count -ne 0) "
            "{ throw 'DNS verification failed after applying settings' }; "
        )
        if flush_cache:
            script += "Clear-DnsClientCache -ErrorAction Stop; "

        success, output = PowerShellExecutor.execute(script)
        if DEBUG_PERF:
            logger.debug("set_dns total: %.0fms", (time.perf_counter() - started) * 1000)
        if not success:
            DNSManager.invalidate_cache()
            return False, f"Failed to set DNS: {output}"

        message = f"DNS set to {primary}"
        if secondary:
            message += f" / {secondary}"
        return True, message

    @staticmethod
    def reset_to_dhcp(adapter_name: Optional[str] = None) -> tuple[bool, str]:
        iface, error = DNSManager._get_iface(adapter_name)
        if not iface:
            return False, error or "No active network adapter found"
        script = (
            f"Set-DnsClientServerAddress -InterfaceAlias {quote_ps_literal(iface)} "
            "-ResetServerAddresses -ErrorAction Stop"
        )
        success, output = PowerShellExecutor.execute(script)
        if not success:
            DNSManager.invalidate_cache()
            return False, f"Failed to reset DNS: {output}"
        return True, "DNS reset to automatic (DHCP)"

    @staticmethod
    def flush_dns_cache() -> tuple[bool, str]:
        success, output = PowerShellExecutor.execute("Clear-DnsClientCache -ErrorAction Stop")
        return (True, "DNS cache flushed") if success else (False, f"Failed to flush DNS: {output}")

    @staticmethod
    def get_current_dns_info() -> Optional[AdapterInfo]:
        return NetworkAdapterDetector.get_active_adapter()

    @staticmethod
    def _dns_query_packet(transaction_id: int, qname: str) -> bytes:
        labels = qname.rstrip(".").split(".")
        encoded_name = b"".join(bytes((len(label.encode("idna")),)) + label.encode("idna") for label in labels) + b"\0"
        # Standard recursive query, one A/IN question.
        return struct.pack("!HHHHHH", transaction_id, 0x0100, 1, 0, 0, 0) + encoded_name + struct.pack("!HH", 1, 1)

    @staticmethod
    def ping_dns_fast(address: str, timeout_ms: int = 1500) -> Optional[float]:
        """Measure a real UDP DNS A-query, returning latency in milliseconds."""
        try:
            address = normalize_ipv4(address)
        except ValueError:
            return None
        if timeout_ms <= 0:
            return None

        transaction_id = random.SystemRandom().randrange(0, 65536)
        packet = DNSManager._dns_query_packet(transaction_id, "example.com")
        started = time.perf_counter()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(timeout_ms / 1000.0)
                sock.connect((address, 53))
                sock.send(packet)
                response = sock.recv(4096)
        except (OSError, socket.timeout):
            return None

        if len(response) < 12:
            return None
        response_id, flags = struct.unpack("!HH", response[:4])
        is_response = bool(flags & 0x8000)
        response_code = flags & 0x000F
        if response_id != transaction_id or not is_response or response_code != 0:
            return None
        return (time.perf_counter() - started) * 1000

    @staticmethod
    def ping_dns(address: str, count: int = 2, timeout_ms: int = 1500) -> tuple[bool, Optional[float]]:
        samples = [DNSManager.ping_dns_fast(address, timeout_ms) for _ in range(max(1, count))]
        valid = [sample for sample in samples if sample is not None]
        return (True, float(median(valid))) if valid else (False, None)
