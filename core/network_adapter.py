from dataclasses import dataclass, field
from typing import Optional
import subprocess
import re


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


def _run_cmd(cmd: str, timeout: int = 20) -> str:
    """Run a command and return stdout."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return r.stdout
    except Exception:
        return ""


def _is_excluded(name: str) -> bool:
    """Check if adapter should be excluded."""
    lower = name.lower()
    return any(kw.lower() in lower for kw in EXCLUDED_KEYWORDS)


class NetworkAdapterDetector:
    """Detects and manages network adapters."""

    @staticmethod
    def get_active_adapter() -> Optional[AdapterInfo]:
        """Get the active network adapter with a real IP."""
        return NetworkAdapterDetector._detect_via_ipconfig()

    @staticmethod
    def _detect_via_ipconfig() -> Optional[AdapterInfo]:
        """Detect adapter using ipconfig - most reliable method."""
        output = _run_cmd("ipconfig /all")
        if not output:
            return None

        adapters = []
        current_name = None
        current_ip = None
        current_dns = []
        skip = False

        for line in output.split("\n"):
            stripped = line.strip()

            # Adapter header: "Ethernet adapter Wi-Fi:" or "Wireless LAN adapter Wi-Fi:"
            if stripped.endswith(":") and ("adapter" in stripped.lower() or "ethernet" in stripped.lower() or "wireless" in stripped.lower()):
                # Save previous adapter if it has a valid IP
                if current_name and current_ip and not current_ip.startswith("169.254"):
                    adapters.append(AdapterInfo(
                        name=current_name, status="Up",
                        ip_address=current_ip, dns_servers=current_dns, is_active=True
                    ))

                # Check if this is a virtual adapter
                if _is_excluded(stripped):
                    skip = True
                else:
                    skip = False
                    current_name = stripped.rstrip(":")
                    current_ip = None
                    current_dns = []
                continue

            if skip:
                continue

            # IPv4 address
            if current_name and "IPv4 Address" in stripped:
                match = re.search(r'[:\s](\d+\.\d+\.\d+\.\d+)', stripped)
                if match:
                    ip = match.group(1)
                    if not ip.startswith("169.254"):
                        current_ip = ip

            # DNS servers
            if current_name and "DNS Servers" in stripped:
                match = re.search(r'[:\s](\d+\.\d+\.\d+\.\d+)', stripped)
                if match:
                    current_dns.append(match.group(1))

            # Continuation of DNS servers (indented IP on next line)
            if current_name and current_dns and re.match(r'^\s+\d+\.\d+\.\d+\.\d+', stripped):
                match = re.match(r'^\s+(\d+\.\d+\.\d+\.\d+)', stripped)
                if match:
                    current_dns.append(match.group(1))

        # Don't forget the last adapter
        if current_name and current_ip and not current_ip.startswith("169.254"):
            adapters.append(AdapterInfo(
                name=current_name, status="Up",
                ip_address=current_ip, dns_servers=current_dns, is_active=True
            ))

        if not adapters:
            return None

        # Prefer Wi-Fi or Ethernet
        best = None
        for adapter in adapters:
            name_lower = adapter.name.lower()
            if "wi-fi" in name_lower or "wifi" in name_lower:
                best = adapter
                break
        if not best:
            for adapter in adapters:
                name_lower = adapter.name.lower()
                if "ethernet" in name_lower:
                    best = adapter
                    break
        if not best:
            best = adapters[0]

        # Always show the DNS servers that are actually in use (static or DHCP-assigned)
        return best

    @staticmethod
    def _check_dns_static(adapter_name: str) -> bool:
        """Check if DNS is manually configured (static) vs DHCP."""
        # ipconfig gives names like "Wireless LAN adapter Wi-Fi"
        # netsh expects just "Wi-Fi" — extract the part after "adapter "
        netsh_name = adapter_name
        if "adapter " in adapter_name.lower():
            idx = adapter_name.lower().index("adapter ") + len("adapter ")
            netsh_name = adapter_name[idx:]

        # Use netsh to check DNS configuration type
        output = _run_cmd(f'netsh interface ip show dnsservers name="{netsh_name}"')
        if not output:
            return False

        # If it says "DNS servers configured through DHCP" or contains "DHCP", it's automatic
        lower = output.lower()
        if "dhcp" in lower and "static" not in lower:
            return False
        if "obtain dns" in lower:
            return False

        # Check for actual IP addresses (static DNS)
        ips = re.findall(r'\d+\.\d+\.\d+\.\d+', output)
        return len(ips) > 0

    @staticmethod
    def get_all_adapters() -> list[AdapterInfo]:
        """Get all network adapters."""
        output = _run_cmd("netsh interface show interface")
        adapters = []
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) >= 4 and "Connected" in line:
                name = " ".join(parts[3:])
                adapters.append(AdapterInfo(name=name, status="Up", is_active=True))
            elif len(parts) >= 4 and "Disconnected" in line:
                name = " ".join(parts[3:])
                adapters.append(AdapterInfo(name=name, status="Down", is_active=False))
        return adapters
