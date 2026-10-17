use serde::{Deserialize, Serialize};
use std::process::Command;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

const CREATE_NO_WINDOW: u32 = 0x08000000;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActiveNetworkInfo {
    pub adapter_name: String,
    pub adapter_description: String,
    pub connection_type: String, // "Wi-Fi" or "Ethernet"
    pub network_identifier: String, // SSID or Profile Name
    pub current_dns: Vec<String>,
    pub dhcp_enabled: bool, // True only if DNS is obtained automatically via DHCP
    pub is_connected: bool,
    pub vpn_active: bool,
}

#[derive(Deserialize)]
struct RawNetworkInfo {
    #[serde(rename = "Connected")]
    connected: bool,
    #[serde(rename = "AdapterName")]
    adapter_name: Option<String>,
    #[serde(rename = "AdapterDescription")]
    adapter_description: Option<String>,
    #[serde(rename = "ConnectionType")]
    connection_type: Option<String>,
    #[serde(rename = "NetworkIdentifier")]
    network_identifier: Option<String>,
    #[serde(rename = "DnsServers")]
    dns_servers: Option<Vec<String>>,
    #[serde(rename = "DhcpEnabled")]
    dhcp_enabled: Option<bool>,
    #[serde(rename = "VpnActive")]
    vpn_active: Option<bool>,
}

pub fn get_active_network_info() -> Result<ActiveNetworkInfo, String> {
    let script = r#"
$vpnAdapters = Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object {
    $_.Status -eq 'Up' -and (
        $_.HardwareInterface -eq $false -and (
            $_.InterfaceDescription -match 'TAP|TUN|WireGuard|Wintun|Tailscale|ZeroTier|OpenVPN|PANGP|AnyConnect|Fortinet|Check Point|Cisco|NordLynx|Proton|WARP|Sing-box|v2ray|xray' -or
            $_.InterfaceAlias -match 'VPN|WireGuard|WARP|Tailscale|ZeroTier|Tun'
        )
    )
}
$vpnConn = Get-VpnConnection -ErrorAction SilentlyContinue | Where-Object { $_.ConnectionStatus -eq 'Connected' }
$vpnActive = ($null -ne $vpnAdapters -and $vpnAdapters.Count -gt 0) -or ($null -ne $vpnConn -and $vpnConn.Count -gt 0)

$physicalAdapters = Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object {
    $_.HardwareInterface -eq $true -and
    $_.InterfaceDescription -notmatch 'Virtual|Hyper-V|VMware|VirtualBox|WSL|vEthernet|Loopback|TAP|TUN|WireGuard|Wintun|Tailscale|ZeroTier'
}

$routes = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Sort-Object RouteMetric
$activeAdapter = $null

foreach ($r in $routes) {
    $matched = $physicalAdapters | Where-Object { $_.InterfaceIndex -eq $r.InterfaceIndex -and $_.Status -eq 'Up' } | Select-Object -First 1
    if ($matched) {
        $activeAdapter = $matched
        break
    }
}

if (-not $activeAdapter) {
    $activeAdapter = $physicalAdapters | Where-Object { $_.Status -eq 'Up' } | Sort-Object { if ($_.PhysicalMediaType -like '*802.11*') { 1 } else { 0 } } | Select-Object -First 1
}

if (-not $activeAdapter) {
    [PSCustomObject]@{
        Connected = $false
        VpnActive = $vpnActive
    } | ConvertTo-Json -Compress
    exit
}

$connType = if ($activeAdapter.PhysicalMediaType -like '*802.11*' -or $activeAdapter.MediaType -like '*802.11*') { 'Wi-Fi' } else { 'Ethernet' }
$ssid = ''
if ($connType -eq 'Wi-Fi') {
    $wlan = netsh wlan show interfaces
    $ssidLine = ($wlan | Where-Object { $_ -match '^\s*SSID\s*:\s*(.+)$' })
    if ($ssidLine -match ':\s*(.+)$') {
        $ssid = $matches[1].Trim()
    }
}

$profile = Get-NetConnectionProfile -InterfaceIndex $activeAdapter.InterfaceIndex -ErrorAction SilentlyContinue
$netId = if ($ssid) { $ssid } elseif ($profile.Name) { $profile.Name } else { $activeAdapter.InterfaceAlias }

$guid = $activeAdapter.InterfaceGuid
$reg = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\$guid" -ErrorAction SilentlyContinue
$isStaticDns = $false
$dnsList = @()

if ($reg -and $reg.NameServer -and ($reg.NameServer.Trim() -ne "")) {
    $isStaticDns = $true
    $dnsList = ($reg.NameServer -split '[, ]') | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' }
} else {
    $netshOut = netsh interface ipv4 show dnsservers name="$($activeAdapter.InterfaceAlias)"
    if ($netshOut -match 'Statically Configured DNS Servers:\s*(.+)') {
        $isStaticDns = $true
    }
}

if ($dnsList.Count -eq 0) {
    $dnsClient = Get-DnsClientServerAddress -InterfaceIndex $activeAdapter.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue
    if ($dnsClient) {
        $dnsList = @($dnsClient.ServerAddresses)
    }
}

$dhcpDnsEnabled = (-not $isStaticDns)

[PSCustomObject]@{
    Connected = $true
    AdapterName = $activeAdapter.InterfaceAlias
    AdapterDescription = $activeAdapter.InterfaceDescription
    ConnectionType = $connType
    NetworkIdentifier = $netId
    DnsServers = @($dnsList)
    DhcpEnabled = $dhcpDnsEnabled
    VpnActive = $vpnActive
} | ConvertTo-Json -Compress
"#;

    let mut cmd = Command::new("powershell");
    cmd.args(["-NoProfile", "-NonInteractive", "-NoLogo", "-Command", script]);

    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);

    let output = cmd.output().map_err(|e| format!("Failed to execute network query: {}", e))?;
    let stdout = String::from_utf8_lossy(&output.stdout);

    if let Ok(raw) = serde_json::from_str::<RawNetworkInfo>(stdout.trim()) {
        if !raw.connected {
            return Ok(ActiveNetworkInfo {
                adapter_name: "Disconnected".to_string(),
                adapter_description: "No active physical network interface found".to_string(),
                connection_type: "Unknown".to_string(),
                network_identifier: "No Connection".to_string(),
                current_dns: Vec::new(),
                dhcp_enabled: true,
                is_connected: false,
                vpn_active: raw.vpn_active.unwrap_or(false),
            });
        }

        Ok(ActiveNetworkInfo {
            adapter_name: raw.adapter_name.unwrap_or_else(|| "Unknown".to_string()),
            adapter_description: raw.adapter_description.unwrap_or_default(),
            connection_type: raw.connection_type.unwrap_or_else(|| "Ethernet".to_string()),
            network_identifier: raw.network_identifier.unwrap_or_else(|| "Local Network".to_string()),
            current_dns: raw.dns_servers.unwrap_or_default(),
            dhcp_enabled: raw.dhcp_enabled.unwrap_or(true),
            is_connected: true,
            vpn_active: raw.vpn_active.unwrap_or(false),
        })
    } else {
        Err(format!("Invalid network info response: {}", stdout))
    }
}
