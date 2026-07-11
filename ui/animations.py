"""Reusable animation utilities for smooth micro-interactions."""

from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, QTimer, Property
)
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget
from PySide6.QtGui import QColor


def lerp_color(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colors. t in [0, 1]."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _current_bg(widget: QWidget) -> str:
    """Extract current background-color from widget's stylesheet."""
    ss = widget.styleSheet()
    for line in ss.split(";"):
        line = line.strip()
        if "background-color:" in line:
            val = line.split("background-color:")[1].strip()
            if val.startswith("#") and len(val) >= 7:
                return val[:7]
    return "#2d2d2d"


def _current_border(widget: QWidget) -> str:
    """Extract current border color from widget's stylesheet (last solid color)."""
    ss = widget.styleSheet()
    for line in ss.split(";"):
        line = line.strip()
        if "border:" in line and "solid" in line:
            parts = line.split("solid")
            if len(parts) >= 2:
                val = parts[-1].strip().rstrip("}")
                if val.startswith("#") and len(val) >= 7:
                    return val[:7]
    return "#404040"


def animate_background(widget: QWidget, target_color: str, duration: int = 150):
    """Smoothly animate background-color of a widget."""
    start = _current_bg(widget)
    if start.lower() == target_color.lower():
        return

    # Store original stylesheet parts to preserve other properties
    anim = QPropertyAnimation(widget, b"styleSheet")
    anim.setDuration(duration)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    original_ss = widget.styleSheet()

    def make_step(color):
        def on_val(value):
            # Replace only background-color, keep rest of stylesheet
            lines = original_ss.split(";")
            new_lines = []
            for line in lines:
                if "background-color:" in line:
                    indent = line[:len(line) - len(line.lstrip())]
                    new_lines.append(f"{indent}background-color: {color}")
                else:
                    new_lines.append(line)
            widget.setStyleSheet(";".join(new_lines))
        return on_val

    # Use frame-based animation with manual interpolation
    anim.setStartValue(0)
    anim.setEndValue(100)

    frames = max(duration // 16, 3)
    step_ms = duration // frames

    def step(t_val):
        progress = t_val / 100.0
        color = lerp_color(start, target_color, progress)
        lines = original_ss.split(";")
        new_lines = []
        for line in lines:
            if "background-color:" in line:
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(f"{indent}background-color: {color}")
            else:
                new_lines.append(line)
        widget.setStyleSheet(";".join(new_lines))

    for i in range(1, frames + 1):
        t = i / frames
        QTimer.singleShot(i * step_ms, lambda p=t: step(int(p * 100)))

    anim.start()
    # Keep reference to prevent garbage collection
    widget._bg_anim = anim


def animate_border(widget: QWidget, target_color: str, duration: int = 150):
    """Smoothly animate border-color of a widget."""
    start = _current_border(widget)
    if start.lower() == target_color.lower():
        return

    original_ss = widget.styleSheet()
    frames = max(duration // 16, 3)
    step_ms = duration // frames

    def step(t_val):
        progress = t_val / 100.0
        color = lerp_color(start, target_color, progress)
        lines = original_ss.split(";")
        new_lines = []
        for line in lines:
            if "border-color:" in line or ("border:" in line and "solid" in line):
                # Find the color part and replace it
                if "border-color:" in line:
                    prefix = line.split("border-color:")[0]
                    new_lines.append(f"{prefix}border-color: {color}")
                elif "solid" in line:
                    parts = line.split("solid")
                    prefix = parts[0] + "solid"
                    suffix = ""
                    for p in parts[1:]:
                        if "#" in p:
                            # Replace the hex color
                            for word in p.split():
                                if word.startswith("#"):
                                    suffix += f" {color}"
                                else:
                                    suffix += f" {word}"
                        else:
                            suffix += f" solid{p}"
                    new_lines.append(f"{prefix}{suffix}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        widget.setStyleSheet(";".join(new_lines))

    for i in range(1, frames + 1):
        t = i / frames
        QTimer.singleShot(i * step_ms, lambda p=t: step(int(p * 100)))


def fade_in(widget: QWidget, duration: int = 200):
    """Fade in a widget using QGraphicsOpacityEffect."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    widget._fade_anim = anim


def fade_out(widget: QWidget, duration: int = 200, on_finished=None):
    """Fade out a widget. Calls on_finished() when done."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start()
    widget._fade_anim = anim


def scale_button(widget: QWidget, from_scale: float, to_scale: float, duration: int = 150):
    """Scale a button by adjusting its geometry. 1.0 = normal size."""
    original_geo = widget.geometry()
    cx = original_geo.center().x()
    cy = original_geo.center().y()
    ow = original_geo.width()
    oh = original_geo.height()

    nw = int(ow * to_scale)
    nh = int(oh * to_scale)
    x = cx - nw // 2
    y = cy - nh // 2

    anim = QPropertyAnimation(widget, b"geometry")
    anim.setDuration(duration)
    anim.setStartValue(original_geo)
    from PySide6.QtCore import QRect
    anim.setEndValue(QRect(x, y, nw, nh))
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    widget._scale_anim = anim


def animate_scale(widget: QWidget, target_scale: float, duration: int = 150):
    """Animate widget to target scale relative to its current size."""
    geo = widget.geometry()
    cx = geo.center().x()
    cy = geo.center().y()
    ow = widget._original_width if hasattr(widget, '_original_width') else geo.width()
    oh = widget._original_height if hasattr(widget, '_original_height') else geo.height()

    if not hasattr(widget, '_original_width'):
        widget._original_width = geo.width()
        widget._original_height = geo.height()

    nw = int(ow * target_scale)
    nh = int(oh * target_scale)
    x = cx - nw // 2
    y = cy - nh // 2

    anim = QPropertyAnimation(widget, b"geometry")
    anim.setDuration(duration)
    anim.setStartValue(geo)
    from PySide6.QtCore import QRect
    anim.setEndValue(QRect(x, y, nw, nh))
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    widget._scale_anim = anim


def animate_dialog_in(dialog, duration: int = 180):
    """Animate a dialog fading in on show. Call from showEvent or after show()."""
    effect = QGraphicsOpacityEffect(dialog)
    dialog.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    dialog._dialog_anim = anim
