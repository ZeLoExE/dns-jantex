from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel,
    QPushButton, QLineEdit, QRadioButton, QButtonGroup,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QThread, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPen, QBrush
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
    favorite_toggled = Signal(str)  # provider name

    def __init__(self, name: str, primary: str, secondary: str,
                 style_sheet: StyleSheet, index: int, parent=None,
                 category: str = "international", tags: list = None,
                 is_favorite: bool = False):
        super().__init__(parent)
        self.name = name
        self.primary = primary
        self.secondary = secondary
        self.ss = style_sheet
        self.index = index
        self.category = category
        self.tags = tags or []
        self.is_favorite = is_favorite
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
        self.setFixedHeight(56)
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
        self._hbox.setContentsMargins(16, 12, 12, 12)
        self._hbox.setSpacing(10)
        h = self._hbox

        # Favorite star button
        self.star_btn = QPushButton()
        self.star_btn.setFixedSize(26, 26)
        self.star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.star_btn.clicked.connect(self._on_star_clicked)
        self._update_star_style()
        h.addWidget(self.star_btn)

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
        self.name_label.setFixedWidth(160)
        self.name_label.setStyleSheet(f"""
            color: {self.ss.text};
            font-size: 15px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        h.addWidget(self.name_label)

        # Primary DNS (fixed width for alignment)
        self.primary_label = QLabel(self.primary)
        self.primary_label.setFixedWidth(140)
        self.primary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.primary_label.setStyleSheet(f"""
            color: {self.ss.text};
            font-family: Consolas, monospace;
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        h.addWidget(self.primary_label)

        # Separator
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {self.ss.border}; font-size: 15px; background: transparent; border: none;")
        h.addWidget(sep)

        # Secondary DNS (fixed width for alignment)
        self.secondary_label = QLabel(self.secondary)
        self.secondary_label.setFixedWidth(140)
        self.secondary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.secondary_label.setStyleSheet(f"""
            color: {self.ss.text};
            font-family: Consolas, monospace;
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        h.addWidget(self.secondary_label)

        h.addStretch()

        # Copy icon button
        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(_load_icon("copy"))
        self.copy_btn.setIconSize(QSize(18, 18))
        self.copy_btn.setFixedSize(34, 30)
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
        self.latency_label.setFixedWidth(70)
        self.latency_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.latency_label.setStyleSheet(f"""
            color: {self.ss.text_secondary};
            font-size: 13px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        h.addWidget(self.latency_label)

    def _copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(f"{self.primary}, {self.secondary}")

    def _on_star_clicked(self):
        self.is_favorite = not self.is_favorite
        self._update_star_style()
        self.favorite_toggled.emit(self.name)

    def _update_star_style(self):
        if self.is_favorite:
            self.star_btn.setText("\u2605")  # ★ filled star
            self.star_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {self.ss.accent};
                    border: none;
                    font-size: 18px;
                }}
                QPushButton:hover {{
                    color: {self.ss.accent_hover};
                }}
            """)
        else:
            self.star_btn.setText("\u2606")  # ☆ outline star
            self.star_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {self.ss.text_tertiary};
                    border: none;
                    font-size: 18px;
                }}
                QPushButton:hover {{
                    color: {self.ss.accent};
                }}
            """)

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
        self.name_label.setStyleSheet(f"color: {ss.text}; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        self.primary_label.setStyleSheet(f"color: {ss.text}; font-family: Consolas, monospace; font-size: 14px; background: transparent; border: none;")
        self.secondary_label.setStyleSheet(f"color: {ss.text}; font-family: Consolas, monospace; font-size: 14px; background: transparent; border: none;")
        self.copy_btn.setStyleSheet(f"QPushButton {{ background-color: transparent; color: {ss.text_secondary}; border: 1px solid {ss.border}; border-radius: 4px; font-size: 14px; }} QPushButton:hover {{ background-color: {ss.accent}; color: white; border-color: {ss.accent}; }}")
        self.latency_label.setStyleSheet(f"color: {ss.text_secondary}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        self._update_star_style()

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
    smart_clicked = Signal()
    favorites_changed = Signal(list)  # list of favorite names

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.rows = []
        self.custom_row = None
        self.button_group = QButtonGroup(self)
        self.latencies = {}
        self.favorites = set()
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
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(8)

        # Title (collapsible on scroll)
        self.title_label = QLabel("DNS Settings")
        self.title_label.setStyleSheet(f"color: {self.ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        self._title_container = QWidget()
        title_container_layout = QVBoxLayout(self._title_container)
        title_container_layout.setContentsMargins(0, 0, 0, 0)
        title_container_layout.setSpacing(0)
        title_container_layout.addWidget(self.title_label)
        self._title_container.setStyleSheet("background: transparent;")
        v.addWidget(self._title_container)

        # Row 1: Action buttons (right-aligned)
        self._title_row = QHBoxLayout()
        self._title_row.setSpacing(8)
        title_row = self._title_row
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

        # Row 2: Filter tags (left) + Search bar (right)
        self._filter_row = QHBoxLayout()
        self._filter_row.setSpacing(8)
        filter_row = self._filter_row

        # Tag filter buttons (left side)
        self.filter_tag = None
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
            filter_row.addWidget(btn)
            self._tag_buttons[tag_key] = btn

        filter_row.addStretch()

        # Search box (right side, expands)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search DNS providers...")
        self.search_input.setFixedHeight(28)
        self.search_input.setMinimumWidth(160)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.ss.card};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 2px 10px;
                font-size: 12px;
            }}
            QLineEdit::placeholder {{ color: #888888; }}
            QLineEdit:focus {{ border-color: {self.ss.accent}; }}
        """)
        self.search_input.textChanged.connect(self._on_search)
        filter_row.addWidget(self.search_input, 1)
        v.addLayout(filter_row)

        # Header — mirrors the exact data row column layout
        self._header_row = QHBoxLayout()
        self._header_row.setContentsMargins(0, 0, 0, 0)
        self._header_row.setSpacing(0)
        hdr = self._header_row

        # Ghost spacer: star(26) + spacing(10) + radio(22) + spacing(10) = 68px
        hdr_spacer = QLabel()
        hdr_spacer.setFixedWidth(68)
        hdr.addWidget(hdr_spacer)

        # Provider column — left-aligned, matching name_label width
        hdr_provider = QLabel("Provider")
        hdr_provider.setFixedWidth(160)
        hdr_provider.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hdr_provider.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        hdr.addWidget(hdr_provider)

        # Primary DNS column — center-aligned, matching primary_label width
        hdr_primary = QLabel("Primary DNS")
        hdr_primary.setFixedWidth(140)
        hdr_primary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr_primary.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        hdr.addWidget(hdr_primary)

        # Separator spacer — matching the "|" label in data rows
        hdr_sep = QLabel("|")
        hdr_sep.setFixedWidth(10)
        hdr_sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr_sep.setStyleSheet(f"color: {self.ss.border}; font-size: 15px; background: transparent; border: none;")
        hdr.addWidget(hdr_sep)

        # Secondary DNS column — center-aligned, matching secondary_label width
        hdr_secondary = QLabel("Secondary DNS")
        hdr_secondary.setFixedWidth(140)
        hdr_secondary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr_secondary.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        hdr.addWidget(hdr_secondary)

        # Stretch — matches the stretch in data rows before copy/latency
        hdr.addStretch()

        # Copy column — center-aligned, matching copy_btn width
        hdr_copy = QLabel("Copy")
        hdr_copy.setFixedWidth(34)
        hdr_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr_copy.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        hdr.addWidget(hdr_copy)

        # Latency column — right-aligned, matching latency_label width
        hdr_latency = QLabel("Latency")
        hdr_latency.setFixedWidth(70)
        hdr_latency.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hdr_latency.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        hdr.addWidget(hdr_latency)
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

        # Sticky: collapse title on scroll
        self._is_compact_mode = False
        self._title_natural_height = 0
        self._title_anim = None
        self._scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)
        QTimer.singleShot(0, self._measure_title_height)

    def add_provider(self, name: str, primary: str, secondary: str,
                     category: str = "international", tags: list = None):
        is_fav = name in self.favorites
        row = ProviderRow(name, primary, secondary, self.ss, len(self.rows),
                          category=category, tags=tags, is_favorite=is_fav)
        self.button_group.addButton(row.radio)
        row.radio.toggled.connect(lambda checked, i=len(self.rows): self.provider_changed.emit(i))
        row.row_clicked.connect(lambda r=row: r.radio.setChecked(True))
        row.favorite_toggled.connect(self._on_favorite_toggled)
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

    def _on_favorite_toggled(self, name: str):
        if name in self.favorites:
            self.favorites.discard(name)
        else:
            self.favorites.add(name)
        self.favorites_changed.emit(sorted(self.favorites))
        self._rebuild_list()

    def _on_manage_clicked(self):
        """Handle Manage DNS button click."""
        self.manage_clicked.emit()

    def set_direction(self, is_rtl: bool):
        dir_val = QBoxLayout.Direction.RightToLeft if is_rtl else QBoxLayout.Direction.LeftToRight
        self._title_row.setDirection(dir_val)
        self._filter_row.setDirection(dir_val)
        self._header_row.setDirection(dir_val)

    def _measure_title_height(self):
        """Capture the natural height of the title container after layout."""
        self._title_container.setMaximumHeight(16777215)
        self._title_natural_height = self._title_container.sizeHint().height()

    def _animate_title_container(self, collapse: bool):
        """Smoothly animate the title container height."""
        if self._title_anim and self._title_anim.state() == QPropertyAnimation.State.Running:
            self._title_anim.stop()

        if self._title_natural_height <= 0:
            self._measure_title_height()
        if self._title_natural_height <= 0:
            return

        start = self._title_container.maximumHeight()
        end = 0 if collapse else self._title_natural_height

        self._title_anim = QPropertyAnimation(self._title_container, b"maximumHeight")
        self._title_anim.setDuration(200)
        self._title_anim.setStartValue(start)
        self._title_anim.setEndValue(end)
        self._title_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._title_anim.start()

    def _on_scroll(self, value):
        """Collapse the title when scrolled past the threshold."""
        threshold = 40
        should_compact = value > threshold
        if should_compact == self._is_compact_mode:
            return
        self._is_compact_mode = should_compact
        self._animate_title_container(collapse=should_compact)

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

    def _tag_btn_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background-color: {self.ss.accent};
                    color: white;
                    border: 2px solid {self.ss.accent};
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text_secondary};
                border: 2px solid {self.ss.border};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 11px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: {self.ss.hover};
                color: {self.ss.text};
                border: 2px solid {self.ss.accent};
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

        # Collect visible rows
        visible_rows = []
        for row in self.rows:
            if self.filter_tag and self.filter_tag not in row.tags:
                row.hide()
                continue
            if hasattr(row, '_search_visible') and not row._search_visible:
                row.hide()
                continue
            visible_rows.append(row)

        # Sort: favorites first, then maintain current list order
        visible_rows.sort(key=lambda r: (0 if r.is_favorite else 1, self.rows.index(r)))

        # Re-add sorted visible rows
        visible_idx = 0
        for row in visible_rows:
            self.list_layout.addWidget(row)
            row.show()
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
            QLineEdit::placeholder {{
                color: #888888;
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

        # Update tag filter buttons
        for key, btn in self._tag_buttons.items():
            btn.setStyleSheet(self._tag_btn_style(key == self.filter_tag))

        # Update rows
        for row in self.rows:
            row.refresh_theme(ss)

        if self.custom_row:
            self.custom_row.refresh_theme(ss)



class BandwidthWorker(QThread):
    """Background thread that samples network I/O and emits throughput."""
    bandwidth_ready = Signal(float, float)  # upload_speed, download_speed (bytes/s)

    def __init__(self, interval_ms=1000):
        super().__init__()
        self.interval_ms = interval_ms
        self._running = True

    def run(self):
        try:
            import psutil
        except ImportError:
            return
        try:
            prev = psutil.net_io_counters()
        except Exception:
            return
        while self._running:
            self.msleep(self.interval_ms)
            try:
                curr = psutil.net_io_counters()
                dt = self.interval_ms / 1000.0
                self.bandwidth_ready.emit(
                    (curr.bytes_sent - prev.bytes_sent) / dt,
                    (curr.bytes_recv - prev.bytes_recv) / dt,
                )
                prev = curr
            except Exception:
                pass

    def stop(self):
        self._running = False


class NetworkStreamChart(QWidget):
    """Real-time flowing line chart for network bandwidth (upload + download)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.upload_points = []
        self.download_points = []
        self.setMinimumSize(120, 50)
        self.setMaximumHeight(60)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def add_point(self, upload_bps: float, download_bps: float):
        self.upload_points.append(upload_bps)
        self.download_points.append(download_bps)
        if len(self.upload_points) > 30:
            self.upload_points = self.upload_points[-30:]
            self.download_points = self.download_points[-30:]
        self.update()

    def paintEvent(self, event):
        if len(self.upload_points) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        all_vals = self.upload_points + self.download_points
        max_val = max(max(all_vals), 1)
        step = w / (len(self.upload_points) - 1)

        from PySide6.QtGui import QPainterPath

        # Download line (green)
        dl_color = QColor("#4caf50")
        dl_fill = QColor("#4caf50")
        dl_fill.setAlpha(25)
        dl_path = QPainterPath()
        dl_path.moveTo(0, h)
        for i, v in enumerate(self.download_points):
            x = i * step
            y = h - (v / max_val) * (h - 8) - 4
            dl_path.lineTo(x, y)
        dl_path.lineTo((len(self.download_points) - 1) * step, h)
        p.setBrush(QBrush(dl_fill))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(dl_path)

        pen_dl = QPen(dl_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen_dl)
        for i in range(len(self.download_points) - 1):
            p.drawLine(
                int(i * step), int(h - (self.download_points[i] / max_val) * (h - 8) - 4),
                int((i + 1) * step), int(h - (self.download_points[i + 1] / max_val) * (h - 8) - 4),
            )

        # Upload line (blue)
        ul_color = QColor("#2196f3")
        ul_fill = QColor("#2196f3")
        ul_fill.setAlpha(25)
        ul_path = QPainterPath()
        ul_path.moveTo(0, h)
        for i, v in enumerate(self.upload_points):
            x = i * step
            y = h - (v / max_val) * (h - 8) - 4
            ul_path.lineTo(x, y)
        ul_path.lineTo((len(self.upload_points) - 1) * step, h)
        p.setBrush(QBrush(ul_fill))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(ul_path)

        pen_ul = QPen(ul_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen_ul)
        for i in range(len(self.upload_points) - 1):
            p.drawLine(
                int(i * step), int(h - (self.upload_points[i] / max_val) * (h - 8) - 4),
                int((i + 1) * step), int(h - (self.upload_points[i + 1] / max_val) * (h - 8) - 4),
            )
        p.end()


class MiniLineChart(QWidget):
    """Small line chart for ping stat history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self.setMinimumSize(120, 30)
        self.setMaximumHeight(40)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def set_data(self, values: list[float]):
        self.points = values[-20:]
        self.update()

    def paintEvent(self, event):
        if len(self.points) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        max_val = max(max(self.points), 1)
        step = w / (len(self.points) - 1)

        # Fill area
        fill = QColor("#f57c00")
        fill.setAlpha(30)
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(0, h)
        for i, v in enumerate(self.points):
            x = i * step
            y = h - (v / max_val) * (h - 6) - 3
            path.lineTo(x, y)
        path.lineTo((len(self.points) - 1) * step, h)
        p.setBrush(QBrush(fill))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)

        # Line
        pen = QPen(QColor("#f57c00"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        for i in range(len(self.points) - 1):
            x1 = i * step
            y1 = h - (self.points[i] / max_val) * (h - 6) - 3
            x2 = (i + 1) * step
            y2 = h - (self.points[i + 1] / max_val) * (h - 6) - 3
            p.drawLine(int(x1), int(y1), int(x2), int(y2))
        p.end()


def _sub_card(ss):
    """Create a small sub-card frame."""
    f = QFrame()
    f.setStyleSheet(f"QFrame {{ background-color: {ss.hover}; border: 1px solid {ss.border}; border-radius: 6px; }}")
    return f


class NetworkInfoCard(QFrame):
    """Network status card with sub-cards grid."""

    speed_test_clicked = Signal()

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self._dns_applied_at = None
        self._success_count = 0
        self._fail_count = 0
        self._ping_stat_history = []
        self._setup_ui()
        self._start_bandwidth_monitor()
        self.destroyed.connect(self._stop_bandwidth_monitor)

    def _setup_ui(self):
        self.setStyleSheet(f"QFrame {{ background-color: {self.ss.card}; border: 1px solid {self.ss.border}; border-radius: 12px; }}")

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 4)
        v.setSpacing(4)

        # Main horizontal split: left column (2 rows of sub-cards) | right column (tall card)
        main_split = QHBoxLayout()
        main_split.setSpacing(4)

        # === LEFT COLUMN (2 stacked rows) ===
        left_col = QVBoxLayout()
        left_col.setSpacing(4)

        # Row A: Internet Status + IPv4 Address
        row_a = QHBoxLayout()
        row_a.setSpacing(4)

        # Internet Status
        self._inet_card = _sub_card(self.ss)
        inet_l = QVBoxLayout(self._inet_card)
        inet_l.setContentsMargins(6, 3, 6, 3)
        inet_l.setSpacing(2)

        inet_top = QHBoxLayout()
        inet_top.setSpacing(6)
        self._wifi_icon = QPushButton()
        self._wifi_icon.setIcon(_load_icon("wifi", "#4caf50"))
        self._wifi_icon.setIconSize(QSize(24, 24))
        self._wifi_icon.setFixedSize(28, 28)
        self._wifi_icon.setStyleSheet("QPushButton { background: transparent; border: none; }")
        inet_top.addWidget(self._wifi_icon)
        self._dot_online = QLabel()
        self._dot_online.setFixedSize(8, 8)
        self._dot_online.setStyleSheet("background-color: #4caf50; border-radius: 4px;")
        inet_top.addWidget(self._dot_online)
        self._online_lbl = QLabel("Online")
        self._online_lbl.setStyleSheet("color: #4caf50; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        inet_top.addWidget(self._online_lbl)
        inet_top.addStretch()
        inet_l.addLayout(inet_top)

        self._status_lbl = QLabel("Status: Connected")
        self._status_lbl.setStyleSheet(f"color: {self.ss.text}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        inet_l.addWidget(self._status_lbl)

        self._adapter_name = QLabel("Active Connection: --")
        self._adapter_name.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 10px; background: transparent; border: none;")
        inet_l.addWidget(self._adapter_name)

        row_a.addWidget(self._inet_card, 1)

        # IPv4 Address
        self._ip_card = _sub_card(self.ss)
        ip_l = QVBoxLayout(self._ip_card)
        ip_l.setContentsMargins(6, 3, 6, 3)
        ip_l.setSpacing(4)

        ip_top = QHBoxLayout()
        ip_top.setSpacing(4)
        self._ip_icon = QPushButton()
        self._ip_icon.setIcon(_load_icon("network", self.ss.text_secondary))
        self._ip_icon.setIconSize(QSize(18, 18))
        self._ip_icon.setFixedSize(20, 20)
        self._ip_icon.setStyleSheet("QPushButton { background: transparent; border: none; }")
        ip_top.addWidget(self._ip_icon)
        self._ip_lbl = QLabel("IPv4 Address")
        self._ip_lbl.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 11px; background: transparent; border: none;")
        ip_top.addWidget(self._ip_lbl)
        ip_top.addStretch()
        self._copy_btn = QPushButton()
        self._copy_btn.setIcon(_load_icon("copy", self.ss.text_secondary))
        self._copy_btn.setIconSize(QSize(14, 14))
        self._copy_btn.setFixedSize(24, 24)
        self._copy_btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; border-radius: 4px; }} QPushButton:hover {{ background: {self.ss.border}; }}")
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.clicked.connect(self._copy_ip)
        ip_top.addWidget(self._copy_btn)
        ip_l.addLayout(ip_top)

        self._ip_value = QLabel("--")
        self._ip_value.setStyleSheet(f"color: {self.ss.text}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        ip_l.addWidget(self._ip_value)

        row_a.addWidget(self._ip_card, 1)
        left_col.addLayout(row_a)

        # Row B: Uptime + Data Usage + DNS in Use
        row_b = QHBoxLayout()
        row_b.setSpacing(4)

        # Uptime
        self._uptime_card = _sub_card(self.ss)
        uptime_l = QVBoxLayout(self._uptime_card)
        uptime_l.setContentsMargins(6, 3, 6, 3)
        uptime_l.setSpacing(2)
        uptime_row = QHBoxLayout()
        uptime_row.setSpacing(4)
        self._uptime_icon = QPushButton()
        self._uptime_icon.setIcon(_load_icon("clock", self.ss.text_secondary))
        self._uptime_icon.setIconSize(QSize(16, 16))
        self._uptime_icon.setFixedSize(18, 18)
        self._uptime_icon.setStyleSheet("QPushButton { background: transparent; border: none; }")
        uptime_row.addWidget(self._uptime_icon)
        self._uptime_title = QLabel("Current Uptime:")
        self._uptime_title.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 10px; background: transparent; border: none;")
        uptime_row.addWidget(self._uptime_title)
        uptime_row.addStretch()
        uptime_l.addLayout(uptime_row)
        self._uptime_value = QLabel("--")
        self._uptime_value.setStyleSheet(f"color: {self.ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        uptime_l.addWidget(self._uptime_value)
        row_b.addWidget(self._uptime_card, 1)

        # Data Usage
        self._usage_card = _sub_card(self.ss)
        usage_l = QVBoxLayout(self._usage_card)
        usage_l.setContentsMargins(6, 3, 6, 3)
        usage_l.setSpacing(2)
        usage_row = QHBoxLayout()
        usage_row.setSpacing(4)
        self._usage_icon = QPushButton()
        self._usage_icon.setIcon(_load_icon("chart", self.ss.text_secondary))
        self._usage_icon.setIconSize(QSize(16, 16))
        self._usage_icon.setFixedSize(18, 18)
        self._usage_icon.setStyleSheet("QPushButton { background: transparent; border: none; }")
        usage_row.addWidget(self._usage_icon)
        self._usage_title = QLabel("Data Usage:")
        self._usage_title.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 10px; background: transparent; border: none;")
        usage_row.addWidget(self._usage_title)
        usage_row.addStretch()
        usage_l.addLayout(usage_row)
        self._queries_value = QLabel("--")
        self._queries_value.setStyleSheet(f"color: {self.ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        usage_l.addWidget(self._queries_value)
        row_b.addWidget(self._usage_card, 1)

        # DNS in Use
        self._dns_card = _sub_card(self.ss)
        dns_l = QVBoxLayout(self._dns_card)
        dns_l.setContentsMargins(6, 3, 6, 3)
        dns_l.setSpacing(2)
        dns_top_row = QHBoxLayout()
        dns_top_row.setSpacing(4)
        self._dns_icon = QPushButton()
        self._dns_icon.setIcon(_load_icon("dns", self.ss.text_secondary))
        self._dns_icon.setIconSize(QSize(16, 16))
        self._dns_icon.setFixedSize(18, 18)
        self._dns_icon.setStyleSheet("QPushButton { background: transparent; border: none; }")
        dns_top_row.addWidget(self._dns_icon)
        self._dns_title = QLabel("DNS in Use:")
        self._dns_title.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 10px; background: transparent; border: none;")
        dns_top_row.addWidget(self._dns_title)
        dns_top_row.addStretch()
        dns_l.addLayout(dns_top_row)
        dns_name_row = QHBoxLayout()
        dns_name_row.setSpacing(6)
        self._dns_name = QLabel("--")
        self._dns_name.setStyleSheet(f"color: {self.ss.text}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        self._dns_name.setMinimumWidth(0)
        dns_name_row.addWidget(self._dns_name)
        self._dns_status_dot = QLabel()
        self._dns_status_dot.setFixedSize(10, 10)
        self._dns_status_dot.setStyleSheet("background-color: #4caf50; border-radius: 5px;")
        dns_name_row.addWidget(self._dns_status_dot)
        dns_name_row.addStretch()
        dns_l.addLayout(dns_name_row)
        self._last_change = QLabel("Last Change: --")
        self._last_change.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 9px; background: transparent; border: none;")
        dns_l.addWidget(self._last_change)
        row_b.addWidget(self._dns_card, 1)

        left_col.addLayout(row_b)
        main_split.addLayout(left_col, 2)

        # === RIGHT COLUMN (tall card: charts + button) ===
        self._right_card = _sub_card(self.ss)
        right_l = QVBoxLayout(self._right_card)
        right_l.setContentsMargins(4, 2, 4, 2)
        right_l.setSpacing(4)

        # Network Stream header
        stream_top = QHBoxLayout()
        self._stream_lbl = QLabel("Network Stream")
        self._stream_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        stream_top.addWidget(self._stream_lbl)
        stream_top.addStretch()
        self._stream_speed = QLabel("0 KB/s")
        self._stream_speed.setStyleSheet(f"color: {self.ss.accent}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        stream_top.addWidget(self._stream_speed)
        right_l.addLayout(stream_top)

        # Legend
        legend_row = QHBoxLayout()
        legend_row.setSpacing(10)
        self._legend_labels = []
        for color_hex, label in [("#4caf50", "Download"), ("#2196f3", "Upload")]:
            dot = QLabel()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(f"background-color: {color_hex}; border-radius: 3px;")
            legend_row.addWidget(dot)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {self.ss.text_tertiary}; font-size: 9px; background: transparent; border: none;")
            legend_row.addWidget(lbl)
            self._legend_labels.append(lbl)
        legend_row.addStretch()
        right_l.addLayout(legend_row)

        self._stream_chart = NetworkStreamChart()
        right_l.addWidget(self._stream_chart)

        # Separator
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f"background-color: {self.ss.border};")
        right_l.addWidget(self._sep)

        # Ping Stat header
        stat_top = QHBoxLayout()
        self._stat_lbl = QLabel("Ping Stat")
        self._stat_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        stat_top.addWidget(self._stat_lbl)
        stat_top.addStretch()
        self._ping_stat_avg = QLabel("Avg: --ms")
        self._ping_stat_avg.setStyleSheet(f"color: {self.ss.accent}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        stat_top.addWidget(self._ping_stat_avg)
        right_l.addLayout(stat_top)

        self._line_chart = MiniLineChart()
        right_l.addWidget(self._line_chart)

        # Test Speed button
        self.speed_btn = QPushButton("Test Speed && Stability")
        self.speed_btn.setFixedHeight(30)
        self.speed_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ss.accent};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.ss.accent_hover}; }}
        """)
        self.speed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speed_btn.clicked.connect(self.speed_test_clicked.emit)
        right_l.addWidget(self.speed_btn)

        main_split.addWidget(self._right_card, 1)
        v.addLayout(main_split)

    def _copy_ip(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._ip_value.text())

    def update_info(self, adapter_name, ip_address, dns_servers):
        self._adapter_name.setText(f"Active Connection: {adapter_name or '--'}")
        self._ip_value.setText(ip_address or "--")
        if dns_servers:
            self._dns_name.setText(dns_servers[0] if len(dns_servers) == 1 else "  |  ".join(dns_servers))
        else:
            self._dns_name.setText("Automatic (DHCP)")

    def set_dns_status(self, color: str):
        self._dns_status_dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

    def add_ping_result(self, ms: float):
        pass

    def add_ping_stat_result(self, ms: float):
        self._ping_stat_history.append(ms)
        if len(self._ping_stat_history) > 20:
            self._ping_stat_history = self._ping_stat_history[-20:]
        self._line_chart.set_data(self._ping_stat_history)
        avg = sum(self._ping_stat_history) / len(self._ping_stat_history)
        self._ping_stat_avg.setText(f"Avg: {avg:.0f}ms")

    def _start_bandwidth_monitor(self):
        """Start background bandwidth sampling."""
        try:
            self._bw_worker = BandwidthWorker(interval_ms=1000)
            self._bw_worker.bandwidth_ready.connect(self._on_bandwidth_sample)
            self._bw_worker.start()
        except ImportError:
            self._bw_worker = None

    def _stop_bandwidth_monitor(self):
        """Stop the bandwidth worker thread."""
        if hasattr(self, '_bw_worker') and self._bw_worker:
            self._bw_worker.stop()
            self._bw_worker.wait(1000)

    def _on_bandwidth_sample(self, upload_bps: float, download_bps: float):
        """Handle a bandwidth sample from the worker."""
        self._stream_chart.add_point(upload_bps, download_bps)
        total = upload_bps + download_bps
        if total >= 1_000_000:
            speed_str = f"{total / 1_000_000:.1f} MB/s"
        elif total >= 1_000:
            speed_str = f"{total / 1_000:.0f} KB/s"
        else:
            speed_str = f"{total:.0f} B/s"
        self._stream_speed.setText(speed_str)

    def update_analytics(self, uptime_seconds: int, success_count: int, fail_count: int):
        if uptime_seconds < 60:
            uptime_str = f"{uptime_seconds}s"
        elif uptime_seconds < 3600:
            uptime_str = f"{uptime_seconds // 60}m {uptime_seconds % 60}s"
        else:
            h = uptime_seconds // 3600
            m = (uptime_seconds % 3600) // 60
            uptime_str = f"{h}h {m}m"
        self._uptime_value.setText(uptime_str)

        total = success_count + fail_count
        self._queries_value.setText(f"{total} Queries")

    def set_last_change(self, text: str):
        self._last_change.setText(f"Last Change: {text}")

    def _sub_card_style(self, ss):
        return f"QFrame {{ background-color: {ss.hover}; border: 1px solid {ss.border}; border-radius: 6px; }}"

    def refresh_theme(self, ss: StyleSheet):
        self.ss = ss
        self.setStyleSheet(f"QFrame {{ background-color: {ss.card}; border: 1px solid {ss.border}; border-radius: 12px; }}")

        # Update all sub-card backgrounds
        sub_card_style = self._sub_card_style(ss)
        for card in (self._inet_card, self._ip_card, self._uptime_card,
                     self._usage_card, self._dns_card, self._right_card):
            card.setStyleSheet(sub_card_style)

        # Internet Status card
        self._adapter_name.setStyleSheet(f"color: {ss.text_tertiary}; font-size: 10px; background: transparent; border: none;")
        self._status_lbl.setStyleSheet(f"color: {ss.text}; font-size: 12px; font-weight: bold; background: transparent; border: none;")

        # IPv4 Address card
        self._ip_icon.setIcon(_load_icon("network", ss.text_secondary))
        self._ip_lbl.setStyleSheet(f"color: {ss.text_tertiary}; font-size: 11px; background: transparent; border: none;")
        self._ip_value.setStyleSheet(f"color: {ss.text}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        self._copy_btn.setIcon(_load_icon("copy", ss.text_secondary))
        self._copy_btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; border-radius: 4px; }} QPushButton:hover {{ background: {ss.border}; }}")

        # Uptime card
        self._uptime_icon.setIcon(_load_icon("clock", ss.text_secondary))
        self._uptime_title.setStyleSheet(f"color: {ss.text_tertiary}; font-size: 10px; background: transparent; border: none;")
        self._uptime_value.setStyleSheet(f"color: {ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")

        # Data Usage card
        self._usage_icon.setIcon(_load_icon("chart", ss.text_secondary))
        self._usage_title.setStyleSheet(f"color: {ss.text_tertiary}; font-size: 10px; background: transparent; border: none;")
        self._queries_value.setStyleSheet(f"color: {ss.text}; font-size: 16px; font-weight: bold; background: transparent; border: none;")

        # DNS in Use card
        self._dns_icon.setIcon(_load_icon("dns", ss.text_secondary))
        self._dns_title.setStyleSheet(f"color: {ss.text_tertiary}; font-size: 10px; background: transparent; border: none;")
        self._dns_name.setStyleSheet(f"color: {ss.text}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        self._last_change.setStyleSheet(f"color: {ss.text_tertiary}; font-size: 9px; background: transparent; border: none;")

        # Right column: Network Stream
        self._stream_lbl.setStyleSheet(f"color: {ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        for lbl in self._legend_labels:
            lbl.setStyleSheet(f"color: {ss.text_tertiary}; font-size: 9px; background: transparent; border: none;")

        # Separator
        self._sep.setStyleSheet(f"background-color: {ss.border};")

        # Ping Stat
        self._stat_lbl.setStyleSheet(f"color: {ss.text_secondary}; font-size: 11px; background: transparent; border: none;")

        # Speed button
        self.speed_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ss.accent}; color: white; border: none; border-radius: 8px; font-size: 13px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {ss.accent_hover}; }}
        """)

    def set_direction(self, is_rtl: bool):
        pass


class CustomDNSCard(QFrame):
    """Standalone card for custom DNS input."""

    custom_dns_apply = Signal(str, str)  # primary, secondary
    save_preset = Signal(str, str)  # primary, secondary

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"QFrame {{ background-color: {self.ss.card}; border: 1px solid {self.ss.border}; border-radius: 12px; }}")
        self.setMinimumHeight(70)

        v = QVBoxLayout(self)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(6)

        # Title row with save preset button
        title_row = QHBoxLayout()
        title = QLabel("Custom DNS")
        title.setStyleSheet(f"color: {self.ss.text}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        title_row.addWidget(title)
        title_row.addStretch()

        self.save_preset_btn = QPushButton()
        self.save_preset_btn.setIcon(_load_icon("manage", self.ss.text_secondary))
        self.save_preset_btn.setIconSize(QSize(12, 12))
        self.save_preset_btn.setFixedSize(24, 24)
        self.save_preset_btn.setToolTip("Save these DNS addresses for quick access later")
        self.save_preset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text_secondary};
                border: 1px solid {self.ss.border};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.ss.hover};
                color: {self.ss.accent};
                border-color: {self.ss.accent};
            }}
        """)
        self.save_preset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_preset_btn.clicked.connect(self._on_save_preset)
        title_row.addWidget(self.save_preset_btn)
        v.addLayout(title_row)

        inputs_row = QHBoxLayout()
        inputs_row.setSpacing(8)

        # Primary DNS input
        pri_col = QVBoxLayout()
        pri_col.setSpacing(2)
        pri_lbl = QLabel("Primary DNS")
        pri_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 10px; background: transparent; border: none;")
        self.primary_input = QLineEdit()
        self.primary_input.setPlaceholderText("e.g., 178.22.122.100")
        self.primary_input.setFixedHeight(26)
        self._style_input(self.primary_input)
        pri_col.addWidget(pri_lbl)
        pri_col.addWidget(self.primary_input)
        inputs_row.addLayout(pri_col)

        # Secondary DNS input
        sec_col = QVBoxLayout()
        sec_col.setSpacing(2)
        sec_lbl = QLabel("Secondary DNS")
        sec_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 10px; background: transparent; border: none;")
        self.secondary_input = QLineEdit()
        self.secondary_input.setPlaceholderText("e.g., 185.51.200.2")
        self.secondary_input.setFixedHeight(26)
        self._style_input(self.secondary_input)
        sec_col.addWidget(sec_lbl)
        sec_col.addWidget(self.secondary_input)
        inputs_row.addLayout(sec_col)

        v.addLayout(inputs_row)

        # Full-width Apply Custom button
        self.apply_custom_btn = QPushButton()
        self.apply_custom_btn.setIcon(_load_icon("apply", self.ss.accent))
        self.apply_custom_btn.setIconSize(QSize(14, 14))
        self.apply_custom_btn.setText(" Apply Custom")
        self.apply_custom_btn.setToolTip("Override current network adapter with the manual DNS inputs above")
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
            QLineEdit::placeholder {{
                color: #888888;
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

    def _on_save_preset(self):
        p = self.primary_input.text().strip()
        s = self.secondary_input.text().strip()
        if p:
            self.save_preset.emit(p, s)

    def refresh_theme(self, ss: StyleSheet):
        self.ss = ss
        self.setStyleSheet(f"QFrame {{ background-color: {ss.card}; border: 1px solid {ss.border}; border-radius: 12px; }}")
        for lbl in self.findChildren(QLabel):
            txt = lbl.text()
            if txt == "Custom DNS":
                lbl.setStyleSheet(f"color: {ss.text}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
            elif txt in ["Primary DNS", "Secondary DNS"]:
                lbl.setStyleSheet(f"color: {ss.text_secondary}; font-size: 10px; background: transparent; border: none;")
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
        self.save_preset_btn.setIcon(_load_icon("manage", ss.text_secondary))
        self.save_preset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ss.text_secondary};
                border: 1px solid {ss.border};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ss.hover};
                color: {ss.accent};
                border-color: {ss.accent};
            }}
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
