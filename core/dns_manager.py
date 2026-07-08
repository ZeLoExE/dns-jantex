import logging
import os
import re
import sys
import threading
import time
from typing import Optional
from .network_adapter import NetworkAdapterDetector, AdapterInfo
from .powershell import PowerShellExecutor

logger = logging.getLogger(__name__)

DEBUG_PERF = os.environ.get("DNS_JANTEX_DEBUG_PERF", "").lower() in ("1", "true", "yes")


class DNSManager:
    """Manages DNS settings for network adapters."""

    # Cache: avoids re-querying adapter info on every operation
    _cached_adapter_name: Optional[str] = None
    _cache_lock = threading.Lock()

    @staticmethod
    def validate_dns(address: str) -> bool:
        """Validate an IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, address):
            return False
        parts = address.split('.')
        return all(0 <= int(part) <= 255 for part in parts)

    @classmethod
    def _get_iface(cls, adapter_name: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """Return the interface alias, using cache when possible.

        Returns (iface_name, error_or_None).
        """
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
    def invalidate_cache(cls):
        """Clear the cached adapter name so the next operation re-queries."""
        with cls._cache_lock:
            cls._cached_adapter_name = None

    @staticmethod
    def set_dns(primary: str, secondary: str = "", adapter_name: Optional[str] = None) -> tuple[bool, str]:
        """Set DNS servers and flush cache in a single PowerShell call."""
        _t0 = time.perf_counter()

        if not DNSManager.validate_dns(primary):
            return False, f"Invalid primary DNS: {primary}"
        if secondary and not DNSManager.validate_dns(secondary):
            return False, f"Invalid secondary DNS: {secondary}"

        iface, err = DNSManager._get_iface(adapter_name)
        if not iface:
            return False, err or "No active network adapter found"

        if secondary:
            dns_servers = f'"{primary}", "{secondary}"'
        else:
            dns_servers = f'"{primary}"'

        # Single combined command: set DNS + flush cache (saves 1 PowerShell spawn)
        ps_cmd = (
            f'Set-DnsClientServerAddress -InterfaceAlias "{iface}" -ServerAddresses ({dns_servers}); '
            f'ipconfig /flushdns'
        )

        success, output = PowerShellExecutor.execute(ps_cmd)
        if DEBUG_PERF:
            logger.debug("set_dns total: %.0fms (iface=%s)", (time.perf_counter() - _t0) * 1000, iface)

        if not success:
            DNSManager.invalidate_cache()
            return False, f"Failed to set DNS: {output}"

        result = f"DNS set to {primary}"
        if secondary:
            result += f" / {secondary}"
        return True, result

    @staticmethod
    def reset_to_dhcp(adapter_name: Optional[str] = None) -> tuple[bool, str]:
        """Reset DNS to automatic (DHCP) and flush cache in a single PowerShell call."""
        _t0 = time.perf_counter()

        iface, err = DNSManager._get_iface(adapter_name)
        if not iface:
            return False, err or "No active network adapter found"

        # Single combined command: reset DNS + flush cache (saves 1 PowerShell spawn)
        ps_cmd = (
            f'Set-DnsClientServerAddress -InterfaceAlias "{iface}" -ResetServerAddresses; '
            f'ipconfig /flushdns'
        )

        success, output = PowerShellExecutor.execute(ps_cmd)
        if DEBUG_PERF:
            logger.debug("reset_to_dhcp total: %.0fms (iface=%s)", (time.perf_counter() - _t0) * 1000, iface)

        if not success:
            DNSManager.invalidate_cache()
            return False, f"Failed to reset DNS: {output}"

        return True, "DNS reset to automatic (DHCP)"

    @staticmethod
    def flush_dns_cache() -> tuple[bool, str]:
        """Flush the DNS resolver cache."""
        success, output = PowerShellExecutor.execute("ipconfig /flushdns")
        return (True, "DNS cache flushed") if success else (False, f"Failed to flush DNS: {output}")

    @staticmethod
    def get_current_dns_info() -> Optional[AdapterInfo]:
        """Get current DNS configuration for the active adapter."""
        return NetworkAdapterDetector.get_active_adapter()

    @staticmethod
    def ping_dns_fast(address: str, timeout_ms: int = 1500) -> Optional[float]:
        """Fast single-packet ping using PowerShell."""
        ps_cmd = f'Test-Connection -ComputerName "{address}" -Count 1 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ResponseTime'

        success, output = PowerShellExecutor.execute(ps_cmd)
        if success and output:
            try:
                return float(output.strip())
            except ValueError:
                return None
        return None

    @staticmethod
    def ping_dns(address: str, count: int = 2) -> tuple[bool, Optional[float]]:
        """Ping a DNS server (legacy wrapper)."""
        results = []
        for _ in range(count):
            ms = DNSManager.ping_dns_fast(address)
            if ms is not None:
                results.append(ms)
        if results:
            return True, sum(results) / len(results)
        return False, None
