import re
import subprocess
import threading
import time
from typing import Optional
from .network_adapter import NetworkAdapterDetector, AdapterInfo


def _run(cmd: str, timeout: int = 15, retries: int = 1) -> tuple[bool, str]:
    """
    Run a command with retries and return (success, output).

    Args:
        cmd: Command to execute
        timeout: Timeout per attempt in seconds
        retries: Number of retry attempts
    """
    last_error = None
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW
            )
            out = r.stdout.strip()
            err = r.stderr.strip()
            combined = (out + "\n" + err).strip()

            if r.returncode == 0:
                return True, combined or out or err

            last_error = combined or err or out

            if any(perm_err in last_error.lower() for perm_err in [
                "no active", "not found", "invalid", "access denied"
            ]):
                return False, last_error

        except subprocess.TimeoutExpired:
            last_error = f"Command timed out after {timeout}s"
            if attempt < retries:
                time.sleep(0.2)
        except Exception as e:
            last_error = str(e)

    return False, last_error or "Command failed after retries"


def _run_netsh(cmd: str, timeout: int = 20) -> tuple[bool, str]:
    """Run a netsh command. Trusts the return code — rc=0 means success regardless of stdout text."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW
        )
        out = r.stdout.strip()
        err = r.stderr.strip()

        if r.returncode != 0:
            return False, err or out or "netsh returned non-zero exit code"

        # netsh sometimes writes warning text to stdout even on success
        # (e.g. "The configured DNS server is incorrect or does not exist")
        # — the return code is the authoritative signal, so we ignore stdout content.
        return True, err or out
    except subprocess.TimeoutExpired:
        return False, f"netsh command timed out after {timeout}s"
    except Exception as e:
        return False, str(e)


def _get_real_interface_name() -> Optional[str]:
    """Get the real Wi-Fi or Ethernet interface name for netsh."""
    try:
        output = subprocess.run(
            "netsh interface show interface",
            shell=True, capture_output=True, text=True,
            timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
        ).stdout
    except Exception:
        return None

    # Find connected interfaces, prefer Wi-Fi
    wifi_name = None
    ethernet_name = None
    first_connected = None

    for line in output.split("\n"):
        if "Connected" in line:
            parts = line.split()
            if len(parts) >= 4:
                name = " ".join(parts[3:])
                # Skip virtual adapters
                lower = name.lower()
                if any(kw in lower for kw in ["vethernet", "hyper-v", "virtual", "vpn", "tunnel"]):
                    continue
                if first_connected is None:
                    first_connected = name
                if "wi-fi" in lower or "wifi" in lower or "wireless" in lower:
                    wifi_name = name
                elif "ethernet" in lower:
                    ethernet_name = name

    return wifi_name or ethernet_name or first_connected


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
        """Set DNS servers using netsh. Clears old entries before applying new ones."""
        if not DNSManager.validate_dns(primary):
            return False, f"Invalid primary DNS: {primary}"
        if secondary and not DNSManager.validate_dns(secondary):
            return False, f"Invalid secondary DNS: {secondary}"

        iface = _get_real_interface_name()
        if not iface:
            return False, "No active network adapter found"

        # Step 1: Reset to DHCP to clear ALL existing DNS entries
        reset_cmd = f'netsh interface ip set dns name="{iface}" dhcp'
        _run_netsh(reset_cmd)

        # Step 2: Clear IPv6 DNS to avoid conflicts
        reset_v6 = f'netsh interface ipv6 set dns name="{iface}" dhcp'
        _run_netsh(reset_v6)

        # Step 3: Set the new primary DNS
        cmd1 = f'netsh interface ip set dns name="{iface}" static {primary}'
        ok1, out1 = _run_netsh(cmd1)
        if not ok1:
            return False, f"Failed to set primary DNS ({primary}): {out1}"

        # Step 4: Set secondary DNS if provided
        if secondary:
            cmd2 = f'netsh interface ip add dns name="{iface}" {secondary} index=2'
            ok2, out2 = _run_netsh(cmd2)
            if not ok2:
                return True, f"Primary DNS set to {primary} (secondary {secondary} failed: {out2})"

        # Step 6: Flush DNS cache
        _run("ipconfig /flushdns", timeout=15, retries=1)

        result = f"DNS set to {primary}"
        if secondary:
            result += f" / {secondary}"
        return True, result

    @staticmethod
    def reset_to_dhcp(adapter_name: Optional[str] = None) -> tuple[bool, str]:
        """Reset DNS to automatic (DHCP) for both IPv4 and IPv6."""
        iface = _get_real_interface_name()
        if not iface:
            return False, "No active network adapter found"

        # Reset IPv4 DNS
        cmd4 = f'netsh interface ip set dns name="{iface}" dhcp'
        ok4, out4 = _run_netsh(cmd4)

        # Reset IPv6 DNS
        cmd6 = f'netsh interface ipv6 set dns name="{iface}" dhcp'
        ok6, out6 = _run_netsh(cmd6)

        # Flush DNS cache after reset
        _run("ipconfig /flushdns", timeout=15, retries=1)

        if ok4 or ok6:
            return True, "DNS reset to automatic (DHCP)"
        else:
            return False, f"Failed to reset DNS: {out4 or out6}"

    @staticmethod
    def flush_dns_cache() -> tuple[bool, str]:
        """Flush the DNS resolver cache."""
        ok, _ = _run("ipconfig /flushdns", timeout=15)
        return (True, "DNS cache flushed") if ok else (False, "Failed to flush DNS")

    @staticmethod
    def get_current_dns_info() -> Optional[AdapterInfo]:
        """Get current DNS configuration for the active adapter."""
        return NetworkAdapterDetector.get_active_adapter()

    @staticmethod
    def ping_dns_fast(address: str, timeout_ms: int = 1500) -> Optional[float]:
        """Fast single-packet ping."""
        try:
            subprocess_timeout = max(2, timeout_ms / 1000 + 1.0)
            result = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout_ms), address],
                capture_output=True, text=True, timeout=subprocess_timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                match = re.search(r'time[=<](\d+)ms', result.stdout, re.IGNORECASE)
                if match:
                    return float(match.group(1))
            return None
        except Exception:
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
