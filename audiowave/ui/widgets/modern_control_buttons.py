# ui/widgets/modern_control_buttons.py
"""
Modern Control Buttons sa animacijama i stilom
"""

from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QFont, QIcon, QPainterPath
from math import sin, pi

# Dodajemo import za SVGIconManager
from ui.utils.svg_icon_manager import get_icon


class ModernButton(QPushButton):
    """Base modern button sa hover i press animacijama"""
    
    def __init__(self, text="", icon_text="", primary=False):
        super().__init__()
        self.setText(text)
        self.icon_text = icon_text  # Ovo ćemo obrisati kasnije u potklasi
        self.is_primary = primary
        self.hover_progress = 0.0
        self.press_progress = 0.0
        
        # Setup
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Animations
        self.hover_anim = QPropertyAnimation(self, b"hover_progress")
        self.hover_anim.setDuration(150)
        self.hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.press_anim = QPropertyAnimation(self, b"press_progress")
        self.press_anim.setDuration(100)
        self.press_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(102, 126, 234, 100))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def get_hover_progress(self):
        return self._hover_progress
    
    def set_hover_progress(self, value):
        self._hover_progress = value
        self.update()
    
    hover_progress = property(get_hover_progress, set_hover_progress)
    _hover_progress = 0.0
    
    def get_press_progress(self):
        return self._press_progress
    
    def set_press_progress(self, value):
        self._press_progress = value
        self.update()
    
    press_progress = property(get_press_progress, set_press_progress)
    _press_progress = 0.0
    
    def enterEvent(self, event):
        """Hover enter"""
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.hover_progress)
        self.hover_anim.setEndValue(1.0)
        self.hover_anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Hover leave"""
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self.hover_progress)
        self.hover_anim.setEndValue(0.0)
        self.hover_anim.start()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Press"""
        self.press_anim.stop()
        self.press_anim.setStartValue(self.press_progress)
        self.press_anim.setEndValue(1.0)
        self.press_anim.start()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Release"""
        self.press_anim.stop()
        self.press_anim.setStartValue(self.press_progress)
        self.press_anim.setEndValue(0.0)
        self.press_anim.start()
        super().mouseReleaseEvent(event)


class GradientButton(ModernButton):
    """Button sa gradient background-om"""
    
    def paintEvent(self, event):
        """Custom paint"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Calculate scale based on press
        scale = 1.0 - (self.press_progress * 0.05)
        
        painter.save()
        painter.translate(width / 2, height / 2)
        painter.scale(scale, scale)
        painter.translate(-width / 2, -height / 2)
        
        # Background gradient
        gradient = QLinearGradient(0, 0, 0, height)
        
        if self.is_primary:
            # Primary button - vibrant gradient
            base_alpha = 200 + int(55 * self.hover_progress)
            gradient.setColorAt(0, QColor(102, 126, 234, base_alpha))
            gradient.setColorAt(1, QColor(118, 75, 162, base_alpha))
        else:
            # Secondary button - subtle
            base_alpha = int(50 + 30 * self.hover_progress)
            gradient.setColorAt(0, QColor(255, 255, 255, base_alpha))
            gradient.setColorAt(1, QColor(200, 200, 200, base_alpha))
        
        # Draw background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        
        radius = height / 2 if self.is_primary else 8
        painter.drawRoundedRect(0, 0, width, height, radius, radius)
        
        # Border
        if self.is_primary:
            border_alpha = int(100 + 100 * self.hover_progress)
            painter.setPen(QPen(QColor(255, 255, 255, border_alpha), 2))
        else:
            border_alpha = int(80 + 80 * self.hover_progress)
            painter.setPen(QPen(QColor(102, 126, 234, border_alpha), 1))
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(1, 1, width - 2, height - 2, radius, radius)
        
        # Ako dugme ima ikonu, ne crtamo tekst (ikona će se prikazati automatski)
        if not self.icon_text and self.text():
            # Draw text only if no icon_text (old way)
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 11, QFont.Weight.Bold if self.is_primary else QFont.Weight.Normal)
            painter.setFont(font)
            painter.drawText(0, 0, width, height, Qt.AlignmentFlag.AlignCenter, self.text())
        
        painter.restore()


