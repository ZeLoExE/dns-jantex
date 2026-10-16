use crate::dns_manager;
use crate::network;
use crate::storage::AppState;
use serde::Serialize;
use std::time::Duration;
use tauri::{AppHandle, Emitter};

#[derive(Debug, Clone, Serialize)]
pub struct CaptivePortalEvent {
    pub is_captive: bool,
    pub network_identifier: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct ProfileAppliedEvent {
    pub network_identifier: String,
    pub dns_name: String,
}

/// Checks Windows NCSI endpoint for Captive Portal redirects or interception.
/// Returns Ok(true) if a Captive Portal is detected, Ok(false) if clean internet, or Err if unreachable.
pub async fn check_captive_portal() -> Result<bool, String> {
    let client = reqwest::Client::builder()
        .redirect(reqwest::redirect::Policy::none())
        .timeout(Duration::from_millis(3000))
        .build()
        .map_err(|e| e.to_string())?;

    let res = client
        .get("http://www.msftconnecttest.com/connecttest.txt")
        .send()
        .await
        .map_err(|e| format!("Connection error: {}", e))?;

    let status = res.status();
    if status.is_redirection() {
        return Ok(true); // Redirected to captive portal login page
    }

    if !status.is_success() {
        return Ok(true); // Non-200 code
    }

    let text = res.text().await.unwrap_or_default();
    if text.trim() == "Microsoft Connect Test" {
        Ok(false) // Verified clean connection
    } else {
        Ok(true) // Intercepted content
    }
}

/// Starts the background monitor for network changes and smart profiles.
pub fn start_profile_watcher(app_handle: AppHandle, state: AppState) {
    tauri::async_runtime::spawn(async move {
        let mut last_network_id = String::new();
        let mut was_captive = false;

        loop {
            tokio::time::sleep(Duration::from_secs(3)).await;

            let net_info = match network::get_active_network_info() {
                Ok(info) => info,
                Err(_) => continue,
            };

            // Emit background network update event for reactive frontend UI
            let _ = app_handle.emit("network_status_updated", &net_info);

            if !net_info.is_connected {
                continue;
            }

            let network_changed = net_info.network_identifier != last_network_id;

            if network_changed || was_captive {
                let (captive_guard_enabled, auto_apply_enabled, auto_flush, profiles, dns_list) = {
                    let storage = state.read().await;
                    (
                        storage.settings.captive_portal_guard,
                        storage.settings.auto_apply_profiles,
                        storage.settings.auto_flush,
                        storage.network_profiles.clone(),
                        storage.dns_list.clone(),
                    )
                };

                let mut is_captive = false;
                if captive_guard_enabled {
                    if let Ok(captive) = check_captive_portal().await {
                        is_captive = captive;
                    }
                }

                if is_captive {
                    was_captive = true;
                    let _ = app_handle.emit(
                        "captive_portal_status",
                        CaptivePortalEvent {
                            is_captive: true,
                            network_identifier: net_info.network_identifier.clone(),
                            message: format!(
                                "Captive Portal detected on {}. Custom DNS held until login completes.",
                                net_info.network_identifier
                            ),
                        },
                    );
                    continue; // Hold applying DNS
                } else {
                    if was_captive {
                        was_captive = false;
                        let _ = app_handle.emit(
                            "captive_portal_status",
                            CaptivePortalEvent {
                                is_captive: false,
                                network_identifier: net_info.network_identifier.clone(),
                                message: "Internet connection verified. Captive portal cleared.".to_string(),
                            },
                        );
                    }
                }

                // If network changed and auto-apply is enabled, find bound profile
                if network_changed && auto_apply_enabled {
                    if let Some(profile) = profiles
                        .iter()
                        .find(|p| p.enabled && p.network_identifier == net_info.network_identifier)
                    {
                        if profile.dns_id == "DHCP" {
                            if dns_manager::reset_to_dhcp(&net_info.adapter_name, auto_flush).is_ok() {
                                let _ = app_handle.emit(
                                    "profile_applied",
                                    ProfileAppliedEvent {
                                        network_identifier: net_info.network_identifier.clone(),
                                        dns_name: "DHCP (Automatic)".to_string(),
                                    },
                                );
                            }
                        } else if let Some(dns) = dns_list.iter().find(|d| d.id == profile.dns_id) {
                            if dns_manager::set_static_dns(
                                &net_info.adapter_name,
                                &dns.primary_ip,
                                Some(&dns.secondary_ip),
                                auto_flush,
                            )
                            .is_ok()
                            {
                                let _ = app_handle.emit(
                                    "profile_applied",
                                    ProfileAppliedEvent {
                                        network_identifier: net_info.network_identifier.clone(),
                                        dns_name: dns.name.clone(),
                                    },
                                );
                            }
                        }
                    }
                }

                last_network_id = net_info.network_identifier;
            }
        }
    });
}
