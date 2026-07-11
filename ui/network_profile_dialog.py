"""Network Profile Manager Dialog — Add, Edit, Remove network DNS profiles."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QWidget, QRadioButton,
    QComboBox, QButtonGroup, QCheckBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QFont

from ui.styles import StyleSheet
from core.network_profiles import (
    load_profiles, add_profile, update_profile, remove_profile, NetworkProfile
)
from core.dns_providers import DNS_PROVIDERS


EMOJI_OPTIONS = ["🌐", "🏠", "🎓", "🎮", "🏢", "📱", "🏥", "✈️", "🚗", "📡"]


class _DialogTitleBar(QWidget):
    """Custom frameless title bar for dialogs."""

    def __init__(self, title: str, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.setFixedHeight(40)
        self._dragging = False
        self._drag_position = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(0)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: {self.ss.text}; font-size: 13px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self.title_label)
        layout.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(46, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text};
                border: none;
                border-radius: 0px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #e81123;
                color: white;
            }}
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(lambda: self.window().close())
        layout.addWidget(close_btn)

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


class NetworkProfileRow(QFrame):
    """A single network profile row with edit/delete/toggle buttons."""

    edited = Signal(str)   # profile_id
    removed = Signal(str)  # profile_id
    toggled = Signal(str, bool)  # profile_id, enabled

    def __init__(self, profile: NetworkProfile, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.ss = style_sheet
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.ss.hover};
                border-radius: 8px;
                border: 1px solid {self.ss.border};
            }}
        """)
        self.setFixedHeight(64)

        h = QHBoxLayout(self)
        h.setContentsMargins(14, 8, 14, 8)
        h.setSpacing(12)

        # Icon
        icon_lbl = QLabel(self.profile.icon)
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            font-size: 20px;
            background-color: {self.ss.card};
            border-radius: 6px;
            border: 1px solid {self.ss.border};
        """)
        h.addWidget(icon_lbl)

        # Name + network info
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        name_lbl = QLabel(self.profile.name)
        name_lbl.setStyleSheet(f"color: {self.ss.text}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        info_col.addWidget(name_lbl)

        network_text = f"{self.profile.network_type.upper()}: {self.profile.network_id}"
        net_lbl = QLabel(network_text)
        net_lbl.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 11px; background: transparent; border: none;")
        info_col.addWidget(net_lbl)
        h.addLayout(info_col, 1)

        # DNS info
        dns_text = f"{self.profile.primary_dns}"
        if self.profile.secondary_dns:
            dns_text += f" | {self.profile.secondary_dns}"
        dns_lbl = QLabel(dns_text)
        dns_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-family: Consolas, monospace; font-size: 12px; background: transparent; border: none;")
        h.addWidget(dns_lbl)

        # Provider label
        prov_lbl = QLabel(self.profile.dns_provider)
        prov_lbl.setFixedWidth(100)
        prov_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prov_lbl.setStyleSheet(f"color: {self.ss.accent}; font-size: 11px; font-weight: 500; background: transparent; border: none;")
        h.addWidget(prov_lbl)

        # Enable toggle
        self.toggle_btn = QPushButton()
        self.toggle_btn.setFixedSize(48, 26)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_toggle_style()
        self.toggle_btn.clicked.connect(self._on_toggle)
        h.addWidget(self.toggle_btn)

        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(55, 28)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.accent};
                border: 1px solid {self.ss.border};
                border-radius: 5px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.accent};
                color: white;
            }}
        """)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edited.emit(self.profile.id))
        h.addWidget(edit_btn)

        # Delete button
        del_btn = QPushButton("Delete")
        del_btn.setFixedSize(60, 28)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.error};
                border: 1px solid {self.ss.border};
                border-radius: 5px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.error};
                color: white;
            }}
        """)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(self._confirm_delete)
        h.addWidget(del_btn)

    def _update_toggle_style(self):
        if self.profile.enabled:
            self.toggle_btn.setText("ON")
            self.toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #22c55e;
                    color: white;
                    border: none;
                    border-radius: 13px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """)
        else:
            self.toggle_btn.setText("OFF")
            self.toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.ss.border};
                    color: {self.ss.text_tertiary};
                    border: none;
                    border-radius: 13px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """)

    def _on_toggle(self):
        self.profile.enabled = not self.profile.enabled
        self._update_toggle_style()
        self.toggled.emit(self.profile.id, self.profile.enabled)

    def _confirm_delete(self):
        reply = QMessageBox.question(
            None, "Delete Profile",
            f"Delete '{self.profile.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.removed.emit(self.profile.id)


class NetworkProfileEditDialog(QDialog):
    """Dialog for adding or editing a network profile."""

    def __init__(self, style_sheet: StyleSheet, profile: NetworkProfile = None, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.profile = profile
        self.result_data = None
        self.selected_icon = profile.icon if profile else "🌐"
        self._dragging = False
        self._drag_position = None
        self._setup_ui()

        if profile:
            self.name_input.setText(profile.name)
            self.network_id_input.setText(profile.network_id)
            if profile.network_type == "ethernet":
                self.ethernet_radio.setChecked(True)
            else:
                self.wifi_radio.setChecked(True)
            for i in range(self.provider_combo.count()):
                if self.provider_combo.itemText(i) == profile.dns_provider:
                    self.provider_combo.setCurrentIndex(i)
                    break
            self.primary_input.setText(profile.primary_dns)
            self.secondary_input.setText(profile.secondary_dns)
            self.enabled_check.setChecked(profile.enabled)
            self._update_icon_selection()

    def _setup_ui(self):
        self.setWindowTitle("Edit Network Profile" if self.profile else "Add Network Profile")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(520)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Main container with rounded corners
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.ss.bg};
                border: 1px solid {self.ss.border};
                border-radius: 12px;
            }}
        """)
        outer.addWidget(container)

        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Title bar
        title_bar = _DialogTitleBar(
            "Edit Network Profile" if self.profile else "Add Network Profile",
            self.ss, self
        )
        cl.addWidget(title_bar)

        # Content area (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.ss.border}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        v = QVBoxLayout(scroll_content)
        v.setContentsMargins(28, 20, 28, 20)
        v.setSpacing(12)

        # Profile name
        name_lbl = QLabel("Profile Name")
        name_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Home Wi-Fi")
        self._style_input(self.name_input)
        v.addWidget(name_lbl)
        v.addWidget(self.name_input)

        # Icon selector
        icon_lbl = QLabel("Icon")
        icon_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        v.addWidget(icon_lbl)

        icon_row = QHBoxLayout()
        icon_row.setSpacing(6)
        self._icon_buttons = []
        for emoji in EMOJI_OPTIONS:
            btn = QPushButton(emoji)
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, e=emoji: self._select_icon(e))
            self._icon_buttons.append((emoji, btn))
            icon_row.addWidget(btn)
        icon_row.addStretch()
        v.addLayout(icon_row)

        # Network type
        type_lbl = QLabel("Network Type")
        type_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        v.addWidget(type_lbl)

        type_row = QHBoxLayout()
        type_row.setSpacing(16)
        self.wifi_radio = QRadioButton("Wi-Fi")
        self.wifi_radio.setChecked(True)
        self._style_radio(self.wifi_radio)
        self.ethernet_radio = QRadioButton("Ethernet")
        self._style_radio(self.ethernet_radio)
        self._type_group = QButtonGroup(self)
        self._type_group.addButton(self.wifi_radio)
        self._type_group.addButton(self.ethernet_radio)
        type_row.addWidget(self.wifi_radio)
        type_row.addWidget(self.ethernet_radio)
        type_row.addStretch()
        v.addLayout(type_row)

        # Network ID
        net_id_row = QHBoxLayout()
        net_id_row.setSpacing(8)
        net_id_col = QVBoxLayout()
        net_id_col.setSpacing(4)
        net_id_lbl = QLabel("Network Name (SSID / Adapter)")
        net_id_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        self.network_id_input = QLineEdit()
        self.network_id_input.setPlaceholderText("e.g., MyHomeWiFi or Ethernet")
        self._style_input(self.network_id_input)
        net_id_col.addWidget(net_id_lbl)
        net_id_col.addWidget(self.network_id_input)
        net_id_row.addLayout(net_id_col, 1)

        # Spacer for label height alignment
        _label_spacer = QLabel("")
        _label_spacer.setFixedHeight(17)
        _label_spacer.setStyleSheet("background: transparent; border: none;")
        detect_col = QVBoxLayout()
        detect_col.setSpacing(4)
        detect_col.addWidget(_label_spacer)
        detect_btn = QPushButton("Detect")
        detect_btn.setFixedHeight(34)
        detect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.accent};
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 11px;
                font-weight: bold;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background-color: {self.ss.accent_hover}; }}
        """)
        detect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        detect_btn.clicked.connect(self._detect_network)
        detect_col.addWidget(detect_btn)
        net_id_row.addLayout(detect_col)
        v.addLayout(net_id_row)

        # DNS provider
        prov_lbl = QLabel("DNS Provider")
        prov_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        v.addWidget(prov_lbl)

        self.provider_combo = QComboBox()
        self.provider_combo.setFixedHeight(34)
        provider_names = [p.name for p in DNS_PROVIDERS]
        self.provider_combo.addItems(provider_names)
        self.provider_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.ss.input_bg};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
            }}
            QComboBox:hover {{ border-color: {self.ss.accent}; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {self.ss.text_secondary};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.ss.card};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                selection-background-color: {self.ss.accent};
                selection-color: white;
                outline: none;
                padding: 4px;
            }}
        """)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        v.addWidget(self.provider_combo)

        # DNS inputs
        dns_row = QHBoxLayout()
        dns_row.setSpacing(12)
        for label_text, attr in [("Primary DNS", "primary_input"), ("Secondary DNS", "secondary_input")]:
            col = QVBoxLayout()
            l = QLabel(label_text)
            l.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
            e = QLineEdit()
            e.setPlaceholderText("e.g., 1.1.1.1" if "Primary" in label_text else "e.g., 1.0.0.1")
            self._style_input(e)
            setattr(self, attr, e)
            col.addWidget(l)
            col.addWidget(e)
            dns_row.addLayout(col)
        v.addLayout(dns_row)

        # Auto-fill DNS from provider selection
        self._on_provider_changed(self.provider_combo.currentText())

        # Enabled checkbox — properly spaced
        self.enabled_check = QCheckBox("Enable this profile")
        self.enabled_check.setChecked(True)
        self.enabled_check.setStyleSheet(f"""
            QCheckBox {{
                color: {self.ss.text};
                font-size: 12px;
                background: transparent;
                border: none;
                spacing: 8px;
                padding-top: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 4px;
                border: 2px solid {self.ss.border};
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.ss.accent};
                border-color: {self.ss.accent};
            }}
        """)
        v.addWidget(self.enabled_check)

        # Separator before buttons
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.ss.border};")
        v.addWidget(sep)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 8, 0, 0)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(90, 36)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 7px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {self.ss.hover}; }}
        """)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setFixedSize(90, 36)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.accent};
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.ss.accent_hover}; }}
        """)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        v.addLayout(btn_row)
        v.addStretch()

        scroll.setWidget(scroll_content)
        cl.addWidget(scroll, 1)

    def _style_input(self, widget: QLineEdit):
        widget.setFixedHeight(34)
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.ss.input_bg};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {self.ss.accent}; }}
        """)

    def _style_radio(self, radio: QRadioButton):
        radio.setStyleSheet(f"""
            QRadioButton {{
                color: {self.ss.text};
                spacing: 8px;
                font-size: 12px;
                background: transparent;
                border: none;
            }}
            QRadioButton::indicator {{
                width: 16px; height: 16px;
                border-radius: 8px;
                border: 2px solid {self.ss.border};
                background: transparent;
            }}
            QRadioButton::indicator:checked {{
                background-color: {self.ss.accent};
                border-color: {self.ss.accent};
            }}
        """)

    def _select_icon(self, emoji: str):
        self.selected_icon = emoji
        self._update_icon_selection()

    def _update_icon_selection(self):
        for emoji, btn in self._icon_buttons:
            if emoji == self.selected_icon:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        font-size: 20px;
                        background-color: {self.ss.accent};
                        border-radius: 6px;
                        border: 2px solid {self.ss.accent};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        font-size: 20px;
                        background-color: {self.ss.card};
                        border-radius: 6px;
                        border: 1px solid {self.ss.border};
                    }}
                    QPushButton:hover {{
                        border-color: {self.ss.accent};
                    }}
                """)

    def _detect_network(self):
        from core.network_adapter import NetworkAdapterDetector
        network_id, network_type = NetworkAdapterDetector.get_current_network_id()
        if network_id:
            self.network_id_input.setText(network_id)
            if network_type == "wifi":
                self.wifi_radio.setChecked(True)
            else:
                self.ethernet_radio.setChecked(True)
        else:
            QMessageBox.information(self, "Detection", "No active network detected.")

    def _on_provider_changed(self, provider_name: str):
        for provider in DNS_PROVIDERS:
            if provider.name == provider_name:
                self.primary_input.setText(provider.primary)
                self.secondary_input.setText(provider.secondary)
                return

    def _save(self):
        name = self.name_input.text().strip()
        network_id = self.network_id_input.text().strip()
        primary = self.primary_input.text().strip()
        secondary = self.secondary_input.text().strip()
        provider_name = self.provider_combo.currentText()
        network_type = "wifi" if self.wifi_radio.isChecked() else "ethernet"

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a profile name.")
            return
        if not network_id:
            QMessageBox.warning(self, "Error", "Please enter a network name.")
            return
        if not primary:
            QMessageBox.warning(self, "Error", "Please enter a Primary DNS address.")
            return

        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, primary):
            QMessageBox.warning(self, "Error", "Invalid Primary DNS address format.")
            return
        if secondary and not re.match(ip_pattern, secondary):
            QMessageBox.warning(self, "Error", "Invalid Secondary DNS address format.")
            return

        self.result_data = {
            "name": name,
            "icon": self.selected_icon,
            "network_id": network_id,
            "network_type": network_type,
            "dns_provider": provider_name,
            "primary_dns": primary,
            "secondary_dns": secondary,
            "enabled": self.enabled_check.isChecked(),
        }
        self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_position:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_position = None

    def showEvent(self, event):
        super().showEvent(event)
        from ui.animations import animate_dialog_in
        animate_dialog_in(self)


