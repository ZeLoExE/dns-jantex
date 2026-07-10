import json
import os
import sys
import time
import traceback
import ctypes
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame,
    QSystemTrayIcon, QApplication, QSplashScreen, QButtonGroup, QCheckBox,
    QMenu, QDialog, QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize, QPoint, QUrl
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor, QPainter, QAction

from ui.styles import StyleSheet, Fonts
from ui.components import DNSCard, NetworkInfoCard, CustomDNSCard, ActionButton, SuccessDialog
from ui.animated_menu import AnimatedMenu
from ui.custom_dns_dialog import CustomDNSManagerDialog
from core.dns_manager import DNSManager
from core.network_adapter import NetworkAdapterDetector
from core.dns_providers import DNS_PROVIDERS
from core.custom_dns import load_custom_dns, add_custom_dns
from core.updater import UpdateChecker, UpdateInfo, download_file


def _proflog(label: str, start: float):
    """Print a profiling timestamp."""
    elapsed = (time.perf_counter() - start) * 1000
    print(f"[PROFILER] {label}: {elapsed:.0f}ms", file=sys.stderr, flush=True)


def _base_dir() -> Path:
    """Return the project root — works both in dev and inside a PyInstaller bundle.
    Used for READ-ONLY resources (icons, translations, VERSION)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _app_dir() -> Path:
    """Return the directory next to the executable — for WRITABLE data (settings, config).
    In dev mode this is the same as _base_dir()."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


# Windows DWM API constants for Windows 11 effects
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2


