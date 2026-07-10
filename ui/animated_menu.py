from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QGraphicsOpacityEffect, QLabel, QComboBox,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QPoint, QSize, QTimer,
    QParallelAnimationGroup, Property, QRectF, Signal
)
from PySide6.QtGui import QIcon, QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QPixmap


class ToggleSwitch(QWidget):
    """Custom toggle switch with green indicator when ON."""

    toggled = Signal(bool)

    def __init__(self, checked=False, on_color="#22c55e", off_color="#3a3d4a",
                 knob_color="#ffffff", parent=None):
        super().__init__(parent)
        self._checked = checked
        self._on_color = on_color
        self._off_color = off_color
        self._knob_color = knob_color
        self._circle_pos = 20.0 if checked else 4.0
        self._anim = None
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _get_circle_pos(self):
        return self._circle_pos

    def _set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    circle_pos = Property(float, _get_circle_pos, _set_circle_pos)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked == checked:
            return
        self._checked = checked
        self._animate()
        self.toggled.emit(self._checked)

    def toggle(self):
        self._checked = not self._checked
        self._animate()
        self.toggled.emit(self._checked)
        return self._checked

    def _animate(self):
        if self._anim and self._anim.state() == QPropertyAnimation.State.Running:
            self._anim.stop()

        self._anim = QPropertyAnimation(self, b"circle_pos")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        if self._checked:
            self._anim.setStartValue(4.0)
            self._anim.setEndValue(20.0)
        else:
            self._anim.setStartValue(20.0)
            self._anim.setEndValue(4.0)

        self._anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self._animate()
            self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_rect = QRectF(0, 0, 44, 24)
        bg_color = QColor(self._on_color) if self._checked else QColor(self._off_color)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg_color))
        p.drawRoundedRect(bg_rect, 12.0, 12.0)

        circle = QRectF(self._circle_pos, 4, 16, 16)
        p.setBrush(QBrush(QColor(self._knob_color)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(circle)

        p.end()


class MenuSectionHeader(QLabel):
    """Section header label for the menu."""

    def __init__(self, text, style_sheet=None, parent=None):
        super().__init__(text.upper(), parent)
        color = style_sheet.text_tertiary if style_sheet else "#6b7084"
        self.setStyleSheet(f"""
            color: {color};
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
            padding: 8px 16px 4px 16px;
            background: transparent;
            border: none;
        """)
        self.setFixedHeight(24)


class MenuTitleLabel(QLabel):
    """Menu title label."""

    def __init__(self, text, style_sheet=None, parent=None):
        super().__init__(text.upper(), parent)
        color = style_sheet.text if style_sheet else "#e8eaed"
        self.setStyleSheet(f"""
            color: {color};
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 0.5px;
            padding: 12px 16px 8px 16px;
            background: transparent;
            border: none;
        """)
        self.setFixedHeight(36)


class _MenuItem(QPushButton):
    """Individual menu item with hover effects and icon."""

    def __init__(self, style_sheet, icon=None, text="", parent=None):
        super().__init__(parent)
        self.ss = style_sheet

        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(18, 18))
        self.setText(text)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.ss.text};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.ss.hover};
            }}
            QPushButton:pressed {{
                background-color: {self.ss.border};
            }}
        """)


class _ToggleRow(QWidget):
    """Row containing label + toggle switch."""

    def __init__(self, style_sheet, icon=None, text="", checked=False, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(12)

        # Icon
        if icon:
            icon_label = QLabel()
            icon_label.setFixedSize(20, 20)
            icon_label.setPixmap(icon.pixmap(18, 18))
            icon_label.setStyleSheet("background: transparent; border: none;")
            layout.addWidget(icon_label)

        # Text
        self.label = QLabel(text)
        self.label.setStyleSheet(f"""
            color: {self.ss.text};
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.label)

        layout.addStretch()

        # Toggle switch - green when ON, themed track when OFF
        off_track = self.ss.border if self.ss else "#3a3d4a"
        self.toggle = ToggleSwitch(
            checked,
            on_color="#22c55e",
            off_color=off_track,
            knob_color="#ffffff"
        )
        layout.addWidget(self.toggle)

    def isChecked(self):
        return self.toggle.isChecked()

    def setChecked(self, checked):
        self.toggle.setChecked(checked)


