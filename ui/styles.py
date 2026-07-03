from PySide6.QtWidgets import QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class Colors:
    """Color constants for the application."""

    # Dark mode colors
    DARK_BG = "#1e1e1e"
    DARK_CARD = "#2d2d2d"
    DARK_HOVER = "#3d3d3d"
    DARK_BORDER = "#404040"
    DARK_TEXT = "#ffffff"
    DARK_TEXT_SECONDARY = "#b0b0b0"
    DARK_ACCENT = "#f57c00"
    DARK_ACCENT_HOVER = "#ff9800"
    DARK_SUCCESS = "#4caf50"
    DARK_ERROR = "#f44336"
    DARK_WARNING = "#ff9800"

    # Light mode colors
    LIGHT_BG = "#f5f5f5"
    LIGHT_CARD = "#ffffff"
    LIGHT_HOVER = "#e8e8e8"
    LIGHT_BORDER = "#e0e0e0"
    LIGHT_TEXT = "#1e1e1e"
    LIGHT_TEXT_SECONDARY = "#666666"
    LIGHT_ACCENT = "#f57c00"
    LIGHT_ACCENT_HOVER = "#e65100"
    LIGHT_SUCCESS = "#4caf50"
    LIGHT_ERROR = "#f44336"
    LIGHT_WARNING = "#ff9800"


