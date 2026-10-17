use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DnsServer {
    pub id: String,
    pub name: String,
    pub primary_ip: String,
    pub secondary_ip: String,
    pub tags: Vec<String>,
    pub is_favorite: bool,
    pub latency_ms: Option<i64>, // None = untested, Some(-1) = timeout, Some(>0) = ms
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkProfile {
    pub id: String,
    pub network_identifier: String, // SSID or Profile name / Gateway
    pub dns_id: String,             // DnsServer ID or "DHCP"
    pub enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub auto_flush: bool,
    pub start_minimized: bool,
    pub auto_apply_profiles: bool,
    pub captive_portal_guard: bool,
    pub skipped_version: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppData {
    pub dns_list: Vec<DnsServer>,
    pub network_profiles: Vec<NetworkProfile>,
    pub settings: AppSettings,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            auto_flush: true,
            start_minimized: false,
            auto_apply_profiles: true,
            captive_portal_guard: true,
            skipped_version: None,
        }
    }
}

impl Default for AppData {
    fn default() -> Self {
        Self {
            dns_list: default_dns_servers(),
            network_profiles: Vec::new(),
            settings: AppSettings::default(),
        }
    }
}

pub fn default_dns_servers() -> Vec<DnsServer> {
    vec![
        DnsServer {
            id: "cloudflare".to_string(),
            name: "Cloudflare DNS".to_string(),
            primary_ip: "1.1.1.1".to_string(),
            secondary_ip: "1.0.0.1".to_string(),
            tags: vec!["Global".to_string(), "Fast".to_string(), "Privacy".to_string()],
            is_favorite: true,
            latency_ms: None,
        },
        DnsServer {
            id: "google".to_string(),
            name: "Google Public DNS".to_string(),
            primary_ip: "8.8.8.8".to_string(),
            secondary_ip: "8.8.4.4".to_string(),
            tags: vec!["Global".to_string(), "Reliable".to_string()],
            is_favorite: true,
            latency_ms: None,
        },
        DnsServer {
            id: "shecan".to_string(),
            name: "Shecan (شکن)".to_string(),
            primary_ip: "178.22.122.100".to_string(),
            secondary_ip: "185.51.200.2".to_string(),
            tags: vec!["Bypass".to_string(), "Anti-Sanction".to_string()],
            is_favorite: true,
            latency_ms: None,
        },
        DnsServer {
            id: "electro".to_string(),
            name: "Electro (الکترو)".to_string(),
            primary_ip: "78.157.42.101".to_string(),
            secondary_ip: "78.157.42.100".to_string(),
            tags: vec!["Gaming".to_string(), "Bypass".to_string()],
            is_favorite: true,
            latency_ms: None,
        },
        DnsServer {
            id: "radar".to_string(),
            name: "Radar Game (رادار گیم)".to_string(),
            primary_ip: "10.202.10.10".to_string(),
            secondary_ip: "10.202.10.11".to_string(),
            tags: vec!["Gaming".to_string(), "Anti-Sanction".to_string()],
            is_favorite: false,
            latency_ms: None,
        },
        DnsServer {
            id: "403online".to_string(),
            name: "403 Online".to_string(),
            primary_ip: "10.202.10.202".to_string(),
            secondary_ip: "10.202.10.102".to_string(),
            tags: vec!["Bypass".to_string(), "Dev".to_string()],
            is_favorite: false,
            latency_ms: None,
        },
        DnsServer {
            id: "quad9".to_string(),
            name: "Quad9".to_string(),
            primary_ip: "9.9.9.9".to_string(),
            secondary_ip: "149.112.112.112".to_string(),
            tags: vec!["Global".to_string(), "Security".to_string()],
            is_favorite: false,
            latency_ms: None,
        },
        DnsServer {
            id: "opendns".to_string(),
            name: "OpenDNS".to_string(),
            primary_ip: "208.67.222.222".to_string(),
            secondary_ip: "208.67.220.220".to_string(),
            tags: vec!["Global".to_string(), "Family".to_string()],
            is_favorite: false,
            latency_ms: None,
        },
        DnsServer {
            id: "adguard".to_string(),
            name: "AdGuard DNS".to_string(),
            primary_ip: "94.140.14.14".to_string(),
            secondary_ip: "94.140.15.15".to_string(),
            tags: vec!["AdBlock".to_string(), "Security".to_string()],
            is_favorite: false,
            latency_ms: None,
        },
        DnsServer {
            id: "controld".to_string(),
            name: "Control D".to_string(),
            primary_ip: "76.76.2.0".to_string(),
            secondary_ip: "76.76.10.0".to_string(),
            tags: vec!["Global".to_string(), "Fast".to_string()],
            is_favorite: false,
            latency_ms: None,
        },
    ]
}

pub fn get_storage_path() -> PathBuf {
    let base_dir = dirs::config_dir()
        .or_else(dirs::data_local_dir)
        .unwrap_or_else(|| PathBuf::from("."))
        .join("DNS Jantex");
    let _ = fs::create_dir_all(&base_dir);
    base_dir.join("config.json")
}

pub fn load_storage() -> AppData {
    let path = get_storage_path();
    if path.exists() {
        if let Ok(content) = fs::read_to_string(&path) {
            if let Ok(mut data) = serde_json::from_str::<AppData>(&content) {
                // Deduplicate and ensure verified default servers exist
                let defaults = default_dns_servers();
                let mut modified = false;
                for def in defaults {
                    if let Some(existing) = data.dns_list.iter_mut().find(|d| d.id == def.id) {
                        if existing.primary_ip != def.primary_ip
                            || existing.secondary_ip != def.secondary_ip
                            || existing.name != def.name
                        {
                            existing.primary_ip = def.primary_ip;
                            existing.secondary_ip = def.secondary_ip;
                            existing.name = def.name;
                            modified = true;
                        }
                    } else {
                        data.dns_list.push(def);
                        modified = true;
                    }
                }

                // Filter out any duplicate IDs
                let mut seen = std::collections::HashSet::new();
                let prev_count = data.dns_list.len();
                data.dns_list.retain(|d| seen.insert(d.id.clone()));
                if data.dns_list.len() != prev_count {
                    modified = true;
                }

                if modified {
                    let to_save = data.clone();
                    std::thread::spawn(move || {
                        let _ = save_storage(&to_save);
                    });
                }
                return data;
            }
        }
    }
    // Fast path: if JSON doesn't exist yet, return embedded default DNS list instantly (<1ms)
    let default_data = AppData::default();
    let to_save = default_data.clone();
    std::thread::spawn(move || {
        let _ = save_storage(&to_save);
    });
    default_data
}

pub fn save_storage(data: &AppData) -> Result<(), String> {
    let path = get_storage_path();
    let content = serde_json::to_string_pretty(data).map_err(|e| e.to_string())?;
    fs::write(&path, content).map_err(|e| e.to_string())?;
    Ok(())
}

pub type AppState = Arc<RwLock<AppData>>;

pub fn init_app_state() -> AppState {
    Arc::new(RwLock::new(load_storage()))
}
