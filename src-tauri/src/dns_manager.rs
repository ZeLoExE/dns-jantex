use std::process::Command;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

const CREATE_NO_WINDOW: u32 = 0x08000000;

/// Checks if the application currently has Administrator privileges.
pub fn is_elevated() -> bool {
    let mut cmd = Command::new("whoami");
    cmd.arg("/groups");

    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);

    if let Ok(output) = cmd.output() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        // S-1-16-12288 is High Mandatory Level (Admin), S-1-16-16384 is System
        stdout.contains("S-1-16-12288")
            || stdout.contains("S-1-16-16384")
            || (stdout.contains("S-1-5-32-544") && stdout.contains("Enabled group"))
    } else {
        false
    }
}

/// Flushes the Windows DNS resolver cache.
pub fn flush_dns_cache() -> Result<(), String> {
    let mut cmd = Command::new("ipconfig");
    cmd.arg("/flushdns");

    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);

    let output = cmd.output().map_err(|e| format!("Failed to flush DNS cache: {}", e))?;
    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr);
        return Err(format!("DNS Flush failed: {}", err));
    }
    Ok(())
}

/// Sets Static IPv4 DNS servers on the specified adapter.
pub fn set_static_dns(
    adapter_name: &str,
    primary_ip: &str,
    secondary_ip: Option<&str>,
    auto_flush: bool,
) -> Result<(), String> {
    // 1. Set Primary DNS
    let mut cmd_primary = Command::new("netsh");
    cmd_primary.args([
        "interface",
        "ipv4",
        "set",
        "dnsservers",
        &format!("name=\"{}\"", adapter_name),
        "static",
        primary_ip,
        "primary",
        "validate=no",
    ]);

    #[cfg(target_os = "windows")]
    cmd_primary.creation_flags(CREATE_NO_WINDOW);

    let output = cmd_primary
        .output()
        .map_err(|e| format!("Failed to execute netsh primary DNS command: {}", e))?;

    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr);
        let out = String::from_utf8_lossy(&output.stdout);
        return Err(format!(
            "Failed to set Primary DNS. Netsh output: {} {}",
            out.trim(),
            err.trim()
        ));
    }

    // 2. Set Secondary DNS if provided
    if let Some(sec_ip) = secondary_ip {
        let sec_trimmed = sec_ip.trim();
        if !sec_trimmed.is_empty() {
            let mut cmd_sec = Command::new("netsh");
            cmd_sec.args([
                "interface",
                "ipv4",
                "add",
                "dnsservers",
                &format!("name=\"{}\"", adapter_name),
                sec_trimmed,
                "index=2",
                "validate=no",
            ]);

            #[cfg(target_os = "windows")]
            cmd_sec.creation_flags(CREATE_NO_WINDOW);

            let _ = cmd_sec.output();
        }
    }

    // 3. Auto flush if enabled
    if auto_flush {
        let _ = flush_dns_cache();
    }

    Ok(())
}

/// Reverts the specified adapter to DHCP for DNS.
pub fn reset_to_dhcp(adapter_name: &str, auto_flush: bool) -> Result<(), String> {
    let mut cmd = Command::new("netsh");
    cmd.args([
        "interface",
        "ipv4",
        "set",
        "dnsservers",
        &format!("name=\"{}\"", adapter_name),
        "source=dhcp",
    ]);

    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);

    let output = cmd
        .output()
        .map_err(|e| format!("Failed to execute netsh reset DHCP command: {}", e))?;

    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr);
        let out = String::from_utf8_lossy(&output.stdout);
        return Err(format!(
            "Failed to reset DNS to DHCP. Netsh output: {} {}",
            out.trim(),
            err.trim()
        ));
    }

    if auto_flush {
        let _ = flush_dns_cache();
    }

    Ok(())
}