class StyleSheet:
    """Generates QSS stylesheets for the application."""

    def __init__(self, dark_mode: bool = True):
        self.dark_mode = dark_mode
        self._update_colors()

    def _update_colors(self):
        """Update color palette based on theme."""
        if self.dark_mode:
            self.bg = Colors.DARK_BG
            self.card = Colors.DARK_CARD
            self.hover = Colors.DARK_HOVER
            self.border = Colors.DARK_BORDER
            self.text = Colors.DARK_TEXT
            self.text_secondary = Colors.DARK_TEXT_SECONDARY
            self.accent = Colors.DARK_ACCENT
            self.accent_hover = Colors.DARK_ACCENT_HOVER
            self.success = Colors.DARK_SUCCESS
            self.error = Colors.DARK_ERROR
            self.warning = Colors.DARK_WARNING
        else:
            self.bg = Colors.LIGHT_BG
            self.card = Colors.LIGHT_CARD
            self.hover = Colors.LIGHT_HOVER
            self.border = Colors.LIGHT_BORDER
            self.text = Colors.LIGHT_TEXT
            self.text_secondary = Colors.LIGHT_TEXT_SECONDARY
            self.accent = Colors.LIGHT_ACCENT
            self.accent_hover = Colors.LIGHT_ACCENT_HOVER
            self.success = Colors.LIGHT_SUCCESS
            self.error = Colors.LIGHT_ERROR
            self.warning = Colors.LIGHT_WARNING

    def get_main_window_style(self) -> str:
        """Get the main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {self.bg};
            }}
        """

    def get_card_style(self) -> str:
        """Get card widget stylesheet."""
        return f"""
            QFrame {{
                background-color: {self.card};
                border: 1px solid {self.border};
                border-radius: 12px;
                padding: 16px;
            }}
        """

    def get_button_style(self, primary: bool = True) -> str:
        """Get button stylesheet."""
        if primary:
            return f"""
                QPushButton {{
                    background-color: {self.accent};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {self.accent_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.accent};
                }}
                QPushButton:disabled {{
                    background-color: {self.border};
                    color: {self.text_secondary};
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.text};
                    border: 1px solid {self.border};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {self.hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.border};
                }}
                QPushButton:disabled {{
                    background-color: {self.border};
                    color: {self.text_secondary};
                }}
            """

    def get_combo_style(self) -> str:
        """Get combo box stylesheet."""
        return f"""
            QComboBox {{
                background-color: {self.card};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: {self.accent};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {self.text};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.card};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
                selection-background-color: {self.accent};
                selection-color: white;
                padding: 4px;
            }}
        """

    def get_line_edit_style(self) -> str:
        """Get line edit stylesheet."""
        return f"""
            QLineEdit {{
                background-color: {self.card};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QLineEdit:hover {{
                border-color: {self.accent};
            }}
            QLineEdit:focus {{
                border-color: {self.accent};
            }}
            QLineEdit:disabled {{
                background-color: {self.hover};
                color: {self.text_secondary};
            }}
        """

    def get_label_style(self, bold: bool = False, secondary: bool = False) -> str:
        """Get label stylesheet."""
        font_weight = "bold" if bold else "normal"
        color = self.text_secondary if secondary else self.text
        return f"""
            QLabel {{
                color: {color};
                font-weight: {font_weight};
                background: transparent;
                border: none;
            }}
        """

    def get_title_style(self) -> str:
        """Get title label stylesheet."""
        return f"""
            QLabel {{
                color: {self.text};
                font-size: 24px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """

    def get_subtitle_style(self) -> str:
        """Get subtitle label stylesheet."""
        return f"""
            QLabel {{
                color: {self.text_secondary};
                font-size: 14px;
                background: transparent;
                border: none;
            }}
        """

    def get_radio_style(self) -> str:
        """Get radio button stylesheet."""
        return f"""
            QRadioButton {{
                color: {self.text};
                spacing: 8px;
                background: transparent;
                border: none;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {self.border};
                background: transparent;
            }}
            QRadioButton::indicator:hover {{
                border-color: {self.accent};
            }}
            QRadioButton::indicator:checked {{
                background-color: {self.accent};
                border-color: {self.accent};
            }}
        """

    def get_spinbox_style(self) -> str:
        """Get spin box stylesheet."""
        return f"""
            QSpinBox {{
                background-color: {self.card};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QSpinBox:hover {{
                border-color: {self.accent};
            }}
            QSpinBox:focus {{
                border-color: {self.accent};
            }}
        """

    def get_progress_style(self) -> str:
        """Get progress bar stylesheet."""
        return f"""
            QProgressBar {{
                background-color: {self.hover};
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.accent};
                border-radius: 4px;
            }}
        """

    def get_tooltip_style(self) -> str:
        """Get tooltip stylesheet."""
        return f"""
            QToolTip {{
                background-color: {self.card};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }}
        """

    def get_scroll_area_style(self) -> str:
        """Get scroll area stylesheet."""
        return f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {self.border};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.text_secondary};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """

    def get_latency_style(self) -> str:
        """Get latency label stylesheet."""
        return f"""
            QLabel {{
                color: {self.accent};
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """

    def get_copy_btn_style(self) -> str:
        """Get copy button stylesheet."""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {self.accent};
                border: 1px solid {self.border};
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
                min-width: 50px;
                max-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {self.accent};
                color: white;
                border-color: {self.accent};
            }}
            QPushButton:pressed {{
                background-color: {self.accent_hover};
            }}
        """

    def get_icon_btn_style(self) -> str:
        """Get icon button stylesheet for header buttons."""
        return f"""
            QPushButton {{
                background-color: {self.card};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
                padding: 4px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {self.hover};
                border-color: {self.accent};
            }}
            QPushButton:pressed {{
                background-color: {self.border};
            }}
        """


class Fonts:
    """Font configuration for the application."""

    @staticmethod
    def get_default_font() -> QFont:
        """Get the default application font."""
        font = QFont("Segoe UI", 10)
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        return font

    @staticmethod
    def get_persian_font() -> QFont:
        """Get the Persian font."""
        # Try Vazirmatn first, fall back to system fonts
        for font_name in ["Vazirmatn", "IRANSans", "Tahoma", "Arial"]:
            font = QFont(font_name, 10)
            if font.exactMatch():
                return font
        return QFont("Arial", 10)

    @staticmethod
    def get_title_font() -> QFont:
        """Get the title font."""
        font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        return font

    @staticmethod
    def get_mono_font() -> QFont:
        """Get monospace font for DNS addresses."""
        return QFont("Consolas", 10)
