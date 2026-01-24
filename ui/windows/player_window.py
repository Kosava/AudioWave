# -*- coding: utf-8 -*-
"""
Player Window - Sa podrškom za multiple stilove i teme
ui/windows/player_window.py
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

from ui.widgets.player_styles import PlayerStyleFactory, ThemeColors, BasePlayerStyle

# Import SVG Icon Manager
try:
    from ui.utils.svg_icon_manager import get_themed_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    print('⚠️ SVG Icon Manager not available for PlayerWindow')


class PlayerWindow(QWidget):
    """
    Player window sa podrškom za različite vizualne stilove.
    Stilovi se automatski prilagođavaju trenutnoj temi.
    """
    
    play_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    volume_changed = pyqtSignal(int)
    seek_requested = pyqtSignal(int)
    toggle_playlist_requested = pyqtSignal()
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.is_playing = False
        self.player_style = "Modern"
        
        self.position = 0
        self.duration = 1000
        self.volume = 70
        self.song_title = "No track playing"
        self.song_artist = "Unknown Artist"
        
        self.styles = {}
        self.current_style_widget = None
        self.theme_colors = ThemeColors()
        
        self.setup_ui()
        print("🎨 Player Window - Multi-Style + Theme Compatible")
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.style_stack = QStackedWidget()
        
        for style_name in PlayerStyleFactory.get_style_names():
            style_widget = PlayerStyleFactory.create_style(style_name, self, self.theme_colors)
            self._connect_style_signals(style_widget)
            self.styles[style_name] = style_widget
            self.style_stack.addWidget(style_widget)
        
        self.current_style_widget = self.styles.get("Modern")
        if self.current_style_widget:
            self.style_stack.setCurrentWidget(self.current_style_widget)
        
        main_layout.addWidget(self.style_stack)
        
        # NOTE: Hamburger menu je sada deo svakog stila (player_styles.py)
        # i povezan je direktno sa mousePressEvent u svakom stilu
        
        self.setMinimumHeight(270)
    
    def _connect_style_signals(self, style_widget: BasePlayerStyle):
        style_widget.play_clicked.connect(self.play_clicked.emit)
        style_widget.stop_clicked.connect(self.stop_clicked.emit)
        style_widget.next_clicked.connect(self.next_clicked.emit)
        style_widget.prev_clicked.connect(self.prev_clicked.emit)
        style_widget.volume_changed.connect(self._on_volume_changed)
        style_widget.seek_requested.connect(self.seek_requested.emit)
        style_widget.toggle_playlist_requested.connect(self.toggle_playlist_requested.emit)
    
    def _on_volume_changed(self, value: int):
        self.volume = value
        self.volume_changed.emit(value)
        for style in self.styles.values():
            style.set_volume(value)
    
    def set_player_style(self, style_name: str):
        """Promeni vizualni stil plejera."""
        if style_name not in self.styles:
            print(f"⚠ Unknown style: {style_name}, using Modern")
            style_name = "Modern"
        
        self.player_style = style_name
        self.current_style_widget = self.styles[style_name]
        self.style_stack.setCurrentWidget(self.current_style_widget)
        self._sync_state_to_current_style()
        print(f"🎨 PlayerWindow style changed to: {style_name}")
    
    def apply_theme(self, theme_name: str):
        """Primeni boje iz teme na sve stilove."""
        print(f"ðŸŽ¨ PlayerWindow applying theme: {theme_name}")
        
        try:
            from core.themes.theme_registry import ThemeRegistry
            theme = ThemeRegistry.get_theme(theme_name)
            self.theme_colors = ThemeColors.from_theme(theme)
            
            for style in self.styles.values():
                style.set_theme_colors(self.theme_colors)
            
            print(f"âœ… Theme colors applied to all styles")
        except Exception as e:
            print(f"⚠ Could not apply theme colors: {e}")
    
    def set_theme_colors(self, theme_colors: ThemeColors):
        """Direktno postavi boje (koristi se iz UnifiedPlayerWindow)."""
        self.theme_colors = theme_colors
        for style in self.styles.values():
            style.set_theme_colors(theme_colors)
    
    def _sync_state_to_current_style(self):
        if self.current_style_widget:
            self.current_style_widget.set_playing(self.is_playing)
            self.current_style_widget.set_position(self.position)
            self.current_style_widget.set_duration(self.duration)
            self.current_style_widget.set_volume(self.volume)
            self.current_style_widget.set_metadata(self.song_title, self.song_artist)
    
    def on_metadata_changed(self, metadata: dict):
        self.song_title = metadata.get('title', 'Unknown')
        self.song_artist = metadata.get('artist', 'Unknown Artist')
        for style in self.styles.values():
            style.set_metadata(self.song_title, self.song_artist)
    
    def on_playback_started(self):
        self.is_playing = True
        for style in self.styles.values():
            style.set_playing(True)
    
    def on_playback_stopped(self):
        self.is_playing = False
        self.song_title = "No track playing"
        self.song_artist = "Unknown Artist"
        for style in self.styles.values():
            style.set_playing(False)
            style.set_metadata(self.song_title, self.song_artist)
    
    def on_playback_paused(self):
        self.is_playing = False
        for style in self.styles.values():
            style.set_playing(False)
    
    def on_playback_resumed(self):
        self.is_playing = True
        for style in self.styles.values():
            style.set_playing(True)
    
    def update_position(self, position_ms: int):
        self.position = position_ms
        for style in self.styles.values():
            style.set_position(position_ms)
    
    def update_duration(self, duration_ms: int):
        self.duration = duration_ms
        for style in self.styles.values():
            style.set_duration(duration_ms)
    
    @property
    def progress_widget(self):
        """Backward compatibility - stilovi sami renderuju progress"""
        return None
    
    @property
    def volume_widget(self):
        """Backward compatibility - vraća self kao proxy za volume metode"""
        return self  # Vraća self koji ima set_volume i toggle_mute
    
    def set_volume(self, value: int):
        """Set volume - propagira na sve stilove"""
        self.volume = max(0, min(100, value))
        for style in self.styles.values():
            style.set_volume(self.volume)
        self.volume_changed.emit(self.volume)
    
    def get_volume(self) -> int:
        """Get current volume"""
        return self.volume
    
    def toggle_mute(self):
        """Toggle mute - čuva prethodni volume"""
        if not hasattr(self, '_last_volume'):
            self._last_volume = 70
        
        if self.volume > 0:
            self._last_volume = self.volume
            self.set_volume(0)
        else:
            self.set_volume(self._last_volume)