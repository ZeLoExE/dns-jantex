import re
import subprocess
import threading
import time
from typing import Optional
from .network_adapter import NetworkAdapterDetector, AdapterInfo
from .powershell import PowerShellExecutor


class DNSManager:
    """Manages DNS settings for network adapters."""

    @staticmethod
    def validate_dns(address: str) -> bool:
        """Validate an IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, address):
            return False
        parts = address.split('.')
        return all(0 <= int(part) <= 255 for part in parts)

    @staticmethod
    def set_dns(primary: str, secondary: str = "", adapter_name: Optional[str] = None) -> tuple[bool, str]:
        """Set DNS servers using PowerShell. Clears old entries before applying new ones."""
        if not DNSManager.validate_dns(primary):
            return False, f"Invalid primary DNS: {primary}"
        if secondary and not DNSManager.validate_dns(secondary):
            return False, f"Invalid secondary DNS: {secondary}"

        adapter = NetworkAdapterDetector.get_active_adapter()
        if not adapter:
            return False, "No active network adapter found"
        
        iface = adapter.name

        # Construct PowerShell command to set DNS
        # We use Set-DnsClientServerAddress which is more modern and atomic than netsh
        if secondary:
            dns_servers = f'"{primary}", "{secondary}"'
        else:
            dns_servers = f'"{primary}"'

        ps_cmd = f'Set-DnsClientServerAddress -InterfaceAlias "{iface}" -ServerAddresses ({dns_servers})'
        
        success, output = PowerShellExecutor.execute(ps_cmd)
        if not success:
            return False, f"Failed to set DNS: {output}"

        # Flush DNS cache after setting new servers
        DNSManager.flush_dns_cache()

        result = f"DNS set to {primary}"
        if secondary:
            result += f" / {secondary}"
        return True, result

    @staticmethod
    def reset_to_dhcp(adapter_name: Optional[str] = None) -> tuple[bool, str]:
        """Reset DNS to automatic (DHCP) for both IPv4 and IPv6."""
        adapter = NetworkAdapterDetector.get_active_adapter()
        if not adapter:
            return False, "No active network adapter found"
        
        iface = adapter.name

        ps_cmd = f'Set-DnsClientServerAddress -InterfaceAlias "{iface}" -ResetServerAddresses'
        
        success, output = PowerShellExecutor.execute(ps_cmd)
        if not success:
            return False, f"Failed to reset DNS: {output}"

        # Flush DNS cache after reset
        DNSManager.flush_dns_cache()

        return True, "DNS reset to automatic (DHCP)"

    @staticmethod
    def flush_dns_cache() -> tuple[bool, str]:
        """Flush the DNS resolver cache."""
        # Direct call to ipconfig is fine, but we'll use PowerShellExecutor for consistency
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
