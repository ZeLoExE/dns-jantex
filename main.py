"""
DNS Jantex - A modern Windows DNS management application.
"""

import sys
import os
import time
import ctypes
import traceback


def _setup_crash_log():
    """Install a global exception handler that writes tracebacks to a log file."""
    log_path = os.path.join(os.environ.get("TEMP", "."), "dns_jantex_crash.log")

    def _excepthook(exc_type, exc_value, exc_tb):
        try:
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        except Exception:
            tb = repr(exc_value)
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"--- crash ---\n{tb}\n")
        except Exception:
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
    except Exception:
        return False


def request_admin():
    """Request UAC elevation to run as administrator."""
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    except Exception:
        sys.exit(1)


def main():
    """Main entry point for the DNS Changer application."""
    _t_start = time.perf_counter()
    _setup_crash_log()

    # Check for admin privileges
    if not is_admin():
        request_admin()
        return

    print(f"[PROFILER] Admin check: {(time.perf_counter() - _t_start) * 1000:.0f}ms", file=sys.stderr, flush=True)

    # Import PySide6 modules
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QIcon

    print(f"[PROFILER] PySide6 import: {(time.perf_counter() - _t_start) * 1000:.0f}ms", file=sys.stderr, flush=True)

    from ui.main_window import MainWindow
    from ui.styles import Fonts

    print(f"[PROFILER] UI module import: {(time.perf_counter() - _t_start) * 1000:.0f}ms", file=sys.stderr, flush=True)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("DNS Jantex")
    app.setOrganizationName("DNS Jantex")

    print(f"[PROFILER] QApplication created: {(time.perf_counter() - _t_start) * 1000:.0f}ms", file=sys.stderr, flush=True)

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
    print(f"[PROFILER] MainWindow created: {(time.perf_counter() - _t_start) * 1000:.0f}ms", file=sys.stderr, flush=True)
    window.show()
    print(f"[PROFILER] Window shown (startup complete): {(time.perf_counter() - _t_start) * 1000:.0f}ms", file=sys.stderr, flush=True)

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
