"""
ui_hud_overlay.py — Glassmorphic Floating Desktop HUD Overlay for JARVIS Mark 58
Lightweight, frameless, semi-transparent PyQt window showing live system telemetry,
GPU status, active AI state, and Iron Man Arc-Reactor visualizer.
Supports both PyQt6 (primary) and PyQt5 (fallback) dynamically.
"""

import sys
import time
import math
import psutil

try:
    from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
    _IS_PYQT6 = True
except ImportError:
    from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
    from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
    _IS_PYQT6 = False


class FloatingHUDOverlay(QWidget):
    """Floating Glassmorphic Desktop HUD Widget for MARK 58."""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.drag_position = QPoint()

        # Telemetry timer (3s interval to save power & CPU load)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(3000)

        # Pulse animation angle (150ms interval for low-power rendering)
        self.pulse_angle = 0
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(150)

        self.cpu_pct = 0
        self.ram_pct = 0
        self.ai_state = "ONLINE"

    def init_ui(self):
        if _IS_PYQT6:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(320, 140)

        # Move to top-right corner of screen by default
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 340, 50)

        # Main Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)

        # Header Label
        self.title_label = QLabel("J.A.R.V.I.S. MARK 58 // APEX TELEMETRY")
        self.title_label.setStyleSheet("color: #00d4ff; font-family: 'Segoe UI', Arial; font-weight: bold; font-size: 10px; letter-spacing: 1px;")

        # Status Label
        self.status_label = QLabel("CPU: 0%  |  RAM: 0%  |  GPU: ACTIVE")
        self.status_label.setStyleSheet("color: #e0f7fc; font-family: 'Consolas', monospace; font-size: 11px;")

        # AI Mode Tag
        self.mode_label = QLabel("MARK 58 SUIT: ONLINE [APEX CORE]")
        self.mode_label.setStyleSheet("color: #00ff88; font-family: 'Segoe UI', Arial; font-weight: bold; font-size: 10px;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.mode_label)
        layout.addStretch()

        self.setLayout(layout)

    def update_telemetry(self):
        self.cpu_pct = psutil.cpu_percent()
        self.ram_pct = psutil.virtual_memory().percent
        self.status_label.setText(f"CPU: {self.cpu_pct}%  |  RAM: {self.ram_pct}%  |  GPU: ACTIVE")

    def update_pulse(self):
        self.pulse_angle = (self.pulse_angle + 5) % 360
        self.update()

    def set_ai_state(self, state: str):
        self.ai_state = state.upper()
        if state.upper() == "SPEAKING":
            color = "#00ff88"
        elif state.upper() == "THINKING":
            color = "#ffaa00"
        elif state.upper() == "LISTENING":
            color = "#00d4ff"
        else:
            color = "#ffffff"
        self.mode_label.setStyleSheet(f"color: {color}; font-family: 'Segoe UI', Arial; font-weight: bold; font-size: 10px;")
        self.mode_label.setText(f"SYSTEM STATE: {self.ai_state}")

    def paintEvent(self, event):
        painter = QPainter(self)
        if _IS_PYQT6:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        else:
            painter.setRenderHint(QPainter.Antialiasing)

        # Glassmorphic Background Panel
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(1, 1, rect.width() - 2, rect.height() - 2, 12, 12)

        # Dark Glass Fill
        painter.fillPath(path, QBrush(QColor(10, 20, 35, 200)))

        # Cyan Neon Border
        pen = QPen(QColor(0, 212, 255, 180), 1.5)
        painter.setPen(pen)
        painter.drawPath(path)

        # Iron Man Arc-Reactor Pulse Ring (Bottom Right)
        arc_x = rect.width() - 35
        arc_y = rect.height() - 35
        radius = 16

        # Outer ring
        painter.setPen(QPen(QColor(0, 212, 255, 120), 2))
        painter.drawEllipse(QPoint(arc_x, arc_y), radius, radius)

        # Pulsing Inner Core
        pulse_val = (math.sin(math.radians(self.pulse_angle)) + 1) / 2.0
        core_r = int(4 + pulse_val * 6)
        if _IS_PYQT6:
            painter.setPen(Qt.PenStyle.NoPen)
        else:
            painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 255, 200, int(150 + pulse_val * 105))))
        painter.drawEllipse(QPoint(arc_x, arc_y), core_r, core_r)

    # Allow dragging floating widget across screen
    def mousePressEvent(self, event):
        btn = event.button()
        left = Qt.MouseButton.LeftButton if _IS_PYQT6 else Qt.LeftButton
        if btn == left:
            pos = event.globalPosition().toPoint() if _IS_PYQT6 else event.globalPos()
            self.drag_position = pos - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        btns = event.buttons()
        left = Qt.MouseButton.LeftButton if _IS_PYQT6 else Qt.LeftButton
        if (btns & left) and not self.drag_position.isNull():
            pos = event.globalPosition().toPoint() if _IS_PYQT6 else event.globalPos()
            self.move(pos - self.drag_position)
            event.accept()


hud_widget_instance = None


def launch_hud_overlay():
    global hud_widget_instance
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    if not hud_widget_instance:
        hud_widget_instance = FloatingHUDOverlay()
        hud_widget_instance.show()
    return hud_widget_instance
