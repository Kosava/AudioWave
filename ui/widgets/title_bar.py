# -*- coding: utf-8 -*-
"""
Title Bar - Wayland Compatible Version
ui/widgets/title_bar.py

WAYLAND FIX:
- Koristi startSystemMove() za drag na Wayland kompozitorima
- Fallback na klasičan drag za X11
- Podržava Niri, Hyprland, KDE Plasma (Wayland), GNOME (Wayland)
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMenu, QApplication
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer
from PyQt6.QtGui import QCursor, QAction
import platform

# Import SVG Icon Manager
try:
    from ui.utils.svg_icon_manager import get_themed_icon, SVGIconManager
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    print('⚠️ SVG Icon Manager not available for TitleBar')


class TitleBar(QWidget):
    """
    Custom title bar sa Wayland podrškom.
    
    Features:
    - ✅ Wayland drag support (startSystemMove)
    - ✅ X11 fallback (manual drag)
    - ✅ Double-click maximize/restore
    - ✅ Context menu (desni klik)
    - ✅ Always on Top
    - ✅ Theme-aware design
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.drag_pos = QPoint()
        
        # Window state
        self._normal_geometry = None
        self._is_maximized = False
        self._is_always_on_top = False
        
        # Drag mode detection
        self._wayland_mode = self._detect_wayland()
        self._drag_started = False
        
        # Theme colors
        self.primary_color = "#667eea"
        self.bg_color = "#0f172a"
        self.text_color = "#ffffff"
        self.is_dark_theme = True
        
        # Setup
        self.setFixedHeight(40)
        self.setObjectName("titleBar")
        
        self.setup_ui()
        self.setup_context_menu()
        self.apply_initial_style()
        
        # Debug info
        if self._wayland_mode:
            print("🌊 [TitleBar] Wayland mode detected - using startSystemMove()")
        else:
            print("🪟 [TitleBar] X11 mode detected - using manual drag")
    
    def _detect_wayland(self) -> bool:
        """
        Detektuj da li je Wayland aktivan.
        
        Returns:
            bool: True ako je Wayland session
        """
        try:
            import os
            
            # Proveri environment varijable
            session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
            wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
            
            # Eksplicitna Wayland detekcija
            if session_type == 'wayland':
                return True
            
            if wayland_display:
                return True
            
            # Proveri Qt platform
            platform_name = QApplication.platformName().lower()
            if 'wayland' in platform_name:
                return True
            
            # Na Linux-u, ako nije eksplicitno X11, pretpostavi Wayland za frameless windows
            if platform.system() == 'Linux':
                # Ako je KDE i WAYLAND_DISPLAY postoji
                if 'KDE' in os.environ.get('XDG_CURRENT_DESKTOP', ''):
                    return wayland_display != ''
                
                # Ako je GNOME i Wayland
                if 'GNOME' in os.environ.get('XDG_CURRENT_DESKTOP', ''):
                    return session_type == 'wayland'
                
                # Za sve ostale WM-ove na Linux-u (Niri, Hyprland, Sway...)
                # Ako postoji WAYLAND_DISPLAY, verovatno je Wayland
                return wayland_display != ''
            
            return False
            
        except Exception as e:
            print(f"⚠️ [TitleBar] Wayland detection failed: {e}")
            return False
    
    def setup_ui(self):
        """Setup title bar UI elements"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(12)
        
        # LEFT SIDE: Logo + Title
        self.logo_label = QLabel("🎵")
        self.logo_label.setObjectName("titleBarLogo")
        self.logo_label.setFixedSize(24, 24)
        layout.addWidget(self.logo_label)
        
        self.title_label = QLabel("AudioWave")
        self.title_label.setObjectName("titleBarTitle")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # RIGHT SIDE: Control Buttons
        self.minimize_btn = QPushButton()
        self.minimize_btn.setObjectName("titleBarMinimize")
        self.minimize_btn.setFixedSize(36, 28)
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.minimize_btn.clicked.connect(self.on_minimize_clicked)
        
        self.maximize_btn = QPushButton()
        self.maximize_btn.setObjectName("titleBarMaximize")
        self.maximize_btn.setFixedSize(36, 28)
        self.maximize_btn.setToolTip("Maximize")
        self.maximize_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.maximize_btn.clicked.connect(self.on_maximize_clicked)
        
        self.close_btn = QPushButton()
        self.close_btn.setObjectName("titleBarClose")
        self.close_btn.setFixedSize(36, 28)
        self.close_btn.setToolTip("Close")
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.clicked.connect(self.on_close_clicked)
        
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)
        
        self.update_icons()
    
    def setup_context_menu(self):
        """Setup context menu (desni klik)"""
        self.context_menu = QMenu(self)
        
        # Always on Top
        self.always_on_top_action = QAction("📌 Always on Top", self)
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.setChecked(self._is_always_on_top)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        self.context_menu.addAction(self.always_on_top_action)
        
        self.context_menu.addSeparator()
        
        # Minimize
        minimize_action = QAction("➖ Minimize", self)
        minimize_action.triggered.connect(self.on_minimize_clicked)
        self.context_menu.addAction(minimize_action)
        
        # Maximize/Restore
        self.maximize_restore_action = QAction("🗖 Maximize", self)
        self.maximize_restore_action.triggered.connect(self.on_maximize_clicked)
        self.context_menu.addAction(self.maximize_restore_action)
        
        self.context_menu.addSeparator()
        
        # Close
        close_action = QAction("✕ Close", self)
        close_action.triggered.connect(self.on_close_clicked)
        self.context_menu.addAction(close_action)
        
        self.update_context_menu_style()
    
    def update_context_menu_style(self):
        """Style context menu based on theme"""
        if self.is_dark_theme:
            menu_bg = "#1e293b"
            menu_text = "#f1f5f9"
            menu_hover = "#334155"
            menu_border = "#475569"
        else:
            menu_bg = "#ffffff"
            menu_text = "#1e293b"
            menu_hover = "#f1f5f9"
            menu_border = "#cbd5e1"
        
        self.context_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {menu_bg};
                color: {menu_text};
                border: 1px solid {menu_border};
                border-radius: 6px;
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {menu_hover};
            }}
            
            QMenu::separator {{
                height: 1px;
                background: {menu_border};
                margin: 4px 8px;
            }}
        """)
    
    def toggle_always_on_top(self, checked):
        """Toggle always on top window flag"""
        self._is_always_on_top = checked
        
        flags = self.parent.windowFlags()
        
        if checked:
            flags |= Qt.WindowType.WindowStaysOnTopHint
            print("📌 Always on Top: ENABLED")
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
            print("📌 Always on Top: DISABLED")
        
        # Save state and re-apply
        was_visible = self.parent.isVisible()
        current_geometry = self.parent.geometry()
        
        self.parent.setWindowFlags(flags)
        
        if was_visible:
            self.parent.setGeometry(current_geometry)
            self.parent.show()
        
        self.always_on_top_action.setChecked(checked)
    
    def is_always_on_top(self) -> bool:
        """Check if window is always on top"""
        return self._is_always_on_top
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click"""
        if self._is_maximized:
            self.maximize_restore_action.setText("🗗 Restore")
        else:
            self.maximize_restore_action.setText("🗖 Maximize")
        
        self.context_menu.exec(event.globalPos())
    
    def update_icons(self):
        """Update button icons based on current theme"""
        if SVG_ICONS_AVAILABLE:
            if 'minimize' not in SVGIconManager.ICONS:
                SVGIconManager.ICONS['minimize'] = '''
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M6 19h12v2H6z" fill="{color}"/>
                    </svg>
                '''
            
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
            
            minimize_color = "#94a3b8" if self.is_dark_theme else "#64748b"
            self.minimize_btn.setIcon(
                get_themed_icon('minimize', minimize_color, self.is_dark_theme, 20)
            )
            self.minimize_btn.setIconSize(QSize(20, 20))
            
            maximize_color = "#94a3b8" if self.is_dark_theme else "#64748b"
            icon_name = 'restore' if self._is_maximized else 'maximize'
            self.maximize_btn.setIcon(
                get_themed_icon(icon_name, maximize_color, self.is_dark_theme, 16)
            )
            self.maximize_btn.setIconSize(QSize(16, 16))
            self.maximize_btn.setToolTip("Restore" if self._is_maximized else "Maximize")
            
            close_color = "#cbd5e1" if self.is_dark_theme else "#64748b"
            self.close_btn.setIcon(
                get_themed_icon('close', close_color, self.is_dark_theme, 18)
            )
            self.close_btn.setIconSize(QSize(18, 18))
        else:
            self.minimize_btn.setText("−")
            self.maximize_btn.setText("□" if not self._is_maximized else "❐")
            self.close_btn.setText("✕")
    
    def update_from_theme(self, theme):
        """Update title bar when theme changes"""
        self.primary_color = getattr(theme, 'primary', '#667eea')
        self.bg_color = getattr(theme, 'bg_main', '#0f172a')
        
        from PyQt6.QtGui import QColor
        try:
            bg_qcolor = QColor(self.bg_color)
            self.is_dark_theme = bg_qcolor.lightness() < 128
        except:
            self.is_dark_theme = True
        
        self.text_color = "#ffffff" if self.is_dark_theme else "#1e293b"
        
        self.update_icons()
        self.apply_dynamic_style()
        self.update_context_menu_style()
        
        print(f"🎨 [TitleBar] Theme updated: {getattr(theme, 'name', 'Unknown')}")
    
    def apply_initial_style(self):
        """Apply initial style"""
        self.setStyleSheet(self.get_titlebar_stylesheet())
    
    def apply_dynamic_style(self):
        """Apply dynamic style based on current theme"""
        self.setStyleSheet(self.get_titlebar_stylesheet())
    
    def get_titlebar_stylesheet(self) -> str:
        """Generate stylesheet based on current colors"""
        border_color = self.primary_color + "33"
        
        if self.is_dark_theme:
            btn_hover_bg = "rgba(255, 255, 255, 0.1)"
            btn_pressed_bg = "rgba(255, 255, 255, 0.15)"
        else:
            btn_hover_bg = "rgba(0, 0, 0, 0.08)"
            btn_pressed_bg = "rgba(0, 0, 0, 0.12)"
        
        return f"""
            #titleBar {{
                background-color: {self.bg_color};
                border-bottom: 1px solid {border_color};
            }}
            
            #titleBarLogo {{
                font-size: 16px;
            }}
            
            #titleBarTitle {{
                font-size: 13px;
                font-weight: 600;
                color: {self.text_color};
                letter-spacing: 1px;
            }}
            
            #titleBarMinimize, #titleBarMaximize, #titleBarClose {{
                background: transparent;
                border: none;
                border-radius: 4px;
            }}
            
            #titleBarMinimize:hover {{
                background: {btn_hover_bg};
            }}
            
            #titleBarMinimize:pressed {{
                background: {btn_pressed_bg};
            }}
            
            #titleBarMaximize:hover {{
                background: {btn_hover_bg};
            }}
            
            #titleBarMaximize:pressed {{
                background: {btn_pressed_bg};
            }}
            
            #titleBarClose:hover {{
                background: #e81123;
            }}
            
            #titleBarClose:pressed {{
                background: #c50f1f;
            }}
        """
    
    # ===== WINDOW DRAG - WAYLAND COMPATIBLE =====
    
    def mousePressEvent(self, event):
        """Handle mouse press - start drag preparation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            self._drag_started = False
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move - initiate drag"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Proveri da li je prozor maximized
            if self._is_maximized:
                self._restore_from_maximize_for_drag(event.globalPosition().toPoint())
                return
            
            # WAYLAND MODE: Koristi startSystemMove()
            if self._wayland_mode and not self._drag_started:
                self._drag_started = True
                
                # startSystemMove() kaže window manager-u da pomeri prozor
                # Ovo radi na Wayland kompozitorima (Niri, Hyprland, KDE Wayland, GNOME Wayland, Sway)
                if hasattr(self.parent.windowHandle(), 'startSystemMove'):
                    print("🌊 [TitleBar] Using Wayland startSystemMove()")
                    self.parent.windowHandle().startSystemMove()
                else:
                    # Fallback na manual drag
                    print("⚠️ [TitleBar] startSystemMove() not available, using manual drag")
                    self._manual_drag(event)
                
                event.accept()
                return
            
            # X11 MODE ili fallback: Manual drag
            if not self._wayland_mode:
                self._manual_drag(event)
            
            event.accept()
    
    def _manual_drag(self, event):
        """Manual window drag (X11 fallback)"""
        delta = event.globalPosition().toPoint() - self.drag_pos
        self.parent.move(self.parent.pos() + delta)
        self.drag_pos = event.globalPosition().toPoint()
    
    def _restore_from_maximize_for_drag(self, mouse_pos):
        """Restore window from maximized state for drag"""
        if self._normal_geometry and self._is_maximized:
            title_bar_width = self.width()
            mouse_x_in_titlebar = mouse_pos.x() - self.parent.x()
            ratio = mouse_x_in_titlebar / title_bar_width if title_bar_width > 0 else 0.5
            ratio = max(0.1, min(0.9, ratio))
            
            normal_width = self._normal_geometry.width()
            normal_height = self._normal_geometry.height()
            
            new_x = mouse_pos.x() - int(normal_width * ratio)
            new_y = mouse_pos.y() - 20
            
            self._is_maximized = False
            self.parent.setGeometry(new_x, new_y, normal_width, normal_height)
            
            self.update_icons()
            self.drag_pos = mouse_pos
            self._drag_started = False
            
            if hasattr(self.parent, 'on_window_state_changed'):
                self.parent.on_window_state_changed(maximized=False)
    
    def mouseDoubleClickEvent(self, event):
        """Double-click to maximize/restore"""
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
            if self._normal_geometry:
                self.parent.setGeometry(self._normal_geometry)
            else:
                self.parent.showNormal()
            self._is_maximized = False
            
            if hasattr(self.parent, 'on_window_state_changed'):
                self.parent.on_window_state_changed(maximized=False)
        else:
            self._normal_geometry = self.parent.geometry()
            
            screen = QApplication.primaryScreen()
            if screen:
                available = screen.availableGeometry()
                self.parent.setGeometry(available)
            else:
                self.parent.showMaximized()
            
            self._is_maximized = True
            
            if hasattr(self.parent, 'on_window_state_changed'):
                self.parent.on_window_state_changed(maximized=True)
        
        self.update_icons()
    
    def on_close_clicked(self):
        """Close window"""
        self.parent.close()
    
    def set_title(self, title: str):
        """Set window title"""
        self.title_label.setText(title)
    
    def get_title(self) -> str:
        """Get current title"""
        return self.title_label.text()
    
    def is_window_maximized(self) -> bool:
        """Check if window is maximized"""
        return self._is_maximized


# ===== FACTORY FUNCTION =====

def create_title_bar(parent_window) -> TitleBar:
    """
    Create title bar instance.
    
    Args:
        parent_window: Parent window
        
    Returns:
        TitleBar: Configured title bar
    """
    title_bar = TitleBar(parent_window)
    return title_bar
