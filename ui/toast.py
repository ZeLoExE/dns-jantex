"""Toast notification — desktop-level popup, bottom-right of screen."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QPainter, QPainterPath, QScreen


class ToastNotification(QWidget):
    """A desktop-level toast that appears at the screen's bottom-right corner."""

    _active_toasts: list["ToastNotification"] = []
    TOAST_W = 370
    TOAST_H = 72
    MARGIN = 20
    GAP = 10

    def __init__(self, title: str, message: str, icon_type: str = "success",
                 dark_mode: bool = True, parent=None):
        # No parent — this is a top-level desktop window
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(self.TOAST_W, self.TOAST_H)
        self._dark = dark_mode
        self._icon_type = icon_type
        self._title = title
        self._message = message

        self._setup_ui()
        self._position_self()

    def _setup_ui(self):
        if self._dark:
            bg = "#1c1f2a"
            border = "#2a2d3a"
            text_color = "#e8eaed"
            sub_color = "#8b8fa3"
        else:
            bg = "#ffffff"
            border = "#e2e5ef"
            text_color = "#1e293b"
            sub_color = "#64748b"

        self._bg = bg
        self._border = border

        container = QFrame(self)
        container.setGeometry(0, 0, self.TOAST_W, self.TOAST_H)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 16px;
            }}
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 10, 16, 10)
        layout.setSpacing(12)

        # Icon circle
        icon_colors = {
            "success": "#22c55e",
            "error": "#ef4444",
            "warning": "#f59e0b",
            "info": "#6366f1",
            "dns": "#6366f1",
            "smart": "#6366f1",
            "flush": "#6366f1",
            "profile": "#6366f1",
        }
        icon_bg = icon_colors.get(self._icon_type, "#6366f1")
        icon_symbols = {
            "success": "\u2713",
            "error": "\u2715",
            "warning": "!",
            "info": "i",
            "dns": "\u2318",
            "smart": "\u26a1",
            "flush": "\u21bb",
            "profile": "\u2302",
        }

        icon_label = QLabel(icon_symbols.get(self._icon_type, "\u2713"))
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: white;
            background-color: {icon_bg};
            border-radius: 22px;
        """)
        layout.addWidget(icon_label)

        # Text
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_lbl = QLabel(self._title)
        title_lbl.setStyleSheet(
            f"color: {text_color}; font-size: 13px; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        text_col.addWidget(title_lbl)

        msg_lbl = QLabel(self._message)
        msg_lbl.setStyleSheet(
            f"color: {sub_color}; font-size: 12px; "
            f"background: transparent; border: none;"
        )
        msg_lbl.setMaximumWidth(240)
        text_col.addWidget(msg_lbl)

        layout.addLayout(text_col, 1)

    def _position_self(self):
        """Position at the bottom-right of the primary screen, stacked with existing toasts."""
        screen: QScreen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()

        x = geo.right() - self.TOAST_W - self.MARGIN
        y = geo.bottom() - self.TOAST_H - self.MARGIN

        # Stack upward for existing visible toasts
        offset = 0
        for t in ToastNotification._active_toasts:
            if t.isVisible():
                offset += t.height() + self.GAP
        y -= offset

        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        ToastNotification._active_toasts.append(self)

        # Slide in from right
        end_pos = self.pos()
        start_pos = QPoint(end_pos.x() + 60, end_pos.y())
        self.move(start_pos)

        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setDuration(200)
        self._slide_anim.setStartValue(start_pos)
        self._slide_anim.setEndValue(end_pos)
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_anim.start()

        # Auto-dismiss after 3 seconds
        QTimer.singleShot(3000, self._fade_out)

    def _fade_out(self):
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.finished.connect(self._cleanup)
        self._fade_anim.start()

    def _cleanup(self):
        if self in ToastNotification._active_toasts:
            ToastNotification._active_toasts.remove(self)
        self.deleteLater()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        path = QPainterPath()
        path.addRoundedRect(0.5, 0.5, self.width() - 1, self.height() - 1, 16, 16)

        p.setBrush(QColor(self._bg))
        p.drawPath(path)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QColor(self._border))
        p.drawPath(path)

        p.end()


def show_toast(title: str, message: str, icon_type: str = "success",
               dark_mode: bool = True, parent=None):
    """Convenience function to show a desktop toast notification."""
    toast = ToastNotification(title, message, icon_type, dark_mode)
    toast.show()
    return toast