class CircularButton(ModernButton):
    """Circular button sa pulse efektom"""
    
    def __init__(self, icon_text="", size=50):
        super().__init__(icon_text=icon_text, primary=True)
        self.setFixedSize(size, size)
        self.pulse_offset = 0.0
        
        # Pulse timer
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(50)
    
    def update_pulse(self):
        """Update pulse animation"""
        self.pulse_offset = (self.pulse_offset + 0.1) % (2 * pi)
        if self.hover_progress > 0:
            self.update()
    
    def paintEvent(self, event):
        """Custom paint"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        size = self.width()
        center = size / 2
        
        # Pulse effect when hovering
        pulse = 1.0
        if self.hover_progress > 0:
            pulse = 1.0 + (sin(self.pulse_offset) * 0.1 * self.hover_progress)
        
        # Press scale
        scale = 1.0 - (self.press_progress * 0.1)
        
        painter.save()
        painter.translate(center, center)
        painter.scale(scale * pulse, scale * pulse)
        painter.translate(-center, -center)
        
        # Outer glow when hovering
        if self.hover_progress > 0:
            glow_radius = center + (10 * self.hover_progress)
            glow_gradient = QLinearGradient(center, 0, center, size)
            glow_alpha = int(60 * self.hover_progress)
            glow_gradient.setColorAt(0, QColor(102, 126, 234, glow_alpha))
            glow_gradient.setColorAt(1, QColor(118, 75, 162, glow_alpha))
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_gradient)
            painter.drawEllipse(
                int(center - glow_radius),
                int(center - glow_radius),
                int(glow_radius * 2),
                int(glow_radius * 2)
            )
        
        # Main circle gradient
        gradient = QLinearGradient(center, 0, center, size)
        base_alpha = 220 + int(35 * self.hover_progress)
        gradient.setColorAt(0, QColor(102, 126, 234, base_alpha))
        gradient.setColorAt(1, QColor(118, 75, 162, base_alpha))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(0, 0, size, size)
        
        # Border
        border_alpha = int(150 + 105 * self.hover_progress)
        painter.setPen(QPen(QColor(255, 255, 255, border_alpha), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(2, 2, size - 4, size - 4)
        
        # Ikona će se prikazati automatski preko setIcon, ne crtamo tekst
        # self.icon_text se više ne koristi za osnovne kontrole
        
        painter.restore()


class GlassButton(ModernButton):
    """Glassmorphism button"""
    
    def paintEvent(self, event):
        """Custom paint with glass effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Scale on press
        scale = 1.0 - (self.press_progress * 0.03)
        
        painter.save()
        painter.translate(width / 2, height / 2)
        painter.scale(scale, scale)
        painter.translate(-width / 2, -height / 2)
        
        # Glass background
        base_alpha = int(40 + 20 * self.hover_progress)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, base_alpha))
        painter.drawRoundedRect(0, 0, width, height, 10, 10)
        
        # Top highlight (glass shine)
        highlight_gradient = QLinearGradient(0, 0, 0, height / 2)
        highlight_alpha = int(30 + 20 * self.hover_progress)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, highlight_alpha))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(highlight_gradient)
        
        # Create rounded path for top half
        path = QPainterPath()
        path.addRoundedRect(0, 0, width, height / 2, 10, 10)
        painter.setClipPath(path)
        painter.drawRect(0, 0, width, height / 2)
        painter.setClipping(False)
        
        # Border with blur effect
        border_color = QColor(102, 126, 234, int(100 + 100 * self.hover_progress))
        painter.setPen(QPen(border_color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, width, height, 10, 10)
        
        # Ikona će se prikazati automatski preko setIcon
        # self.icon_text se više ne koristi za osnovne kontrole
        
        painter.restore()


class ControlButtonPanel(QWidget):
    """Panel sa svim control buttonima"""
    
    # Signals
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    
    def __init__(self, style="gradient"):
        super().__init__()
        self.style = style  # "gradient", "circular", "glass"
        self.is_playing = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup button panel"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Create buttons based on style
        if self.style == "circular":
            # Prethodno dugme
            self.btn_prev = CircularButton("", 40)
            self.btn_prev.setIcon(get_icon("prev", size=20))
            self.btn_prev.setIconSize(QSize(20, 20))
            
            # Play dugme
            self.btn_play = CircularButton("", 55)
            self.btn_play.setIcon(get_icon("play", size=24))
            self.btn_play.setIconSize(QSize(24, 24))
            
            # Sledeće dugme
            self.btn_next = CircularButton("", 40)
            self.btn_next.setIcon(get_icon("next", size=20))
            self.btn_next.setIconSize(QSize(20, 20))
            
            # Stop dugme
            self.btn_stop = CircularButton("", 40)
            self.btn_stop.setIcon(get_icon("stop", size=20))
            self.btn_stop.setIconSize(QSize(20, 20))
            
        elif self.style == "glass":
            # Prethodno dugme
            self.btn_prev = GlassButton()
            self.btn_prev.setFixedSize(40, 40)
            self.btn_prev.setIcon(get_icon("prev", size=20))
            self.btn_prev.setIconSize(QSize(20, 20))
            
            # Play dugme
            self.btn_play = GlassButton()
            self.btn_play.setFixedSize(55, 55)
            self.btn_play.setIcon(get_icon("play", size=24))
            self.btn_play.setIconSize(QSize(24, 24))
            
            # Sledeće dugme
            self.btn_next = GlassButton()
            self.btn_next.setFixedSize(40, 40)
            self.btn_next.setIcon(get_icon("next", size=20))
            self.btn_next.setIconSize(QSize(20, 20))
            
            # Stop dugme
            self.btn_stop = GlassButton()
            self.btn_stop.setFixedSize(40, 40)
            self.btn_stop.setIcon(get_icon("stop", size=20))
            self.btn_stop.setIconSize(QSize(20, 20))
            
        else:  # gradient (default)
            # Prethodno dugme
            self.btn_prev = GradientButton()
            self.btn_prev.setFixedSize(40, 40)
            self.btn_prev.setIcon(get_icon("prev", size=20))
            self.btn_prev.setIconSize(QSize(20, 20))
            
            # Play dugme
            self.btn_play = GradientButton(primary=True)
            self.btn_play.setFixedSize(55, 55)
            self.btn_play.setIcon(get_icon("play", size=24))
            self.btn_play.setIconSize(QSize(24, 24))
            
            # Sledeće dugme
            self.btn_next = GradientButton()
            self.btn_next.setFixedSize(40, 40)
            self.btn_next.setIcon(get_icon("next", size=20))
            self.btn_next.setIconSize(QSize(20, 20))
            
            # Stop dugme
            self.btn_stop = GradientButton()
            self.btn_stop.setFixedSize(40, 40)
            self.btn_stop.setIcon(get_icon("stop", size=20))
            self.btn_stop.setIconSize(QSize(20, 20))
        
        # Connect signals
        self.btn_prev.clicked.connect(self.prev_clicked.emit)
        self.btn_play.clicked.connect(self.on_play_clicked)
        self.btn_next.clicked.connect(self.next_clicked.emit)
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        
        # Layout
        layout.addStretch()
        layout.addWidget(self.btn_prev)
        layout.addWidget(self.btn_play)
        layout.addWidget(self.btn_next)
        layout.addWidget(self.btn_stop)
        layout.addStretch()
    
    def on_play_clicked(self):
        """Toggle play/pause"""
        if self.is_playing:
            self.pause_clicked.emit()
            self.set_playing(False)
        else:
            self.play_clicked.emit()
            self.set_playing(True)
    
    def on_stop_clicked(self):
        """Stop playback"""
        self.stop_clicked.emit()
        self.set_playing(False)
    
    def set_playing(self, playing):
        """Update play button state"""
        self.is_playing = playing
        # Koristimo SVG ikone umesto icon_text
        icon_name = "pause" if playing else "play"
        self.btn_play.setIcon(get_icon(icon_name, size=24))
        self.btn_play.setIconSize(QSize(24, 24))
        self.btn_play.update()
    
    def set_paused(self):
        """Set to paused state"""
        self.is_playing = False
        self.btn_play.setIcon(get_icon("play", size=24))
        self.btn_play.setIconSize(QSize(24, 24))
        self.btn_play.update()


# Example usage
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
    import sys
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Modern Buttons Demo")
    window.setStyleSheet("background: #1a1a2e;")
    
    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setSpacing(30)
    
    # Gradient style
    gradient_panel = ControlButtonPanel("gradient")
    gradient_panel.play_clicked.connect(lambda: print("Play!"))
    layout.addWidget(gradient_panel)
    
    # Circular style
    circular_panel = ControlButtonPanel("circular")
    layout.addWidget(circular_panel)
    
    # Glass style
    glass_panel = ControlButtonPanel("glass")
    layout.addWidget(glass_panel)
    
    window.setCentralWidget(central)
    window.resize(600, 400)
    window.show()
    
    sys.exit(app.exec())