import json
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame, QMessageBox,
    QSystemTrayIcon, QApplication, QSplashScreen, QButtonGroup
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor, QPainter

from ui.styles import StyleSheet, Fonts
from ui.components import DNSCard, NetworkInfoCard, ActionButton
from ui.custom_dns_dialog import CustomDNSManagerDialog
from core.dns_manager import DNSManager
from core.network_adapter import NetworkAdapterDetector
from core.dns_providers import DNS_PROVIDERS
from core.custom_dns import load_custom_dns


class PingWorker(QThread):
    """Worker thread for parallel pinging DNS servers."""
    result_ready = Signal(int, object)  # index, latency_ms or None
    finished_all = Signal()

    def __init__(self, providers):
        super().__init__()
        self.providers = providers
        self._running = True

    def run(self):
        import concurrent.futures

        def ping_one(args):
            idx, provider = args
            if not self._running:
                return idx, None
            ms = DNSManager.ping_dns_fast(provider.primary, timeout_ms=1200)
            return idx, ms

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(self.providers), 20)) as pool:
            futures = [pool.submit(ping_one, (i, p)) for i, p in enumerate(self.providers)]
            for future in concurrent.futures.as_completed(futures):
                if not self._running:
                    break
                try:
                    idx, ms = future.result(timeout=3)
                    self.result_ready.emit(idx, ms)
                except Exception:
                    pass

        self.finished_all.emit()

    def stop(self):
        self._running = False


