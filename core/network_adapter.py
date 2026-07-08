from dataclasses import dataclass, field
from typing import Optional
from .powershell import PowerShellExecutor


@dataclass
class AdapterInfo:
    """Represents a network adapter's information."""
    name: str
    status: str
    ip_address: Optional[str] = None
    dns_servers: list[str] = field(default_factory=list)
    is_active: bool = False


# Virtual/hidden adapters to exclude
EXCLUDED_KEYWORDS = [
    "vEthernet", "Hyper-V", "Teredo", "Tunnel", "isatap",
    "6to4", "Loopback", "Bluetooth", "Cellular", "WWAN",
    "Virtual", "VPN", "TAP", "Wintun", "WireGuard",
    "VMware", "VirtualBox", "Default Switch"
]


def _is_excluded(name: str) -> bool:
    """Check if adapter should be excluded."""
    lower = name.lower()
    return any(kw.lower() in lower for kw in EXCLUDED_KEYWORDS)


class NetworkAdapterDetector:
    """Detects and manages network adapters."""

    @staticmethod
    def get_active_adapter() -> Optional[AdapterInfo]:
        """Get the active network adapter with a real IP."""
        adapters = NetworkAdapterDetector.get_all_adapters()
        
        # Filter for active adapters with a valid IP (not APIPA)
        active_adapters = [
            a for a in adapters 
            if a.is_active and a.ip_address and not a.ip_address.startswith("169.254")
        ]
        
        if not active_adapters:
            return None

        # Prefer Wi-Fi or Ethernet
        for adapter in active_adapters:
            name_lower = adapter.name.lower()
            if "wi-fi" in name_lower or "wifi" in name_lower:
                return adapter
        for adapter in active_adapters:
            name_lower = adapter.name.lower()
            if "ethernet" in name_lower:
                return adapter

        return active_adapters[0]

    @staticmethod
    def get_all_adapters() -> list[AdapterInfo]:
        """Get all network adapters."""
        ps_cmd = (
            '$results = Get-NetAdapter | ForEach-Object { '
            '  $adapter = $_; '
            '  $ipAddress = $null; '
            '  $dnsServers = @(); '
            '  if ($adapter.Status -eq "Up") { '
            '    $ipInfo = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -First 1; '
            '    if ($ipInfo) { $ipAddress = $ipInfo.IPAddress }; '
            '    $dnsInfo = Get-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue; '
            '    if ($dnsInfo) { $dnsServers = $dnsInfo.ServerAddresses } '
            '  } '
            '  [PSCustomObject]@{ '
            '    Name = $adapter.Name; '
            '    Status = $adapter.Status; '
            '    IPAddress = $ipAddress; '
            '    DNSServers = $dnsServers; '
            '    IsActive = ($adapter.Status -eq "Up") '
            '  } '
            '}; '
            '$results | ConvertTo-Json'
        )
        
        success, data = PowerShellExecutor.execute_json(ps_cmd)
        if not success or not data:
            return []

        if isinstance(data, dict):
            data = [data]

        adapters = []
        for item in data:
            name = item.get("Name", "")
            if _is_excluded(name):
                continue
                
            adapters.append(AdapterInfo(
                name=name,
                status=item.get("Status", "Unknown"),
                ip_address=item.get("IPAddress"),
                dns_servers=item.get("DNSServers", []),
                is_active=item.get("IsActive", False)
            ))
        return adapters

    @staticmethod
    def _check_dns_static(adapter_name: str) -> bool:
        """Check if DNS is manually configured (static) vs DHCP."""
        ps_cmd = (
            f'$adapter = Get-NetAdapter | Where-Object {{ $_.Name -eq "{adapter_name}" }}; '
            'if ($adapter) { '
            '  $dns = Get-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue; '
            '  if ($dns) { $dns.PrefixOrigin } else { "Unknown" } '
            '} else { "NotFound" }'
        )
        
        success, output = PowerShellExecutor.execute(ps_cmd)
        if not success or not output:
            return False
            
        origin = output.strip().lower()
        return "manual" in origin