class _DropdownRow(QWidget):
    """Row containing label + dropdown combo."""

    def __init__(self, style_sheet, icon=None, text="", options=None, current_index=0, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(12)

        # Icon
        if icon:
            icon_label = QLabel()
            icon_label.setFixedSize(20, 20)
            icon_label.setPixmap(icon.pixmap(18, 18))
            icon_label.setStyleSheet("background: transparent; border: none;")
            layout.addWidget(icon_label)

        # Text
        self.label = QLabel(text)
        self.label.setStyleSheet(f"""
            color: {self.ss.text};
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.label)

        layout.addStretch()

        # Combo box - themed
        self.combo = QComboBox()
        if options:
            self.combo.addItems(options)
        if current_index >= 0:
            self.combo.setCurrentIndex(current_index)
        self.combo.setFixedWidth(110)
        self.combo.setFixedHeight(30)
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.ss.input_bg};
                color: {self.ss.text};
                border: 1px solid {self.ss.border};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QComboBox:hover {{
                border-color: {self.ss.accent};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
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
        layout.addWidget(self.combo)


class _CheckableRow(QWidget):
    """Row with icon, label, and a toggle switch."""

    toggled = Signal(bool)

    def __init__(self, style_sheet, icon=None, text="", checked=False, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(12)

        # Icon
        if icon:
            icon_label = QLabel()
            icon_label.setFixedSize(20, 20)
            icon_label.setPixmap(icon.pixmap(18, 18))
            icon_label.setStyleSheet("background: transparent; border: none;")
            layout.addWidget(icon_label)

        # Text
        self.label = QLabel(text)
        self.label.setStyleSheet(f"""
            color: {self.ss.text};
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.label)

        layout.addStretch()

        # Toggle switch (same as Dark Mode)
        off_track = self.ss.border
        self.toggle = ToggleSwitch(
            checked,
            on_color="#22c55e",
            off_color=off_track,
            knob_color="#ffffff"
        )
        layout.addWidget(self.toggle)
        self.toggle.toggled.connect(self.toggled)

    def isChecked(self):
        return self.toggle.isChecked()

    def setChecked(self, checked):
        self.toggle.setChecked(checked)


class AnimatedMenu(QWidget):
    """Custom animated dropdown menu with preferences layout."""

    def __init__(self, style_sheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self._items = []
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        """Set up the menu UI."""
        self.container = QFrame(self)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.ss.card};
                border: 1px solid {self.ss.border};
                border-radius: 14px;
            }}
        """)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.container.setGraphicsEffect(shadow)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        self.opacity_effect = QGraphicsOpacityEffect(self.container)
        self.opacity_effect.setOpacity(0.0)
        self.container.setGraphicsEffect(shadow)

    def _setup_animations(self):
        """Set up the slide and fade animations."""
        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(220)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(180)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.open_group = QParallelAnimationGroup(self)
        self.open_group.addAnimation(self.slide_anim)
        self.open_group.addAnimation(self.opacity_anim)

        self.close_slide_anim = QPropertyAnimation(self, b"pos")
        self.close_slide_anim.setDuration(180)
        self.close_slide_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self.close_opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.close_opacity_anim.setDuration(150)
        self.close_opacity_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        self.close_group = QParallelAnimationGroup(self)
        self.close_group.addAnimation(self.close_slide_anim)
        self.close_group.addAnimation(self.close_opacity_anim)
        self.close_group.finished.connect(self._on_close_finished)

    def add_title(self, text=""):
        """Add a menu title header."""
        title = MenuTitleLabel(text, self.ss, self.container)
        self.container_layout.addWidget(title)
        self._items.append(title)

    def add_section_header(self, text=""):
        """Add a section header label."""
        header = MenuSectionHeader(text, self.ss, self.container)
        self.container_layout.addWidget(header)
        self._items.append(header)

    def add_toggle_row(self, icon=None, text="", checked=False):
        """Add a row with label and toggle switch."""
        row = _ToggleRow(self.ss, icon, text, checked, self.container)
        self.container_layout.addWidget(row)
        self._items.append(row)
        return row

    def add_dropdown_row(self, icon=None, text="", options=None, current_index=0):
        """Add a row with label and dropdown combo."""
        row = _DropdownRow(self.ss, icon, text, options, current_index, self.container)
        self.container_layout.addWidget(row)
        self._items.append(row)
        return row

    def add_checkable_row(self, icon=None, text="", checked=False):
        """Add a row with label and checkbox indicator."""
        row = _CheckableRow(self.ss, icon, text, checked, self.container)
        self.container_layout.addWidget(row)
        self._items.append(row)
        return row

    def add_action(self, icon=None, text="", checkable=False, checked=False):
        """Add a menu action item."""
        item = _MenuItem(self.ss, icon, text, self.container)
        self.container_layout.addWidget(item)
        self._items.append(item)
        return item

    def add_separator(self):
        """Add a visual separator."""
        sep = QFrame(self.container)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.ss.border}; margin: 4px 16px;")
        self.container_layout.addWidget(sep)
        self._items.append(sep)

    def popup(self, pos):
        """Show the menu at the given position with animation."""
        self.container.adjustSize()
        w = self.container.sizeHint().width() + 16
        h = self.container.sizeHint().height() + 16
        self.setFixedSize(w, h)
        self.container.move(8, 8)

        final_pos = QPoint(pos.x(), pos.y())
        start_pos = QPoint(final_pos.x(), final_pos.y() - 10)

        self.opacity_effect.setOpacity(0.0)
        self.move(start_pos)
        self.show()
        self.raise_()

        self.slide_anim.setStartValue(start_pos)
        self.slide_anim.setEndValue(final_pos)
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.open_group.start()

    def close_with_animation(self):
        """Close the menu with reverse animation."""
        if not self.isVisible():
            return

        current_pos = self.pos()
        self.close_slide_anim.setStartValue(current_pos)
        self.close_slide_anim.setEndValue(QPoint(current_pos.x(), current_pos.y() - 10))
        self.close_opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.close_opacity_anim.setEndValue(0.0)
        self.close_group.start()

    def _on_close_finished(self):
        """Handle close animation completion."""
        self.hide()

    def mousePressEvent(self, event):
        """Handle mouse press outside menu to close."""
        if not self.container.geometry().contains(self.mapFromGlobal(event.globalPosition().toPoint())):
            self.close_with_animation()
            event.accept()
        else:
            super().mousePressEvent(event)

    def paintEvent(self, event):
        pass
