use crate::dns_manager;
use crate::network::{self, ActiveNetworkInfo};
use crate::ping_tester::{self, test_dns_ip_latency};
use crate::profile_watcher;
use crate::storage::{self, AppData, AppSettings, AppState, DnsServer, NetworkProfile};
use crate::updater::{self, UpdateInfo};
use std::collections::HashMap;
use std::process::Command;
use tauri::State;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

const CREATE_NO_WINDOW: u32 = 0x08000000;

#[tauri::command]
pub fn get_active_network() -> Result<ActiveNetworkInfo, String> {
    network::get_active_network_info()
}

#[tauri::command]
pub async fn get_app_data(state: State<'_, AppState>) -> Result<AppData, String> {
    let data = state.read().await;
    Ok(data.clone())
}

#[tauri::command]
pub async fn save_dns_server(server: DnsServer, state: State<'_, AppState>) -> Result<(), String> {
    let mut data = state.write().await;
    if let Some(pos) = data.dns_list.iter().position(|d| d.id == server.id) {
        data.dns_list[pos] = server;
    } else {
        data.dns_list.push(server);
    }
    storage::save_storage(&data)?;
    Ok(())
}

#[tauri::command]
pub async fn delete_dns_server(id: String, state: State<'_, AppState>) -> Result<(), String> {
    let mut data = state.write().await;
    data.dns_list.retain(|d| d.id != id);
    storage::save_storage(&data)?;
    Ok(())
}

#[tauri::command]
pub async fn toggle_favorite(id: String, state: State<'_, AppState>) -> Result<bool, String> {
    let mut data = state.write().await;
    let mut new_state = false;
    if let Some(dns) = data.dns_list.iter_mut().find(|d| d.id == id) {
        dns.is_favorite = !dns.is_favorite;
        new_state = dns.is_favorite;
    }
    storage::save_storage(&data)?;
    Ok(new_state)
}

#[tauri::command]
pub async fn apply_dns(
    adapter_name: String,
    dns_id: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let (auto_flush, dns_opt) = {
        let data = state.read().await;
        let dns = data.dns_list.iter().find(|d| d.id == dns_id).cloned();
        (data.settings.auto_flush, dns)
    };

    if let Some(dns) = dns_opt {
        dns_manager::set_static_dns(
            &adapter_name,
            &dns.primary_ip,
            Some(&dns.secondary_ip),
            auto_flush,
        )
    } else {
        Err(format!("DNS server with ID '{}' not found", dns_id))
    }
}

#[tauri::command]
pub fn apply_custom_dns(
    adapter_name: String,
    primary: String,
    secondary: Option<String>,
    auto_flush: bool,
) -> Result<(), String> {
    dns_manager::set_static_dns(
        &adapter_name,
        &primary,
        secondary.as_deref(),
        auto_flush,
    )
}

#[tauri::command]
pub async fn reset_dhcp(
    adapter_name: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let auto_flush = {
        let data = state.read().await;
        data.settings.auto_flush
    };
    dns_manager::reset_to_dhcp(&adapter_name, auto_flush)
}

#[tauri::command]
pub fn flush_dns() -> Result<(), String> {
    dns_manager::flush_dns_cache()
}

#[tauri::command]
pub async fn ping_dns(dns_id: String, state: State<'_, AppState>) -> Result<i64, String> {
    let target_ip = {
        let data = state.read().await;
        data.dns_list
            .iter()
            .find(|d| d.id == dns_id)
            .map(|d| d.primary_ip.clone())
    };

    if let Some(ip) = target_ip {
        let latency = match test_dns_ip_latency(&ip, 1500).await {
            Ok(ms) => ms,
            Err(_) => -1, // Mark as timeout
        };
        let mut data = state.write().await;
        if let Some(dns) = data.dns_list.iter_mut().find(|d| d.id == dns_id) {
            dns.latency_ms = Some(latency);
        }
        let _ = storage::save_storage(&data);
        Ok(latency)
    } else {
        Err("DNS server not found".to_string())
    }
}

#[tauri::command]
pub async fn ping_all_dns(
    state: State<'_, AppState>,
) -> Result<HashMap<String, i64>, String> {
    let servers: Vec<(String, String)> = {
        let data = state.read().await;
        data.dns_list
            .iter()
            .map(|d| (d.id.clone(), d.primary_ip.clone()))
            .collect()
    };

    let results = ping_tester::bulk_test_dns_latencies(servers, 1500).await;

    let mut data = state.write().await;
    for (id, lat) in &results {
        if let Some(dns) = data.dns_list.iter_mut().find(|d| &d.id == id) {
            dns.latency_ms = Some(*lat);
        }
    }
    let _ = storage::save_storage(&data);

    Ok(results)
}

#[tauri::command]
pub async fn save_network_profile(
    profile: NetworkProfile,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let mut data = state.write().await;
    if let Some(pos) = data.network_profiles.iter().position(|p| p.id == profile.id) {
        data.network_profiles[pos] = profile;
    } else {
        data.network_profiles.push(profile);
    }
    storage::save_storage(&data)?;
    Ok(())
}

#[tauri::command]
pub async fn delete_network_profile(
    id: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let mut data = state.write().await;
    data.network_profiles.retain(|p| p.id != id);
    storage::save_storage(&data)?;
    Ok(())
}

#[tauri::command]
pub async fn save_settings(
    settings: AppSettings,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let mut data = state.write().await;
    data.settings = settings;
    storage::save_storage(&data)?;
    Ok(())
}

#[tauri::command]
pub async fn check_for_updates(state: State<'_, AppState>) -> Result<Option<UpdateInfo>, String> {
    let skipped = {
        let data = state.read().await;
        data.settings.skipped_version.clone()
    };
    updater::check_latest_release(skipped.as_deref()).await
}

#[tauri::command]
pub async fn skip_update_version(
    version: String,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let mut data = state.write().await;
    data.settings.skipped_version = Some(version);
    storage::save_storage(&data)?;
    Ok(())
}

#[tauri::command]
pub fn is_admin_elevated() -> Result<bool, String> {
    Ok(dns_manager::is_elevated())
}

#[tauri::command]
pub async fn check_captive_portal() -> Result<bool, String> {
    profile_watcher::check_captive_portal().await
}

#[tauri::command]
pub fn open_external_url(url: String) -> Result<(), String> {
    let mut cmd = Command::new("cmd");
    cmd.args(["/c", "start", &url]);

    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);

    cmd.spawn().map_err(|e| e.to_string())?;
    Ok(())
}
