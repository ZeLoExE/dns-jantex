pub mod commands;
pub mod dns_manager;
pub mod network;
pub mod ping_tester;
pub mod profile_watcher;
pub mod storage;
pub mod updater;

use profile_watcher::start_profile_watcher;
use tauri::menu::{MenuBuilder, MenuItemBuilder};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::Manager;

pub fn run() {
    let app_state = storage::init_app_state();

    let app = tauri::Builder::default()
        .manage(app_state.clone())
        .setup({
            let app_state = app_state.clone();
            move |app| {
                // Ensure all webview windows are shown, unminimized, and focused on startup
                for (_, w) in app.webview_windows() {
                    let _ = w.show();
                    let _ = w.unminimize();
                    let _ = w.set_focus();
                }

                // Build Tray Menu
                let show_i = MenuItemBuilder::with_id("show", "Open DNS Jantex").build(app)?;
                let dhcp_i = MenuItemBuilder::with_id("dhcp", "Reset to DHCP").build(app)?;
                let quit_i = MenuItemBuilder::with_id("quit", "Quit").build(app)?;
                let menu = MenuBuilder::new(app)
                    .item(&show_i)
                    .separator()
                    .item(&dhcp_i)
                    .separator()
                    .item(&quit_i)
                    .build()?;

                let mut tray_builder = TrayIconBuilder::new()
                    .menu(&menu)
                    .show_menu_on_left_click(false)
                    .tooltip("DNS Jantex v2");

                if let Some(icon) = app.default_window_icon() {
                    tray_builder = tray_builder.icon(icon.clone());
                }

                let tray = tray_builder
                    .on_menu_event(move |app_handle, event| match event.id.as_ref() {
                        "show" => {
                            for (_, w) in app_handle.webview_windows() {
                                let _ = w.show();
                                let _ = w.unminimize();
                                let _ = w.set_focus();
                            }
                        }
                        "dhcp" => {
                            if let Ok(info) = network::get_active_network_info() {
                                let _ = dns_manager::reset_to_dhcp(&info.adapter_name, true);
                            }
                        }
                        "quit" => {
                            app_handle.exit(0);
                        }
                        _ => {}
                    })
                    .on_tray_icon_event(|tray, event| {
                        if let TrayIconEvent::Click {
                            button: MouseButton::Left,
                            button_state: MouseButtonState::Up,
                            ..
                        } = event
                        {
                            let app = tray.app_handle();
                            for (_, window) in app.webview_windows() {
                                let is_visible = window.is_visible().unwrap_or(false);
                                if is_visible {
                                    let _ = window.hide();
                                } else {
                                    let _ = window.show();
                                    let _ = window.unminimize();
                                    let _ = window.set_focus();
                                }
                            }
                        }
                    })
                    .build(app)?;

                // Store tray handle in app state so it is never dropped
                app.manage(tray);

                // Start background profile watcher and captive portal guard
                start_profile_watcher(app.handle().clone(), app_state.clone());

                Ok(())
            }
        })
        .on_window_event(|window, event| {
            // Hide to system tray on window close instead of exiting
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_active_network,
            commands::get_app_data,
            commands::save_dns_server,
            commands::delete_dns_server,
            commands::toggle_favorite,
            commands::apply_dns,
            commands::apply_custom_dns,
            commands::reset_dhcp,
            commands::flush_dns,
            commands::ping_dns,
            commands::ping_all_dns,
            commands::save_network_profile,
            commands::delete_network_profile,
            commands::save_settings,
            commands::check_for_updates,
            commands::skip_update_version,
            commands::is_admin_elevated,
            commands::check_captive_portal,
            commands::open_external_url,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|_app_handle, _event| {});
}
