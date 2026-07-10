import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap


def _base_dir() -> Path:
    """Return the project root — works both in dev and inside a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent


class AboutDialog(QDialog):
    """Modern About dialog matching the application theme."""

    def __init__(self, style_sheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.setWindowTitle("About DNS Jantex")
        self.setFixedSize(420, 480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(self._get_dialog_style())

        self._setup_ui()

    def _get_dialog_style(self) -> str:
        """Get dialog stylesheet matching the application theme."""
        ss = self.ss
        return f"""
            QDialog {{
                background-color: {ss.card};
                border: 1px solid {ss.border};
                border-radius: 16px;
            }}
        """

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        # App icon
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = _base_dir() / "assets" / "icon.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(
                64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)

        # App name
        name_label = QLabel("DNS Jantex")
        name_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {self.ss.text}; background: transparent;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # Version
        version = self._get_version()
        version_label = QLabel(f"Version {version}")
        version_label.setStyleSheet(f"color: {self.ss.text_secondary}; background: transparent; font-size: 13px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # Description
        desc_label = QLabel(
            "A modern DNS changer for Windows with automatic updates, "
            "multiple DNS providers, and a clean user experience."
        )
        desc_label.setStyleSheet(f"color: {self.ss.text_secondary}; background: transparent; font-size: 12px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Features
        features_title = QLabel("Features")
        features_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        features_title.setStyleSheet(f"color: {self.ss.text}; background: transparent;")
        layout.addWidget(features_title)

        features = [
            "One-click DNS switching",
            "Restore Default DNS",
            "Flush DNS Cache",
            "Automatic Updates",
            "Multi-language Support",
        ]
        for feature in features:
            feature_label = QLabel(f"  •  {feature}")
            feature_label.setStyleSheet(f"color: {self.ss.text_secondary}; background: transparent; font-size: 12px;")
            layout.addWidget(feature_label)

        # Developer
        dev_label = QLabel("Developer: Aydin (ZeLoExE)")
        dev_label.setStyleSheet(f"color: {self.ss.text_secondary}; background: transparent; font-size: 12px;")
        layout.addWidget(dev_label)

        # License
        license_label = QLabel("License: MIT License")
        license_label.setStyleSheet(f"color: {self.ss.text_secondary}; background: transparent; font-size: 12px;")
        layout.addWidget(license_label)

        layout.addStretch()

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        # GitHub button
        self.github_btn = QPushButton("GitHub")
        self.github_btn.setFixedHeight(36)
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.hover};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {self.ss.accent};
                background-color: {self.ss.card};
            }}
        """)
        self.github_btn.clicked.connect(self._open_github)
        btn_layout.addWidget(self.github_btn)

        # Donate button
        self.donate_btn = QPushButton("Donate")
        self.donate_btn.setFixedHeight(36)
        self.donate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.donate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.accent};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.ss.accent_hover};
            }}
        """)
        self.donate_btn.clicked.connect(self._open_donate)
        btn_layout.addWidget(self.donate_btn)

        layout.addLayout(btn_layout)

        # Close button (centered)
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedSize(100, 36)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.hover};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {self.ss.accent};
                background-color: {self.ss.card};
            }}
        """)
        self.close_btn.clicked.connect(self.close)
        close_layout.addWidget(self.close_btn)
        close_layout.addStretch()
        layout.addLayout(close_layout)

    def _get_version(self) -> str:
        """Read version from VERSION file."""
        version_file = _base_dir() / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        return "unknown"

    def _open_github(self):
        """Open GitHub repository in default browser."""
        import webbrowser
        webbrowser.open("https://github.com/ZeLoExE/dns-jantex")

    def _open_donate(self):
        """Open donation page in default browser."""
        import webbrowser
        webbrowser.open("https://daramet.com/ZeLoExE")
