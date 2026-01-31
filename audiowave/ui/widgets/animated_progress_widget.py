# ui/widgets/animated_progress_widget.py
# NAJMANJI MOGUĆ­I TOOLTIP – bez viška, dinamički, smooth

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QRadialGradient
from math import sin, pi


class AnimatedProgressBar(QWidget):
    """Progress bar sa najkompaktnijim tooltip-om ikad"""

    seek_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        self.setMinimumWidth(200)

        self.position = 0
        self.duration = 1
        self.is_seeking = False
        self.hover_position = -1

        self.animation_offset = 0
        self.pulse_intensity = 0.0

        # Tooltip – ultra-kompaktan
        self.tooltip_label = QLabel(self)
        self.tooltip_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6a4aff, stop:1 #8a6cff);
            color: #ffffff;
            border: 1px solid #9a7eff;
            border-radius: 6px;
            padding: 2px 4px;          /* minimalan padding - brojevi blizu ivica ali ne zalepljeni */
            font-size: 11px;
            font-weight: 600;
            text-align: center;
        """)
        self.tooltip_label.hide()
        self.tooltip_label.raise_()

        # Animacije – glađe nego ikad
        self.tooltip_move_anim = QPropertyAnimation(self.tooltip_label, b"pos")
        self.tooltip_move_anim.setDuration(240)
        self.tooltip_move_anim.setEasingCurve(QEasingCurve.Type.OutExpo)

        self.tooltip_fade_anim = QPropertyAnimation(self.tooltip_label, b"windowOpacity")
        self.tooltip_fade_anim.setDuration(300)
        self.tooltip_fade_anim.setEasingCurve(QEasingCurve.Type.InOutSine)

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(12)

        self.setMouseTracking(True)

    def update_animation(self):
        self.animation_offset = (self.animation_offset + 0.10) % (2 * pi)
        self.pulse_intensity = (sin(self.animation_offset) + 1) / 2
        self.update()

    def set_position(self, position_ms):
        if not self.is_seeking:
            self.position = position_ms
            self.update()

    def set_duration(self, duration_ms):
        self.duration = max(1, duration_ms)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_seeking = True
            self.seek_to_position(event.pos().x())

    def mouseMoveEvent(self, event):
        self.hover_position = event.pos().x()
        if self.is_seeking:
            self.seek_to_position(event.pos().x())

        if self.duration > 0:
            percentage = self.hover_position / self.width()
            hover_ms = int(percentage * self.duration)

            total_seconds = hover_ms // 1000
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            if hours > 0:
                time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                time_str = f"{minutes}:{seconds:02d}"

            self.tooltip_label.setText(time_str)
            self.tooltip_label.adjustSize()  # sam se prilagođ­ava tekstu

            target_x = event.pos().x() - self.tooltip_label.width() // 2
            target_y = event.pos().y() - self.tooltip_label.height() - 35

            target_x = max(10, min(target_x, self.width() - self.tooltip_label.width() - 10))
            target_y = max(10, target_y)

            if self.tooltip_label.isVisible():
                self.tooltip_move_anim.setStartValue(self.tooltip_label.pos())
                self.tooltip_move_anim.setEndValue(QPoint(target_x, target_y))
                self.tooltip_move_anim.start()
            else:
                self.tooltip_label.move(target_x, target_y)

            if not self.tooltip_label.isVisible():
                self.tooltip_label.setWindowOpacity(0.0)
                self.tooltip_label.show()
                self.tooltip_fade_anim.setStartValue(0.0)
                self.tooltip_fade_anim.setEndValue(1.0)
                self.tooltip_fade_anim.start()

        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_seeking = False
            self.seek_to_position(event.pos().x())
            self.tooltip_fade_anim.setStartValue(1.0)
            self.tooltip_fade_anim.setEndValue(0.0)
            self.tooltip_fade_anim.start()
            QTimer.singleShot(300, self.tooltip_label.hide)

    def leaveEvent(self, event):
        self.hover_position = -1
        self.tooltip_fade_anim.setStartValue(1.0)
        self.tooltip_fade_anim.setEndValue(0.0)
        self.tooltip_fade_anim.start()
        QTimer.singleShot(300, self.tooltip_label.hide)
        self.update()

    def seek_to_position(self, x):
        width = self.width()
        percentage = max(0, min(1, x / width))
        new_position = int(percentage * self.duration)
        self.position = new_position
        self.seek_requested.emit(new_position)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        padding_left = 12
        padding_right = 12
        track_width = width - padding_left - padding_right

        bar_height = 8
        bar_y = height - bar_height - 5

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawRoundedRect(padding_left, bar_y, track_width, bar_height, 4, 4)

        if self.duration > 0:
            progress_ratio = self.position / self.duration
            progress_width = int(progress_ratio * track_width)
            gradient = QLinearGradient(padding_left, bar_y, padding_left + track_width, bar_y + bar_height)
            gradient.setColorAt(0, QColor(102, 126, 234))
            gradient.setColorAt(1, QColor(118, 75, 162))
            painter.setBrush(gradient)
            painter.drawRoundedRect(padding_left, bar_y, progress_width, bar_height, 4, 4)

        if self.hover_position >= 0:
            hover_x = max(padding_left, min(padding_left + track_width, self.hover_position))
            painter.setPen(QPen(QColor(200, 220, 255, 100), 2))
            painter.drawLine(hover_x, bar_y - 6, hover_x, bar_y + bar_height + 6)

        handle_x = padding_left + int((self.position / self.duration) * track_width) if self.duration > 0 else padding_left
        handle_y = bar_y + bar_height // 2

        glow_gradient = QRadialGradient(handle_x, handle_y, 15)
        glow_gradient.setColorAt(0, QColor(102, 126, 234, int(180 * self.pulse_intensity)))
        glow_gradient.setColorAt(1, QColor(102, 126, 234, 0))
        painter.setBrush(glow_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(handle_x - 15, handle_y - 15, 30, 30)

        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(handle_x - 8, handle_y - 8, 16, 16)

        inner_gradient = QLinearGradient(handle_x - 6, handle_y - 6, handle_x + 6, handle_y + 6)
        inner_gradient.setColorAt(0, QColor(102, 126, 234))
        inner_gradient.setColorAt(1, QColor(118, 75, 162))
        painter.setBrush(inner_gradient)
        painter.drawEllipse(handle_x - 6, handle_y - 6, 12, 12)


class AnimatedProgressWidget(QWidget):
    seek_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(6)

        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.seek_requested.connect(self.seek_requested.emit)

        time_layout = QHBoxLayout()
        time_layout.setSpacing(0)

        self.time_current = QLabel("0:00")
        self.time_current.setObjectName("time_current")

        self.time_total = QLabel("0:00")
        self.time_total.setObjectName("time_total")

        time_layout.addWidget(self.time_current)
        time_layout.addStretch()
        time_layout.addWidget(self.time_total)

        layout.addWidget(self.progress_bar)
        layout.addLayout(time_layout)

    def on_position_changed(self, position_ms):
        self.progress_bar.set_position(position_ms)
        seconds = position_ms // 1000
        minutes = seconds // 60
        seconds %= 60
        self.time_current.setText(f"{minutes}:{seconds:02d}")

    def on_duration_changed(self, duration_ms):
        self.progress_bar.set_duration(duration_ms)
        seconds = duration_ms // 1000
        minutes = seconds // 60
        seconds %= 60
        self.time_total.setText(f"{minutes}:{seconds:02d}")