# -*- coding: utf-8 -*-
"""
Title Bar - Custom frameless title bar sa theme integracijom
ui/widgets/title_bar.py

PRISTUP 1: Minimalistički
- Logo + Naslov
- Minimize + Maximize + Close
- Drag window funkcionalnost
- Dupli klik za maximize/restore
- Automatsko praćenje tema (ThemeManager)
- SVG ikone (SVGIconManager)
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer
from PyQt6.QtGui import QCursor

# Import SVG Icon Manager
try:
    from ui.utils.svg_icon_manager import get_themed_icon, SVGIconManager
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    print('⚠️ SVG Icon Manager not available for TitleBar')


class TitleBar(QWidget):
    """
    Custom title bar widget sa theme-aware dizajnom.
    
    Features:
    - Drag window
    - Double-click to maximize/restore
    - Minimize / Maximize / Close buttons
    - Automatski prati promene tema
    - SVG ikone koje se prilagođavaju boji
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.drag_pos = QPoint()
        
        # Čuvamo normalan geometry za restore nakon maximize
        self._normal_geometry = None
        self._is_maximized = False
        
        # Default theme values (dok se ne učita prava tema)
        self.primary_color = "#667eea"
        self.bg_color = "#0f172a"
        self.text_color = "#ffffff"
        self.is_dark_theme = True
        
        # Setup UI
        self.setFixedHeight(40)
        self.setObjectName("titleBar")
        
        self.setup_ui()
        self.apply_initial_style()
    
    def setup_ui(self):
        """Setup title bar UI elements"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(12)
        
        # ===== LEFT SIDE: Logo + Title =====
        # App icon/logo
        self.logo_label = QLabel("🎵")
        self.logo_label.setObjectName("titleBarLogo")
        self.logo_label.setFixedSize(24, 24)
        layout.addWidget(self.logo_label)
        
        # App title
        self.title_label = QLabel("AudioWave")
        self.title_label.setObjectName("titleBarTitle")
        layout.addWidget(self.title_label)
        
        # Spacer (gurne dugmad na desnu stranu)
        layout.addStretch()
        
        # ===== RIGHT SIDE: Control Buttons =====
        # Minimize button
        self.minimize_btn = QPushButton()
        self.minimize_btn.setObjectName("titleBarMinimize")
        self.minimize_btn.setFixedSize(36, 28)
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.minimize_btn.clicked.connect(self.on_minimize_clicked)
        
        # Maximize button
        self.maximize_btn = QPushButton()
        self.maximize_btn.setObjectName("titleBarMaximize")
        self.maximize_btn.setFixedSize(36, 28)
        self.maximize_btn.setToolTip("Maximize")
        self.maximize_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.maximize_btn.clicked.connect(self.on_maximize_clicked)
        
        # Close button
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("titleBarClose")
        self.close_btn.setFixedSize(36, 28)
        self.close_btn.setToolTip("Close")
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.on_close_clicked)
        
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)
        
        # Set default icons (biće zamenjeni sa themed verzijama)
        self.update_icons()
    
    def update_icons(self):
        """Update button icons based on current theme"""
        if SVG_ICONS_AVAILABLE:
            # Proveri da li minimize ikona postoji, ako ne - dodaj je
            if 'minimize' not in SVGIconManager.ICONS:
                # Dodaj minimize ikonu dinamički
                SVGIconManager.ICONS['minimize'] = '''
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M6 19h12v2H6z" fill="{color}"/>
                    </svg>
                '''
            
            # Dodaj maximize ikone ako ne postoje
            if 'maximize' not in SVGIconManager.ICONS:
                SVGIconManager.ICONS['maximize'] = '''
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <rect x="4" y="4" width="16" height="16" rx="2" ry="2" 
                              fill="none" stroke="{color}" stroke-width="2"/>
                    </svg>
                '''
            
            if 'restore' not in SVGIconManager.ICONS:
                SVGIconManager.ICONS['restore'] = '''
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <rect x="8" y="4" width="12" height="12" rx="1" ry="1" 
                              fill="none" stroke="{color}" stroke-width="2"/>
                        <path d="M4 8v10a2 2 0 0 0 2 2h10" 
                              fill="none" stroke="{color}" stroke-width="2"/>
                    </svg>
                '''
            
            # Minimize icon - svetlo siva
            minimize_color = "#94a3b8" if self.is_dark_theme else "#64748b"
            self.minimize_btn.setIcon(
                get_themed_icon('minimize', minimize_color, self.is_dark_theme, 20)
            )
            self.minimize_btn.setIconSize(QSize(20, 20))
            
            # Maximize/Restore icon - zavisno od stanja
            maximize_color = "#94a3b8" if self.is_dark_theme else "#64748b"
            icon_name = 'restore' if self._is_maximized else 'maximize'
            self.maximize_btn.setIcon(
                get_themed_icon(icon_name, maximize_color, self.is_dark_theme, 16)
            )
            self.maximize_btn.setIconSize(QSize(16, 16))
            self.maximize_btn.setToolTip("Restore" if self._is_maximized else "Maximize")
            
            # Close icon - neutralna boja (hover će biti crven)
            close_color = "#cbd5e1" if self.is_dark_theme else "#64748b"
            self.close_btn.setIcon(
                get_themed_icon('close', close_color, self.is_dark_theme, 18)
            )
            self.close_btn.setIconSize(QSize(18, 18))
        else:
            # Fallback na text
            self.minimize_btn.setText("−")
            self.maximize_btn.setText("□" if not self._is_maximized else "❐")
            self.close_btn.setText("✕")
    
    def update_from_theme(self, theme):
        """
        Update title bar kada se tema promeni.
        Poziva se iz UnifiedPlayerWindow kada ThemeManager emituje theme_changed signal.
        
        Args:
            theme: BaseTheme objekat sa atributima (primary, bg_main, itd)
        """
        # Sačuvaj boje iz teme
        self.primary_color = getattr(theme, 'primary', '#667eea')
        self.bg_color = getattr(theme, 'bg_main', '#0f172a')
        
        # Detektuj da li je dark tema
        from PyQt6.QtGui import QColor
        try:
            bg_qcolor = QColor(self.bg_color)
            self.is_dark_theme = bg_qcolor.lightness() < 128
        except:
            self.is_dark_theme = True
        
        self.text_color = "#ffffff" if self.is_dark_theme else "#1e293b"
        
        # Update ikone sa novim bojama
        self.update_icons()
        
        # Update stylesheet
        self.apply_dynamic_style()
        
        print(f"🎨 [TitleBar] Theme updated: {getattr(theme, 'name', 'Unknown')}")
        print(f"   Primary: {self.primary_color}, BG: {self.bg_color}, Dark: {self.is_dark_theme}")
    
    def apply_initial_style(self):
        """Primeni default stil dok se ne učita tema"""
        self.setStyleSheet(self.get_titlebar_stylesheet())
    
    def apply_dynamic_style(self):
        """Primeni dinamički stil baziran na trenutnoj temi"""
        self.setStyleSheet(self.get_titlebar_stylesheet())
    
    def get_titlebar_stylesheet(self) -> str:
        """
        Generiše stylesheet za title bar baziran na trenutnim bojama.
        
        Returns:
            str: CSS stylesheet
        """
        # Border boja - light verzija primary color-a
        border_color = self.primary_color + "33"  # 20% opacity
        
        # Hover boja za dugmad
        if self.is_dark_theme:
            btn_hover_bg = "rgba(255, 255, 255, 0.1)"
            btn_pressed_bg = "rgba(255, 255, 255, 0.15)"
        else:
            btn_hover_bg = "rgba(0, 0, 0, 0.08)"
            btn_pressed_bg = "rgba(0, 0, 0, 0.12)"
        
        return f"""
            /* ===== TITLE BAR CONTAINER ===== */
            #titleBar {{
                background-color: {self.bg_color};
                border-bottom: 1px solid {border_color};
            }}
            
            /* ===== LOGO ===== */
            #titleBarLogo {{
                font-size: 16px;
            }}
            
            /* ===== TITLE ===== */
            #titleBarTitle {{
                font-size: 13px;
                font-weight: 600;
                color: {self.text_color};
                letter-spacing: 1px;
            }}
            
            /* ===== CONTROL BUTTONS BASE ===== */
            #titleBarMinimize, #titleBarMaximize, #titleBarClose {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            
            /* ===== MINIMIZE BUTTON ===== */
            #titleBarMinimize:hover {{
                background: {btn_hover_bg};
            }}
            
            #titleBarMinimize:pressed {{
                background: {btn_pressed_bg};
            }}
            
            /* ===== MAXIMIZE BUTTON ===== */
            #titleBarMaximize:hover {{
                background: {btn_hover_bg};
            }}
            
            #titleBarMaximize:pressed {{
                background: {btn_pressed_bg};
            }}
            
            /* ===== CLOSE BUTTON ===== */
            #titleBarClose:hover {{
                background: #e81123;  /* Windows-style red */
            }}
            
            #titleBarClose:pressed {{
                background: #c50f1f;  /* Darker red */
            }}
        """
    
    # ===== WINDOW DRAG FUNCTIONALITY =====
    
    def mousePressEvent(self, event):
        """Započni drag window"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Pomeri prozor tokom drag-a"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Ako je prozor maximized, restore pre drag-a
            if self._is_maximized:
                # Restore prozor na poziciju miša
                self._restore_from_maximize_for_drag(event.globalPosition().toPoint())
                return
            
            # Izračunaj koliko se miš pomerio
            delta = event.globalPosition().toPoint() - self.drag_pos
            
            # Pomeri parent window
            self.parent.move(self.parent.pos() + delta)
            
            # Update drag poziciju
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()
    
    def _restore_from_maximize_for_drag(self, mouse_pos):
        """
        Restore prozor iz maximized stanja za drag.
        Pozicionira prozor tako da je title bar pod kursorom.
        """
        if self._normal_geometry and self._is_maximized:
            # Izračunaj relativnu poziciju miša u odnosu na širinu title bar-a
            title_bar_width = self.width()
            mouse_x_in_titlebar = mouse_pos.x() - self.parent.x()
            ratio = mouse_x_in_titlebar / title_bar_width if title_bar_width > 0 else 0.5
            ratio = max(0.1, min(0.9, ratio))  # Clamp
            
            # Restore geometry
            normal_width = self._normal_geometry.width()
            normal_height = self._normal_geometry.height()
            
            # Pozicioniraj prozor tako da je kursor na istom relativnom mestu
            new_x = mouse_pos.x() - int(normal_width * ratio)
            new_y = mouse_pos.y() - 20  # Malo iznad kursora
            
            self._is_maximized = False
            self.parent.setGeometry(new_x, new_y, normal_width, normal_height)
            
            # Update ikonu
            self.update_icons()
            
            # Update drag poziciju
            self.drag_pos = mouse_pos
            
            # Notify parent za resize grip
            if hasattr(self.parent, 'on_window_state_changed'):
                self.parent.on_window_state_changed(maximized=False)
    
    def mouseDoubleClickEvent(self, event):
        """
        Double-click za toggle maximize/restore.
        Standardno Windows/macOS ponašanje.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.on_maximize_clicked()
            event.accept()
    
    # ===== BUTTON CALLBACKS =====
    
    def on_minimize_clicked(self):
        """Minimize window"""
        self.parent.showMinimized()
    
    def on_maximize_clicked(self):
        """Toggle maximize/restore window"""
        if self._is_maximized:
            # Restore to normal
            if self._normal_geometry:
                self.parent.setGeometry(self._normal_geometry)
            else:
                self.parent.showNormal()
            self._is_maximized = False
            
            # Notify parent za resize grip
            if hasattr(self.parent, 'on_window_state_changed'):
                self.parent.on_window_state_changed(maximized=False)
        else:
            # Save current geometry before maximize
            self._normal_geometry = self.parent.geometry()
            
            # Maximize
            # Za frameless window, koristimo available geometry umesto showMaximized
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen:
                available = screen.availableGeometry()
                self.parent.setGeometry(available)
            else:
                self.parent.showMaximized()
            
            self._is_maximized = True
            
            # Notify parent za resize grip
            if hasattr(self.parent, 'on_window_state_changed'):
                self.parent.on_window_state_changed(maximized=True)
        
        # Update ikone
        self.update_icons()
    
    def on_close_clicked(self):
        """Close window (sa proper cleanup)"""
        self.parent.close()
    
    def set_title(self, title: str):
        """
        Postavi naslov aplikacije.
        
        Args:
            title: Novi naslov
        """
        self.title_label.setText(title)
    
    def get_title(self) -> str:
        """
        Vrati trenutni naslov.
        
        Returns:
            str: Trenutni naslov
        """
        return self.title_label.text()
    
    def is_window_maximized(self) -> bool:
        """
        Proveri da li je prozor maximized.
        
        Returns:
            bool: True ako je maximized
        """
        return self._is_maximized


# ===== CONVENIENCE FUNKCIJA =====

def create_title_bar(parent_window) -> TitleBar:
    """
    Factory funkcija za kreiranje title bara.
    
    Args:
        parent_window: QMainWindow ili QWidget koji će biti parent
        
    Returns:
        TitleBar: Konfigurisana title bar instanca
    """
    title_bar = TitleBar(parent_window)
    return title_bar