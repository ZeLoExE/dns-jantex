// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;
        if !dns_jantex_lib::dns_manager::is_elevated() {
            if let Ok(exe_path) = std::env::current_exe() {
                let _ = std::process::Command::new("powershell")
                    .args([
                        "-NoProfile",
                        "-Command",
                        &format!("Start-Process -FilePath '{}' -Verb RunAs", exe_path.to_string_lossy()),
                    ])
                    .creation_flags(0x08000000) // CREATE_NO_WINDOW
                    .spawn();
                std::process::exit(0);
            }
        }
    }

    dns_jantex_lib::run();
}
