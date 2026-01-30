# -*- coding: utf-8 -*-
"""
Player Styles - Brutalni stilovi za TrayWave Player
ui/widgets/player_styles.py

KOMPATIBILNOST SA TEMAMA:
Svaki stil koristi boje iz trenutne teme preko ThemeColors klase.

FIXED: Dodao mouseMoveEvent i mouseReleaseEvent za volume i progress drag funkcionalnost
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import (QPainter, QColor, QLinearGradient, QRadialGradient,
                         QPen, QFont, QConicalGradient, QPainterPath)
from math import sin, cos, pi
import random
from dataclasses import dataclass

# Import SVG Icon Manager za elegantne ikone
try:
    from ui.utils.svg_icon_manager import render_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    print('⚠️ SVG Icon Manager not available, using text fallback')


@dataclass
class ThemeColors:
    """Boje iz trenutne teme."""
    primary: str = "#667eea"
    secondary: str = "#764ba2"
    bg_main: str = "#1a1a2e"
    bg_secondary: str = "#16213e"
    text_primary: str = "#ffffff"
    text_secondary: str = "#a0a0b0"
    accent: str = "#e94560"
    is_dark: bool = True
    
    @classmethod
    def from_theme(cls, theme) -> 'ThemeColors':
        colors = cls()
        if hasattr(theme, 'primary'): colors.primary = theme.primary
        if hasattr(theme, 'secondary'): colors.secondary = theme.secondary
        if hasattr(theme, 'bg_main'): colors.bg_main = theme.bg_main
        if hasattr(theme, 'bg_secondary'): colors.bg_secondary = getattr(theme, 'bg_secondary', theme.bg_main)
        try:
            colors.is_dark = QColor(colors.bg_main).lightness() < 128
        except:
            colors.is_dark = True
        colors.text_primary = "#ffffff" if colors.is_dark else "#333333"
        colors.text_secondary = "#a0a0b0" if colors.is_dark else "#666666"
        colors.accent = colors.primary
        return colors


class BasePlayerStyle(QWidget):
    """Base class for all player styles."""
    play_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    volume_changed = pyqtSignal(int)
    seek_requested = pyqtSignal(int)
    toggle_playlist_requested = pyqtSignal()  # Dodato za hamburger menu
    
    def __init__(self, parent=None, theme_colors: ThemeColors = None):
        super().__init__(parent)
        self.is_playing = False
        self.position = 0
        self.duration = 1000
        self.volume = 70
        self.song_title = "No track playing"
        self.song_artist = "Unknown Artist"
        self.animation_phase = 0.0
        self.theme_colors = theme_colors or ThemeColors()
        
        # âœ… FIXED: Tracking za drag operacije
        self.is_dragging_progress = False
        self.is_dragging_volume = False
        
        # Menu rect za klik detekciju
        self.menu_rect = QRectF()
        
        self._update_colors_from_theme()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate)
        self.animation_timer.start(30)
        
        # âœ… Omoguci mouse tracking za hover efekte
        self.setMouseTracking(True)
    
    def _update_colors_from_theme(self): pass
    def set_theme_colors(self, tc: ThemeColors):
        self.theme_colors = tc
        self._update_colors_from_theme()
        self.update()
    def _animate(self):
        self.animation_phase = (self.animation_phase + 0.05) % (2 * pi)
        self.update()
    def set_playing(self, p): self.is_playing = p; self.update()
    def set_position(self, p): self.position = p; self.update()
    def set_duration(self, d): self.duration = max(1, d); self.update()
    def set_volume(self, v): self.volume = max(0, min(100, v)); self.update()
    def set_metadata(self, t, a):
        self.song_title = t or "No track playing"
        self.song_artist = a or "Unknown Artist"
        self.update()
    def format_time(self, ms):
        s = ms // 1000
        return f"{s//60}:{s%60:02d}"
    
    def wheelEvent(self, e):
        """âœ… FIXED: Dodao wheel event za volume control"""
        delta = e.angleDelta().y()
        
        if delta > 0:
            new_volume = min(100, self.volume + 5)
        else:
            new_volume = max(0, self.volume - 5)
        
        self.volume = new_volume
        self.volume_changed.emit(new_volume)
        self.update()
        
        e.accept()
    
    def _draw_menu_icon(self, p, x, y, size=28, color=None):
        """Helper za crtanje hamburger menu ikone u gornjem desnom uglu."""
        if not SVG_ICONS_AVAILABLE:
            return
        
        if color is None:
            # Auto-detect boja
            if hasattr(self, 'txt'):
                color = f"#{self.txt.red():02x}{self.txt.green():02x}{self.txt.blue():02x}"
            else:
                color = "#ffffff"
        
        self.menu_rect = QRectF(x, y, size, size)  # ÄŒuvam za klik detekciju
        render_icon(p, "menu", self.menu_rect, color)


class ModernStyle(BasePlayerStyle):
    """Modern stil - Neonski akcenti, glow efekti."""
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent, theme_colors)
        self.setMinimumSize(400, 270)
        self.prev_rect = self.play_rect = self.next_rect = self.stop_rect = QRectF()
        self.progress_rect = self.volume_rect = QRectF()
    
    def _update_colors_from_theme(self):
        tc = self.theme_colors
        self.accent = QColor(tc.primary)
        self.accent2 = QColor(tc.secondary)
        self.bg1 = QColor(tc.bg_main)
        self.bg2 = QColor(tc.bg_secondary)
        self.txt = QColor(tc.text_primary)
        self.txt2 = QColor(tc.text_secondary)
    
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Background
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, self.bg1)
        bg.setColorAt(1, self.bg2)
        p.fillRect(0, 0, w, h, bg)
        
        # Animated glow
        gx = w/2 + sin(self.animation_phase)*w*0.3
        gy = h/2 + cos(self.animation_phase)*h*0.2
        gl = QRadialGradient(gx, gy, w*0.4)
        gl.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 60))
        gl.setColorAt(1, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 0))
        p.fillRect(0, 0, w, h, gl)
        
        # Title
        p.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        gi = int(80 + sin(self.animation_phase) * 30)
        p.setPen(QColor(self.accent.red(), self.accent.green(), self.accent.blue(), gi))
        p.drawText(0, 40, w, 40, Qt.AlignmentFlag.AlignCenter, self.song_title)
        p.setPen(self.txt)
        p.drawText(0, 38, w, 40, Qt.AlignmentFlag.AlignCenter, self.song_title)
        
        # Artist
        p.setFont(QFont("Segoe UI", 12))
        p.setPen(self.txt2)
        p.drawText(0, 75, w, 25, Qt.AlignmentFlag.AlignCenter, self.song_artist)
        
        # Progress bar
        py, ph, pm = 120, 8, 40
        self.progress_rect = QRectF(pm, py, w-2*pm, ph)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 30))
        p.drawRoundedRect(self.progress_rect, 4, 4)
        
        if self.duration > 0:
            pr = self.position / self.duration
            fw = int((w - 2*pm) * pr)
            pg = QLinearGradient(pm, 0, w-pm, 0)
            pg.setColorAt(0, self.accent)
            pg.setColorAt(1, self.accent2)
            p.setBrush(pg)
            p.drawRoundedRect(QRectF(pm, py, fw, ph), 4, 4)
            
            # Handle glow
            hx = pm + fw
            hg = QRadialGradient(hx, py + ph/2, 20)
            hg.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 150))
            hg.setColorAt(1, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 0))
            p.setBrush(hg)
            p.drawEllipse(QRectF(hx-20, py-16, 40, 40))
            p.setBrush(self.txt)
            p.drawEllipse(QRectF(hx-6, py-2, 12, 12))
        
        # Time labels
        p.setFont(QFont("Segoe UI", 10))
        p.setPen(self.txt2)
        p.drawText(int(pm), int(py+15), 60, 20, Qt.AlignmentFlag.AlignLeft, self.format_time(self.position))
        p.drawText(int(w-pm-60), int(py+15), 60, 20, Qt.AlignmentFlag.AlignRight, self.format_time(self.duration))
        
        # Control buttons
        cy, bs, ss, sp = 170, 56, 44, 20
        tw = ss*3 + bs + sp*3
        sx = (w - tw) / 2
        
        self.prev_rect = QRectF(sx, cy, ss, ss)
        self._btn(p, self.prev_rect, "previous_elegant")
        
        self.play_rect = QRectF(sx + ss + sp, cy - 6, bs, bs)
        self._play(p, self.play_rect)
        
        self.next_rect = QRectF(sx + ss + bs + sp*2, cy, ss, ss)
        self._btn(p, self.next_rect, "next_elegant")
        
        self.stop_rect = QRectF(sx + ss*2 + bs + sp*3, cy, ss, ss)
        self._btn(p, self.stop_rect, "stop_elegant")
        
        # Volume
        vy, vw = 235, 150
        vx = (w - vw) / 2
        self.volume_rect = QRectF(vx, vy, vw, 8)
        
        # Volume ikonica
        if SVG_ICONS_AVAILABLE:
            vol_icon_rect = QRectF(vx-32, vy-8, 26, 26)
            color = f"#{self.txt2.red():02x}{self.txt2.green():02x}{self.txt2.blue():02x}"
            render_icon(p, "volume_elegant", vol_icon_rect, color)
        else:
            p.setPen(self.txt2)
            p.setFont(QFont("Segoe UI", 14))
            p.drawText(int(vx-35), int(vy-5), 30, 20, Qt.AlignmentFlag.AlignCenter, "♪")
        
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 30))
        p.drawRoundedRect(self.volume_rect, 4, 4)
        
        vf = int(vw * (self.volume / 100))
        vg = QLinearGradient(vx, 0, vx + vw, 0)
        vg.setColorAt(0, self.txt2)
        vg.setColorAt(1, self.txt)
        p.setBrush(vg)
        p.drawRoundedRect(QRectF(vx, vy, vf, 8), 4, 4)
        
        p.setPen(self.txt2)
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(int(vx + vw + 10), int(vy - 5), 40, 20, Qt.AlignmentFlag.AlignLeft, f"{self.volume}%")
        
        # Hamburger menu ikona (gornji desni ugao)
        self._draw_menu_icon(p, w - 38, 10, 28)
    
    def _btn(self, p, r, icon_name):
        """Render button sa SVG ikonom"""
        # Background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 60))
        p.drawRoundedRect(r, r.width()/2, r.height()/2)
        
        # SVG ikonica
        if SVG_ICONS_AVAILABLE:
            # Render SVG ikonicu sa accent bojom
            color = f"#{self.txt.red():02x}{self.txt.green():02x}{self.txt.blue():02x}"
            icon_rect = r.adjusted(r.width()*0.2, r.height()*0.2, -r.width()*0.2, -r.height()*0.2)
            render_icon(p, icon_name, icon_rect, color)
        else:
            # Fallback na text
            p.setPen(self.txt)
            p.setFont(QFont("Segoe UI", 16))
            fallback_text = {"previous_elegant": "â—„", "next_elegant": "â–º", "stop_elegant": "â– "}.get(icon_name, "?")
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, fallback_text)
    
    def _play(self, p, r):
        c = r.center()
        if self.is_playing:
            gs = r.width() + 40 + sin(self.animation_phase) * 10
            g = QRadialGradient(c, gs/2)
            g.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 100))
            g.setColorAt(1, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 0))
            p.setBrush(g)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(c, gs/2, gs/2)
        
        bg = QLinearGradient(r.topLeft(), r.bottomRight())
        bg.setColorAt(0, self.accent)
        bg.setColorAt(1, self.accent2)
        p.setBrush(bg)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(r)
        
        
        # SVG ikonica
        if SVG_ICONS_AVAILABLE:
            icon_name = "pause_elegant" if self.is_playing else "play_elegant"
            color = f"#{self.txt.red():02x}{self.txt.green():02x}{self.txt.blue():02x}"
            icon_rect = r.adjusted(r.width()*0.25, r.height()*0.25, -r.width()*0.25, -r.height()*0.25)
            render_icon(p, icon_name, icon_rect, color)
        else:
            # Fallback na text
            p.setPen(self.txt)
            p.setFont(QFont("Segoe UI", 22))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "II" if self.is_playing else "â–¶")
    
    def mousePressEvent(self, e):
        """âœ… FIXED: Dodao drag tracking + menu klik"""
        pt = e.position()
        if self.menu_rect.contains(pt):
            self.toggle_playlist_requested.emit()
        elif self.play_rect.contains(pt):
            self.play_clicked.emit()
        elif self.prev_rect.contains(pt):
            self.prev_clicked.emit()
        elif self.next_rect.contains(pt):
            self.next_clicked.emit()
        elif self.stop_rect.contains(pt):
            self.stop_clicked.emit()
        elif self.progress_rect.contains(pt):
            self.is_dragging_progress = True
            self._handle_progress_drag(pt)
        elif self.volume_rect.contains(pt):
            self.is_dragging_volume = True
            self._handle_volume_drag(pt)
    
    def mouseMoveEvent(self, e):
        """✓ FIXED: Dodao mouse move handler"""
        if self.is_dragging_progress:
            self._handle_progress_drag(e.position())
        elif self.is_dragging_volume:
            self._handle_volume_drag(e.position())
    
    def mouseReleaseEvent(self, e):
        """✓ FIXED: Dodao mouse release handler"""
        self.is_dragging_progress = False
        self.is_dragging_volume = False
    
    def _handle_progress_drag(self, pt):
        """Handle progress bar drag"""
        r = (pt.x() - self.progress_rect.x()) / self.progress_rect.width()
        r = max(0, min(1, r))
        self.seek_requested.emit(int(r * self.duration))
    
    def _handle_volume_drag(self, pt):
        """Handle volume bar drag"""
        r = (pt.x() - self.volume_rect.x()) / self.volume_rect.width()
        r = max(0, min(1, r))
        new_volume = int(r * 100)
        self.volume = new_volume
        self.volume_changed.emit(new_volume)
        self.update()


class VinylStyle(BasePlayerStyle):
    """Vinyl Player stil - Rotirajuća ploča, VU metar, Vintage Volume Knob! 🎵"""
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent, theme_colors)
        self.setMinimumSize(450, 290)
        self.vinyl_rotation = 0
        self.vu_left = self.vu_right = 0
        self.prev_rect = self.play_rect = self.next_rect = QRectF()
        self.volume_knob_rect = QRectF()  # Za volume knob
    
    def _update_colors_from_theme(self):
        tc = self.theme_colors
        self.wood_dark = QColor(45, 31, 31) if tc.is_dark else QColor(180, 150, 120)
        self.wood_light = QColor(139, 90, 43) if tc.is_dark else QColor(210, 180, 140)
        self.gold = QColor(tc.primary)
        self.green = QColor(74, 124, 63)
        self.red = QColor(201, 48, 44)
    
    def _animate(self):
        super()._animate()
        if self.is_playing:
            self.vinyl_rotation = (self.vinyl_rotation + 2) % 360
            # ✓ Smooth VU meter animacija (kao original!)
            self.vu_left += (0.4 + random.random() * 0.5 - self.vu_left) * 0.15
            self.vu_right += (0.4 + random.random() * 0.5 - self.vu_right) * 0.15
        else:
            self.vu_left += (0.1 - self.vu_left) * 0.15
            self.vu_right += (0.1 - self.vu_right) * 0.15
    
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # ✓ ORIGINALNI BACKGROUND sa gradijentom
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, self.wood_dark)
        bg.setColorAt(1, self.wood_dark.darker(130))
        p.fillRect(0, 0, w, h, bg)
        
        # ✓ WOOD GRAIN tekstura!
        p.setPen(QPen(QColor(self.wood_light.red(), self.wood_light.green(), self.wood_light.blue(), 30), 1))
        for i in range(0, w, 4):
            p.drawLine(i, 0, i, h)
        
        # ✓ VELIKI VINYL DISC (180px) sa conical gradient!
        vs = 180
        vx, vy = 40, int((h - vs) / 2 - 20)
        vc = QRectF(vx, vy, vs, vs).center()
        
        p.save()
        p.translate(vc)
        p.rotate(self.vinyl_rotation)
        p.translate(-vc)
        
        # Conical gradient za realistični vinyl izgled
        vg = QConicalGradient(vc, 0)
        vg.setColorAt(0, QColor(17, 17, 17))
        vg.setColorAt(0.25, QColor(51, 51, 51))
        vg.setColorAt(0.5, QColor(17, 17, 17))
        vg.setColorAt(0.75, QColor(51, 51, 51))
        vg.setColorAt(1, QColor(17, 17, 17))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(vg)
        p.drawEllipse(QRectF(vx, vy, vs, vs))
        
        # ✓ GROOVES (8 koncentričnih krugova)
        p.setPen(QPen(QColor(60, 60, 60, 80), 1))
        for i in range(8):
            gs = vs - 40 - i * 16
            if gs > 40:
                p.drawEllipse(vc, gs/2, gs/2)
        
        # ✓ CENTER LABEL sa gold gradijentom
        ls = 60
        lg = QLinearGradient(vc.x() - ls/2, vc.y() - ls/2, vc.x() + ls/2, vc.y() + ls/2)
        lg.setColorAt(0, self.gold)
        lg.setColorAt(1, self.wood_light)
        p.setBrush(lg)
        p.drawEllipse(vc, ls/2, ls/2)
        p.setBrush(QColor(20, 20, 20))
        p.drawEllipse(vc, 8, 8)
        
        p.restore()
        
        # ✓ TONEARM koji se pomera! 🎸
        ta = 25 if self.is_playing else 5
        p.save()
        p.translate(vx + vs - 10, vy + 20)
        p.rotate(ta)
        ag = QLinearGradient(0, 0, 0, 100)
        ag.setColorAt(0, QColor(150, 150, 150))
        ag.setColorAt(1, QColor(100, 100, 100))
        p.setBrush(ag)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(-3, 0, 6, 100, 3, 3)
        p.setBrush(QColor(80, 80, 80))
        p.drawRect(-6, 95, 12, 20)
        p.restore()
        
        # Right side - info and controls
        rx = vx + vs + 30
        
        # ✓ Song info
        p.setPen(self.gold)
        p.setFont(QFont("Georgia", 16, QFont.Weight.Bold))
        p.drawText(rx, 40, w - rx - 20, 30, Qt.AlignmentFlag.AlignLeft, self.song_title)
        p.setPen(self.wood_light)
        p.setFont(QFont("Georgia", 11))
        p.drawText(rx, 65, w - rx - 20, 25, Qt.AlignmentFlag.AlignLeft, self.song_artist)
        
        # ✓ Buttons
        cy, bs, sp = 110, 52, 15
        self.prev_rect = QRectF(rx, cy, bs, bs)
        self._vbtn(p, self.prev_rect, "previous_elegant", self.wood_light)
        
        self.play_rect = QRectF(rx + bs + sp, cy, bs + 10, bs + 10)
        pc = self.red if self.is_playing else self.green
        self._vbtn(p, self.play_rect, "pause_elegant" if self.is_playing else "play_elegant", pc)
        
        self.next_rect = QRectF(rx + bs*2 + sp*2 + 10, cy, bs, bs)
        self._vbtn(p, self.next_rect, "next_elegant", self.wood_light)
        
        # ✓ VERTIKALNI VU METER (kao original!)
        vuy, vbw, vbh, vsp = 200, 12, 80, 4
        p.setPen(QColor(100, 80, 60))
        p.setFont(QFont("Arial", 9))
        p.drawText(rx, vuy - 15, 100, 15, Qt.AlignmentFlag.AlignLeft, "VU METER")
        
        vul = (self.vu_left + self.vu_right) / 2
        for i in range(10):
            bx = rx + i * (vbw + vsp)
            p.setBrush(self.wood_dark.darker(150))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(int(bx), int(vuy), vbw, vbh)
            
            ft = i / 10
            if vul > ft:
                c = self.red if i >= 8 else (self.gold if i >= 6 else self.green)
                p.setBrush(c)
                fh = min(vbh, int((vul - ft) * 10 * vbh))
                p.drawRect(int(bx), int(vuy + vbh - fh), vbw, fh)
        
        # 🎚️ NOVI - VINTAGE VOLUME KNOB! (kao na pravim gramophone-ima)
        knob_size = 45
        knob_x = vx + vs / 2 - knob_size / 2
        knob_y = vy + vs + 15
        self.volume_knob_rect = QRectF(knob_x, knob_y, knob_size, knob_size)
        
        # Knob pozadina (metalni prsten)
        p.setPen(QPen(QColor(80, 80, 80), 2))
        p.setBrush(QColor(40, 40, 40))
        p.drawEllipse(self.volume_knob_rect)
        
        # Knob gradient (3D efekat)
        kg = QRadialGradient(self.volume_knob_rect.center(), knob_size / 2)
        kg.setColorAt(0, QColor(120, 120, 120))
        kg.setColorAt(0.7, QColor(80, 80, 80))
        kg.setColorAt(1, QColor(40, 40, 40))
        p.setBrush(kg)
        p.drawEllipse(self.volume_knob_rect.adjusted(2, 2, -2, -2))
        
        # Marker linija (pokazuje current volume)
        p.save()
        p.translate(self.volume_knob_rect.center())
        # Volume od 0-100 mapiramo na -135° do +135° (270° total)
        angle = -135 + (self.volume / 100) * 270
        p.rotate(angle)
        p.setPen(QPen(self.gold, 3))
        # ✓ FIXED: Konvertovao u int
        y1 = int(-knob_size/2 + 8)
        y2 = int(-knob_size/2 + 18)
        p.drawLine(0, y1, 0, y2)
        p.restore()
        
        # Volume oznake (tickmarks)
        p.setPen(QPen(QColor(100, 90, 80), 1))
        for vol in [0, 25, 50, 75, 100]:
            a = -135 + (vol / 100) * 270
            p.save()
            p.translate(self.volume_knob_rect.center())
            p.rotate(a)
            # ✓ FIXED: Konvertovao u int
            ty1 = int(-knob_size/2 - 2)
            ty2 = int(-knob_size/2 - 7)
            p.drawLine(0, ty1, 0, ty2)
            p.restore()
        
        # Volume label
        p.setPen(self.gold)
        p.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        p.drawText(int(knob_x - 10), int(knob_y + knob_size + 5), int(knob_size + 20), 15, 
                   Qt.AlignmentFlag.AlignCenter, f"VOL {self.volume}")
        
        # âœ… Time
        p.setPen(self.gold)
        p.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        p.drawText(rx, h - 40, 200, 30, Qt.AlignmentFlag.AlignLeft,
                   f"{self.format_time(self.position)} / {self.format_time(self.duration)}")
        
        # Hamburger menu ikona (gornji desni ugao) - zlatna vintage boja
        color = f"#{self.gold.red():02x}{self.gold.green():02x}{self.gold.blue():02x}"
        if SVG_ICONS_AVAILABLE:
            menu_rect = QRectF(w - 38, 10, 28, 28)
            render_icon(p, "menu", menu_rect, color)
    
    def _vbtn(self, p, r, icon_name, c):
        """Vintage button sa SVG ikonom"""
        # Shadow
        sr = r.translated(3, 3)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 100))
        p.drawRoundedRect(sr, 8, 8)
        
        # Button background sa gradijentom
        bg = QLinearGradient(r.topLeft(), r.bottomLeft())
        bg.setColorAt(0, c.lighter(120))
        bg.setColorAt(0.5, c)
        bg.setColorAt(1, c.darker(130))
        p.setBrush(bg)
        p.drawRoundedRect(r, 8, 8)
        
        # Highlight
        p.setPen(QPen(QColor(255, 255, 255, 50), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r.adjusted(2, 2, -2, -2), 6, 6)
        
        # SVG ikonica
        if SVG_ICONS_AVAILABLE:
            ic = QColor(255, 255, 255) if c in [self.green, self.red] else QColor(40, 30, 20)
            color = f"#{ic.red():02x}{ic.green():02x}{ic.blue():02x}"
            icon_rect = r.adjusted(r.width()*0.2, r.height()*0.2, -r.width()*0.2, -r.height()*0.2)
            render_icon(p, icon_name, icon_rect, color)
        else:
            # Fallback na text
            ic = QColor(255, 255, 255) if c in [self.green, self.red] else QColor(40, 30, 20)
            p.setPen(ic)
            p.setFont(QFont("Segoe UI", 18))
            fallback = {"previous_elegant": "â—„", "next_elegant": "â–º", "play_elegant": "â–¶", "pause_elegant": "II"}.get(icon_name, "?")
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, fallback)
    
    def mousePressEvent(self, e):
        """âœ… FIXED: Dodao volume knob drag tracking + menu klik"""
        pt = e.position()
        if self.menu_rect.contains(pt):
            self.toggle_playlist_requested.emit()
        elif self.play_rect.contains(pt):
            self.play_clicked.emit()
        elif self.prev_rect.contains(pt):
            self.prev_clicked.emit()
        elif self.next_rect.contains(pt):
            self.next_clicked.emit()
        elif self.volume_knob_rect.contains(pt):
            self.is_dragging_volume = True
            self._handle_knob_drag(pt)
    
    def mouseMoveEvent(self, e):
        """✓ FIXED: Dodao knob drag"""
        if self.is_dragging_volume:
            self._handle_knob_drag(e.position())
    
    def mouseReleaseEvent(self, e):
        """✓ FIXED: Dodao mouse release"""
        self.is_dragging_volume = False
    
    def _handle_knob_drag(self, pt):
        """Handle vintage volume knob rotation"""
        # Računamo ugao od centra knoba do miša
        center = self.volume_knob_rect.center()
        dx = pt.x() - center.x()
        dy = pt.y() - center.y()
        
        from math import atan2, degrees
        angle = degrees(atan2(dy, dx)) + 90  # +90 da bi 0° bilo gore
        
        # Normalizujemo ugao na -135° do +135° (270° total)
        if angle < 0:
            angle += 360
        
        # Mapiramo ugao na volume (0-100)
        # -135° (225°) = 0%, +135° (135°) = 100%
        if angle >= 225 or angle <= 135:
            if angle >= 225:
                normalized = angle - 225
            else:
                normalized = angle + 135
            
            new_volume = int((normalized / 270) * 100)
            new_volume = max(0, min(100, new_volume))
            
            self.volume = new_volume
            self.volume_changed.emit(new_volume)
            self.update()


class WaveformStyle(BasePlayerStyle):
    """Cyberpunk stil - Živi waveform, neon boje."""
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent, theme_colors)
        self.setMinimumSize(400, 340)  # ✓ Optimizovano za kompaktan layout
        self.waveform_data = [random.random() * 100 for _ in range(64)]
        self.grid_offset = 0
        self.prev_rect = self.play_rect = self.next_rect = self.progress_rect = QRectF()
        self.volume_rect = QRectF()  # Za volume bar
    
    def _update_colors_from_theme(self):
        tc = self.theme_colors
        self.cyan = QColor(tc.primary)
        self.magenta = QColor(tc.secondary)
        self.bg1 = QColor(tc.bg_main)
        self.bg2 = QColor(tc.bg_secondary)
        self.txt = QColor(tc.text_primary)
    
    def _animate(self):
        super()._animate()
        self.grid_offset = (self.grid_offset + 1) % 30
        if self.is_playing:
            self.waveform_data = [random.random() * 100 for _ in range(64)]
        else:
            self.waveform_data = [max(5, d * 0.95) for d in self.waveform_data]
    
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Background
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, self.bg1)
        bg.setColorAt(1, self.bg2)
        p.fillRect(0, 0, w, h, bg)
        
        # Animated grid
        p.setPen(QPen(QColor(self.cyan.red(), self.cyan.green(), self.cyan.blue(), 40), 1))
        gs = 30
        for x in range(0, w + gs, gs):
            p.drawLine(x, 0, x, h)
        for y in range(-gs + self.grid_offset, h + gs, gs):
            p.drawLine(0, y, w, y)
        
        # Waveform
        wy, wh = 50, 100
        bw = (w - 40) / len(self.waveform_data)
        pr = self.position / self.duration if self.duration > 0 else 0
        pb = int(pr * len(self.waveform_data))
        
        for i, ht in enumerate(self.waveform_data):
            bx = 20 + i * bw
            bh = (ht / 100) * wh
            by = wy + (wh - bh) / 2
            
            if i < pb:
                bbg = QLinearGradient(0, by, 0, by + bh)
                bbg.setColorAt(0, self.cyan)
                bbg.setColorAt(1, self.magenta)
                p.setBrush(bbg)
                p.setPen(QPen(QColor(self.cyan.red(), self.cyan.green(), self.cyan.blue(), 100), 2))
            else:
                p.setBrush(QColor(255, 255, 255, 50))
                p.setPen(Qt.PenStyle.NoPen)
            
            p.drawRoundedRect(QRectF(bx, by, bw - 2, bh), 2, 2)
        
        # Title
        p.setPen(self.txt)
        p.setFont(QFont("Orbitron", 18, QFont.Weight.Bold))
        p.drawText(0, 170, w, 30, Qt.AlignmentFlag.AlignCenter, self.song_title)
        
        # Artist (NOVO!)
        p.setPen(QColor(self.txt.red(), self.txt.green(), self.txt.blue(), 180))
        p.setFont(QFont("Orbitron", 11))
        p.drawText(0, 195, w, 20, Qt.AlignmentFlag.AlignCenter, self.song_artist)
        
        # Progress bar (pomereno na 225 da ima mesta za artist)
        py = 225
        self.progress_rect = QRectF(40, py, w - 80, 6)
        
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 30))
        p.drawRoundedRect(self.progress_rect, 3, 3)
        
        if self.duration > 0:
            fw = int(self.progress_rect.width() * pr)
            pg = QLinearGradient(40, 0, w - 40, 0)
            pg.setColorAt(0, self.cyan)
            pg.setColorAt(1, self.magenta)
            p.setBrush(pg)
            p.drawRoundedRect(QRectF(40, py, fw, 6), 3, 3)
        
        # Time - POBOLJŠANO sa neon efektom
        p.setPen(self.cyan)
        p.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        p.drawText(40, py + 15, 100, 20, Qt.AlignmentFlag.AlignLeft, self.format_time(self.position))
        p.setPen(self.magenta)
        p.drawText(w - 140, py + 15, 100, 20, Qt.AlignmentFlag.AlignRight, self.format_time(self.duration))
        
        # Controls (pomereno viÅ¡e da ne dodiruje volume bar)
        cy, bs = 245, 60
        self.play_rect = QRectF((w - bs) / 2, cy, bs, bs)
        self._hex_btn(p, self.play_rect, "pause_elegant" if self.is_playing else "play_elegant", self.cyan if self.is_playing else self.magenta)
        
        self.prev_rect = QRectF((w - bs) / 2 - bs - 20, cy + 10, bs - 20, bs - 20)
        self._hex_btn(p, self.prev_rect, "previous_elegant", self.cyan)
        
        self.next_rect = QRectF((w + bs) / 2 + 20, cy + 10, bs - 20, bs - 20)
        self._hex_btn(p, self.next_rect, "next_elegant", self.magenta)
        
        # 🎚️ NOVO - NEON VOLUME BAR (cyberpunk stil!)
        # Pozicioniran ispod kontrola sa dovoljno prostora
        vy = h - 25  # ✓ Optimizovano za manji gap
        vw = 200
        vx = (w - vw) / 2
        self.volume_rect = QRectF(vx, vy, vw, 6)
        
        # Volume ikonica
        if SVG_ICONS_AVAILABLE:
            vol_icon_rect = QRectF(vx-32, vy-8, 26, 26)
            color = f"#{self.cyan.red():02x}{self.cyan.green():02x}{self.cyan.blue():02x}"
            render_icon(p, "volume_elegant", vol_icon_rect, color)
        else:
            p.setPen(self.cyan)
            p.setFont(QFont("Segoe UI", 14))
            p.drawText(int(vx - 30), int(vy - 5), 25, 20, Qt.AlignmentFlag.AlignCenter, "♪")
        
        # Volume background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 30))
        p.drawRoundedRect(self.volume_rect, 3, 3)
        
        # Volume fill sa neon gradijentom
        vf = int(vw * (self.volume / 100))
        if vf > 0:
            vg = QLinearGradient(vx, 0, vx + vw, 0)
            vg.setColorAt(0, self.cyan)
            vg.setColorAt(1, self.magenta)
            p.setBrush(vg)
            p.drawRoundedRect(QRectF(vx, vy, vf, 6), 3, 3)
        
        # Volume label
        p.setPen(self.txt)
        p.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        p.drawText(int(vx + vw + 10), int(vy - 5), 40, 20, Qt.AlignmentFlag.AlignLeft, f"{self.volume}%")
        
        # Hamburger menu ikona (gornji desni ugao) - cyan neon boja
        color = f"#{self.cyan.red():02x}{self.cyan.green():02x}{self.cyan.blue():02x}"
        if SVG_ICONS_AVAILABLE:
            menu_rect = QRectF(w - 38, 10, 28, 28)
            render_icon(p, "menu", menu_rect, color)
    
    def _hex_btn(self, p, r, icon_name, col):
        """Hexagonal button sa SVG ikonom"""
        path = QPainterPath()
        c = r.center()
        rad = r.width() / 2
        
        # Hexagon shape
        for j in range(6):
            angle = (j * 60 - 90) * pi / 180
            x = c.x() + rad * cos(angle)
            y = c.y() + rad * sin(angle)
            if j == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        
        p.setBrush(col)
        p.drawPath(path)
        
        # SVG ikonica
        if SVG_ICONS_AVAILABLE:
            # Kontrastna boja za ikonicu (crna ili bela)
            icon_color = "#000000" if col.lightness() > 128 else "#ffffff"
            icon_rect = r.adjusted(r.width()*0.25, r.height()*0.25, -r.width()*0.25, -r.height()*0.25)
            render_icon(p, icon_name, icon_rect, icon_color)
        else:
            # Fallback na text
            p.setPen(QColor(0, 0, 0))
            p.setFont(QFont("Segoe UI", 20))
            fallback = {"previous_elegant": "â—„", "next_elegant": "â–º", "play_elegant": "â–¶", "pause_elegant": "II"}.get(icon_name, "?")
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, fallback)

    
    def mousePressEvent(self, e):
        """âœ… FIXED: Dodao drag tracking + menu klik"""
        pt = e.position()
        if self.menu_rect.contains(pt):
            self.toggle_playlist_requested.emit()
        elif self.play_rect.contains(pt):
            self.play_clicked.emit()
        elif self.prev_rect.contains(pt):
            self.prev_clicked.emit()
        elif self.next_rect.contains(pt):
            self.next_clicked.emit()
        elif self.progress_rect.contains(pt):
            self.is_dragging_progress = True
            self._handle_progress_drag(pt)
        elif self.volume_rect.contains(pt):
            self.is_dragging_volume = True
            self._handle_volume_drag(pt)
    
    def mouseMoveEvent(self, e):
        """✓ FIXED: Dodao mouse move handler"""
        if self.is_dragging_progress:
            self._handle_progress_drag(e.position())
        elif self.is_dragging_volume:
            self._handle_volume_drag(e.position())
    
    def mouseReleaseEvent(self, e):
        """✓ FIXED: Dodao mouse release handler"""
        self.is_dragging_progress = False
        self.is_dragging_volume = False
    
    def _handle_progress_drag(self, pt):
        """Handle progress bar drag"""
        r = (pt.x() - self.progress_rect.x()) / self.progress_rect.width()
        r = max(0, min(1, r))
        self.seek_requested.emit(int(r * self.duration))
    
    def _handle_volume_drag(self, pt):
        """Handle volume bar drag"""
        r = (pt.x() - self.volume_rect.x()) / self.volume_rect.width()
        r = max(0, min(1, r))
        new_volume = int(r * 100)
        self.volume = new_volume
        self.volume_changed.emit(new_volume)
        self.update()


class MinimalZenStyle(BasePlayerStyle):
    """Minimalistički zen stil - breathing animacija."""
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent, theme_colors)
        self.setMinimumSize(400, 290)
        self.breath_phase = 0
        self.play_rect = self.prev_rect = self.next_rect = self.progress_rect = QRectF()
    
    def _update_colors_from_theme(self):
        tc = self.theme_colors
        if tc.is_dark:
            self.bg1 = QColor(tc.bg_main)
            self.bg2 = QColor(tc.bg_secondary)
            self.txt1 = QColor(tc.text_primary)
            self.txt2 = QColor(tc.text_secondary)
        else:
            self.bg1 = QColor(250, 250, 250)
            self.bg2 = QColor(240, 240, 240)
            self.txt1 = QColor(60, 60, 60)
            self.txt2 = QColor(160, 160, 160)
        self.accent = QColor(tc.primary)
    
    def _animate(self):
        super()._animate()
        self.breath_phase = (self.breath_phase + 0.02) % (2 * pi)
    
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Background
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, self.bg1)
        bg.setColorAt(1, self.bg2)
        p.fillRect(0, 0, w, h, bg)
        
        # Subtle decorative circles
        p.setPen(QPen(QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 20), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(w * 0.6, -h * 0.3, h * 0.8, h * 0.8))
        p.drawEllipse(QRectF(-w * 0.2, h * 0.5, h * 0.6, h * 0.6))
        
        # Title
        p.setPen(self.txt1)
        p.setFont(QFont("Helvetica Neue", 28, QFont.Weight.Light))
        p.drawText(0, 50, w, 50, Qt.AlignmentFlag.AlignCenter, self.song_title)
        
        # Artist
        p.setPen(self.txt2)
        af = QFont("Helvetica Neue", 11)
        af.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        p.setFont(af)
        p.drawText(0, 95, w, 25, Qt.AlignmentFlag.AlignCenter, self.song_artist.upper())
        
        # Minimal progress line
        py = 140
        self.progress_rect = QRectF(60, py, w - 120, 1)
        
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.txt2)
        p.drawRoundedRect(self.progress_rect, 0.5, 0.5)
        
        pr = self.position / self.duration if self.duration > 0 else 0
        fw = int(self.progress_rect.width() * pr)
        p.setBrush(self.txt1)
        p.drawRoundedRect(QRectF(60, py, fw, 1), 0.5, 0.5)
        
        # Handle dot
        hx = 60 + fw
        p.drawEllipse(QRectF(hx - 4, py - 4, 8, 8))
        
        # Central play button
        cy, bs = 200, 80
        self.play_rect = QRectF((w - bs) / 2, cy, bs, bs)
        
        # Breathing animation when playing
        if self.is_playing:
            sc = 1 + sin(self.breath_phase) * 0.15
            al = int(100 - sin(self.breath_phase) * 50)
            bsz = bs * sc
            
            p.setPen(QPen(QColor(self.accent.red(), self.accent.green(), self.accent.blue(), al), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF((w - bsz) / 2, cy - (bsz - bs) / 2, bsz, bsz))
        
        # Play button circle
        p.setPen(QPen(self.txt1, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(self.play_rect)
        
        # Play/pause icon - SVG
        if SVG_ICONS_AVAILABLE:
            icon_name = "pause_elegant" if self.is_playing else "play_elegant"
            color = f"#{self.txt1.red():02x}{self.txt1.green():02x}{self.txt1.blue():02x}"
            icon_rect = self.play_rect.adjusted(self.play_rect.width()*0.3, self.play_rect.height()*0.3, -self.play_rect.width()*0.3, -self.play_rect.height()*0.3)
            render_icon(p, icon_name, icon_rect, color)
        else:
            p.setFont(QFont("Segoe UI", 24))
            p.drawText(self.play_rect, Qt.AlignmentFlag.AlignCenter, "II" if self.is_playing else "â–¶")
        
        
        # Side controls
        sy = h - 50
        self.prev_rect = QRectF(30, sy, 80, 30)
        self.next_rect = QRectF(w - 110, sy, 80, 30)
        
        # Prev/Next sa SVG ikonama
        if SVG_ICONS_AVAILABLE:
            # Prev ikonica
            prev_icon_rect = QRectF(30, sy+5, 20, 20)
            color = f"#{self.txt2.red():02x}{self.txt2.green():02x}{self.txt2.blue():02x}"
            render_icon(p, "previous_elegant", prev_icon_rect, color)
            p.setPen(self.txt2)
            p.setFont(QFont("Helvetica Neue", 10))
            p.drawText(55, sy, 80, 30, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Prev")
            # Next ikonica
            next_icon_rect = QRectF(w - 50, sy+5, 20, 20)
            render_icon(p, "next_elegant", next_icon_rect, color)
            p.drawText(w - 110, sy, 55, 30, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "Next")
        else:
            p.setPen(self.txt2)
            p.setFont(QFont("Helvetica Neue", 10))
            p.drawText(self.prev_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "â—„ Prev")
            p.drawText(self.next_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "Next â–º")
        
        # Time display
        p.drawText(0, sy, w, 30, Qt.AlignmentFlag.AlignCenter,
                   f"{self.format_time(self.position)} / {self.format_time(self.duration)}")
        
        # Hamburger menu ikona (gornji desni ugao) - minimalistiÄka boja
        color = f"#{self.txt2.red():02x}{self.txt2.green():02x}{self.txt2.blue():02x}"
        if SVG_ICONS_AVAILABLE:
            menu_rect = QRectF(w - 38, 10, 28, 28)
            render_icon(p, "menu", menu_rect, color)
    
    def mousePressEvent(self, e):
        """âœ… FIXED: Dodao drag tracking + menu klik"""
        pt = e.position()
        if self.menu_rect.contains(pt):
            self.toggle_playlist_requested.emit()
        elif self.play_rect.contains(pt):
            self.play_clicked.emit()
        elif self.prev_rect.contains(pt):
            self.prev_clicked.emit()
        elif self.next_rect.contains(pt):
            self.next_clicked.emit()
        elif self.progress_rect.contains(pt):
            self.is_dragging_progress = True
            self._handle_progress_drag(pt)
    
    def mouseMoveEvent(self, e):
        """✓ FIXED: Dodao mouse move handler"""
        if self.is_dragging_progress:
            self._handle_progress_drag(e.position())
    
    def mouseReleaseEvent(self, e):
        """✓ FIXED: Dodao mouse release handler"""
        self.is_dragging_progress = False
    
    def _handle_progress_drag(self, pt):
        """Handle progress bar drag"""
        r = (pt.x() - self.progress_rect.x()) / self.progress_rect.width()
        r = max(0, min(1, r))
        self.seek_requested.emit(int(r * self.duration))


class PlayerStyleFactory:
    """Factory za kreiranje stilova."""
    STYLES = {
        "Modern": ModernStyle,
        "Vinyl Player": VinylStyle,
        "Wave Form": WaveformStyle,
        "Minimal Zen": MinimalZenStyle,
    }
    
    @classmethod
    def get_style_names(cls):
        return list(cls.STYLES.keys())
    
    @classmethod
    def create_style(cls, name, parent=None, theme_colors=None):
        style_class = cls.STYLES.get(name, ModernStyle)
        return style_class(parent, theme_colors)