"""
DNS Jantex - A modern Windows DNS management application.
"""

import sys
import os
import time
import ctypes
import logging
import traceback

logger = logging.getLogger(__name__)

DEBUG_PERF = os.environ.get("DNS_JANTEX_DEBUG_PERF", "").lower() in ("1", "true", "yes")

# Application name for single-instance mutex
APP_NAME = "DNSJantex"


def _setup_crash_log():
    """Install a global exception handler that writes tracebacks to a log file."""
    log_path = os.path.join(os.environ.get("TEMP", "."), "dns_jantex_crash.log")

    def _excepthook(exc_type, exc_value, exc_tb):
        try:
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        except (TypeError, ValueError):
            tb = repr(exc_value)
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"--- crash ---\n{tb}\n")
        except OSError:
            pass

    sys.excepthook = _excepthook


def _app_dir() -> str:
    """Return the directory where the app resources live (works in dev and bundled)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _bundle_dir() -> str:
    """Return the PyInstaller temp bundle dir (or source root in dev)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


# Add the source root to sys.path for development mode
if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def is_admin():
    """Check if the application is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, OSError):
        logger.warning("Could not determine admin status")
        return False


def request_admin():
    """Request UAC elevation to run as administrator."""
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    except (AttributeError, OSError) as exc:
        logger.error("UAC elevation failed: %s", exc)
        sys.exit(1)


def main():
    """Main entry point for the DNS Changer application."""
    _t_start = time.perf_counter()
    _setup_crash_log()

    # Check for admin privileges
    if not is_admin():
        request_admin()
        return

    if DEBUG_PERF:
        logger.debug("Admin check: %.0fms", (time.perf_counter() - _t_start) * 1000)

    # Single-instance enforcement
    from single_instance import SingleInstance
    si = SingleInstance(APP_NAME)
    if not si.try_lock():
        # Another instance is already running — find and restore its window
        # Try both English and Persian window titles
        SingleInstance.find_and_restore_window(window_titles=[
            "DNS Jantex",
            "DNS Changer",
            "DNS جنتکس",
        ])
        sys.exit(0)

    if DEBUG_PERF:
        logger.debug("Single-instance check: %.0fms", (time.perf_counter() - _t_start) * 1000)

    # Import PySide6 modules
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon

    if DEBUG_PERF:
        logger.debug("PySide6 import: %.0fms", (time.perf_counter() - _t_start) * 1000)

    from ui.main_window import MainWindow
    from ui.styles import Fonts

    if DEBUG_PERF:
        logger.debug("UI module import: %.0fms", (time.perf_counter() - _t_start) * 1000)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("DNS Jantex")
    app.setOrganizationName("DNS Jantex")

    if DEBUG_PERF:
        logger.debug("QApplication created: %.0fms", (time.perf_counter() - _t_start) * 1000)

    # Set application icon
    icon_path = os.path.join(_bundle_dir(), "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Set default font
    app.setFont(Fonts.get_default_font())

    # Set high DPI scaling
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create and show main window
    window = MainWindow()
    if DEBUG_PERF:
        logger.debug("MainWindow created: %.0fms", (time.perf_counter() - _t_start) * 1000)
    window.show()
    if DEBUG_PERF:
        logger.debug("Window shown (startup complete): %.0fms", (time.perf_counter() - _t_start) * 1000)

    # Release mutex on application exit
    app.aboutToQuit.connect(si.release)

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
