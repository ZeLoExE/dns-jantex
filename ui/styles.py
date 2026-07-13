from PySide6.QtGui import QFont


class Colors:
    """Color constants for the application."""

    # Dark mode colors (Midnight theme - blue-tinted dark)
    DARK_BG = "#0f1117"
    DARK_SURFACE = "#181b23"
    DARK_CARD = "#1c1f2a"
    DARK_HOVER = "#252836"
    DARK_BORDER = "#2a2d3a"
    DARK_TEXT = "#e8eaed"
    DARK_TEXT_SECONDARY = "#8b8fa3"
    DARK_TEXT_TERTIARY = "#5c6078"
    DARK_ACCENT = "#6366f1"
    DARK_ACCENT_HOVER = "#818cf8"
    DARK_ACCENT_SUBTLE = "#6366f120"
    DARK_SUCCESS = "#22c55e"
    DARK_ERROR = "#ef4444"
    DARK_WARNING = "#f59e0b"
    DARK_INPUT_BG = "#252836"

    # Light mode colors (Clean theme)
    LIGHT_BG = "#f8f9fc"
    LIGHT_SURFACE = "#ffffff"
    LIGHT_CARD = "#ffffff"
    LIGHT_HOVER = "#f1f3f9"
    LIGHT_BORDER = "#e2e5ef"
    LIGHT_TEXT = "#1e293b"
    LIGHT_TEXT_SECONDARY = "#64748b"
    LIGHT_TEXT_TERTIARY = "#94a3b8"
    LIGHT_ACCENT = "#6366f1"
    LIGHT_ACCENT_HOVER = "#4f46e5"
    LIGHT_ACCENT_SUBTLE = "#6366f115"
    LIGHT_SUCCESS = "#22c55e"
    LIGHT_ERROR = "#ef4444"
    LIGHT_WARNING = "#f59e0b"
    LIGHT_INPUT_BG = "#f1f3f9"


