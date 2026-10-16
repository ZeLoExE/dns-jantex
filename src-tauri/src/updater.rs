use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateInfo {
    pub current_version: String,
    pub latest_version: String,
    pub release_url: String,
    pub release_notes: String,
    pub download_url: Option<String>,
}

#[derive(Deserialize)]
struct GitHubRelease {
    tag_name: String,
    html_url: String,
    body: Option<String>,
    assets: Option<Vec<GitHubAsset>>,
}

#[derive(Deserialize)]
struct GitHubAsset {
    name: String,
    browser_download_url: String,
}

pub async fn check_latest_release(skipped_version: Option<&str>) -> Result<Option<UpdateInfo>, String> {
    let current_version = env!("CARGO_PKG_VERSION").to_string();

    let client = reqwest::Client::builder()
        .user_agent("DNS-Jantex-Desktop-App")
        .timeout(Duration::from_millis(4000))
        .build()
        .map_err(|e| e.to_string())?;

    let res = client
        .get("https://api.github.com/repos/ZeLoExE/dns-jantex/releases/latest")
        .send()
        .await
        .map_err(|e| format!("Updater request error: {}", e))?;

    if !res.status().is_success() {
        return Ok(None); // e.g. 404 if no release yet, or rate limited
    }

    let release = res.json::<GitHubRelease>().await.map_err(|e| e.to_string())?;

    let latest_tag = release.tag_name.trim_start_matches('v').trim().to_string();

    // Check if user chose to skip this release
    if let Some(skipped) = skipped_version {
        if skipped.trim_start_matches('v').trim() == latest_tag {
            return Ok(None);
        }
    }

    // Compare versions (semver check or string inequality)
    if is_newer_version(&latest_tag, &current_version) {
        let mut download_url = None;
        if let Some(assets) = release.assets {
            if let Some(exe_asset) = assets
                .iter()
                .find(|a| a.name.ends_with(".exe") || a.name.ends_with(".msi"))
            {
                download_url = Some(exe_asset.browser_download_url.clone());
            }
        }

        Ok(Some(UpdateInfo {
            current_version,
            latest_version: latest_tag,
            release_url: release.html_url,
            release_notes: release.body.unwrap_or_default(),
            download_url,
        }))
    } else {
        Ok(None)
    }
}

/// Simple semver comparison helper (e.g. "2.0.1" > "2.0.0")
fn is_newer_version(latest: &str, current: &str) -> bool {
    let parse_parts = |s: &str| -> Vec<u32> {
        s.split('.')
            .map(|part| part.chars().take_while(|c| c.is_ascii_digit()).collect::<String>())
            .filter_map(|p| p.parse::<u32>().ok())
            .collect()
    };

    let latest_parts = parse_parts(latest);
    let current_parts = parse_parts(current);

    for (l, c) in latest_parts.iter().zip(current_parts.iter()) {
        if l > c {
            return true;
        }
        if l < c {
            return false;
        }
    }

    latest_parts.len() > current_parts.len()
}