class DNSWorker(QThread):
    """Worker thread for DNS operations to keep UI responsive."""
    finished = Signal(bool, str)  # success, message

    def __init__(self, operation: str, primary: str = "", secondary: str = ""):
        super().__init__()
        self.operation = operation
        self.primary = primary
        self.secondary = secondary

    def run(self):
        try:
            if self.operation == "set":
                success, message = DNSManager.set_dns(self.primary, self.secondary)
            elif self.operation == "reset":
                success, message = DNSManager.reset_to_dhcp()
            elif self.operation == "flush":
                success, message = DNSManager.flush_dns_cache()
            else:
                success, message = False, "Unknown operation"
            
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DNS Changer")
        self.setMinimumSize(1050, 700)
        self.resize(1100, 750)

        # Load translations
        self.translations = self._load_translations()
        self.current_lang = "en"

        # Load settings
        self.settings = self._load_settings()

        # Initialize theme
        self.dark_mode = self.settings.get("dark_mode", True)
        self.style_sheet = StyleSheet(self.dark_mode)

        # Initialize components
        self.dns_card = None
        self.network_card = None
        self.ping_worker = None
        self.dns_worker = None

        # Set up UI
        self._setup_ui()
        self._apply_theme()

        # Load current DNS info
        self._refresh_dns_info()

        # Auto-apply last selected provider if enabled
        if self.settings.get("auto_apply", False):
            last_provider = self.settings.get("last_provider", 0)
            if last_provider >= 0:
                QTimer.singleShot(500, lambda: self._apply_dns_by_index(last_provider))

    def _load_translations(self) -> dict:
        """Load translations from JSON files."""
        translations = {}
        base_dir = Path(__file__).parent.parent / "translations"

        for lang in ["en", "fa"]:
            lang_file = base_dir / f"{lang}.json"
            if lang_file.exists():
                with open(lang_file, "r", encoding="utf-8") as f:
                    translations[lang] = json.load(f)

        return translations

    def _load_settings(self) -> dict:
        """Load application settings."""
        settings_file = Path(__file__).parent.parent / "config" / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_settings(self):
        """Save application settings."""
        settings_dir = Path(__file__).parent.parent / "config"
        settings_dir.mkdir(exist_ok=True)
        settings_file = settings_dir / "settings.json"

        settings = {
            "dark_mode": self.dark_mode,
            "language": self.current_lang,
            "last_provider": self._get_selected_provider_index(),
            "auto_apply": self.settings.get("auto_apply", False)
        }

        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def t(self, key: str) -> str:
        """Get translated text for the current language."""
        return self.translations.get(self.current_lang, {}).get(key, key)

    def _setup_ui(self):
        """Set up the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Title
        self.title = QLabel(self.t("app_title"))
        self.title.setStyleSheet(self.style_sheet.get_title_style())
        self.title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header_layout.addWidget(self.title)

        header_layout.addStretch()

        # Theme toggle button with icon
        self.theme_btn = QPushButton()
        self.theme_btn.setFixedSize(38, 38)
        self.theme_btn.setStyleSheet(self.style_sheet.get_icon_btn_style())
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        self._update_theme_button()
        header_layout.addWidget(self.theme_btn)

        # Language switch button with icon
        self.lang_btn = QPushButton()
        self.lang_btn.setFixedSize(38, 38)
        self.lang_btn.setStyleSheet(self.style_sheet.get_icon_btn_style())
        self.lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_btn.setToolTip("Switch Language (EN/FA)")
        self.lang_btn.clicked.connect(self._toggle_language)
        self._update_lang_button()
        header_layout.addWidget(self.lang_btn)

        main_layout.addLayout(header_layout)

        # Network info card
        self.network_card = NetworkInfoCard(self.style_sheet)
        main_layout.addWidget(self.network_card)

        # DNS settings card
        self.dns_card = DNSCard(self.style_sheet)
        self._load_all_providers()
        self.dns_card.add_custom_option()
        self.dns_card.provider_changed.connect(self._on_provider_changed)
        self.dns_card.manage_clicked.connect(self._open_custom_dns_manager)
        self.dns_card.ping_clicked.connect(self._on_ping_clicked)
        main_layout.addWidget(self.dns_card, 1)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        # Apply button
        self.apply_btn = ActionButton(self.t("apply"), self.style_sheet, primary=True)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        buttons_layout.addWidget(self.apply_btn)

        # Reset DHCP button
        self.reset_btn = ActionButton(self.t("reset_dhcp"), self.style_sheet, primary=False)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        buttons_layout.addWidget(self.reset_btn)

        # Flush DNS button
        self.flush_btn = ActionButton(self.t("flush_dns"), self.style_sheet, primary=False)
        self.flush_btn.clicked.connect(self._on_flush_clicked)
        buttons_layout.addWidget(self.flush_btn)

        main_layout.addLayout(buttons_layout)

        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(self.style_sheet.get_label_style(secondary=True))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

    def _apply_theme(self):
        """Apply the current theme to all components."""
        self.style_sheet = StyleSheet(self.dark_mode)

        self.setStyleSheet(self.style_sheet.get_main_window_style())

        if self.network_card:
            self.network_card.refresh_theme(self.style_sheet)

        if self.dns_card:
            self.dns_card.refresh_theme(self.style_sheet)

        self.apply_btn.refresh_theme(self.style_sheet)
        self.reset_btn.refresh_theme(self.style_sheet)
        self.flush_btn.refresh_theme(self.style_sheet)

        self.theme_btn.setStyleSheet(self.style_sheet.get_icon_btn_style())
        self.lang_btn.setStyleSheet(self.style_sheet.get_icon_btn_style())
        self.title.setStyleSheet(self.style_sheet.get_title_style())

        self._update_theme_button()
        self._update_lang_button()

        self.status_label.setStyleSheet(self.style_sheet.get_label_style(secondary=True))

    def _update_theme_button(self):
        """Update the theme toggle button icon."""
        if self.dark_mode:
            self.theme_btn.setText("\u2600")  # Sun icon
            self.theme_btn.setToolTip("Switch to Light Mode")
        else:
            self.theme_btn.setText("\u263E")  # Moon icon
            self.theme_btn.setToolTip("Switch to Dark Mode")

    def _update_lang_button(self):
        """Update the language button icon."""
        if self.current_lang == "en":
            self.lang_btn.setText("\U0001F310")  # Globe icon
            self.lang_btn.setToolTip("Switch to Persian")
        else:
            self.lang_btn.setText("\U0001F310")
            self.lang_btn.setToolTip("Switch to English")

    def _toggle_theme(self):
        """Toggle between dark and light mode."""
        self.dark_mode = not self.dark_mode
        self._apply_theme()
        self._save_settings()

    def _toggle_language(self):
        """Toggle between English and Persian."""
        new_lang = "fa" if self.current_lang == "en" else "en"
        self.current_lang = new_lang
        is_rtl = (new_lang == "fa")

        if is_rtl:
            self.setFont(Fonts.get_persian_font())
        else:
            self.setFont(Fonts.get_default_font())

        self._update_ui_text()
        self._update_lang_button()
        self._apply_theme()

        # Reverse all horizontal layouts for RTL
        direction = Qt.LayoutDirection.RightToLeft if is_rtl else Qt.LayoutDirection.LeftToRight
        self.setLayoutDirection(direction)
        self.network_card.set_direction(is_rtl)
        self.dns_card.set_direction(is_rtl)

        # Also reverse the header and action button rows
        for layout in self.findChildren(QHBoxLayout):
            layout.setDirection(
                QBoxLayout.Direction.RightToLeft if is_rtl
                else QBoxLayout.Direction.LeftToRight
            )

        self._save_settings()

    def _update_ui_text(self):
        """Update all UI text with current language translations."""
        self.setWindowTitle(self.t("app_title"))
        self.apply_btn.setText(self.t("apply"))
        self.reset_btn.setText(self.t("reset_dhcp"))
        self.flush_btn.setText(self.t("flush_dns"))
        if hasattr(self, 'dns_card') and self.dns_card:
            self.dns_card.ping_btn.setText(self.t("test_latency"))
            self.dns_card.manage_btn.setText("\u2795 " + self.t("manage_dns"))
            self.dns_card.sort_btn.setText(self.t("sort"))
            self.dns_card.title_label.setText(self.t("dns_settings"))

    def _refresh_dns_info(self):
        """Refresh and display current DNS configuration."""
        adapter = DNSManager.get_current_dns_info()
        if adapter:
            self.network_card.update_info(
                adapter.name,
                adapter.ip_address,
                adapter.dns_servers
            )
        else:
            self.network_card.update_info(None, None, None)

    def _load_all_providers(self):
        """Load built-in + custom DNS providers into the card."""
        # Clear existing rows
        self.dns_card.rows.clear()
        while self.dns_card.list_layout.count():
            item = self.dns_card.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.dns_card.button_group = QButtonGroup(self.dns_card)

        # Add built-in providers
        for provider in DNS_PROVIDERS:
            self.dns_card.add_provider(provider.name, provider.primary, provider.secondary, provider.category)

        # Add custom providers
        for entry in load_custom_dns():
            self.dns_card.add_provider(entry.name, entry.primary, entry.secondary)

    def _open_custom_dns_manager(self):
        """Open the Custom DNS Manager dialog."""
        dialog = CustomDNSManagerDialog(self.style_sheet, parent=self)
        dialog.dns_changed.connect(self._on_custom_dns_changed)
        dialog.exec()

    def _on_custom_dns_changed(self):
        """Handle changes in custom DNS list."""
        self._load_all_providers()
        # Re-add custom input row
        self.dns_card.add_custom_option()
        self.dns_card.refresh_theme(self.style_sheet)

    def _get_selected_provider_index(self) -> int:
        """Get the index of the currently selected provider."""
        if self.dns_card:
            for i, row in enumerate(self.dns_card.rows):
                if row.radio.isChecked():
                    return i
        return 0

    def _on_provider_changed(self, index: int):
        """Handle DNS provider selection change."""
        # Save the selection
        self._save_settings()

    def _on_apply_clicked(self):
        """Handle Apply button click."""
        primary, secondary = self.dns_card.get_selected_dns()
        if not primary:
            self._show_error(self.t("invalid_dns").format(address="None"))
            return

        # Disable buttons and show status
        self._set_buttons_enabled(False)
        self.status_label.setText("Applying DNS...")

        # Create and start worker thread
        self.dns_worker = DNSWorker("set", primary, secondary or "")
        self.dns_worker.finished.connect(self._on_dns_operation_finished)
        self.dns_worker.start()

    def _on_reset_clicked(self):
        """Handle Default DNS button click - reset to DHCP."""
        self._set_buttons_enabled(False)
        self.status_label.setText("Resetting to Default DNS...")

        # Create and start worker thread
        self.dns_worker = DNSWorker("reset")
        self.dns_worker.finished.connect(self._on_dns_operation_finished)
        self.dns_worker.start()

    def _on_flush_clicked(self):
        """Handle Flush DNS button click."""
        self._set_buttons_enabled(False)
        self.status_label.setText("Flushing DNS cache...")

        # Create and start worker thread
        self.dns_worker = DNSWorker("flush")
        self.dns_worker.finished.connect(self._on_dns_operation_finished)
        self.dns_worker.start()

    def _on_dns_operation_finished(self, success: bool, message: str):
        """Handle DNS operation completion."""
        if success:
            self._show_success(message)
            self._refresh_dns_info()
            self._play_success_sound()
        else:
            self._show_error(message)

        self._set_buttons_enabled(True)
        self.status_label.setText("")
        self.dns_worker = None

    def _on_ping_clicked(self):
        """Handle Test Latency button click."""
        if self.ping_worker and self.ping_worker.isRunning():
            return

        self.dns_card.ping_btn.setEnabled(False)
        self.dns_card.ping_btn.setText("\u23F3 Testing...")

        self.ping_worker = PingWorker(DNS_PROVIDERS)
        self.ping_worker.result_ready.connect(self._on_ping_result)
        self.ping_worker.finished_all.connect(self._on_ping_finished)
        self.ping_worker.start()

    def _on_ping_result(self, index: int, latency):
        """Handle ping result - called for each provider as it finishes."""
        if self.dns_card:
            self.dns_card.update_latency(index, latency)

    def _on_ping_finished(self):
        """Handle ping completion."""
        self.dns_card.ping_btn.setEnabled(True)
        self.dns_card.ping_btn.setText(self.t("test_latency"))

    def _apply_dns_by_index(self, index: int):
        """Apply DNS by provider index."""
        if 0 <= index < len(DNS_PROVIDERS):
            provider = DNS_PROVIDERS[index]
            # Run async to avoid blocking UI during startup
            self.dns_worker = DNSWorker("set", provider.primary, provider.secondary)
            self.dns_worker.finished.connect(self._on_dns_operation_finished)
            self.dns_worker.start()

    def _set_buttons_enabled(self, enabled: bool):
        """Enable or disable all action buttons."""
        self.apply_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        self.flush_btn.setEnabled(enabled)
        if self.dns_card:
            self.dns_card.ping_btn.setEnabled(enabled)

    def _show_success(self, message: str):
        """Show success notification."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(self.t("success"))
        msg.setText(message)
        msg.setStyleSheet(self.style_sheet.get_card_style())
        msg.exec()

    def _play_success_sound(self):
        """Play a soft confirmation chime."""
        try:
            import winsound
            import wave
            import struct
            import io
            import math

            # Generate a soft two-note chime (C5 -> E5)
            sample_rate = 22050
            duration = 0.15
            volume = 0.25

            notes = [523.25, 659.25]  # C5, E5
            all_samples = []

            for freq in notes:
                num_samples = int(sample_rate * duration)
                for i in range(num_samples):
                    t = i / sample_rate
                    # Smooth envelope (fade in/out)
                    env = math.sin(math.pi * i / num_samples)
                    sample = int(32767 * volume * env * math.sin(2 * math.pi * freq * t))
                    all_samples.append(struct.pack('<h', sample))

            # Create WAV in memory
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(all_samples))

            # Play synchronously
            wav_buf.seek(0)
            winsound.PlaySound(wav_buf.read(), winsound.SND_MEMORY | winsound.SND_ASYNC)
        except Exception:
            pass  # Silently ignore sound errors

    def _show_error(self, message: str):
        """Show error notification."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(self.t("error"))
        msg.setText(message)
        msg.setStyleSheet(self.style_sheet.get_card_style())
        msg.exec()

    def _show_warning(self, message: str):
        """Show warning notification."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(self.t("warning"))
        msg.setText(message)
        msg.setStyleSheet(self.style_sheet.get_card_style())
        msg.exec()

    def closeEvent(self, event):
        """Handle window close event."""
        # Save settings before closing
        self._save_settings()

        # Stop ping worker if running
        if self.ping_worker and self.ping_worker.isRunning():
            self.ping_worker.stop()
            self.ping_worker.wait(1000)

        # Stop DNS worker if running
        if self.dns_worker and self.dns_worker.isRunning():
            self.dns_worker.terminate()
            self.dns_worker.wait(1000)

        event.accept()