class StyleSheet:
    """Generates QSS stylesheets for the application."""

    def __init__(self, dark_mode: bool = True):
        self.dark_mode = dark_mode
        self._update_colors()

    def _update_colors(self):
        """Update color palette based on theme."""
        if self.dark_mode:
            self.bg = Colors.DARK_BG
            self.surface = Colors.DARK_SURFACE
            self.card = Colors.DARK_CARD
            self.hover = Colors.DARK_HOVER
            self.border = Colors.DARK_BORDER
            self.text = Colors.DARK_TEXT
            self.text_secondary = Colors.DARK_TEXT_SECONDARY
            self.text_tertiary = Colors.DARK_TEXT_TERTIARY
            self.accent = Colors.DARK_ACCENT
            self.accent_hover = Colors.DARK_ACCENT_HOVER
            self.accent_subtle = Colors.DARK_ACCENT_SUBTLE
            self.success = Colors.DARK_SUCCESS
            self.error = Colors.DARK_ERROR
            self.warning = Colors.DARK_WARNING
            self.input_bg = Colors.DARK_INPUT_BG
        else:
            self.bg = Colors.LIGHT_BG
            self.surface = Colors.LIGHT_SURFACE
            self.card = Colors.LIGHT_CARD
            self.hover = Colors.LIGHT_HOVER
            self.border = Colors.LIGHT_BORDER
            self.text = Colors.LIGHT_TEXT
            self.text_secondary = Colors.LIGHT_TEXT_SECONDARY
            self.text_tertiary = Colors.LIGHT_TEXT_TERTIARY
            self.accent = Colors.LIGHT_ACCENT
            self.accent_hover = Colors.LIGHT_ACCENT_HOVER
            self.accent_subtle = Colors.LIGHT_ACCENT_SUBTLE
            self.success = Colors.LIGHT_SUCCESS
            self.error = Colors.LIGHT_ERROR
            self.warning = Colors.LIGHT_WARNING
            self.input_bg = Colors.LIGHT_INPUT_BG

    def get_main_window_style(self) -> str:
        """Get the main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {self.bg};
            }}
        """

    def get_title_bar_style(self) -> str:
        """Get the custom title bar container stylesheet."""
        return f"""
            QWidget#titleBar {{
                background-color: {self.bg};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """

    def get_minimize_btn_style(self) -> str:
        """Get minimize button stylesheet matching Windows 11."""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {self.text};
                border: none;
                border-radius: 0px;
                font-size: 16px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: {self.hover};
            }}
            QPushButton:pressed {{
                background-color: {self.border};
            }}
        """

    def get_close_btn_style(self) -> str:
        """Get close button stylesheet matching Windows 11."""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {self.text};
                border: none;
                border-radius: 0px;
                font-size: 16px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: #e81123;
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #c42b1c;
                color: white;
            }}
        """

    def get_card_style(self) -> str:
        """Get card widget stylesheet."""
        return f"""
            QFrame {{
                background-color: {self.card};
                border: 1px solid {self.border};
                border-radius: 16px;
                padding: 20px;
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
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: bold;
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {self.accent_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.accent};
                }}
                QPushButton:disabled {{
                    background-color: {self.border};
                    color: {self.text_tertiary};
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.text};
                    border: 2px solid {self.border};
                    border-radius: 10px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {self.hover};
                    border-color: {self.accent};
                }}
                QPushButton:pressed {{
                    background-color: {self.border};
                }}
                QPushButton:disabled {{
                    background-color: {self.hover};
                    color: {self.text_tertiary};
                    border-color: {self.border};
                }}
            """

    def get_combo_style(self) -> str:
        """Get combo box stylesheet."""
        return f"""
            QComboBox {{
                background-color: {self.input_bg};
                color: {self.text};
                border: 2px solid {self.border};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 36px;
            }}
            QComboBox:hover {{
                border-color: {self.accent};
            }}
            QComboBox:focus {{
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
                border-top: 6px solid {self.text_secondary};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.surface};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
                selection-background-color: {self.accent};
                selection-color: white;
                outline: none;
                padding: 4px;
            }}
        """

    def get_line_edit_style(self) -> str:
        """Get line edit stylesheet."""
        return f"""
            QLineEdit {{
                background-color: {self.input_bg};
                color: {self.text};
                border: 2px solid {self.border};
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 14px;
                min-height: 36px;
            }}
            QLineEdit:hover {{
                border-color: {self.text_tertiary};
            }}
            QLineEdit:focus {{
                border-color: {self.accent};
                border-width: 2px;
            }}
            QLineEdit:disabled {{
                background-color: {self.hover};
                color: {self.text_tertiary};
                border-color: {self.border};
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
                font-size: 28px;
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
                spacing: 10px;
                background: transparent;
                border: none;
            }}
            QRadioButton::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
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
                background-color: {self.input_bg};
                color: {self.text};
                border: 2px solid {self.border};
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 36px;
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
                height: 10px;
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
                background-color: {self.surface};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
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
                width: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {self.border};
                border-radius: 3px;
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
                font-size: 12px;
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
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 56px;
                max-width: 64px;
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
                border-radius: 10px;
                padding: 6px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {self.hover};
                border-color: {self.accent};
            }}
            QPushButton:pressed {{
                background-color: {self.border};
            }}
        """

    def get_tag_btn_style(self, active: bool = False) -> str:
        """Get tag filter chip button stylesheet."""
        if active:
            return f"""
                QPushButton {{
                    background-color: {self.accent};
                    color: white;
                    border: 1px solid {self.accent};
                    border-radius: 14px;
                    padding: 5px 14px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """
        return f"""
            QPushButton {{
                background-color: {self.hover};
                color: {self.text_secondary};
                border: 1px solid {self.border};
                border-radius: 14px;
                padding: 5px 14px;
                font-size: 11px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: {self.card};
                color: {self.text};
                border-color: {self.accent};
            }}
        """

    def get_provider_row_style(self) -> str:
        """Get provider row stylesheet."""
        return f"""
            QFrame {{
                background-color: {self.hover};
                border-radius: 8px;
                border: 1px solid {self.border};
            }}
            QFrame:hover {{
                border-color: {self.accent};
                background-color: {self.card};
            }}
        """

    def get_input_style(self) -> str:
        """Get input field stylesheet with accent focus."""
        return f"""
            QLineEdit {{
                background-color: {self.input_bg};
                color: {self.text};
                border: 1px solid {self.border};
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {self.accent};
            }}
        """

    def get_dialog_style(self) -> str:
        """Get glassmorphism dialog stylesheet."""
        if self.dark_mode:
            return f"""
                QMessageBox {{
                    background-color: rgba(24, 27, 35, 220);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 16px;
                }}
                QMessageBox QLabel {{
                    color: {self.text};
                    font-size: 14px;
                    font-weight: 500;
                    background: transparent;
                    border: none;
                }}
                QMessageBox QPushButton {{
                    background-color: {self.accent};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 24px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 70px;
                    min-height: 28px;
                }}
                QMessageBox QPushButton:hover {{
                    background-color: {self.accent_hover};
                }}
                QMessageBox QPushButton:pressed {{
                    background-color: {self.accent};
                }}
            """
        else:
            return f"""
                QMessageBox {{
                    background-color: rgba(255, 255, 255, 230);
                    border: 1px solid rgba(255, 255, 255, 0.6);
                    border-radius: 16px;
                }}
                QMessageBox QLabel {{
                    color: {self.text};
                    font-size: 14px;
                    font-weight: 500;
                    background: transparent;
                    border: none;
                }}
                QMessageBox QPushButton {{
                    background-color: {self.accent};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 24px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 70px;
                    min-height: 28px;
                }}
                QMessageBox QPushButton:hover {{
                    background-color: {self.accent_hover};
                }}
                QMessageBox QPushButton:pressed {{
                    background-color: {self.accent};
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
