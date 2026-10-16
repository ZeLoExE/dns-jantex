export interface DnsServer {
  id: string;
  name: string;
  primary_ip: string;
  secondary_ip: string;
  tags: string[];
  is_favorite: boolean;
  latency_ms: number | null; // null = untested, -1 = timeout/error, >0 = ms
}

export interface NetworkProfile {
  id: string;
  network_identifier: string; // SSID or Profile name / Gateway
  dns_id: string; // DnsServer id or "DHCP"
  enabled: boolean;
}

export interface AppSettings {
  auto_flush: boolean;
  start_minimized: boolean;
  auto_apply_profiles: boolean;
  captive_portal_guard: boolean;
  skipped_version: string | null;
}

export interface AppData {
  dns_list: DnsServer[];
  network_profiles: NetworkProfile[];
  settings: AppSettings;
}

export interface ActiveNetworkInfo {
  adapter_name: string;
  adapter_description: string;
  connection_type: "Wi-Fi" | "Ethernet" | string;
  network_identifier: string;
  current_dns: string[];
  dhcp_enabled: boolean;
  is_connected: boolean;
  vpn_active: boolean;
}

export interface UpdateInfo {
  current_version: string;
  latest_version: string;
  release_url: string;
  release_notes: string;
  download_url: string | null;
}

export interface CaptivePortalEvent {
  is_captive: boolean;
  network_identifier: string;
  message: string;
}

export interface ProfileAppliedEvent {
  network_identifier: string;
  dns_name: string;
}
