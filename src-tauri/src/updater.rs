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
        .user_agent("DNS-Jantex-Updater")
        .timeout(Duration::from_millis(8000))
        .build()
        .map_err(|e| e.to_string())?;

    let res = client
        .get("https://api.github.com/repos/ZeLoExE/dns-jantex/releases/latest")
        .send()
        .await
        .map_err(|e| format!("Updater request error: {}", e))?;

    if !res.status().is_success() {
        return Ok(None);
    }

    let release = res.json::<GitHubRelease>().await.map_err(|e| e.to_string())?;

    let latest_tag = release.tag_name.trim_start_matches('v').trim().to_string();

    // Check if user chose to skip this release
    if let Some(skipped) = skipped_version {
        if skipped.trim_start_matches('v').trim() == latest_tag {
            return Ok(None);
        }
    }

    // Compare semantic versions (e.g. 4.0.1 > 4.0.0)
    if is_newer_version(&latest_tag, &current_version) {
        let mut download_url = None;
        if let Some(assets) = release.assets {
            if let Some(exe_asset) = assets
                .iter()
                .find(|a| a.name.contains("Setup") && a.name.ends_with(".exe"))
                .or_else(|| assets.iter().find(|a| a.name.ends_with(".exe")))
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

/// Downloads the new installer from GitHub and launches it with elevation, then exits the app.
pub async fn download_and_install_update(download_url: &str) -> Result<(), String> {
    let client = reqwest::Client::builder()
        .user_agent("DNS-Jantex-Updater")
        .timeout(Duration::from_secs(300))
        .build()
        .map_err(|e| e.to_string())?;

    let res = client
        .get(download_url)
        .send()
        .await
        .map_err(|e| format!("Download request error: {}", e))?;

    if !res.status().is_success() {
        return Err(format!("Download failed with HTTP status: {}", res.status()));
    }

    let bytes = res.bytes().await.map_err(|e| format!("Failed to read update payload: {}", e))?;

    let temp_dir = std::env::temp_dir();
    let installer_path = temp_dir.join("DNS-Jantex-Update-Setup.exe");

    std::fs::write(&installer_path, &bytes)
        .map_err(|e| format!("Failed to write installer to temp directory: {}", e))?;

    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        let installer_str = installer_path.to_string_lossy().to_string();
        let current_exe = std::env::current_exe().unwrap_or_else(|_| {
            std::path::PathBuf::from(r"C:\Program Files\DNS Jantex\DNS Jantex.exe")
        });
        let current_exe_str = current_exe.to_string_lossy().to_string();

        // 1. Wait briefly (ping 127.0.0.1 -n 2) for current process to release locks
        // 2. Run the NSIS installer silently (/S)
        // 3. Relaunch the updated app (current exe path or Program Files path)
        let cmd_script = format!(
            "ping 127.0.0.1 -n 2 > nul & \"{}\" /S & (if exist \"{}\" (start \"\" \"{}\") else (start \"\" \"%ProgramFiles%\\DNS Jantex\\DNS Jantex.exe\"))",
            installer_str, current_exe_str, current_exe_str
        );

        let mut cmd = std::process::Command::new("cmd");
        cmd.args(["/C", &cmd_script]);
        cmd.creation_flags(0x08000000); // CREATE_NO_WINDOW
        cmd.spawn().map_err(|e| format!("Failed to spawn update installer: {}", e))?;
    }

    // Immediately terminate the running app so NSIS installer can replace files without conflict
    std::process::exit(0);
}

/// Simple semver comparison helper (e.g. "4.0.1" > "4.0.0")
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
