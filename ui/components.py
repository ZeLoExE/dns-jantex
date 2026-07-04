from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel,
    QPushButton, QLineEdit, QRadioButton, QButtonGroup,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QIcon
from typing import Optional

from ui.styles import StyleSheet


def _load_icon(name: str, color: str = None) -> QIcon:
    """Load an SVG icon, replacing currentColor with the given color."""
    from pathlib import Path
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QImage, QPainter, QPixmap
    from PySide6.QtCore import QByteArray
    path = Path(__file__).parent.parent / "assets" / "icons" / f"{name}.svg"
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
    return QIcon(QPixmap.fromImage(img))


class ProviderRow(QFrame):
    """A single row for a DNS provider."""

    row_clicked = Signal()

    def __init__(self, name: str, primary: str, secondary: str,
                 style_sheet: StyleSheet, index: int, parent=None, category: str = "international", tags: list = None):
        super().__init__(parent)
        self.name = name
        self.primary = primary
        self.secondary = secondary
        self.ss = style_sheet
        self.index = index
        self.category = category
        self.tags = tags or []
        self._search_visible = True
        self.latency_label = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._setup_ui()

    def mousePressEvent(self, event):
        """Handle click anywhere on the row."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.row_clicked.emit()
        super().mousePressEvent(event)

    def _setup_ui(self):
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.ss.hover};
                border-radius: 6px;
                border: 1px solid {self.ss.border};
            }}
            QFrame:hover {{
                border-color: {self.ss.accent};
            }}
        """)

        self._hbox = QHBoxLayout(self)
        self._hbox.setContentsMargins(16, 6, 12, 6)
        self._hbox.setSpacing(10)
        h = self._hbox

        # Radio
        self.radio = QRadioButton()
        self.radio.setFixedSize(22, 22)
        self.radio.setStyleSheet(f"""
            QRadioButton {{
                spacing: 0px;
            }}
            QRadioButton::indicator {{
                width: 18px; height: 18px;
                border-radius: 9px;
                border: 2px solid {self.ss.border};
                background: transparent;
                margin: 0px;
            }}
            QRadioButton::indicator:hover {{
                border-color: {self.ss.accent};
            }}
            QRadioButton::indicator:checked {{
                background-color: {self.ss.accent};
                border-color: {self.ss.accent};
            }}
        """)
        h.addWidget(self.radio)

        # Name
        self.name_label = QLabel(self.name)
        self.name_label.setFixedWidth(100)
        self.name_label.setStyleSheet(f"""
            color: {self.ss.text};
            font-size: 13px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        h.addWidget(self.name_label)

        # Primary DNS (fixed width for alignment)
        self.primary_label = QLabel(self.primary)
        self.primary_label.setFixedWidth(130)
        self.primary_label.setStyleSheet(f"""
            color: {self.ss.text};
            font-family: Consolas, monospace;
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        h.addWidget(self.primary_label)

        # Separator
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {self.ss.border}; font-size: 13px; background: transparent; border: none;")
        h.addWidget(sep)

        # Secondary DNS (fixed width for alignment)
        self.secondary_label = QLabel(self.secondary)
        self.secondary_label.setFixedWidth(130)
        self.secondary_label.setStyleSheet(f"""
            color: {self.ss.text};
            font-family: Consolas, monospace;
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        h.addWidget(self.secondary_label)

        h.addStretch()

        # Copy icon button
        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(_load_icon("copy"))
        self.copy_btn.setIconSize(QSize(16, 16))
        self.copy_btn.setFixedSize(30, 26)
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text_secondary};
                border: 1px solid {self.ss.border};
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.accent};
                color: white;
                border-color: {self.ss.accent};
            }}
        """)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy)
        h.addWidget(self.copy_btn)

        # Latency
        self.latency_label = QLabel("-- ms")
        self.latency_label.setFixedWidth(65)
        self.latency_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.latency_label.setStyleSheet(f"""
            color: {self.ss.text_secondary};
            font-size: 11px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        h.addWidget(self.latency_label)

    def _copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(f"{self.primary}, {self.secondary}")

    def set_latency(self, ms: Optional[float]):
        if ms is not None:
            self.latency_label.setText(f"{ms:.0f} ms")
            self.latency_label.setStyleSheet(f"""
                color: {self.ss.accent};
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                border: none;
            """)
        else:
            self.latency_label.setText("Timeout")
            self.latency_label.setStyleSheet(f"""
                color: {self.ss.error};
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                border: none;
            """)

    def refresh_theme(self, ss: StyleSheet):
        self.ss = ss
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ss.hover};
                border-radius: 6px;
                border: 1px solid {ss.border};
            }}
            QFrame:hover {{
                border-color: {ss.accent};
            }}
        """)
        self.radio.setStyleSheet(f"""
            QRadioButton::indicator {{
                width: 16px; height: 16px;
                border-radius: 8px;
                border: 2px solid {ss.border};
                background: transparent;
            }}
            QRadioButton::indicator:hover {{
                border-color: {ss.accent};
            }}
            QRadioButton::indicator:checked {{
                background-color: {ss.accent};
                border-color: {ss.accent};
            }}
        """)
        self.name_label.setStyleSheet(f"color: {ss.text}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        self.primary_label.setStyleSheet(f"color: {ss.text}; font-family: Consolas, monospace; font-size: 12px; background: transparent; border: none;")
        self.secondary_label.setStyleSheet(f"color: {ss.text}; font-family: Consolas, monospace; font-size: 12px; background: transparent; border: none;")
        self.copy_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {ss.text_secondary}; border: 1px solid {ss.border}; border-radius: 4px; font-size: 14px; }} QPushButton:hover {{ background-color: {ss.accent}; color: white; border-color: {ss.accent}; }}")
        self.latency_label.setStyleSheet(f"color: {ss.text_secondary}; font-size: 11px; font-weight: bold; background: transparent; border: none;")

    def set_direction(self, is_rtl: bool):
        self._hbox.setDirection(
            QBoxLayout.Direction.RightToLeft if is_rtl
            else QBoxLayout.Direction.LeftToRight
        )


