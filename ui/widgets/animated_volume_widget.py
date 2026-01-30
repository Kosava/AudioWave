# ui/widgets/animated_volume_widget.py - SA SCROLL WHEEL I FIXED MUTE BUTTON

"""
Animated Volume Widget - SA MOUSE WHEEL + VIDLJIV MUTE BUTTON
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QMouseEvent, QWheelEvent
from math import sin, pi


class AnimatedVolumeBar(QWidget):
    """Custom volume bar - SA SCROLL WHEEL"""
    
    value_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.volume = 70
        self.target_volume = 70
        self.animation_offset = 0
        self.setFixedHeight(8)
        self.setMinimumWidth(100)
        
        # Mouse tracking
        self.is_dragging = False
        self.setMouseTracking(True)
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(50)
    
    def animate(self):
        """Smooth animation"""
        if abs(self.volume - self.target_volume) > 0.5:
            diff = self.target_volume - self.volume
            self.volume += diff * 0.2
        else:
            self.volume = self.target_volume
        
        self.animation_offset = (self.animation_offset + 0.1) % (2 * pi)
        self.update()
    
    def set_volume(self, volume):
        """Postavi volume"""
        self.target_volume = max(0, min(100, volume))
        self.volume = self.target_volume
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.update_volume_from_position(event.pos())
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move"""
        if self.is_dragging:
            self.update_volume_from_position(event.pos())
        self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel"""
        delta = event.angleDelta().y()
        
        if delta > 0:
            new_volume = min(100, self.volume + 5)
        else:
            new_volume = max(0, self.volume - 5)
        
        self.set_volume(new_volume)
        self.value_changed.emit(int(new_volume))
        
        event.accept()
    
    def update_volume_from_position(self, pos: QPoint):
        """Update volume based on position"""
        width = self.width()
        x = max(0, min(width, pos.x()))
        
        new_volume = int((x / width) * 100)
        self.target_volume = new_volume
        self.volume = new_volume
        
        self.value_changed.emit(new_volume)
        self.update()
    
    def paintEvent(self, event):
        """Custom painting"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 15))
        painter.drawRoundedRect(0, 0, width, height, 4, 4)
        
        # Volume fill
        fill_width = int((self.volume / 100) * width)
        if fill_width > 0:
            gradient = QLinearGradient(0, 0, fill_width, 0)
            
            pulse = sin(self.animation_offset) * 0.15 + 0.85
            
            gradient.setColorAt(0, QColor(102, 126, 234, int(200 * pulse)))
            gradient.setColorAt(0.5, QColor(118, 75, 162, int(220 * pulse)))
            gradient.setColorAt(1, QColor(102, 126, 234, int(200 * pulse)))
            
            painter.setBrush(gradient)
            painter.drawRoundedRect(0, 0, fill_width, height, 4, 4)
        
        # Glow
        if self.volume > 0:
            glow_alpha = int((sin(self.animation_offset) * 0.2 + 0.6) * 100)
            painter.setPen(QPen(QColor(102, 126, 234, glow_alpha), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(0, 0, width - 1, height - 1, 4, 4)


class AnimatedVolumeWidget(QWidget):
    """Complete volume control"""
    
    volume_changed = pyqtSignal(int)
    mute_toggled = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.last_volume = 70
        self.is_muted = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI"""
        self.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Mute button
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(30, 30)
        self.mute_btn.setCheckable(True)
        self.mute_btn.clicked.connect(self.toggle_mute)
        self.mute_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_btn.setStyleSheet("""
            QPushButton {
                background: rgba(102, 126, 234, 0.12);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 15px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.2);
                border: 2px solid rgba(102, 126, 234, 0.5);
            }
            QPushButton:checked {
                background: rgba(234, 102, 102, 0.25);
                border: 2px solid rgba(234, 102, 102, 0.5);
            }
        """)
        
        # Volume bar
        self.volume_bar = AnimatedVolumeBar()
        self.volume_bar.setFixedWidth(120)
        self.volume_bar.value_changed.connect(self.on_volume_changed)
        
        # Volume label
        self.volume_label = QLabel("70")
        self.volume_label.setFixedWidth(28)
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_label.setStyleSheet("""
            color: white;
            font-size: 11px;
            font-weight: 600;
            background: rgba(102, 126, 234, 0.15);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 6px;
            padding: 4px 2px;
        """)
        
        layout.addWidget(self.mute_btn)
        layout.addWidget(self.volume_bar)
        layout.addWidget(self.volume_label)
    
    def on_volume_changed(self, value):
        """Handle volume change"""
        if self.is_muted and value > 0:
            self.is_muted = False
            self.mute_btn.setChecked(False)
            self.update_mute_icon()
        
        self.volume_label.setText(str(value))
        self.volume_changed.emit(value)
        
        if value > 0:
            self.last_volume = value
            self.update_mute_icon()
    
    def toggle_mute(self):
        """Toggle mute"""
        current = int(self.volume_bar.volume)
        
        if current > 0:
            self.last_volume = current
            self.volume_bar.set_volume(0)
            self.is_muted = True
            self.mute_btn.setText("🔇")
            self.volume_label.setText("0")
            self.volume_changed.emit(0)
        else:
            self.volume_bar.set_volume(self.last_volume)
            self.is_muted = False
            self.update_mute_icon()
            self.volume_label.setText(str(self.last_volume))
            self.volume_changed.emit(self.last_volume)
        
        self.mute_toggled.emit(self.is_muted)
    
    def update_mute_icon(self):
        """Update mute icon"""
        value = int(self.volume_bar.volume)
        
        if value == 0:
            self.mute_btn.setText("🔇")
        elif value < 33:
            self.mute_btn.setText("🔈")
        elif value < 66:
            self.mute_btn.setText("🔉")
        else:
            self.mute_btn.setText("🔊")
    
    def set_volume(self, value):
        """Set volume programmatically"""
        self.volume_bar.set_volume(value)
        self.volume_label.setText(str(value))
    
    def get_volume(self):
        """Get current volume"""
        return int(self.volume_bar.volume)