class NetworkProfileManagerDialog(QDialog):
    """Main dialog for managing network profiles."""

    profiles_changed = Signal()

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self._dragging = False
        self._drag_position = None
        self._setup_ui()
        self._load_entries()

    def _setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(780, 520)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Main container
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.ss.bg};
                border: 1px solid {self.ss.border};
                border-radius: 12px;
            }}
        """)
        outer.addWidget(container)

        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Title bar
        title_bar = _DialogTitleBar("Network Profiles", self.ss, self)
        cl.addWidget(title_bar)

        # Content
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        v = QVBoxLayout(content)
        v.setContentsMargins(24, 16, 24, 20)
        v.setSpacing(12)

        # Header row
        hdr = QHBoxLayout()
        hdr_title = QLabel("Network Profiles")
        hdr_title.setStyleSheet(f"color: {self.ss.text}; font-size: 20px; font-weight: bold; background: transparent; border: none;")
        hdr.addWidget(hdr_title)
        hdr.addStretch()

        add_btn = QPushButton("+ Add Profile")
        add_btn.setFixedHeight(34)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.accent};
                color: white;
                border: none;
                border-radius: 7px;
                padding: 0 18px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.ss.accent_hover}; }}
        """)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_entry)
        hdr.addWidget(add_btn)
        v.addLayout(hdr)

        # Column headers
        col_hdr = QHBoxLayout()
        col_hdr.setContentsMargins(14, 0, 14, 0)
        col_hdr.setSpacing(12)
        for text, width in [("", 44), ("Profile", 140), ("DNS Addresses", 200), ("Provider", 100), ("Status", 48), ("", 55), ("", 60)]:
            lbl = QLabel(text)
            if width:
                lbl.setFixedWidth(width)
            lbl.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 11px; background: transparent; border: none;")
            col_hdr.addWidget(lbl)
        v.addLayout(col_hdr)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.ss.border};")
        v.addWidget(sep)

        # Scroll area for entries
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.ss.border};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)

        scroll.setWidget(self.container)
        v.addWidget(scroll, 1)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.hover};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 7px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {self.ss.border}; }}
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        v.addLayout(btn_row)

        cl.addWidget(content, 1)

    def _load_entries(self):
        """Load and display all network profiles."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        profiles = load_profiles()

        if not profiles:
            empty = QLabel("No network profiles yet. Click '+ Add Profile' to create one.")
            empty.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 12px; padding: 30px; background: transparent; border: none;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(empty)
        else:
            for profile in profiles:
                widget = NetworkProfileRow(profile, self.ss)
                widget.edited.connect(self._edit_entry)
                widget.removed.connect(self._remove_entry)
                widget.toggled.connect(self._toggle_entry)
                self.list_layout.addWidget(widget)

        self.list_layout.addStretch()

    def _add_entry(self):
        dialog = NetworkProfileEditDialog(self.ss, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            add_profile(d["name"], d["icon"], d["network_id"], d["network_type"],
                        d["dns_provider"], d["primary_dns"], d["secondary_dns"], d["enabled"])
            self._load_entries()
            self.profiles_changed.emit()

    def _edit_entry(self, profile_id: str):
        profile = None
        for p in load_profiles():
            if p.id == profile_id:
                profile = p
                break
        if not profile:
            return

        dialog = NetworkProfileEditDialog(self.ss, profile=profile, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            update_profile(profile_id, d["name"], d["icon"], d["network_id"], d["network_type"],
                           d["dns_provider"], d["primary_dns"], d["secondary_dns"], d["enabled"])
            self._load_entries()
            self.profiles_changed.emit()

    def _remove_entry(self, profile_id: str):
        remove_profile(profile_id)
        self._load_entries()
        self.profiles_changed.emit()

    def _toggle_entry(self, profile_id: str, enabled: bool):
        profiles = load_profiles()
        for p in profiles:
            if p.id == profile_id:
                p.enabled = enabled
                break
        from core.network_profiles import save_profiles
        save_profiles(profiles)
        self.profiles_changed.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_position:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_position = None

    def showEvent(self, event):
        super().showEvent(event)
        from ui.animations import animate_dialog_in
        animate_dialog_in(self)