class CustomTitleBar(QWidget):
    """Custom frameless window title bar with drag support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(40)
        self._dragging = False
        self._drag_position = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(0)

        # App icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        icon_path = _base_dir() / "assets" / "icon.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                20, 20, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.icon_label.setPixmap(pixmap)
        layout.addWidget(self.icon_label)

        # Title
        self.title_label = QLabel("DNS Changer")
        self.title_label.setStyleSheet("font-size: 12px; font-weight: 500; background: transparent; border: none;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Minimize button
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(46, 32)
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.clicked.connect(self._minimize)
        layout.addWidget(self.minimize_btn)

        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(46, 32)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self._close)
        layout.addWidget(self.close_btn)

    def _minimize(self):
        # Hide to system tray instead of minimizing to taskbar
        main = self.window()
        if hasattr(main, '_minimize_to_tray'):
            main._minimize_to_tray()
        else:
            main.showMinimized()

    def _close(self):
        self.window().close()

    def update_theme(self, style_sheet: StyleSheet):
        """Update title bar styling for current theme."""
        self.setStyleSheet(style_sheet.get_title_bar_style())
        self.title_label.setStyleSheet(f"color: {style_sheet.text}; font-size: 12px; font-weight: 500; background: transparent; border: none;")
        self.minimize_btn.setStyleSheet(style_sheet.get_minimize_btn_style())
        self.close_btn.setStyleSheet(style_sheet.get_close_btn_style())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.window().pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_position:
            self.window().move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_position = None


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


class DNSInfoWorker(QThread):
    """Background thread that fetches DNS adapter info + pings the DNS server.

    Emitted results are (adapter, provider_name, dns_servers, ping_ms_or_None).
    Running this off the main thread avoids blocking startup with 2 PowerShell calls.
    """
    info_ready = Signal(object, object, object, object)  # adapter, provider_name, dns_servers, ping_ms

    def run(self):
        try:
            adapter = DNSManager.get_current_dns_info()
            provider_name = None
            dns_servers = None
            ping_ms = None
            if adapter:
                dns_servers = adapter.dns_servers
                provider_name = _match_dns_to_providers(adapter.dns_servers)
                if dns_servers:
                    ping_ms = DNSManager.ping_dns_fast(dns_servers[0].strip(), timeout_ms=2000)
            self.info_ready.emit(adapter, provider_name, dns_servers, ping_ms)
        except Exception:
            self.info_ready.emit(None, None, None, None)


def _match_dns_to_providers(dns_servers):
    """Standalone helper to match DNS servers to a known provider name."""
    if not dns_servers:
        return None
    dns_set = set(s.strip() for s in dns_servers)
    for provider in DNS_PROVIDERS:
        provider_set = {provider.primary, provider.secondary}
        if dns_set == provider_set or dns_set.issubset(provider_set):
            return provider.name
    return "Custom DNS"


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


class UpdateCheckWorker(QThread):
    """Worker thread for checking updates in the background."""
    update_available = Signal(object)  # UpdateInfo or None
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.result = None
        self.error_msg = None

    def run(self):
        try:
            from core.updater import UpdateChecker
            checker = UpdateChecker()
            self.result = checker.check_for_update()
        except Exception as e:
            self.error_msg = str(e)


class DownloadWorker(QThread):
    """Worker thread for downloading update files."""
    progress = Signal(int, int)  # bytes_downloaded, total_bytes

    def __init__(self, url: str, dest: Path):
        super().__init__()
        self.url = url
        self.dest = dest
        self.success = False

    def run(self):
        self.success = download_file(self.url, self.dest, self._on_progress)

    def _on_progress(self, downloaded, total):
        self.progress.emit(downloaded, total)


class UpdateDialog(QDialog):
    """Dialog shown when an update is available."""

    def __init__(self, update_info: UpdateInfo, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.ss = style_sheet
        self.result = False  # True if user clicks Install

        self.setWindowTitle("Update Available")
        self.setFixedSize(480, 480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(style_sheet.get_dialog_style() if hasattr(style_sheet, 'get_dialog_style') else "")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        # Title
        title = QLabel("Update Available")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {style_sheet.text}; background: transparent;")
        layout.addWidget(title)

        # Version info
        version_text = f"Version {update_info.version} is now available."
        ver_label = QLabel(version_text)
        ver_label.setStyleSheet(f"color: {style_sheet.text}; background: transparent; font-size: 13px;")
        layout.addWidget(ver_label)

        # Release notes (scrollable, markdown stripped)
        notes = update_info.release_notes.strip()
        if notes:
            import re
            # Strip markdown formatting
            notes = re.sub(r'^#{1,6}\s+', '', notes, flags=re.MULTILINE)  # ### headers
            notes = re.sub(r'\*\*(.+?)\*\*', r'\1', notes)  # **bold**
            notes = re.sub(r'\*(.+?)\*', r'\1', notes)  # *italic*
            notes = re.sub(r'^\s*[-*]\s+', '  •  ', notes, flags=re.MULTILINE)  # - items
            notes = notes.strip()

            notes_scroll = QScrollArea()
            notes_scroll.setWidgetResizable(True)
            notes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            notes_scroll.setMaximumHeight(200)
            notes_scroll.setStyleSheet(f"""
                QScrollArea {{ border: none; background: transparent; }}
                QScrollBar:vertical {{
                    background: transparent; width: 6px;
                }}
                QScrollBar::handle:vertical {{
                    background: {style_sheet.border}; border-radius: 3px; min-height: 30px;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            """)

            notes_label = QLabel(notes)
            notes_label.setStyleSheet(f"color: {style_sheet.text_secondary}; background: transparent; font-size: 11px;")
            notes_label.setWordWrap(True)
            notes_label.setAlignment(Qt.AlignmentFlag.AlignTop)
            notes_scroll.setWidget(notes_label)
            layout.addWidget(notes_scroll, 1)

        # Size info
        if update_info.size_bytes > 0:
            size_mb = update_info.size_bytes / (1024 * 1024)
            size_label = QLabel(f"Download size: {size_mb:.1f} MB")
            size_label.setStyleSheet(f"color: {style_sheet.text_secondary}; background: transparent; font-size: 11px;")
            layout.addWidget(size_label)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background-color: {style_sheet.border};
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background-color: {style_sheet.accent};
            }}
        """)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {style_sheet.text_secondary}; background: transparent; font-size: 11px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.later_btn = QPushButton("Later")
        self.later_btn.setFixedHeight(36)
        self.later_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.later_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {style_sheet.card};
                color: {style_sheet.text};
                border: 1px solid {style_sheet.border};
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {style_sheet.accent};
            }}
        """)
        self.later_btn.clicked.connect(self._on_later)
        btn_layout.addWidget(self.later_btn)

        self.install_btn = QPushButton("Install Now")
        self.install_btn.setFixedHeight(36)
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {style_sheet.accent};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {style_sheet.accent_hover};
            }}
        """)
        self.install_btn.clicked.connect(self._on_install)
        btn_layout.addWidget(self.install_btn)

        layout.addLayout(btn_layout)

    def _on_later(self):
        self.result = False
        self.reject()

    def _on_install(self):
        self.result = True
        self.accept()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        _t_init = time.perf_counter()

        # Frameless window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Window
        )
        self.setWindowTitle("DNS Changer")
        self.setFixedSize(1050, 775)

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
        self.title_bar = None
        self._dns_info_worker = None

        # Analytics state
        self._dns_applied_at = None
        self._dns_success_count = 0
        self._dns_fail_count = 0
        self._last_adapter_name = None  # track adapter changes for uptime reset

        # Update check state
        self._update_checking = False

        # Set up UI
        _proflog("MainWindow pre-_setup_ui", _t_init)
        self._setup_ui()
        _proflog("MainWindow _setup_ui", _t_init)
        self._apply_theme()
        _proflog("MainWindow _apply_theme", _t_init)

        # Build the overflow menu
        self._build_overflow_menu()

        # Enable Windows 11 DWM effects (shadow + rounded corners)
        self._setup_dwm()

        # System tray setup
        self._setup_system_tray()
        _proflog("MainWindow pre-_refresh_dns_info", _t_init)

        # Load current DNS info in background thread (non-blocking)
        self._refresh_dns_info_async()
        _proflog("MainWindow total __init__", _t_init)

        # Auto-apply last selected provider if enabled
        if self.settings.get("auto_apply", False):
            last_provider = self.settings.get("last_provider", 0)
            if last_provider >= 0:
                QTimer.singleShot(500, lambda: self._apply_dns_by_index(last_provider))

        # Periodic DNS status check (every 30 seconds)
        self._dns_status_timer = QTimer(self)
        self._dns_status_timer.timeout.connect(self._periodic_dns_check)
        self._dns_status_timer.start(30000)

        # Live uptime display (every 1 second, pure local computation)
        self._uptime_timer = QTimer(self)
        self._uptime_timer.timeout.connect(self._tick_uptime)
        self._uptime_timer.start(1000)

        # Auto-update check on startup (silent, after 5 seconds)
        if self.settings.get("auto_update_check", True):
            QTimer.singleShot(5000, lambda: self._check_for_updates(silent=True))

    # SVG icon cache: (name, color) -> QIcon — avoids re-reading + re-rendering on every call
    _icon_cache: dict[tuple[str, str | None], QIcon] = {}

    def _load_icon(self, name: str, color: str = None) -> QIcon:
        """Load an SVG icon, replacing currentColor with the given color. Uses a cache."""
        cache_key = (name, color)
        cached = MainWindow._icon_cache.get(cache_key)
        if cached is not None:
            return cached

        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtGui import QImage, QPainter, QPixmap
        from PySide6.QtCore import QByteArray
        path = _base_dir() / "assets" / "icons" / f"{name}.svg"
        data = path.read_bytes().decode("utf-8")
        if color:
            data = data.replace("currentColor", color)
        renderer = QSvgRenderer(QByteArray(data.encode("utf-8")))
        if not renderer.isValid():
            return QIcon()
        img = QImage(48, 48, QImage.Format.Format_ARGB32)
        img.fill(0)
        painter = QPainter(img)
        renderer.render(painter)
        painter.end()
        icon = QIcon(QPixmap.fromImage(img))
        MainWindow._icon_cache[cache_key] = icon
        return icon

    def _load_translations(self) -> dict:
        """Load translations from JSON files."""
        translations = {}
        base_dir = _base_dir() / "translations"

        for lang in ["en", "fa"]:
            lang_file = base_dir / f"{lang}.json"
            if lang_file.exists():
                with open(lang_file, "r", encoding="utf-8") as f:
                    translations[lang] = json.load(f)

        return translations

    def _load_settings(self) -> dict:
        """Load application settings."""
        settings_file = _app_dir() / "config" / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_settings(self):
        """Save application settings."""
        settings_dir = _app_dir() / "config"
        settings_dir.mkdir(exist_ok=True)
        settings_file = settings_dir / "settings.json"

        settings = {
            "dark_mode": self.dark_mode,
            "language": self.current_lang,
            "last_provider": self._get_selected_provider_index(),
            "auto_apply": self.settings.get("auto_apply", False),
            "favorites": sorted(self.dns_card.favorites) if self.dns_card else self.settings.get("favorites", []),
            "auto_flush_dns": self.settings.get("auto_flush_dns", False),
            "auto_update_check": self.settings.get("auto_update_check", True),
        }

        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

    def t(self, key: str) -> str:
        """Get translated text for the current language."""
        return self.translations.get(self.current_lang, {}).get(key, key)

    def _setup_dwm(self):
        """Enable Windows 11 DWM effects (native shadow + rounded corners)."""
        if sys.platform != "win32":
            return

        try:
            hwnd = int(self.winId())

            # Enable rounded corners (Windows 11+)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), 4
            )

            # Enable dark mode title bar if dark theme
            if self.dark_mode:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(ctypes.c_int(1)), 4
                )
            else:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(ctypes.c_int(0)), 4
                )

            # Extend frame into client area for native shadow
            class MARGINS(ctypes.Structure):
                _fields_ = [
                    ("cxLeftWidth", ctypes.c_int),
                    ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int),
                    ("cyBottomHeight", ctypes.c_int),
                ]

            margins = MARGINS(0, 0, 1, 0)  # 1px top for shadow
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(
                hwnd, ctypes.byref(margins)
            )
        except Exception:
            pass  # Silently ignore DWM errors on older Windows

    def _setup_system_tray(self):
        """Set up the system tray icon with context menu."""
        self.tray_icon = QSystemTrayIcon(self)

        # Load the application icon for the tray
        icon_path = _base_dir() / "assets" / "icon.png"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            # Fallback: use a standard icon
            self.tray_icon.setIcon(self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            ))

        self.tray_icon.setToolTip("DNS Changer")

        # Create context menu
        tray_menu = QMenu()

        # Open action
        open_action = QAction("Open", self)
        open_action.triggered.connect(self._show_from_tray)
        tray_menu.addAction(open_action)

        # Separator
        tray_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_from_tray)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # Double-click to restore
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        """Handle tray icon activation (double-click to restore)."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_from_tray()

    def _minimize_to_tray(self):
        """Hide window to system tray."""
        self.hide()
        self.tray_icon.show()

    def _show_from_tray(self):
        """Restore and activate the main window from tray."""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _exit_from_tray(self):
        """Exit the application completely from tray menu."""
        self.tray_icon.hide()
        QApplication.quit()

    def _setup_ui(self):
        """Set up the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar (frameless window)
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Content area with margins
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 14, 24, 14)
        content_layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(14)

        # Title
        self.title = QLabel(self.t("app_title"))
        self.title.setStyleSheet(self.style_sheet.get_title_style())
        self.title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        header_layout.addWidget(self.title)

        header_layout.addStretch()

        # Menu button (three dots)
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(40, 40)
        self.menu_btn.setStyleSheet(self.style_sheet.get_icon_btn_style())
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setToolTip("Menu")
        self.menu_btn.clicked.connect(self._toggle_menu)
        header_layout.addWidget(self.menu_btn)

        content_layout.addLayout(header_layout)

        # Network info + Custom DNS cards side by side (compact, fixed height)
        top_cards_layout = QHBoxLayout()
        top_cards_layout.setSpacing(14)

        self.network_card = NetworkInfoCard(self.style_sheet)
        self.network_card.speed_test_clicked.connect(self._on_ping_clicked)
        top_cards_layout.addWidget(self.network_card, 65)

        self.custom_dns_card = CustomDNSCard(self.style_sheet)
        self.custom_dns_card.custom_dns_apply.connect(self._on_apply_custom_dns)
        self.custom_dns_card.save_preset.connect(self._on_save_preset)
        top_cards_layout.addWidget(self.custom_dns_card, 35)

        content_layout.addLayout(top_cards_layout)

        # DNS settings card (stretches to fill remaining space)
        self.dns_card = DNSCard(self.style_sheet)
        self.dns_card.favorites = set(self.settings.get("favorites", []))
        self._load_all_providers()
        self.dns_card.provider_changed.connect(self._on_provider_changed)
        self.dns_card.manage_clicked.connect(self._open_custom_dns_manager)
        self.dns_card.smart_clicked.connect(self._on_smart_connect)
        self.dns_card.favorites_changed.connect(self._on_favorites_changed)
        content_layout.addWidget(self.dns_card, 1)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)

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

        content_layout.addLayout(buttons_layout)

        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(self.style_sheet.get_label_style(secondary=True))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)

        # Add content area to main layout
        main_layout.addWidget(content_widget, 1)

    def _apply_theme(self):
        """Apply the current theme to all components."""
        self.style_sheet = StyleSheet(self.dark_mode)

        self.setStyleSheet(self.style_sheet.get_main_window_style())

        # Update title bar theme
        if self.title_bar:
            self.title_bar.update_theme(self.style_sheet)

        # Update DWM dark mode attribute
        self._setup_dwm()

        if self.network_card:
            self.network_card.refresh_theme(self.style_sheet)

        if hasattr(self, 'custom_dns_card') and self.custom_dns_card:
            self.custom_dns_card.refresh_theme(self.style_sheet)

        if self.dns_card:
            self.dns_card.refresh_theme(self.style_sheet)
            self._refresh_dns_card_icons()

        self.apply_btn.refresh_theme(self.style_sheet)
        self.reset_btn.refresh_theme(self.style_sheet)
        self.flush_btn.refresh_theme(self.style_sheet)

        self.title.setStyleSheet(self.style_sheet.get_title_style())

        if hasattr(self, 'menu_btn'):
            self.menu_btn.setStyleSheet(self.style_sheet.get_icon_btn_style())

        self.status_label.setStyleSheet(self.style_sheet.get_label_style(secondary=True))

    def _refresh_dns_card_icons(self):
        """Re-render DNS card button icons with current theme color."""
        color = self.style_sheet.text
        self.dns_card.sort_btn.setIcon(self._load_icon("sort", color))
        self.dns_card.sort_btn.setIconSize(QSize(14, 14))
        self.dns_card.manage_btn.setIcon(self._load_icon("manage", color))
        self.dns_card.manage_btn.setIconSize(QSize(14, 14))
        for row in self.dns_card.rows:
            row.copy_btn.setIcon(self._load_icon("copy", color))
            row.copy_btn.setIconSize(QSize(16, 16))
        if self.dns_card.custom_row:
            self.dns_card.custom_row.refresh_theme(self.style_sheet)

    def _build_overflow_menu(self):
        """Build the AnimatedMenu once and store it."""
        menu = AnimatedMenu(self.style_sheet, parent=self)
        icon_color = self.style_sheet.text

        # Menu title
        menu.add_title("PREFERENCES")

        # Section: MODE & LANG
        menu.add_section_header("MODE & LANG")

        # Dark Mode toggle
        self._theme_toggle = menu.add_toggle_row(
            self._load_icon("moon" if self.dark_mode else "sun", icon_color),
            "Dark Mode",
            checked=self.dark_mode
        )
        self._theme_toggle.toggle.toggled.connect(self._on_theme_toggle)

        # Language dropdown
        lang_options = ["English", "فارسی"]
        current_lang_idx = 0 if self.current_lang == "en" else 1
        self._lang_dropdown = menu.add_dropdown_row(
            self._load_icon("language", icon_color),
            "Language",
            options=lang_options,
            current_index=current_lang_idx
        )
        self._lang_dropdown.combo.currentIndexChanged.connect(self._on_language_change)

        # Auto Flush DNS
        self._auto_flush_row = menu.add_checkable_row(
            self._load_icon("flush", icon_color),
            "Auto Flush DNS",
            checked=self.settings.get("auto_flush_dns", False)
        )
        self._auto_flush_row.toggled.connect(self._on_auto_flush_toggle)

        menu.add_separator()

        # Check for Updates
        update_item = menu.add_action(self._load_icon("update", icon_color), "Check for Updates")
        update_item.clicked.connect(self._on_update_btn_clicked)

        menu.add_separator()

        # About
        about_item = menu.add_action(self._load_icon("about", icon_color), "About DNS Jantex")
        about_item.clicked.connect(self._show_about)

        # GitHub
        github_item = menu.add_action(self._load_icon("github", icon_color), "GitHub Repository")
        github_item.clicked.connect(self._open_github)

        # Donate
        donate_item = menu.add_action(self._load_icon("heart", icon_color), "Donate")
        donate_item.clicked.connect(self._open_donate)

        self._overflow_menu = menu


    def _toggle_menu(self):
        """Toggle the overflow menu open/close."""
        if self._overflow_menu.isVisible():
            self._overflow_menu.close_with_animation()
        else:
            pos = self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height()))
            self._overflow_menu.popup(pos)

    def _on_auto_flush_toggle(self, checked):
        """Handle Auto Flush DNS toggle from menu."""
        self.settings["auto_flush_dns"] = checked
        self._save_settings()

    def _on_theme_toggle(self, checked):
        """Handle Dark Mode toggle switch change."""
        self.dark_mode = checked
        self._overflow_menu.hide()
        self._apply_theme()
        self._save_settings()
        self._rebuild_menu()

    def _on_language_change(self, index):
        """Handle language dropdown change."""
        new_lang = "en" if index == 0 else "fa"
        if new_lang != self.current_lang:
            self.current_lang = new_lang
            is_rtl = (new_lang == "fa")
            if is_rtl:
                self.setFont(Fonts.get_persian_font())
            else:
                self.setFont(Fonts.get_default_font())
            self._overflow_menu.hide()
            self._update_ui_text()
            self._apply_theme()
            self._save_settings()
            self._rebuild_menu()

    def _rebuild_menu(self):
        """Rebuild the menu to update toggle states and text."""
        self._build_overflow_menu()

    def _show_about(self):
        """Show the About dialog."""
        from ui.dialogs.about_dialog import AboutDialog
        dialog = AboutDialog(self.style_sheet, parent=self)
        dialog.exec()

    def _open_github(self):
        """Open GitHub repository in default browser."""
        import webbrowser
        webbrowser.open("https://github.com/ZeLoExE/dns-jantex")

    def _open_donate(self):
        """Open donation page in default browser."""
        import webbrowser
        webbrowser.open("https://daramet.com/ZeLoExE")

    def _update_ui_text(self):
        """Update all UI text with current language translations."""
        self.setWindowTitle(self.t("app_title"))
        self.apply_btn.setText(self.t("apply"))
        self.reset_btn.setText(self.t("reset_dhcp"))
        self.flush_btn.setText(self.t("flush_dns"))
        if hasattr(self, 'dns_card') and self.dns_card:
            self.dns_card.manage_btn.setText(" " + self.t("manage_dns"))
            self.dns_card.sort_btn.setText(" " + self.t("sort"))
            self.dns_card.title_label.setText(self.t("dns_settings"))

    # ── Update system ──────────────────────────────────────────────

    def _on_update_btn_clicked(self):
        self._check_for_updates()

    def _check_for_updates(self, silent: bool = False):
        """Check GitHub for a newer version. silent=True suppresses 'up to date' messages."""
        # Prevent concurrent checks
        if hasattr(self, '_update_checking') and self._update_checking:
            return

        self._update_silent = silent
        self._update_checking = True

        self._update_check_worker = UpdateCheckWorker()
        self._update_check_worker.finished.connect(self._on_update_check_done)
        self._update_check_worker.start()

    def _on_update_check_done(self):
        """Read the worker's result and dispatch on the main thread."""
        worker = self._update_check_worker
        self._update_checking = False

        if worker.error_msg:
            self._on_update_check_error(worker.error_msg)
        else:
            self._on_update_check_result(worker.result)

    def _on_update_check_result(self, info):
        """Handle the result of an update check."""
        if info is None:
            if not self._update_silent:
                dialog = SuccessDialog(
                    "No Updates", "You're already using the latest version.",
                    self.style_sheet, "success", self
                )
                dialog.exec()
            return

        # Skip if user already dismissed or attempted this version
        skipped = self.settings.get("skipped_version", "")
        if skipped == info.version:
            if not self._update_silent:
                dialog = SuccessDialog(
                    "No Updates", "You're already using the latest version.",
                    self.style_sheet, "success", self
                )
                dialog.exec()
            return

        # New version different from previously skipped — clear skip
        if skipped and skipped != info.version:
            self.settings["skipped_version"] = ""
            self._save_settings()

        try:
            dialog = UpdateDialog(info, self.style_sheet, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._start_update_download(info)
            else:
                # User clicked "Later" — remember this version
                self.settings["skipped_version"] = info.version
                self._save_settings()
        except Exception as e:
            traceback.print_exc()

    def _on_update_check_error(self, error_msg):
        """Handle an update check failure."""
        if not self._update_silent:
            dialog = SuccessDialog(
                "Update Check Failed",
                f"Could not check for updates.\n{error_msg}",
                self.style_sheet, "error", self
            )
            dialog.exec()

    def _start_update_download(self, info: UpdateInfo):
        """Download the installer in background, then prompt to launch updater."""
        import tempfile

        self._update_info = info
        self._update_temp_dir = Path(tempfile.gettempdir()) / "dns_jantex_update"
        self._update_temp_dir.mkdir(exist_ok=True)

        # Determine filename from URL
        filename = info.download_url.split("/")[-1].split("?")[0]
        self._update_installer_path = self._update_temp_dir / filename

        self.status_label.setText("Downloading update...")
        self._set_buttons_enabled(False)

        # Download in a thread
        self._download_worker = DownloadWorker(info.download_url, self._update_installer_path)
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.start()

    def _on_download_progress(self, downloaded, total):
        if total > 0:
            pct = int(downloaded * 100 / total)
            self.status_label.setText(f"Downloading update... {pct}%")

    def _on_download_finished(self):
        self._set_buttons_enabled(True)
        if not self._download_worker.success:
            self.status_label.setText("Download failed. Please try again later.")
            QTimer.singleShot(4000, lambda: self.status_label.setText(""))
            self._cleanup_update_files()
            return

        self.status_label.setText("Download complete. Launching updater...")
        QTimer.singleShot(500, self._launch_updater)

    def _launch_updater(self):
        """Launch Updater.exe and close this application."""
        import subprocess

        # When frozen, Updater.exe lives next to the main exe; in dev, next to project root
        if getattr(sys, "frozen", False):
            app_dir = Path(sys.executable).parent
        else:
            app_dir = Path(__file__).resolve().parent.parent

        updater_exe = app_dir / "Updater.exe"

        if not updater_exe.exists():
            # Try dist directory
            updater_exe = app_dir.parent / "dist" / "Updater" / "Updater.exe"

        if not updater_exe.exists():
            self.status_label.setText("Updater.exe not found.")
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))
            self._cleanup_update_files()
            return

        # Launch the updater
        subprocess.Popen(
            [str(updater_exe), str(self._update_installer_path), "DNSChanger.exe"],
            creationflags=subprocess.DETACHED_PROCESS,
        )

        # Close the main application
        self.tray_icon.hide()
        QApplication.quit()

    def _cleanup_update_files(self):
        """Remove temporary update files."""
        import shutil
        try:
            if self._update_temp_dir.exists():
                shutil.rmtree(self._update_temp_dir, ignore_errors=True)
        except Exception:
            pass

    def _refresh_dns_info_async(self):
        """Refresh DNS info in a background thread so the UI is never blocked."""
        if self._dns_info_worker and self._dns_info_worker.isRunning():
            return
        self._dns_info_worker = DNSInfoWorker()
        self._dns_info_worker.info_ready.connect(self._on_dns_info_ready)
        self._dns_info_worker.start()

    def _on_dns_info_ready(self, adapter, provider_name, dns_servers, ping_ms):
        """Handle background DNS info fetch completing."""
        if adapter:
            # Detect adapter change — reset uptime
            if self._last_adapter_name and self._last_adapter_name != adapter.name:
                self._dns_applied_at = time.time()
                self._dns_success_count = 0
                self._dns_fail_count = 0
            self._last_adapter_name = adapter.name

            self.network_card.update_info(
                adapter.name,
                adapter.ip_address,
                [provider_name] if provider_name else adapter.dns_servers
            )
            # Update DNS status dot based on ping result
            if ping_ms is None:
                color = "#f44336"
                self._dns_fail_count += 1
            elif ping_ms < 100:
                color = "#4caf50"
                self._dns_success_count += 1
            else:
                color = "#ff9800"
                self._dns_success_count += 1
            self.network_card.set_dns_status(color)
            if ping_ms is not None:
                self.network_card.add_ping_result(ping_ms)
            # Initialize analytics if not already tracking
            if self._dns_applied_at is None:
                self._dns_applied_at = time.time()
                self._dns_success_count = 0
                self._dns_fail_count = 0
            self._update_analytics()
        else:
            self.network_card.update_info(None, None, None)

    def _refresh_dns_info(self):
        """Refresh and display current DNS configuration (kept for non-startup use)."""
        adapter = DNSManager.get_current_dns_info()
        if adapter:
            provider_name = self._match_dns_to_provider(adapter.dns_servers)
            self.network_card.update_info(
                adapter.name,
                adapter.ip_address,
                [provider_name] if provider_name else adapter.dns_servers
            )
            self._check_dns_status(adapter.dns_servers)
            # Initialize analytics if not already tracking
            if self._dns_applied_at is None:
                self._dns_applied_at = time.time()
                self._dns_success_count = 0
                self._dns_fail_count = 0
        else:
            self.network_card.update_info(None, None, None)

    def _check_dns_status(self, dns_servers):
        """Ping the first DNS server, set status dot, and update analytics."""
        if not dns_servers:
            return
        dns = dns_servers[0].strip()
        ms = DNSManager.ping_dns_fast(dns, timeout_ms=2000)
        if ms is None:
            color = "#f44336"
            self._dns_fail_count += 1
        elif ms < 100:
            color = "#4caf50"
            self._dns_success_count += 1
        else:
            color = "#ff9800"
            self._dns_success_count += 1
        self.network_card.set_dns_status(color)
        if ms is not None:
            self.network_card.add_ping_result(ms)
        self._update_analytics()

    def _tick_uptime(self):
        """Lightweight 1-second tick: recompute elapsed time and update the label."""
        if self._dns_applied_at is None:
            return
        uptime = int(time.time() - self._dns_applied_at)
        if uptime < 60:
            uptime_str = f"{uptime}s"
        elif uptime < 3600:
            uptime_str = f"{uptime // 60}m {uptime % 60}s"
        else:
            h = uptime // 3600
            m = (uptime % 3600) // 60
            uptime_str = f"{h}h {m}m"
        self.network_card._uptime_value.setText(uptime_str)

    def _update_analytics(self):
        """Update the analytics display with current stats."""
        if self._dns_applied_at is None:
            return
        uptime = int(time.time() - self._dns_applied_at)
        self.network_card.update_analytics(uptime, self._dns_success_count, self._dns_fail_count)

        # Update last change time display
        if uptime < 60:
            change_str = "just now"
        elif uptime < 3600:
            change_str = f"{uptime // 60}m ago"
        else:
            h = uptime // 3600
            m = (uptime % 3600) // 60
            change_str = f"{h}h {m}m ago"
        self.network_card.set_last_change(change_str)

    def _periodic_dns_check(self):
        """Periodically ping the current DNS to update status and analytics (async)."""
        self._refresh_dns_info_async()

    def _match_dns_to_provider(self, dns_servers):
        """Return provider name if DNS matches a known provider, else 'Custom DNS'."""
        if not dns_servers:
            return None
        dns_set = set(s.strip() for s in dns_servers)
        for provider in DNS_PROVIDERS:
            provider_set = {provider.primary, provider.secondary}
            if dns_set == provider_set or dns_set.issubset(provider_set):
                return provider.name
        return "Custom DNS"

    def _load_all_providers(self):
        """Load built-in + custom DNS providers into the card."""
        _t0 = time.perf_counter()
        # Clear existing rows
        self.dns_card.rows.clear()
        while self.dns_card.list_layout.count():
            item = self.dns_card.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.dns_card.button_group = QButtonGroup(self.dns_card)

        # Add built-in providers
        for provider in DNS_PROVIDERS:
            self.dns_card.add_provider(provider.name, provider.primary, provider.secondary, provider.category, provider.tags)

        # Add custom providers from the unified store
        for entry in load_custom_dns():
            self.dns_card.add_provider(entry.name, entry.primary, entry.secondary)
        _proflog("_load_all_providers", _t0)

    def _open_custom_dns_manager(self):
        """Open the Custom DNS Manager dialog."""
        dialog = CustomDNSManagerDialog(self.style_sheet, parent=self)
        dialog.dns_changed.connect(self._on_custom_dns_changed)
        dialog.exec()

    def _on_custom_dns_changed(self):
        """Handle changes in custom DNS list."""
        self._load_all_providers()
        self.dns_card.refresh_theme(self.style_sheet)

    def _on_apply_custom_dns(self, primary: str, secondary: str):
        """Handle Apply Custom DNS button click."""
        self._set_buttons_enabled(False)
        self.status_label.setText("Applying DNS...")
        self.dns_worker = DNSWorker("set", primary, secondary or "")
        self.dns_worker.finished.connect(self._on_dns_operation_finished)
        self.dns_worker.start()

    def _on_save_preset(self, primary: str, secondary: str):
        """Save a custom DNS pair to the unified custom DNS store."""
        # Reject duplicate primary+secondary pairs
        for entry in load_custom_dns():
            if entry.primary == primary and entry.secondary == secondary:
                self.status_label.setText("This preset already exists")
                QTimer.singleShot(2000, lambda: self.status_label.setText(""))
                return

        # Auto-generate name: "Custom Preset 1", "Custom Preset 2", ...
        existing_names = [e.name for e in load_custom_dns()]
        existing_nums = []
        for name in existing_names:
            if name.startswith("Custom Preset "):
                try:
                    existing_nums.append(int(name.split("Custom Preset ")[1]))
                except (ValueError, IndexError):
                    pass
        next_num = max(existing_nums, default=0) + 1
        preset_name = f"Custom Preset {next_num}"

        # Save to the same store used by Manage DNS modal
        entry = add_custom_dns(preset_name, primary, secondary or "")

        # Inject into the live DNS table as a favorite at the top
        self.dns_card.favorites.add(preset_name)
        self.settings["favorites"] = sorted(self.dns_card.favorites)
        self.dns_card.add_provider(preset_name, primary, secondary or "", category="custom")
        self.dns_card._rebuild_list()

        self.status_label.setText(f"Preset saved: {preset_name}")
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))

    def _get_selected_provider_index(self) -> int:
        """Get the index of the currently selected provider."""
        if self.dns_card:
            for i, row in enumerate(self.dns_card.rows):
                if row.radio.isChecked():
                    return i
        return 0

    def _on_provider_changed(self, index: int):
        """Handle DNS provider selection change."""
        self._save_settings()

    def _on_favorites_changed(self, favorites: list):
        """Handle favorites list change."""
        self.settings["favorites"] = favorites
        self._save_settings()

    def _auto_flush_after_apply(self):
        """Flush DNS cache automatically after a successful Apply."""
        self.dns_worker = DNSWorker("flush")
        self.dns_worker.finished.connect(lambda ok, msg: None)
        self.dns_worker.start()

    def _on_apply_clicked(self):
        """Handle Apply button click."""
        primary, secondary = self.dns_card.get_selected_dns()
        if not primary:
            self._show_error(self.t("invalid_dns").format(address="None"))
            return

        # Disable buttons and show status
        self._set_buttons_enabled(False)
        self.status_label.setText("Applying DNS...")
        self._dns_op_start = time.perf_counter()

        # Create and start worker thread
        self.dns_worker = DNSWorker("set", primary, secondary or "")
        self.dns_worker.finished.connect(self._on_dns_operation_finished)
        self.dns_worker.start()

    def _on_reset_clicked(self):
        """Handle Default DNS button click - reset to DHCP."""
        self._set_buttons_enabled(False)
        self.status_label.setText("Resetting to Default DNS...")
        self._dns_op_start = time.perf_counter()

        # Create and start worker thread
        self.dns_worker = DNSWorker("reset")
        self.dns_worker.finished.connect(self._on_dns_operation_finished)
        self.dns_worker.start()

    def _on_flush_clicked(self):
        """Handle Flush DNS button click."""
        self._set_buttons_enabled(False)
        self.status_label.setText("Flushing DNS cache...")
        self._dns_op_start = time.perf_counter()

        # Create and start worker thread
        self.dns_worker = DNSWorker("flush")
        self.dns_worker.finished.connect(self._on_dns_operation_finished)
        self.dns_worker.start()

    def _on_dns_operation_finished(self, success: bool, message: str):
        """Handle DNS operation completion."""
        elapsed = (time.perf_counter() - getattr(self, '_dns_op_start', time.perf_counter())) * 1000
        print(f"[PROFILER] DNS operation '{getattr(self.dns_worker, 'operation', '?')}' total (UI thread): {elapsed:.0f}ms success={success}", file=sys.stderr, flush=True)

        was_set = success and self.dns_worker and self.dns_worker.operation == "set"

        if success:
            self._dns_applied_at = time.time()
            self._dns_success_count = 0
            self._dns_fail_count = 0
            self.network_card.set_last_change("just now")
            self._show_success(message)
            # Invalidate adapter cache after DNS change
            DNSManager.invalidate_cache()
            self._refresh_dns_info_async()
            op = getattr(self.dns_worker, 'operation', '')
            if op == "flush":
                self._play_flush_sound()
            else:
                self._play_success_sound()
        else:
            self._show_error(message)
            # Invalidate cache on failure too (adapter may have changed)
            DNSManager.invalidate_cache()

        self._set_buttons_enabled(True)
        self.status_label.setText("")
        self.dns_worker = None

        # Auto-flush DNS after a successful Apply, if enabled
        if was_set and self.settings.get("auto_flush_dns", False):
            self._auto_flush_after_apply()

    def _on_ping_clicked(self):
        """Handle Test Speed & Stability button click."""
        if self.ping_worker and self.ping_worker.isRunning():
            return

        self.ping_worker = PingWorker(DNS_PROVIDERS)
        self.ping_worker.result_ready.connect(self._on_ping_result)
        self.ping_worker.finished_all.connect(self._on_ping_finished)
        self.ping_worker.start()

    def _on_ping_result(self, index: int, latency):
        """Handle ping result - called for each provider as it finishes."""
        if self.dns_card:
            self.dns_card.update_latency(index, latency)
        if latency is not None and hasattr(self, 'network_card'):
            self.network_card.add_ping_stat_result(latency)

    def _on_ping_finished(self):
        """Handle ping completion."""
        pass

    def _on_smart_connect(self):
        """Benchmark all providers and auto-select the fastest one."""
        if self.ping_worker and self.ping_worker.isRunning():
            return

        self.dns_card.smart_btn.setEnabled(False)
        self.status_label.setText("Benchmarking DNS providers...")

        self._smart_benchmark_results = {}
        self.ping_worker = PingWorker(DNS_PROVIDERS)
        self.ping_worker.result_ready.connect(self._on_smart_ping_result)
        self.ping_worker.finished_all.connect(self._on_smart_benchmark_done)
        self.ping_worker.start()

    def _on_smart_ping_result(self, index: int, latency):
        if latency is not None:
            self._smart_benchmark_results[index] = latency
            self.dns_card.update_latency(index, latency)

    def _on_smart_benchmark_done(self):
        """Select the fastest provider after benchmark completes."""
        self.ping_worker = None
        self.dns_card.smart_btn.setEnabled(True)

        if self._smart_benchmark_results:
            fastest_idx = min(self._smart_benchmark_results, key=self._smart_benchmark_results.get)
            fastest_ms = self._smart_benchmark_results[fastest_idx]
            fastest_name = DNS_PROVIDERS[fastest_idx].name

            # Find visible row index for this provider
            for i, row in enumerate(self.dns_card.rows):
                if row.name == fastest_name:
                    self.dns_card.select_provider(i)
                    break

            self.status_label.setText(f"Smart Connect: {fastest_name} ({fastest_ms:.0f} ms)")
        else:
            self.status_label.setText("Smart Connect: no DNS responded")

        self._save_settings()
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))

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

    def _show_success(self, message: str):
        """Show success notification."""
        dialog = SuccessDialog(self.t("success"), message, self.style_sheet, "success", self)
        dialog.exec()

    def _play_success_sound(self):
        """Play the success chime (apply/reset)."""
        self._play_sound("success")

    def _play_flush_sound(self):
        """Play the flush blip."""
        self._play_sound("flush")

    def _play_sound(self, name: str):
        """Load and play a wav from assets/sounds/."""
        try:
            from PySide6.QtMultimedia import QSoundEffect
            sound_path = _base_dir() / "assets" / "sounds" / f"{name}.wav"
            if not sound_path.exists():
                return
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(str(sound_path)))
            effect.setVolume(0.5)
            effect.play()
            # Prevent garbage collection
            if not hasattr(self, '_sound_effects'):
                self._sound_effects = []
            self._sound_effects.append(effect)
        except Exception:
            pass

    def _show_error(self, message: str):
        """Show error notification."""
        dialog = SuccessDialog(self.t("error"), message, self.style_sheet, "error", self)
        dialog.exec()

    def _show_warning(self, message: str):
        """Show warning notification."""
        dialog = SuccessDialog(self.t("warning"), message, self.style_sheet, "warning", self)
        dialog.exec()

    def closeEvent(self, event):
        """Handle window close event - exit completely, not minimize to tray."""
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

        # Hide tray icon before exiting
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()

        event.accept()
