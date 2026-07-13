"""DNS Jantex — unprivileged desktop application entry point."""

from __future__ import annotations

import logging
import os
import sys
import time
import traceback

logger = logging.getLogger(__name__)
DEBUG_PERF = os.environ.get("DNS_JANTEX_DEBUG_PERF", "").lower() in {"1", "true", "yes"}


def _setup_crash_log() -> None:
    from core.paths import ensure_data_dir

    log_path = ensure_data_dir() / "dns_jantex_crash.log"

    def _excepthook(exc_type, exc_value, exc_tb):
        try:
            text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        except (TypeError, ValueError):
            text = repr(exc_value)
        try:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"--- crash ---\n{text}\n")
        except OSError:
            pass

    sys.excepthook = _excepthook


def main() -> None:
    started = time.perf_counter()
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from core.paths import bundle_dir, migrate_legacy_config

    _setup_crash_log()
    migrate_legacy_config()

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    from ui.main_window import MainWindow
    from ui.styles import Fonts

    app = QApplication(sys.argv)
    app.setApplicationName("DNS Jantex")
    app.setOrganizationName("DNS Jantex")

    icon_path = bundle_dir() / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setFont(Fonts.get_default_font())

    window = MainWindow()
    window.show()
    if DEBUG_PERF:
        logger.debug("Startup complete: %.0fms", (time.perf_counter() - started) * 1000)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