class CustomDNSRow(QFrame):
    """Custom DNS input row."""

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.primary_input = None
        self.secondary_input = None
        self.radio = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.ss.hover};
                border-radius: 6px;
                border: 1px solid {self.ss.border};
            }}
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(12, 8, 12, 8)
        v.setSpacing(6)

        # Radio row
        h = QHBoxLayout()
        self.radio = QRadioButton()
        self.radio.setFixedWidth(18)
        self.radio.setStyleSheet(f"""
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
        lbl = QLabel("Custom DNS")
        lbl.setStyleSheet(f"color: {self.ss.text}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        h.addWidget(self.radio)
        h.addWidget(lbl)
        h.addStretch()
        v.addLayout(h)

        # Input row
        inp = QHBoxLayout()
        inp.setSpacing(12)

        for label_text, attr in [("Primary DNS", "primary_input"), ("Secondary DNS", "secondary_input")]:
            col = QVBoxLayout()
            l = QLabel(label_text)
            l.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
            e = QLineEdit()
            e.setPlaceholderText("e.g., 178.22.122.100" if "Primary" in label_text else "e.g., 185.51.200.2")
            e.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {self.ss.card};
                    color: {self.ss.text};
                    border: 1px solid {self.ss.border};
                    border-radius: 6px;
                    padding: 6px 10px;
                    font-size: 12px;
                }}
                QLineEdit:focus {{
                    border-color: {self.ss.accent};
                }}
            """)
            setattr(self, attr, e)
            col.addWidget(l)
            col.addWidget(e)
            inp.addLayout(col)

        v.addLayout(inp)

    def refresh_theme(self, ss: StyleSheet):
        self.ss = ss
        self.setStyleSheet(f"QFrame {{ background-color: {ss.hover}; border-radius: 6px; border: 1px solid {ss.border}; }}")
        self.radio.setStyleSheet(f"QRadioButton::indicator {{ width: 16px; height: 16px; border-radius: 8px; border: 2px solid {ss.border}; background: transparent; }} QRadioButton::indicator:checked {{ background-color: {ss.accent}; border-color: {ss.accent}; }}")
        if self.primary_input:
            self.primary_input.setStyleSheet(f"QLineEdit {{ background-color: {ss.card}; color: {ss.text}; border: 1px solid {ss.border}; border-radius: 6px; padding: 6px 10px; font-size: 12px; }} QLineEdit:focus {{ border-color: {ss.accent}; }}")
        if self.secondary_input:
            self.secondary_input.setStyleSheet(f"QLineEdit {{ background-color: {ss.card}; color: {ss.text}; border: 1px solid {ss.border}; border-radius: 6px; padding: 6px 10px; font-size: 12px; }} QLineEdit:focus {{ border-color: {ss.accent}; }}")


