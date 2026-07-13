from dataclasses import dataclass, field
from typing import Optional
from .powershell import PowerShellExecutor, quote_ps_literal


@dataclass
class AdapterInfo:
    """Represents a network adapter's information."""
    name: str
    status: str
    ip_address: Optional[str] = None
    dns_servers: list[str] = field(default_factory=list)
    is_active: bool = False
    route_metric: int = 2_147_483_647
    is_wireless: bool = False


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

        # The lowest metric default route is the adapter Windows actually uses.
        # Name-based Wi-Fi/Ethernet preferences select the wrong interface when
        # both are connected or on localized Windows installations.
        return min(active_adapters, key=lambda adapter: (adapter.route_metric, adapter.name.lower()))

    @staticmethod
    def get_all_adapters() -> list[AdapterInfo]:
        """Get all network adapters."""
        ps_cmd = (
            '$results = Get-NetAdapter | ForEach-Object { '
            '  $adapter = $_; '
            '  $ipAddress = $null; '
            '  $dnsServers = @(); '
            '  $routeMetric = [int]::MaxValue; '
            '  if ($adapter.Status -eq "Up") { '
            '    $ipInfo = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1; '
            '    if ($ipInfo) { $ipAddress = $ipInfo.IPAddress }; '
            '    $dnsInfo = Get-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue; '
            '    if ($dnsInfo) { $dnsServers = @($dnsInfo.ServerAddresses) }; '
            '    $route = Get-NetRoute -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Sort-Object RouteMetric | Select-Object -First 1; '
            '    $ipIf = Get-NetIPInterface -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue; '
            '    if ($route) { $routeMetric = [int]$route.RouteMetric + [int]$ipIf.InterfaceMetric } '
            '  } '
            '  [PSCustomObject]@{ '
            '    Name = $adapter.Name; '
            '    Status = $adapter.Status; '
            '    IPAddress = $ipAddress; '
            '    DNSServers = $dnsServers; '
            '    IsActive = ($adapter.Status -eq "Up"); '
            '    RouteMetric = $routeMetric; '
            '    IsWireless = ([string]$adapter.PhysicalMediaType -match "802\\.11|Wireless") '
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
            if not isinstance(name, str) or _is_excluded(name):
                continue
            dns_value = item.get("DNSServers", [])
            if isinstance(dns_value, str):
                dns_servers = [dns_value]
            elif isinstance(dns_value, list):
                dns_servers = [value for value in dns_value if isinstance(value, str)]
            else:
                dns_servers = []

            adapters.append(AdapterInfo(
                name=name,
                status=item.get("Status", "Unknown"),
                ip_address=item.get("IPAddress"),
                dns_servers=dns_servers,
                is_active=bool(item.get("IsActive", False)),
                route_metric=int(item.get("RouteMetric", 2_147_483_647) or 2_147_483_647),
                is_wireless=bool(item.get("IsWireless", False)),
            ))
        return adapters

    @staticmethod
    def is_dns_already_applied(primary_dns: str, secondary_dns: str = "") -> bool:
        """Check if the adapter's current DNS already matches the profile's DNS.

        Returns True if the current DNS configuration matches (no action needed).
        Returns False if the DNS is different or if the adapter is on DHCP with custom DNS required.
        """
        adapter = NetworkAdapterDetector.get_active_adapter()
        if not adapter:
            return False

        current_dns = [d.strip() for d in adapter.dns_servers if d.strip()]

        # If profile has no DNS (DHCP), check if adapter is also on DHCP
        if not primary_dns:
            # Profile expects DHCP — if adapter has no DNS servers, it's already applied
            return len(current_dns) == 0

        # Build expected DNS list
        expected_dns = [primary_dns.strip()]
        if secondary_dns and secondary_dns.strip():
            expected_dns.append(secondary_dns.strip())

        # Compare: check if current DNS matches expected DNS (order-independent)
        current_set = set(current_dns)
        expected_set = set(expected_dns)

        return current_set == expected_set

    @staticmethod
    def _check_dns_static(adapter_name: str) -> bool:
        """Check if DNS is manually configured (static) vs DHCP."""
        adapter_literal = quote_ps_literal(adapter_name)
        ps_cmd = (
            f'$adapter = Get-NetAdapter | Where-Object {{ $_.Name -eq {adapter_literal} }}; '
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

    @staticmethod
    def get_current_wifi_ssid() -> Optional[str]:
        """Get the current Wi-Fi SSID via netsh. Returns None if not on Wi-Fi."""
        import subprocess
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=10,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
            if result.returncode != 0:
                return None
            for line in result.stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith("SSID") and ":" in stripped:
                    ssid = stripped.split(":", 1)[1].strip()
                    if ssid:
                        return ssid
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    @staticmethod
    def get_current_network_id() -> tuple[Optional[str], str]:
        """Return (network_id, network_type) for the current connection.

        For Wi-Fi: returns (SSID, "wifi")
        For Ethernet: returns (adapter_name, "ethernet")
        """
        adapter = NetworkAdapterDetector.get_active_adapter()
        if not adapter:
            return None, "unknown"

        # Only use an SSID when Wi-Fi owns Windows' preferred default route.
        # Otherwise a connected but idle Wi-Fi adapter could apply its profile
        # to the active Ethernet adapter.
        if adapter.is_wireless:
            ssid = NetworkAdapterDetector.get_current_wifi_ssid()
            return (ssid, "wifi") if ssid else (None, "unknown")
        return adapter.name, "ethernet"
