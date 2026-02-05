# -*- coding: utf-8 -*-
# plugins/visualizer/visualizer_plugin.py
"""
Visualizer Plugin - NAPREDNI audio visualizer sa multiple stilovima

Podržava:
- Spectrum Analyzer (vertikalni stubići)
- Waveform (AudioWave signature talasi)
- Circular Spectrum (kružni prikaz)
- Particles (čestice sa basom)

Features:
- GStreamer spectrum element za FFT analizu
- Theme-aware boje sa glow efektima
- 60 FPS smooth animacije
- Fullscreen mode
- Customizable stilovi
"""

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient, QPainterPath, QFont
import math
import random
import time


class VisualizerWidget(QWidget):
    """
    Main visualizer widget - crta audio vizualizacije
    
    Vizualizacije:
    - spectrum: Vertikalni stubići (Winamp style)
    - waveform: Talasna forma (AudioWave signature!)
    - circular: Kružni spektar
    - particles: Čestice koje eksplodiraju
    """
    
    def __init__(self, engine=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        
        # Audio data
        self.spectrum_data = [0.0] * 64  # 64 frequency bands
        self.waveform_data = []
        
        # Visualization settings
        self.viz_style = "waveform"  # Default: AudioWave signature!
        self.show_glow = True
        self.show_peaks = True
        self.sensitivity = 1.5
        
        # Theme colors (će se postaviti kroz apply_theme)
        self.primary_color = QColor("#667eea")
        self.secondary_color = QColor("#764ba2")
        self.glow_color = QColor("#667eea")
        
        # Particles system
        self.particles = []
        
        # Peak holders za spectrum
        self.peak_values = [0.0] * 64
        self.peak_decay = 0.95
        
        # Animation timer - 60 FPS
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualization)
        self.fps = 60
        self.timer.setInterval(1000 // self.fps)
        
        # Setup
        self.setMinimumSize(600, 300)
        self.setStyleSheet("background-color: #0a0a0f;")
        
        print("🎨 VisualizerWidget initialized")
    
    def start(self):
        """Pokreni vizualizaciju"""
        if self.engine:
            self._setup_gstreamer_spectrum()
        self.timer.start()
        print("▶️ Visualizer started")
    
    def stop(self):
        """Zaustavi vizualizaciju"""
        self.timer.stop()
        print("⏸️ Visualizer stopped")
    
    def _setup_gstreamer_spectrum(self):
        """Setup GStreamer spectrum element za FFT analizu"""
        try:
            # GStreamer spectrum element će slati spektralne podatke
            if hasattr(self.engine, 'setup_spectrum_analyzer'):
                self.engine.setup_spectrum_analyzer(
                    bands=64,
                    threshold=-80,
                    interval=int(1000000000 / self.fps)  # nanoseconds
                )
                print("✅ GStreamer spectrum analyzer configured")
        except Exception as e:
            print(f"⚠️ Could not setup spectrum: {e}")
    
    def update_visualization(self):
        """Update vizualizacije - poziva se 60x u sekundi"""
        # Dobij nove audio podatke
        self._fetch_audio_data()
        
        # Update particles
        if self.viz_style == "particles":
            self._update_particles()
        
        # Repaint
        self.update()
    
    def _fetch_audio_data(self):
        """Dobij audio podatke iz engine-a"""
        if self.engine and hasattr(self.engine, 'get_spectrum_data'):
            try:
                data = self.engine.get_spectrum_data()
                if data:
                    self.spectrum_data = data[:64]  # Ensure 64 bands
                    
                    # Generiši particles na jakom basu
                    if self.viz_style == "particles" and len(data) > 0:
                        bass_energy = sum(data[:8]) / 8  # Prvi 8 banda = bas
                        if bass_energy > 0.7:
                            self._spawn_particles(int(bass_energy * 20))
            except:
                pass
        else:
            # Fallback: simuliraj podatke za testiranje
            self._simulate_audio_data()
    
    def _simulate_audio_data(self):
        """Simuliraj audio podatke za testiranje (bez pravog audio-a)"""
        import time
        t = time.time() * 2
        
        for i in range(64):
            # Simuliraj različite frekvencije
            freq_factor = (i / 64) * 4
            value = abs(math.sin(t + freq_factor)) * random.uniform(0.7, 1.0)
            
            # Primeni sensitivity
            value *= self.sensitivity
            value = min(value, 1.0)
            
            self.spectrum_data[i] = value
            
            # Update peaks
            if value > self.peak_values[i]:
                self.peak_values[i] = value
            else:
                self.peak_values[i] *= self.peak_decay
    
    def paintEvent(self, event):
        """Crtaj vizualizaciju"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Pozadina
        painter.fillRect(self.rect(), QColor("#0a0a0f"))
        
        # Crtaj odabrani stil
        if self.viz_style == "spectrum":
            self._draw_spectrum(painter)
        elif self.viz_style == "waveform":
            self._draw_waveform(painter)
        elif self.viz_style == "circular":
            self._draw_circular(painter)
        elif self.viz_style == "particles":
            self._draw_particles(painter)
        elif self.viz_style == "bars_mirror":
            self._draw_bars_mirror(painter)
        elif self.viz_style == "frequency_rings":
            self._draw_frequency_rings(painter)
        elif self.viz_style == "oscilloscope":
            self._draw_oscilloscope(painter)
        elif self.viz_style == "fireworks":
            self._draw_fireworks(painter)
        elif self.viz_style == "matrix":
            self._draw_matrix(painter)
        elif self.viz_style == "plasma":
            self._draw_plasma(painter)
    
    def _draw_spectrum(self, painter):
        """Crtaj SPECTRUM ANALYZER - vertikalni stubići sa glow efektom"""
        width = self.width()
        height = self.height()
        
        num_bars = len(self.spectrum_data)
        bar_width = width / num_bars
        
        for i, value in enumerate(self.spectrum_data):
            # Pozicija
            x = i * bar_width
            bar_height = value * height * 0.8
            y = height - bar_height
            
            # Gradient boja - od primary do secondary
            gradient = QLinearGradient(x, height, x, y)
            
            # Dinamička boja bazirana na frekvenciji
            if i < 16:  # Bass - crvenkasto
                color1 = QColor("#ff0080")
                color2 = QColor("#ff4040")
            elif i < 32:  # Mid - primarno
                color1 = self.primary_color
                color2 = self.secondary_color
            else:  # High - plavo
                color1 = QColor("#00d4ff")
                color2 = QColor("#0080ff")
            
            gradient.setColorAt(0, color1)
            gradient.setColorAt(1, color2)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Crtaj stub
            painter.drawRect(int(x + 1), int(y), int(bar_width - 2), int(bar_height))
            
            # Glow efekat
            if self.show_glow and value > 0.3:
                glow_color = QColor(color2)
                glow_color.setAlpha(int(value * 100))
                painter.setBrush(QBrush(glow_color))
                glow_rect = QRectF(x, y - 5, bar_width, bar_height + 10)
                painter.drawRect(glow_rect)
            
            # Peak indicator
            if self.show_peaks:
                peak_y = height - (self.peak_values[i] * height * 0.8)
                painter.setPen(QPen(QColor("#ffffff"), 2))
                painter.drawLine(int(x), int(peak_y), int(x + bar_width), int(peak_y))
    
    def _draw_waveform(self, painter):
        """
        Crtaj WAVEFORM - AudioWave signature vizualizacija!
        
        Talasna forma koja teče kroz ekran sa elegantnim gradient bojama
        """
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Kreiraj smooth path kroz spektralne podatke
        path = QPainterPath()
        
        num_points = len(self.spectrum_data)
        if num_points == 0:
            return
        
        # Početna tačka
        first_value = self.spectrum_data[0] * height * 0.4 * self.sensitivity
        path.moveTo(0, center_y - first_value)
        
        # Kreiraj smooth krivu kroz sve tačke
        for i in range(1, num_points):
            x = (i / num_points) * width
            value = self.spectrum_data[i] * height * 0.4 * self.sensitivity
            
            # Upper wave
            y_upper = center_y - value
            
            # Smooth curve sa Bezier
            if i > 0:
                prev_x = ((i - 1) / num_points) * width
                control_x = (prev_x + x) / 2
                path.quadTo(control_x, y_upper, x, y_upper)
            else:
                path.lineTo(x, y_upper)
        
        # Mirror path za donji talas
        mirror_path = QPainterPath()
        mirror_path.moveTo(0, center_y + first_value)
        
        for i in range(1, num_points):
            x = (i / num_points) * width
            value = self.spectrum_data[i] * height * 0.4 * self.sensitivity
            y_lower = center_y + value
            
            if i > 0:
                prev_x = ((i - 1) / num_points) * width
                control_x = (prev_x + x) / 2
                mirror_path.quadTo(control_x, y_lower, x, y_lower)
            else:
                mirror_path.lineTo(x, y_lower)
        
        # Gradient fill između talasa
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0.0, QColor(self.primary_color.red(), self.primary_color.green(), self.primary_color.blue(), 100))
        gradient.setColorAt(0.5, QColor(self.secondary_color.red(), self.secondary_color.green(), self.secondary_color.blue(), 150))
        gradient.setColorAt(1.0, QColor(self.primary_color.red(), self.primary_color.green(), self.primary_color.blue(), 100))
        
        # Fill area između gornjeg i donjeg talasa
        fill_path = QPainterPath(path)
        
        # Dodaj mirror path u reverse
        for i in range(num_points - 1, -1, -1):
            x = (i / num_points) * width
            value = self.spectrum_data[i] * height * 0.4 * self.sensitivity
            y_lower = center_y + value
            fill_path.lineTo(x, y_lower)
        
        fill_path.closeSubpath()
        
        painter.fillPath(fill_path, QBrush(gradient))
        
        # Crtaj outline - gornji talas
        painter.setPen(QPen(self.primary_color, 3))
        painter.drawPath(path)
        
        # Crtaj outline - donji talas
        painter.setPen(QPen(self.secondary_color, 3))
        painter.drawPath(mirror_path)
        
        # Glow efekat
        if self.show_glow:
            glow_color = QColor(self.glow_color)
            glow_color.setAlpha(80)
            painter.setPen(QPen(glow_color, 6))
            painter.drawPath(path)
            painter.drawPath(mirror_path)
        
        # Center line
        painter.setPen(QPen(QColor("#ffffff"), 1, Qt.PenStyle.DashLine))
        painter.setOpacity(0.3)
        painter.drawLine(0, int(center_y), width, int(center_y))
    
    def _draw_circular(self, painter):
        """Crtaj CIRCULAR SPECTRUM - kružni prikaz spektra"""
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        
        radius_inner = min(width, height) * 0.2
        radius_outer = min(width, height) * 0.45
        
        num_bars = len(self.spectrum_data)
        angle_step = 360.0 / num_bars
        
        for i, value in enumerate(self.spectrum_data):
            angle = i * angle_step
            angle_rad = math.radians(angle)
            
            # Bar length baziran na audio amplitudi
            bar_length = value * (radius_outer - radius_inner) * self.sensitivity
            
            # Inner i outer pozicije
            inner_x = center_x + radius_inner * math.cos(angle_rad)
            inner_y = center_y + radius_inner * math.sin(angle_rad)
            
            outer_x = center_x + (radius_inner + bar_length) * math.cos(angle_rad)
            outer_y = center_y + (radius_inner + bar_length) * math.sin(angle_rad)
            
            # Gradient boja po frekvenciji
            if i < num_bars // 3:
                color = QColor("#ff0080")  # Bass - pink
            elif i < 2 * num_bars // 3:
                color = self.primary_color  # Mid - primary
            else:
                color = QColor("#00d4ff")  # High - cyan
            
            # Crtaj liniju
            pen = QPen(color, 3)
            painter.setPen(pen)
            painter.drawLine(int(inner_x), int(inner_y), int(outer_x), int(outer_y))
            
            # Glow
            if self.show_glow and value > 0.4:
                glow_color = QColor(color)
                glow_color.setAlpha(int(value * 150))
                painter.setPen(QPen(glow_color, 6))
                painter.drawLine(int(inner_x), int(inner_y), int(outer_x), int(outer_y))
        
        # Inner circle
        painter.setPen(QPen(self.primary_color, 2))
        painter.setBrush(QBrush(QColor("#0a0a0f")))
        painter.drawEllipse(
            int(center_x - radius_inner), 
            int(center_y - radius_inner),
            int(radius_inner * 2), 
            int(radius_inner * 2)
        )
    
    def _spawn_particles(self, count):
        """Kreiraj nove čestice"""
        width = self.width()
        height = self.height()
        
        for _ in range(count):
            particle = {
                'x': random.uniform(0, width),
                'y': height,
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-15, -5),
                'life': 1.0,
                'size': random.uniform(2, 6),
                'color': random.choice([
                    self.primary_color,
                    self.secondary_color,
                    QColor("#ff0080"),
                    QColor("#00d4ff")
                ])
            }
            self.particles.append(particle)
    
    def _update_particles(self):
        """Update particle sistem"""
        gravity = 0.5
        
        for particle in self.particles[:]:
            # Physics
            particle['vy'] += gravity
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 0.02
            
            # Remove dead particles
            if particle['life'] <= 0 or particle['y'] > self.height():
                self.particles.remove(particle)
    
    def _draw_particles(self, painter):
        """Crtaj PARTICLES - čestice koje eksplodiraju"""
        # Prvo nacrtaj spectrum kao pozadinu
        painter.setOpacity(0.3)
        self._draw_spectrum(painter)
        painter.setOpacity(1.0)
        
        # Crtaj particles
        for particle in self.particles:
            color = QColor(particle['color'])
            color.setAlpha(int(particle['life'] * 255))
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            size = particle['size'] * particle['life']
            painter.drawEllipse(
                QPointF(particle['x'], particle['y']),
                size, size
            )
            
            # Glow
            if self.show_glow:
                glow_color = QColor(color)
                glow_color.setAlpha(int(particle['life'] * 100))
                painter.setBrush(QBrush(glow_color))
                painter.drawEllipse(
                    QPointF(particle['x'], particle['y']),
                    size * 2, size * 2
                )
    
    def _draw_bars_mirror(self, painter):
        """
        BARS MIRROR - Vertikalni stubići sa mirror efektom (gore i dole)
        Najjači bas udara i gore i dole!
        """
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        num_bars = len(self.spectrum_data)
        bar_width = width / num_bars
        
        for i, value in enumerate(self.spectrum_data):
            x = i * bar_width
            bar_height = value * (height / 2) * 0.9 * self.sensitivity
            
            # Boje - bas je najjači!
            if i < 16:
                color = QColor("#ff0080")  # Bas - pink
            elif i < 32:
                color = self.primary_color
            else:
                color = QColor("#00d4ff")  # High - cyan
            
            # Gornji stub
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(int(x + 1), int(center_y - bar_height), int(bar_width - 2), int(bar_height))
            
            # Donji stub (mirror)
            painter.drawRect(int(x + 1), int(center_y), int(bar_width - 2), int(bar_height))
            
            # Glow efekat
            if self.show_glow and value > 0.4:
                glow_color = QColor(color)
                glow_color.setAlpha(int(value * 120))
                painter.setBrush(QBrush(glow_color))
                # Gornji glow
                painter.drawRect(int(x), int(center_y - bar_height - 3), int(bar_width), int(bar_height + 6))
                # Donji glow
                painter.drawRect(int(x), int(center_y - 3), int(bar_width), int(bar_height + 6))
    
    def _draw_frequency_rings(self, painter):
        """
        FREQUENCY RINGS - Koncentrični prstenovi koji pulsiraju
        Svaka frekvencija = jedan prsten!
        """
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        
        max_radius = min(width, height) * 0.45
        num_rings = min(len(self.spectrum_data), 20)  # Max 20 prstenova
        
        for i in range(num_rings):
            value = self.spectrum_data[i * (len(self.spectrum_data) // num_rings)]
            
            # Radijus prstena baziran na audio amplitudi
            base_radius = (i + 1) * (max_radius / num_rings)
            pulse_amount = value * 20 * self.sensitivity
            radius = base_radius + pulse_amount
            
            # Boje - rainbow spektar
            hue = (i * 360 / num_rings) % 360
            color = QColor.fromHsv(int(hue), 255, 255)
            color.setAlpha(int(100 + value * 155))
            
            # Crtaj prsten (samo outline)
            pen = QPen(color, 2 + int(value * 3))
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                QPointF(center_x, center_y),
                radius, radius
            )
            
            # Glow na jakim frekvencijama
            if self.show_glow and value > 0.5:
                glow_color = QColor(color)
                glow_color.setAlpha(int(value * 80))
                painter.setPen(QPen(glow_color, 6))
                painter.drawEllipse(
                    QPointF(center_x, center_y),
                    radius, radius
                )
    
    def _draw_oscilloscope(self, painter):
        """
        OSCILLOSCOPE - Retro osciloskop prikaz
        Kao na starim TV-ima!
        """
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Grid lines (kao na osciloskopu)
        painter.setPen(QPen(QColor("#1a4d2e"), 1, Qt.PenStyle.DotLine))
        painter.setOpacity(0.3)
        
        # Horizontalne grid linije
        for i in range(5):
            y = (i + 1) * height / 6
            painter.drawLine(0, int(y), width, int(y))
        
        # Vertikalne grid linije
        for i in range(8):
            x = (i + 1) * width / 9
            painter.drawLine(int(x), 0, int(x), height)
        
        painter.setOpacity(1.0)
        
        # Osciloskop trace - smooth kriva
        path = QPainterPath()
        num_points = len(self.spectrum_data)
        
        # Početna tačka
        first_value = self.spectrum_data[0] * height * 0.4 * self.sensitivity
        path.moveTo(0, center_y + first_value * math.sin(time.time() * 2))
        
        # Kreiraj osciloskop signal
        for i in range(1, num_points):
            x = (i / num_points) * width
            # Kombiniraj više frekvencija za kompleksan signal
            value = 0
            for j in range(min(8, num_points)):
                value += self.spectrum_data[j] * math.sin((i + j) * 0.1 + time.time())
            value *= height * 0.08 * self.sensitivity
            
            y = center_y + value
            path.lineTo(x, y)
        
        # Zeleni trace kao na pravim osciloskopima
        painter.setPen(QPen(QColor("#00ff41"), 2))
        painter.drawPath(path)
        
        # Glow efekat
        if self.show_glow:
            painter.setPen(QPen(QColor("#00ff41"), 6))
            painter.setOpacity(0.5)
            painter.drawPath(path)
            painter.setOpacity(1.0)
    
    def _draw_fireworks(self, painter):
        """
        FIREWORKS - Vatromet vizualizacija
        Svaki jak bas = eksplozija!
        """
        width = self.width()
        height = self.height()
        
        # Detektuj jake bassove i kreiraj eksplozije
        if len(self.spectrum_data) > 8:
            bass_energy = sum(self.spectrum_data[:8]) / 8
            
            if bass_energy > 0.6 and random.random() > 0.7:
                # Kreiraj novu eksploziju
                explosion = {
                    'x': random.uniform(width * 0.2, width * 0.8),
                    'y': random.uniform(height * 0.2, height * 0.6),
                    'particles': [],
                    'age': 0,
                    'max_age': 60,
                    'color': random.choice([
                        QColor("#ff0080"),
                        QColor("#00d4ff"),
                        QColor("#ffdd00"),
                        QColor("#00ff88"),
                        QColor("#ff4444"),
                    ])
                }
                
                # Generiši čestice za eksploziju
                num_particles = int(bass_energy * 50)
                for _ in range(num_particles):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(1, 5)
                    explosion['particles'].append({
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed - 2,  # Gravitacija
                        'x': 0,
                        'y': 0,
                    })
                
                # Dodaj u particle sistem
                if not hasattr(self, 'explosions'):
                    self.explosions = []
                self.explosions.append(explosion)
        
        # Update i crtaj postojeće eksplozije
        if not hasattr(self, 'explosions'):
            self.explosions = []
        
        gravity = 0.15
        
        for explosion in self.explosions[:]:
            explosion['age'] += 1
            life = 1.0 - (explosion['age'] / explosion['max_age'])
            
            if life <= 0:
                self.explosions.remove(explosion)
                continue
            
            # Update i crtaj čestice
            for particle in explosion['particles']:
                particle['vy'] += gravity  # Gravitacija
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                
                # Crtaj česticu
                px = explosion['x'] + particle['x']
                py = explosion['y'] + particle['y']
                
                color = QColor(explosion['color'])
                color.setAlpha(int(life * 255))
                
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                
                size = 3 * life
                painter.drawEllipse(QPointF(px, py), size, size)
                
                # Trail efekat
                if life > 0.5:
                    trail_color = QColor(explosion['color'])
                    trail_color.setAlpha(int(life * 100))
                    painter.setBrush(QBrush(trail_color))
                    painter.drawEllipse(
                        QPointF(px - particle['vx'], py - particle['vy']),
                        size * 0.5, size * 0.5
                    )
    
    def _draw_matrix(self, painter):
        """
        MATRIX - Matrix-style falling code
        Audio kontroliše brzinu i gustinu koda!
        """
        if not hasattr(self, 'matrix_columns'):
            # Inicijalizuj matrix kolone
            width = self.width()
            height = self.height()
            char_size = 20
            num_columns = width // char_size
            
            self.matrix_columns = []
            for i in range(num_columns):
                self.matrix_columns.append({
                    'x': i * char_size,
                    'chars': [],
                    'speed': random.uniform(1, 3),
                })
        
        width = self.width()
        height = self.height()
        char_size = 20
        
        # Dobij prosečnu energiju
        avg_energy = sum(self.spectrum_data) / len(self.spectrum_data) if self.spectrum_data else 0
        
        # Update kolone
        for col in self.matrix_columns:
            # Dodaj nove karaktere baziran na audio energiji
            if random.random() < avg_energy * 0.3:
                col['chars'].append({
                    'char': chr(random.randint(33, 126)),  # ASCII karakteri
                    'y': 0,
                    'brightness': 1.0,
                })
            
            # Update postojeće karaktere
            for char in col['chars'][:]:
                char['y'] += col['speed'] * (1 + avg_energy)
                char['brightness'] -= 0.02
                
                if char['y'] > height or char['brightness'] <= 0:
                    col['chars'].remove(char)
        
        # Crtaj karaktere
        font = QFont("Monospace", 14)
        painter.setFont(font)
        
        for col in self.matrix_columns:
            for i, char in enumerate(col['chars']):
                # Leading char je svetliji (beli)
                if i == len(col['chars']) - 1:
                    color = QColor("#ffffff")
                else:
                    # Ostali su zeleni sa fading
                    green_value = int(255 * char['brightness'])
                    color = QColor(0, green_value, 0)
                
                painter.setPen(QPen(color))
                painter.drawText(
                    int(col['x']), 
                    int(char['y']), 
                    char['char']
                )
    
    def _draw_plasma(self, painter):
        """
        PLASMA - Retro plasma efekat
        Audio modulira plasma frekvencije!
        """
        width = self.width()
        height = self.height()
        
        # Dobij prosečnu energiju
        avg_energy = sum(self.spectrum_data) / len(self.spectrum_data) if self.spectrum_data else 0
        
        # Plasma parametri (modulirani audio-om)
        t = time.time() * (1 + avg_energy)
        
        # Crtaj plasma pixel po pixel (optimizovano - svaki 4. pixel)
        pixel_size = 4
        
        for y in range(0, height, pixel_size):
            for x in range(0, width, pixel_size):
                # Plasma funkcija
                v = math.sin(x * 0.01 + t)
                v += math.sin(y * 0.01 + t)
                v += math.sin((x + y) * 0.01 + t)
                v += math.sin(math.sqrt(x*x + y*y) * 0.01 + t)
                
                # Audio modulacija
                freq_index = int((x / width) * len(self.spectrum_data))
                if freq_index < len(self.spectrum_data):
                    v += self.spectrum_data[freq_index] * 2
                
                # Konvertuj u boju
                v = (v + 4) / 8  # Normalizuj 0-1
                
                # Rainbow boje
                hue = int((v + t * 0.1) * 360) % 360
                saturation = int(200 + avg_energy * 55)
                value = int(150 + avg_energy * 105)
                
                color = QColor.fromHsv(hue, saturation, value)
                
                painter.fillRect(x, y, pixel_size, pixel_size, color)
    
    def apply_theme(self, primary, secondary):
        """Primeni theme boje"""
        self.primary_color = QColor(primary)
        self.secondary_color = QColor(secondary)
        self.glow_color = QColor(primary)
        print(f"🎨 Visualizer theme: {primary} / {secondary}")
    
    def set_style(self, style):
        """Postavi visualization style"""
        self.viz_style = style
        print(f"🎨 Visualizer style: {style}")
    
    def set_fps(self, fps):
        """Postavi FPS"""
        self.fps = fps
        self.timer.setInterval(1000 // fps)
        print(f"🎬 Visualizer FPS: {fps}")


class VisualizerDialog(QDialog):
    """
    Visualizer Dialog - Main window za visualizer
    
    Features:
    - Style selector
    - FPS kontrola
    - Sensitivity kontrola
    - Fullscreen toggle
    - Glow & peaks toggles
    """
    
    def __init__(self, parent=None, engine=None, app=None, plugin_manager=None, **kwargs):
        super().__init__(parent)
        
        # Dobij engine iz parent-a ako nije prosleđen
        if engine is None and parent and hasattr(parent, 'engine'):
            engine = parent.engine
        elif engine is None and app and hasattr(app, 'engine'):
            engine = app.engine
        
        self.engine = engine
        self.app = app  # Sačuvaj app reference
        self.plugin_manager = plugin_manager  # Sačuvaj plugin_manager reference
        self.is_fullscreen = False
        
        self.setup_ui()
        self.apply_theme()
        
        # Auto-start visualizer
        self.visualizer.start()
        
        print("🎨 VisualizerDialog opened")
    
    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("🎵 AudioWave Visualizer")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Visualizer widget
        self.visualizer = VisualizerWidget(self.engine, self)
        layout.addWidget(self.visualizer, 1)
        
        # Controls panel
        controls = self.create_controls()
        layout.addWidget(controls)
    
    def create_controls(self):
        """Kreiraj control panel"""
        panel = QWidget()
        panel.setObjectName("controlsPanel")
        panel.setStyleSheet("""
            #controlsPanel {
                background-color: #16162a;
                border-top: 2px solid #667eea;
                padding: 10px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            QComboBox, QSlider {
                background-color: #2a2a4a;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #667eea;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7b8eef;
            }
            QCheckBox {
                color: #ffffff;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Style selector
        style_label = QLabel("Style:")
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Waveform 🌊",      # Original
            "Spectrum 📊",      # Original  
            "Circular ⭕",      # Original
            "Particles ✨",     # Original
            "Bars Mirror 🔮",   # NEW!
            "Frequency Rings 💍", # NEW!
            "Oscilloscope 📺",  # NEW!
            "Fireworks 🎆",     # NEW!
            "Matrix 💚",        # NEW!
            "Plasma 🌈",        # NEW!
        ])
        self.style_combo.setCurrentIndex(0)  # Default: Waveform (AudioWave!)
        self.style_combo.currentIndexChanged.connect(self.on_style_changed)
        
        layout.addWidget(style_label)
        layout.addWidget(self.style_combo)
        
        # FPS control
        fps_label = QLabel("FPS:")
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(30, 120)
        self.fps_slider.setValue(60)
        self.fps_slider.setMaximumWidth(150)
        self.fps_slider.valueChanged.connect(self.on_fps_changed)
        
        self.fps_value_label = QLabel("60")
        self.fps_value_label.setMinimumWidth(30)
        
        layout.addWidget(fps_label)
        layout.addWidget(self.fps_slider)
        layout.addWidget(self.fps_value_label)
        
        # Sensitivity
        sens_label = QLabel("Sensitivity:")
        self.sens_slider = QSlider(Qt.Orientation.Horizontal)
        self.sens_slider.setRange(50, 300)
        self.sens_slider.setValue(150)
        self.sens_slider.setMaximumWidth(150)
        self.sens_slider.valueChanged.connect(self.on_sensitivity_changed)
        
        layout.addWidget(sens_label)
        layout.addWidget(self.sens_slider)
        
        layout.addStretch()
        
        # Toggles
        self.glow_check = QCheckBox("Glow")
        self.glow_check.setChecked(True)
        self.glow_check.toggled.connect(self.on_glow_toggled)
        
        self.peaks_check = QCheckBox("Peaks")
        self.peaks_check.setChecked(True)
        self.peaks_check.toggled.connect(self.on_peaks_toggled)
        
        layout.addWidget(self.glow_check)
        layout.addWidget(self.peaks_check)
        
        # Fullscreen button
        self.fullscreen_btn = QPushButton("⛶ Fullscreen")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        
        layout.addWidget(self.fullscreen_btn)
        
        return panel
    
    def on_style_changed(self, index):
        """Style promenjen"""
        styles = [
            "waveform", "spectrum", "circular", "particles",
            "bars_mirror", "frequency_rings", "oscilloscope", 
            "fireworks", "matrix", "plasma"
        ]
        self.visualizer.set_style(styles[index])
    
    def on_fps_changed(self, value):
        """FPS promenjen"""
        self.visualizer.set_fps(value)
        self.fps_value_label.setText(str(value))
    
    def on_sensitivity_changed(self, value):
        """Sensitivity promenjen"""
        self.visualizer.sensitivity = value / 100.0
    
    def on_glow_toggled(self, checked):
        """Glow toggle"""
        self.visualizer.show_glow = checked
    
    def on_peaks_toggled(self, checked):
        """Peaks toggle"""
        self.visualizer.show_peaks = checked
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.is_fullscreen:
            self.showNormal()
            self.fullscreen_btn.setText("⛶ Fullscreen")
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("⛶ Exit Fullscreen")
            self.is_fullscreen = True
    
    def apply_theme(self):
        """Primeni trenutnu temu"""
        try:
            # Get theme iz app-a (možda prosleđen kao argument)
            if self.app and hasattr(self.app, 'config'):
                theme_name = self.app.config.get_theme()
                
                from core.themes.theme_registry import ThemeRegistry
                theme = ThemeRegistry.get_theme(theme_name)
                
                self.visualizer.apply_theme(theme.primary, theme.secondary)
            # Fallback: probaj iz parent-a
            elif self.parent() and hasattr(self.parent(), 'app'):
                app = self.parent().app
                if hasattr(app, 'config'):
                    theme_name = app.config.get_theme()
                    
                    from core.themes.theme_registry import ThemeRegistry
                    theme = ThemeRegistry.get_theme(theme_name)
                    
                    self.visualizer.apply_theme(theme.primary, theme.secondary)
            else:
                # Ultimate fallback
                self.visualizer.apply_theme("#667eea", "#764ba2")
        except Exception as e:
            print(f"⚠️ Could not apply theme: {e}")
            # Fallback
            self.visualizer.apply_theme("#667eea", "#764ba2")
    
    def closeEvent(self, event):
        """Stop visualizer pri zatvaranju"""
        self.visualizer.stop()
        event.accept()
    
    def keyPressEvent(self, event):
        """ESC za exit iz fullscreen"""
        if event.key() == Qt.Key.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)