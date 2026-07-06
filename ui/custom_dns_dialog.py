"""Custom DNS Manager Dialog - Add, Edit, Remove custom DNS entries."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.styles import StyleSheet
from core.custom_dns import (
    load_custom_dns, add_custom_dns, update_custom_dns,
    remove_custom_dns, CustomDNSEntry
)


class CustomDNSEntryWidget(QFrame):
    """A single custom DNS entry row with edit/delete buttons."""

    edited = Signal(str)  # entry_id
    removed = Signal(str)  # entry_id

    def __init__(self, entry: CustomDNSEntry, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.entry = entry
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
        self.setFixedHeight(48)

        h = QHBoxLayout(self)
        h.setContentsMargins(12, 6, 12, 6)
        h.setSpacing(10)

        # Name
        name_lbl = QLabel(self.entry.name)
        name_lbl.setFixedWidth(120)
        name_lbl.setStyleSheet(f"color: {self.ss.text}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        h.addWidget(name_lbl)

        # Primary DNS
        pri_lbl = QLabel(self.entry.primary)
        pri_lbl.setStyleSheet(f"color: {self.ss.text}; font-family: Consolas, monospace; font-size: 12px; background: transparent; border: none;")
        h.addWidget(pri_lbl, 1)

        # Separator
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {self.ss.border}; background: transparent; border: none;")
        h.addWidget(sep)

        # Secondary DNS
        sec_lbl = QLabel(self.entry.secondary)
        sec_lbl.setStyleSheet(f"color: {self.ss.text}; font-family: Consolas, monospace; font-size: 12px; background: transparent; border: none;")
        h.addWidget(sec_lbl, 1)

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
        edit_btn.clicked.connect(lambda: self.edited.emit(self.entry.id))
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
        del_btn.clicked.connect(lambda: self._confirm_delete())
        h.addWidget(del_btn)

    def _confirm_delete(self):
        reply = QMessageBox.question(
            None, "Delete DNS",
            f"Delete '{self.entry.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.removed.emit(self.entry.id)


class CustomDNSEditDialog(QDialog):
    """Dialog for adding or editing a custom DNS entry."""

    def __init__(self, style_sheet: StyleSheet, entry: CustomDNSEntry = None, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self.entry = entry
        self.result_data = None
        self._setup_ui()

        if entry:
            self.name_input.setText(entry.name)
            self.primary_input.setText(entry.primary)
            self.secondary_input.setText(entry.secondary)

    def _setup_ui(self):
        self.setWindowTitle("Edit Custom DNS" if self.entry else "Add Custom DNS")
        self.setFixedSize(420, 250)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.ss.bg};
                border: 1px solid {self.ss.border};
                border-radius: 12px;
            }}
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        # Title
        title = QLabel("Edit Custom DNS" if self.entry else "Add Custom DNS")
        title.setStyleSheet(f"color: {self.ss.text}; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        v.addWidget(title)

        # Name
        name_lbl = QLabel("DNS Name")
        name_lbl.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 11px; background: transparent; border: none;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., My Gaming DNS")
        self._style_input(self.name_input)
        v.addWidget(name_lbl)
        v.addWidget(self.name_input)

        # DNS inputs row
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

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(85, 34)
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
        save_btn.setFixedSize(85, 34)
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

    def _style_input(self, widget: QLineEdit):
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.ss.hover};
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

    def _save(self):
        name = self.name_input.text().strip()
        primary = self.primary_input.text().strip()
        secondary = self.secondary_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a DNS name.")
            return
        if not primary:
            QMessageBox.warning(self, "Error", "Please enter a Primary DNS address.")
            return

        # Basic IP validation
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, primary):
            QMessageBox.warning(self, "Error", "Invalid Primary DNS address format.")
            return
        if secondary and not re.match(ip_pattern, secondary):
            QMessageBox.warning(self, "Error", "Invalid Secondary DNS address format.")
            return

        self.result_data = (name, primary, secondary)
        self.accept()


class CustomDNSManagerDialog(QDialog):
    """Main dialog for managing custom DNS entries."""

    dns_changed = Signal()  # Emitted when list changes

    def __init__(self, style_sheet: StyleSheet, parent=None):
        super().__init__(parent)
        self.ss = style_sheet
        self._setup_ui()
        self._load_entries()

    def _setup_ui(self):
        self.setWindowTitle("Custom DNS Manager")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.ss.bg};
            }}
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Custom DNS Manager")
        title.setStyleSheet(f"color: {self.ss.text}; font-size: 20px; font-weight: bold; background: transparent; border: none;")
        hdr.addWidget(title)
        hdr.addStretch()

        add_btn = QPushButton("+ Add DNS")
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
        self.list_layout.addStretch()

        scroll.setWidget(self.container)
        v.addWidget(scroll, 1)

        # Close button
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
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        v.addLayout(btn_row)

    def _load_entries(self):
        """Load and display all custom DNS entries."""
        # Clear existing widgets
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = load_custom_dns()

        if not entries:
            empty = QLabel("No custom DNS entries yet. Click '+ Add DNS' to create one.")
            empty.setStyleSheet(f"color: {self.ss.text_secondary}; font-size: 12px; padding: 20px; background: transparent; border: none;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(empty)
        else:
            for entry in entries:
                widget = CustomDNSEntryWidget(entry, self.ss)
                widget.edited.connect(self._edit_entry)
                widget.removed.connect(self._remove_entry)
                self.list_layout.addWidget(widget)

        self.list_layout.addStretch()

    def _add_entry(self):
        """Open dialog to add a new custom DNS entry."""
        dialog = CustomDNSEditDialog(self.ss, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            name, primary, secondary = dialog.result_data
            add_custom_dns(name, primary, secondary)
            self._load_entries()
            self.dns_changed.emit()

    def _edit_entry(self, entry_id: str):
        """Open dialog to edit an existing custom DNS entry."""
        entry = None
        for e in load_custom_dns():
            if e.id == entry_id:
                entry = e
                break

        if not entry:
            return

        dialog = CustomDNSEditDialog(self.ss, entry=entry, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            name, primary, secondary = dialog.result_data
            update_custom_dns(entry_id, name, primary, secondary)
            self._load_entries()
            self.dns_changed.emit()

    def _remove_entry(self, entry_id: str):
        """Remove a custom DNS entry."""
        remove_custom_dns(entry_id)
        self._load_entries()
        self.dns_changed.emit()