class DNSCard(QFrame):
    """DNS settings card with provider list."""

    provider_changed = Signal(int)
    manage_clicked = Signal()
    ping_clicked = Signal()
    smart_clicked = Signal()

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.rows = []
        self.custom_row = None
        self.button_group = QButtonGroup(self)
        self.latencies = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.ss.card};
                border: 1px solid {self.ss.border};
                border-radius: 12px;
            }}
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        # Title row with sort button
        self._title_row = QHBoxLayout()
        title_row = self._title_row
        self.title_label = QLabel("DNS Settings")
        self.title_label.setStyleSheet(f"color: {self.ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        title_row.addWidget(self.title_label)
        title_row.addStretch()

        # Manage Custom DNS button
        self.manage_btn = QPushButton()
        self.manage_btn.setIcon(_load_icon("manage"))
        self.manage_btn.setIconSize(QSize(14, 14))
        self.manage_btn.setText(" Manage DNS")
        self.manage_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.accent};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.accent};
                color: white;
                border-color: {self.ss.accent};
            }}
        """)
        self.manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manage_btn.clicked.connect(self._on_manage_clicked)
        title_row.addWidget(self.manage_btn)

        # Sort button
        self.sort_btn = QPushButton()
        self.sort_btn.setIcon(_load_icon("sort"))
        self.sort_btn.setIconSize(QSize(14, 14))
        self.sort_btn.setText(" Sort")
        self.sort_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text_secondary};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.hover};
                color: {self.ss.text};
                border-color: {self.ss.accent};
            }}
        """)
        self.sort_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sort_order = None  # None = unsorted, True = ascending, False = descending
        self.sort_btn.clicked.connect(self._toggle_sort)
        title_row.addWidget(self.sort_btn)

        # Iran filter button
        self.filter_iran = False
        self.iran_btn = QPushButton(" Iran")
        self.iran_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text_secondary};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.hover};
                color: {self.ss.text};
                border-color: {self.ss.accent};
            }}
        """)
        self.iran_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.iran_btn.clicked.connect(self._toggle_iran_filter)
        title_row.addWidget(self.iran_btn)

        # Test Latency button
        self.ping_btn = QPushButton()
        self.ping_btn.setIcon(_load_icon("latency"))
        self.ping_btn.setIconSize(QSize(14, 14))
        self.ping_btn.setText(" Test Latency")
        self.ping_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text_secondary};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.hover};
                color: {self.ss.text};
                border-color: {self.ss.accent};
            }}
        """)
        self.ping_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ping_btn.clicked.connect(self.ping_clicked.emit)
        title_row.addWidget(self.ping_btn)

        # Smart Connect button
        self.smart_btn = QPushButton()
        self.smart_btn.setIcon(_load_icon("smart"))
        self.smart_btn.setIconSize(QSize(14, 14))
        self.smart_btn.setText(" Smart Connect")
        self.smart_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.accent};
                border: 1px solid {self.ss.accent};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.ss.accent};
                color: white;
            }}
        """)
        self.smart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.smart_btn.clicked.connect(self.smart_clicked.emit)
        title_row.addWidget(self.smart_btn)

        v.addLayout(title_row)

        # Tag filter buttons
        self.filter_tag = None
        self._tag_row = QHBoxLayout()
        self._tag_row.setSpacing(6)
        self._tag_buttons = {}
        tag_defs = [
            ("gaming", "Gaming"),
            ("adblock", "Ad Blocking"),
            ("family", "Family Safe"),
            ("privacy", "Privacy"),
            ("security", "Security"),
            ("anti-sanction", "Anti-Sanction"),
        ]
        for tag_key, tag_label in tag_defs:
            btn = QPushButton(tag_label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._tag_btn_style(False))
            btn.clicked.connect(lambda checked, k=tag_key: self._toggle_tag_filter(k))
            self._tag_row.addWidget(btn)
            self._tag_buttons[tag_key] = btn
        self._tag_row.addStretch()
        v.addLayout(self._tag_row)

        # Search box
        self._search_row = QHBoxLayout()
        self._search_row.setContentsMargins(0, 0, 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search DNS providers...")
        self.search_input.setFixedHeight(32)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.ss.card};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {self.ss.accent};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search)
        self._search_row.addWidget(self.search_input)
        v.addLayout(self._search_row)

        # Header
        self._header_row = QHBoxLayout()
        hdr = self._header_row
        hdr.setContentsMargins(28, 0, 12, 0)
        for text, width in [("Provider", 100), ("Primary DNS", 140), ("Secondary DNS", 140), ("", 0), ("Copy", 55), ("Latency", 65)]:
            l = QLabel(text)
            l.setFixedWidth(width) if width else None
            l.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
            if text == "Latency":
                l.setAlignment(Qt.AlignmentFlag.AlignRight)
            hdr.addWidget(l)
            if text == "":
                hdr.addStretch()
        v.addLayout(hdr)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.ss.border};")
        v.addWidget(sep)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.ss.border};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)

        self._scroll.setWidget(self.container)
        v.addWidget(self._scroll, 1)

    def add_provider(self, name: str, primary: str, secondary: str, category: str = "international", tags: list = None):
        row = ProviderRow(name, primary, secondary, self.ss, len(self.rows), category=category, tags=tags)
        self.button_group.addButton(row.radio)
        row.radio.toggled.connect(lambda checked, i=len(self.rows): self.provider_changed.emit(i))
        # Make entire row clickable
        row.row_clicked.connect(lambda r=row: r.radio.setChecked(True))
        self.rows.append(row)
        self.list_layout.addWidget(row)

        if len(self.rows) == 1:
            row.radio.setChecked(True)

    def add_custom_option(self):
        self.custom_row = CustomDNSRow(self.ss)
        self.button_group.addButton(self.custom_row.radio)
        self.custom_row.radio.toggled.connect(lambda: self.provider_changed.emit(-1))
        self.list_layout.addWidget(self.custom_row)

    def get_selected_dns(self) -> tuple[Optional[str], Optional[str]]:
        for i, row in enumerate(self.rows):
            if row.radio.isChecked():
                return row.primary, row.secondary
        if self.custom_row and self.custom_row.radio.isChecked():
            p = self.custom_row.primary_input.text().strip() if self.custom_row.primary_input else ""
            s = self.custom_row.secondary_input.text().strip() if self.custom_row.secondary_input else ""
            return (p, s) if p else (None, None)
        return None, None

    def update_latency(self, index: int, latency: Optional[float]):
        if 0 <= index < len(self.rows):
            self.rows[index].set_latency(latency)
            # Store latency for sorting
            self.latencies[self.rows[index].name] = latency if latency is not None else 99999

    def select_provider(self, index: int):
        if 0 <= index < len(self.rows):
            self.rows[index].radio.setChecked(True)

    def _on_manage_clicked(self):
        """Handle Manage DNS button click."""
        self.manage_clicked.emit()

    def set_direction(self, is_rtl: bool):
        dir_val = QBoxLayout.Direction.RightToLeft if is_rtl else QBoxLayout.Direction.LeftToRight
        self._title_row.setDirection(dir_val)
        self._header_row.setDirection(dir_val)

    def _on_search(self, text: str):
        """Filter visible rows by search text."""
        query = text.lower().strip()
        for row in self.rows:
            if not query:
                row._search_visible = True
            else:
                row._search_visible = (
                    query in row.name.lower() or
                    query in row.primary.lower() or
                    query in row.secondary.lower()
                )
        self._rebuild_list()

    def _toggle_sort(self):
        """Toggle sort order for pings: None -> ascending -> descending -> None."""
        if self.sort_order is None:
            self.sort_order = True  # ascending (lowest first)
        elif self.sort_order is True:
            self.sort_order = False  # descending (highest first)
        else:
            self.sort_order = None  # back to original order

        self._apply_sort()

    def _apply_sort(self):
        """Apply the current sort order to the provider list."""
        selected_name = None
        for row in self.rows:
            if row.radio.isChecked():
                selected_name = row.name
                break

        if self.sort_order is None:
            # Reset to original insertion order by index
            self.rows.sort(key=lambda r: r.index)
        elif self.sort_order is True:
            # Ascending: lowest latency first (None/timeout goes last)
            self.rows.sort(key=lambda r: self.latencies.get(r.name, 99999))
        else:
            # Descending: highest latency first
            self.rows.sort(key=lambda r: self.latencies.get(r.name, 0), reverse=True)

        self._rebuild_list(selected_name)

        # Update button text to reflect current state
        if self.sort_order is None:
            self.sort_btn.setText(" Sort")
        elif self.sort_order is True:
            self.sort_btn.setText(" Sort")
        else:
            self.sort_btn.setText(" Sort")

    def _toggle_iran_filter(self):
        """Toggle Iran-only DNS filter."""
        self.filter_iran = not self.filter_iran
        if self.filter_iran:
            self.iran_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.ss.accent};
                    color: white;
                    border: 1px solid {self.ss.accent};
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                }}
            """)
        else:
            self.iran_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.ss.text_secondary};
                    border: 1px solid {self.ss.border};
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {self.ss.hover};
                    color: {self.ss.text};
                    border-color: {self.ss.accent};
                }}
            """)
        self._rebuild_list()

    def _tag_btn_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background-color: {self.ss.accent};
                    color: white;
                    border: 1px solid {self.ss.accent};
                    border-radius: 6px;
                    padding: 3px 10px;
                    font-size: 11px;
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text_secondary};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.hover};
                color: {self.ss.text};
                border-color: {self.ss.accent};
            }}
        """

    def _toggle_tag_filter(self, tag: str):
        """Toggle a tag filter. Clicking the same tag again disables it."""
        if self.filter_tag == tag:
            self.filter_tag = None
        else:
            self.filter_tag = tag
        for key, btn in self._tag_buttons.items():
            btn.setStyleSheet(self._tag_btn_style(key == self.filter_tag))
        self._rebuild_list()

    def _rebuild_list(self, selected_name: Optional[str] = None):
        """Rebuild the provider list after sorting."""
        # Disconnect all radio signals temporarily
        for row in self.rows:
            try:
                row.radio.toggled.disconnect()
            except RuntimeError:
                pass

        # Remove all widgets from layout
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.hide()

        # Re-add rows in new order, filtered by category, tag, and search
        visible_idx = 0
        for i, row in enumerate(self.rows):
            if self.filter_iran and row.category != "iran":
                row.hide()
                continue
            if self.filter_tag and self.filter_tag not in row.tags:
                row.hide()
                continue
            if hasattr(row, '_search_visible') and not row._search_visible:
                row.hide()
                continue
            self.list_layout.addWidget(row)
            row.show()
            # Reconnect with correct index
            row.radio.toggled.connect(lambda checked, idx=visible_idx: self.provider_changed.emit(idx))
            if selected_name and row.name == selected_name:
                row.radio.setChecked(True)
            visible_idx += 1

        # Re-add custom row
        if self.custom_row:
            self.list_layout.addWidget(self.custom_row)

    def refresh_theme(self, ss: StyleSheet):
        self.ss = ss
        self.setStyleSheet(f"QFrame {{ background-color: {ss.card}; border: 1px solid {ss.border}; border-radius: 12px; }}")

        # Update manage button
        self.manage_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ss.accent};
                border: 1px solid {ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {ss.accent};
                color: white;
                border-color: {ss.accent};
            }}
        """)

        # Update sort button
        self.sort_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ss.text_secondary};
                border: 1px solid {ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {ss.hover};
                color: {ss.text};
                border-color: {ss.accent};
            }}
        """)

        # Update Iran filter button
        if self.filter_iran:
            self.iran_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ss.accent};
                    color: white;
                    border: 1px solid {ss.accent};
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                }}
            """)
        else:
            self.iran_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {ss.text_secondary};
                    border: 1px solid {ss.border};
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {ss.hover};
                    color: {ss.text};
                    border-color: {ss.accent};
                }}
            """)

        # Update ping button
        self.ping_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ss.text_secondary};
                border: 1px solid {ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {ss.hover};
                color: {ss.text};
                border-color: {ss.accent};
            }}
        """)

        # Update smart connect button
        self.smart_btn.setIcon(_load_icon("smart", ss.accent))
        self.smart_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ss.accent};
                border: 1px solid {ss.accent};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ss.accent};
                color: white;
            }}
        """)

        # Update search input
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ss.card};
                color: {ss.text};
                border: 1px solid {ss.border};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {ss.accent};
            }}
        """)

        # Update title and header labels
        self.title_label.setStyleSheet(f"color: {ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        for lbl in self.findChildren(QLabel):
            txt = lbl.text()
            if txt in ["Provider", "Primary DNS", "Secondary DNS", "Copy", "Latency", ""]:
                lbl.setStyleSheet(f"color: {ss.text_secondary}; font-size: 11px; background: transparent; border: none;")

        # Update rows
        for row in self.rows:
            row.refresh_theme(ss)

        if self.custom_row:
            self.custom_row.refresh_theme(ss)


class NetworkInfoCard(QFrame):
    """Network information card."""

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"QFrame {{ background-color: {self.ss.card}; border: 1px solid {self.ss.border}; border-radius: 12px; }}")
        self.setMinimumHeight(90)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(10)

        title = QLabel("Network Status")
        title.setStyleSheet(f"color: {self.ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        v.addWidget(title)

        self._grid = QHBoxLayout()
        self._grid.setSpacing(40)
        grid = self._grid

        for label_text, attr in [("Active Adapter", "adapter_name"), ("IPv4 Address", "ip_address")]:
            col = QVBoxLayout()
            l = QLabel(label_text)
            l.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
            val = QLabel("--")
            val.setStyleSheet(f"color: {self.ss.text}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
            setattr(self, attr, val)
            col.addWidget(l)
            col.addWidget(val)
            grid.addLayout(col)

        # Current DNS with status dot
        dns_col = QVBoxLayout()
        dns_label = QLabel("Current DNS")
        dns_label.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        dns_col.addWidget(dns_label)

        dns_row = QHBoxLayout()
        dns_row.setSpacing(6)
        self.current_dns = QLabel("--")
        self.current_dns.setStyleSheet(f"color: {self.ss.text}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        dns_row.addWidget(self.current_dns)

        self._status_dot = QLabel()
        self._status_dot.setFixedSize(10, 10)
        self._status_dot.setStyleSheet(f"background-color: {self.ss.text_secondary}; border-radius: 5px;")
        dns_row.addWidget(self._status_dot)
        dns_row.addStretch()

        dns_col.addLayout(dns_row)
        grid.addLayout(dns_col)

        grid.addStretch()
        v.addLayout(grid)

        # Analytics row
        analytics_row = QHBoxLayout()
        analytics_row.setSpacing(16)

        self._uptime_label = QLabel("Uptime: --")
        self._uptime_label.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 10px; background: transparent; border: none;")
        analytics_row.addWidget(self._uptime_label)

        self._success_label = QLabel("Success: --")
        self._success_label.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 10px; background: transparent; border: none;")
        analytics_row.addWidget(self._success_label)

        self._blocked_label = QLabel("Blocked queries: --")
        self._blocked_label.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 10px; background: transparent; border: none;")
        analytics_row.addWidget(self._blocked_label)

        analytics_row.addStretch()
        v.addLayout(analytics_row)

    def update_info(self, adapter_name, ip_address, dns_servers):
        self.adapter_name.setText(adapter_name or "--")
        self.ip_address.setText(ip_address or "--")
        if dns_servers:
            self.current_dns.setText("  |  ".join(dns_servers))
            self.current_dns.setStyleSheet(f"color: {self.ss.text}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        else:
            self.current_dns.setText("Automatic (DHCP)")
            self.current_dns.setStyleSheet(f"""
                color: {self.ss.accent};
                font-size: 13px;
                font-weight: bold;
                background: transparent;
                border: none;
            """)
        self._status_dot.setStyleSheet(f"background-color: {self.ss.text_secondary}; border-radius: 5px;")

    def set_dns_status(self, color: str):
        """Update the status dot color: '#4caf50' green, '#ff9800' yellow, '#f44336' red."""
        self._status_dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

    def update_analytics(self, uptime_seconds: int, success_count: int, fail_count: int):
        """Update the analytics labels with current stats."""
        # Format uptime
        if uptime_seconds < 60:
            uptime_str = f"{uptime_seconds}s"
        elif uptime_seconds < 3600:
            uptime_str = f"{uptime_seconds // 60}m {uptime_seconds % 60}s"
        else:
            h = uptime_seconds // 3600
            m = (uptime_seconds % 3600) // 60
            uptime_str = f"{h}h {m}m"

        total = success_count + fail_count
        if total > 0:
            rate = (success_count / total) * 100
            color = "#4caf50" if rate >= 95 else "#ff9800" if rate >= 70 else "#f44336"
            self._success_label.setText(f"Success: {rate:.0f}%")
            self._success_label.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        else:
            self._success_label.setText("Success: --")
            self._success_label.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 10px; background: transparent; border: none;")

        self._uptime_label.setText(f"Uptime: {uptime_str}")
        self._blocked_label.setText(f"Queries checked: {total}")

    def refresh_theme(self, ss: StyleSheet):
        self.ss = ss
        self.setStyleSheet(f"QFrame {{ background-color: {ss.card}; border: 1px solid {ss.border}; border-radius: 12px; }}")
        for lbl in self.findChildren(QLabel):
            txt = lbl.text()
            if txt == "Network Status":
                lbl.setStyleSheet(f"color: {ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
            elif txt in ["Active Adapter", "IPv4 Address", "Current DNS"]:
                lbl.setStyleSheet(f"color: {ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
            elif txt.startswith("Uptime:") or txt.startswith("Queries"):
                lbl.setStyleSheet(f"color: {ss.text_secondary}; font-size: 10px; background: transparent; border: none;")
            else:
                lbl.setStyleSheet(f"color: {ss.text}; font-size: 13px; font-weight: bold; background: transparent; border: none;")

    def set_direction(self, is_rtl: bool):
        self._grid.setDirection(
            QBoxLayout.RightToLeft if is_rtl
            else QBoxLayout.LeftToRight
        )


class CustomDNSCard(QFrame):
    """Standalone card for custom DNS input."""

    custom_dns_apply = Signal(str, str)  # primary, secondary

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"QFrame {{ background-color: {self.ss.card}; border: 1px solid {self.ss.border}; border-radius: 12px; }}")
        self.setMinimumHeight(90)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(10)

        title = QLabel("Custom DNS")
        title.setStyleSheet(f"color: {self.ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        v.addWidget(title)

        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(10)

        # Primary DNS input
        pri_col = QVBoxLayout()
        pri_lbl = QLabel("Primary DNS")
        pri_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        self.primary_input = QLineEdit()
        self.primary_input.setPlaceholderText("e.g., 178.22.122.100")
        self.primary_input.setFixedHeight(28)
        self._style_input(self.primary_input)
        pri_col.addWidget(pri_lbl)
        pri_col.addWidget(self.primary_input)
        inputs_row.addLayout(pri_col)

        # Secondary DNS input
        sec_col = QVBoxLayout()
        sec_lbl = QLabel("Secondary DNS")
        sec_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        self.secondary_input = QLineEdit()
        self.secondary_input.setPlaceholderText("e.g., 185.51.200.2")
        self.secondary_input.setFixedHeight(28)
        self._style_input(self.secondary_input)
        sec_col.addWidget(sec_lbl)
        sec_col.addWidget(self.secondary_input)
        inputs_row.addLayout(sec_col)

        v.addLayout(inputs_row)

        # Apply button
        self.apply_custom_btn = QPushButton()
        self.apply_custom_btn.setIcon(_load_icon("apply", self.ss.accent))
        self.apply_custom_btn.setIconSize(QSize(14, 14))
        self.apply_custom_btn.setText(" Apply")
        self.apply_custom_btn.setFixedHeight(28)
        self.apply_custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.accent};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.ss.accent_hover}; }}
        """)
        self.apply_custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_custom_btn.clicked.connect(self._on_apply_custom)
        v.addWidget(self.apply_custom_btn)

        v.addStretch()

    def _style_input(self, widget):
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.ss.card};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {self.ss.accent};
            }}
        """)

    def _on_apply_custom(self):
        p = self.primary_input.text().strip()
        s = self.secondary_input.text().strip()
        if p:
            self.custom_dns_apply.emit(p, s)

    def refresh_theme(self, ss: StyleSheet):
        self.ss = ss
        self.setStyleSheet(f"QFrame {{ background-color: {ss.card}; border: 1px solid {ss.border}; border-radius: 12px; }}")
        for lbl in self.findChildren(QLabel):
            txt = lbl.text()
            if txt == "Custom DNS":
                lbl.setStyleSheet(f"color: {ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
            elif txt in ["Primary DNS", "Secondary DNS"]:
                lbl.setStyleSheet(f"color: {ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        self._style_input(self.primary_input)
        self._style_input(self.secondary_input)
        self.apply_custom_btn.setIcon(_load_icon("apply", ss.accent))
        self.apply_custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ss.accent};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {ss.accent_hover}; }}
        """)


class ActionButton(QPushButton):
    """Action button."""

    def __init__(self, text: str, style_sheet: StyleSheet, primary: bool = True, parent=None):
        super().__init__(text, parent)
        self.ss = style_sheet
        self.is_primary = primary
        self._apply_style()

    def _apply_style(self):
        if self.is_primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.ss.accent};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: bold;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {self.ss.accent_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.ss.accent};
                }}
                QPushButton:disabled {{
                    background-color: {self.ss.border};
                    color: {self.ss.text_secondary};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.ss.text};
                    border: 1px solid {self.ss.border};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {self.ss.hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.ss.border};
                }}
                QPushButton:disabled {{
                    background-color: {self.ss.border};
                    color: {self.ss.text_secondary};
                }}
            """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setMinimumWidth(120)

    def refresh_theme(self, style_sheet: StyleSheet):
        self.ss = style_sheet
        self._apply_style()
