# -*- coding: utf-8 -*-
"""
Unified Player Window - SA CUSTOM TITLE BAR (Pristup 1)
ui/windows/unified_player_window.py

AudioWave - Modern desktop music player
Version 0.3.0
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication, QSizeGrip, QMessageBox
from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QIcon
import traceback
import sys

# âœ… ISPRAVNI IMPORTI
try:
    from ui.panels.playlist_panel import PlaylistPanel
except ImportError:
    from ..panels.playlist_panel import PlaylistPanel

try:
    from ui.handlers.keyboard_handler import KeyboardHandler
except ImportError:
    class KeyboardHandler:
        def __init__(self, parent): pass
        def handle_key_event(self, event): return False

try:
    from core.playback_controller import PlaybackController
except ImportError:
    class PlaybackController:
        def __init__(self, app, window): pass
        def on_play_clicked(self): pass
        def on_stop_clicked(self): pass
        def on_next_clicked(self): pass
        def on_prev_clicked(self): pass
        def on_seek_requested(self, pos): pass
        def on_track_ended(self): pass

try:
    from ui.windows.player_window import PlayerWindow
except ImportError:
    class PlayerWindow(QWidget):
        def __init__(self, app):
            super().__init__()
            from PyQt6.QtCore import pyqtSignal
            self.play_clicked = pyqtSignal()
            self.stop_clicked = pyqtSignal()
            self.next_clicked = pyqtSignal()
            self.prev_clicked = pyqtSignal()
            self.volume_changed = pyqtSignal(int)
            self.toggle_playlist_requested = pyqtSignal()
            self.seek_requested = pyqtSignal(int)

try:
    from core.config import Config
except ImportError:
    class Config:
        def __init__(self): pass
        def get_tray_settings(self): return {}
        def set_tray_settings(self, settings): pass
        def get(self, key, default=None): return default
        def set(self, key, value): pass

try:
    from ui.tray.tray_icon import TrayIcon
except ImportError:
    from PyQt6.QtCore import pyqtSignal, QObject
    class TrayIcon(QObject):
        def __init__(self, app, window): 
            super().__init__()
            self.show_requested = pyqtSignal()
            self.hide_requested = pyqtSignal()
            self.quit_requested = pyqtSignal()
            self.play_pause_requested = pyqtSignal()
            self.next_requested = pyqtSignal()
            self.prev_requested = pyqtSignal()
            self.stop_requested = pyqtSignal()
        def show(self): pass
        def hide(self): pass
        def reload_from_settings(self): pass
        def cleanup(self): pass

try:
    from ui.tray.notifications import TrayNotifications
except ImportError:
    class TrayNotifications:
        def __init__(self, tray_icon=None): pass
        def running_in_tray(self): pass
        def window_restored(self): pass
        def minimized_to_tray(self): pass
        def track_changed(self, track_info): pass
        def playback_state_changed(self, is_playing): pass

# ðŸŽ¨ Import custom title bar
try:
    from ui.widgets.title_bar import TitleBar
    TITLE_BAR_AVAILABLE = True
except ImportError:
    TITLE_BAR_AVAILABLE = False
    print('âš ï¸ Custom TitleBar not available, using system title bar')


class UnifiedPlayerWindow(QMainWindow):
    """Glavni prozor - SA CUSTOM TITLE BAR"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.engine = app.engine
        
        # âœ… Track last highlighted file to prevent duplicates
        self._last_highlighted_file = None
        
        # âœ… Auto-play enabled by default
        self.auto_play_enabled = True
        
        # System Tray
        self.config = Config()
        self.tray_settings = self.config.get_tray_settings()
        self.tray_icon = TrayIcon(app, self)
        self.tray_notifications = TrayNotifications(self.tray_icon)
        
        # ðŸŽ¨ Proveri da li koristimo custom title bar
        self.use_custom_titlebar = TITLE_BAR_AVAILABLE
        
        # ðŸŽ¨ Ako koristimo custom title bar, iskljuÄi sistemski
        if self.use_custom_titlebar:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.Window
            )
            print("ðŸŽ¨ [UnifiedPlayerWindow] Custom title bar enabled")
        
        # Window setup
        self.setWindowTitle("AudioWave")
        self.setGeometry(100, 100, 550, 650)
        self.setMinimumSize(500, 450)
        
        try:
            self.setWindowIcon(QIcon("resources/icons/audiowave_color.png"))
        except:
            pass
        
        # Components
        self.player_window = PlayerWindow(app)
        self.playlist_panel = PlaylistPanel(app)
        self.playback_controller = PlaybackController(app, self)
        self.keyboard_handler = KeyboardHandler(self)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ðŸŽ¨ Dodaj custom title bar ako je dostupan
        if self.use_custom_titlebar:
            self.title_bar = TitleBar(self)
            layout.addWidget(self.title_bar)
            print("ðŸŽ¨ [UnifiedPlayerWindow] Title bar widget added to layout")
        
        # Dodaj player i playlist
        layout.addWidget(self.player_window)
        layout.addWidget(self.playlist_panel, 1)
        
        # âœ… FIX: Resize grip - saÄuvaj referencu na central widget
        self._central_widget = central_widget
        self.size_grip = None
        self.add_resize_grip()
        
        # Setup
        self.setup_connections()
        self.setup_tray_connections()
        
        # ðŸŽ¨ Setup theme connections
        self.setup_theme_connections()
        
        # Keyboard
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        QApplication.instance().installEventFilter(self)
        
        # Focus
        QTimer.singleShot(50, self.focus_playlist)
        
        # Show tray icon
        if self.tray_settings.get("enabled", True):
            if hasattr(self.tray_icon, 'show'):
                self.tray_icon.show()
        
        # ðŸŽ¨ Primeni inicijalnu temu na title bar
        if self.use_custom_titlebar:
            QTimer.singleShot(100, self.apply_initial_theme_to_titlebar)
        
        # ✅ Load saved window geometry
        QTimer.singleShot(150, self.load_window_geometry)
    
    def add_resize_grip(self):
        """
        Dodaj resize grip u donji desni ugao.
        âœ… FIX: Pravilno kreiranje i pozicioniranje resize grip-a
        """
        if self.size_grip is not None:
            # VeÄ‡ postoji, samo osiguraj da je vidljiv
            self.size_grip.show()
            self._update_resize_grip_position()
            return
        
        # Kreiraj novi size grip
        self.size_grip = QSizeGrip(self._central_widget)
        self.size_grip.setObjectName("resizeGrip")
        self.size_grip.setFixedSize(16, 16)
        
        # Stilizuj ga da bude diskretniji
        self.size_grip.setStyleSheet("""
            QSizeGrip {
                background: transparent;
                width: 16px;
                height: 16px;
            }
        """)
        
        # Pozicioniraj
        self._update_resize_grip_position()
        
        # PrikaÅ¾i
        self.size_grip.show()
        self.size_grip.raise_()  # Osiguraj da je iznad drugih widgeta
        
        print("âœ… [UnifiedPlayerWindow] Resize grip created and shown")
    
    def _update_resize_grip_position(self):
        """Update poziciju resize grip-a"""
        if self.size_grip and self._central_widget:
            grip_size = self.size_grip.size()
            self.size_grip.move(
                self._central_widget.width() - grip_size.width(),
                self._central_widget.height() - grip_size.height()
            )
    
    def resizeEvent(self, event):
        """
        Update resize grip position kada se prozor resize-uje.
        âœ… FIX: Sigurnije aÅ¾uriranje pozicije
        """
        super().resizeEvent(event)
        self._update_resize_grip_position()
    
    def showEvent(self, event):
        """
        Handle show event - osiguraj da je resize grip vidljiv.
        âœ… FIX: Dodato za reÅ¡avanje problema sa resize grip-om
        """
        super().showEvent(event)
        
        # OdloÅ¾eno aÅ¾uriranje resize grip-a
        QTimer.singleShot(50, self._ensure_resize_grip_visible)
    
    def _ensure_resize_grip_visible(self):
        """
        Osiguraj da je resize grip vidljiv i pravilno pozicioniran.
        âœ… FIX: Dodatna metoda za osiguravanje vidljivosti
        """
        if self.size_grip:
            # Proveri da li je maximized
            is_maximized = False
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                is_maximized = self.title_bar.is_window_maximized()
            
            if is_maximized:
                self.size_grip.hide()
            else:
                self.size_grip.show()
                self.size_grip.raise_()
                self._update_resize_grip_position()
    
    def on_window_state_changed(self, maximized: bool):
        """
        Callback kada se stanje prozora promeni (maximize/restore).
        Poziva se iz TitleBar-a.
        
        Args:
            maximized: True ako je prozor maximized
        """
        if self.size_grip:
            if maximized:
                self.size_grip.hide()
                print("ðŸ“² [UnifiedPlayerWindow] Resize grip hidden (maximized)")
            else:
                self.size_grip.show()
                self.size_grip.raise_()
                self._update_resize_grip_position()
                print("ðŸ“² [UnifiedPlayerWindow] Resize grip shown (restored)")
    
    def focus_playlist(self):
        """Focus playlist"""
        if hasattr(self.playlist_panel, 'file_list'):
            self.playlist_panel.file_list.setFocus()
    
    def setup_connections(self):
        """Setup all connections"""
        # Player â†” Controller
        self.player_window.play_clicked.connect(self.playback_controller.on_play_clicked)
        self.player_window.stop_clicked.connect(self.playback_controller.on_stop_clicked)
        self.player_window.next_clicked.connect(self.playback_controller.on_next_clicked)
        self.player_window.prev_clicked.connect(self.playback_controller.on_prev_clicked)
        self.player_window.volume_changed.connect(self.engine.set_volume)
        self.player_window.toggle_playlist_requested.connect(self.toggle_playlist_visibility)
        self.player_window.seek_requested.connect(self.playback_controller.on_seek_requested)
        
        # Playlist â†” Controller
        # âœ… ONLY this path triggers highlight on double-click
        self.playlist_panel.play_requested.connect(self.on_playlist_play_requested)
        self.playlist_panel.settings_requested.connect(self.open_settings)
        self.playlist_panel.playlist_changed.connect(self.on_playlist_changed)
        
        # Engine â†” Player (UI updates only, NOT highlight)
        if hasattr(self.engine, 'metadata_changed'):
            self.engine.metadata_changed.connect(self.player_window.on_metadata_changed)
        if hasattr(self.engine, 'position_changed'):
            self.engine.position_changed.connect(self.player_window.update_position)
        if hasattr(self.engine, 'duration_changed'):
            self.engine.duration_changed.connect(self.player_window.update_duration)
        if hasattr(self.engine, 'playback_started'):
            self.engine.playback_started.connect(self.on_playback_started)
        if hasattr(self.engine, 'playback_stopped'):
            self.engine.playback_stopped.connect(self.on_playback_stopped)
        if hasattr(self.engine, 'track_ended'):
            self.engine.track_ended.connect(self.playback_controller.on_track_ended)
    
    def setup_theme_connections(self):
        """
        ðŸŽ¨ Setup theme manager connections
        Povezuje ThemeManager signale sa title bar update-om
        """
        if hasattr(self.app, 'theme_manager'):
            # PoveÅ¾i theme_changed signal sa naÅ¡om metodom
            self.app.theme_manager.theme_changed.connect(self.on_theme_changed)
            print("ðŸŽ¨ [UnifiedPlayerWindow] Theme manager connected")
        else:
            print("âš ï¸ [UnifiedPlayerWindow] Theme manager not found in app")
    
    def apply_initial_theme_to_titlebar(self):
        """
        ðŸŽ¨ Primeni inicijalnu temu na title bar
        Poziva se nakon Å¡to je window kreiran
        """
        if not self.use_custom_titlebar:
            return
        
        if hasattr(self.app, 'theme_manager'):
            current_theme_name = self.app.theme_manager.current_theme
            theme = self.app.theme_manager.registry.get_theme(current_theme_name)
            
            if hasattr(self, 'title_bar'):
                self.title_bar.update_from_theme(theme)
                print(f"ðŸŽ¨ [UnifiedPlayerWindow] Initial theme applied to title bar: {current_theme_name}")
    
    def on_theme_changed(self, theme_name: str):
        """
        ðŸŽ¨ Callback kada se tema promeni
        
        Args:
            theme_name: Ime nove teme
        """
        if not self.use_custom_titlebar:
            return
        
        try:
            # Dobij theme objekat iz ThemeRegistry
            theme = self.app.theme_manager.registry.get_theme(theme_name)
            
            # Update title bar sa novom temom
            if hasattr(self, 'title_bar'):
                self.title_bar.update_from_theme(theme)
                print(f"ðŸŽ¨ [UnifiedPlayerWindow] Title bar updated with theme: {theme_name}")
            
        except Exception as e:
            print(f"âŒ [UnifiedPlayerWindow] Error updating title bar theme: {e}")
            traceback.print_exc()
    
    def on_playlist_play_requested(self, file_path):
        """Handle play request from playlist - SINGLE SOURCE OF TRUTH"""
        try:
            # âœ… Check if this is a different file before highlighting
            if self._last_highlighted_file != file_path:
                # Highlight in playlist
                if hasattr(self.playlist_panel, 'highlight_file'):
                    self.playlist_panel.highlight_file(file_path)
                self._last_highlighted_file = file_path
            
            # Start playback - koristi direktno engine.play_file()
            if hasattr(self.engine, 'play_file'):
                self.engine.play_file(file_path)
            else:
                print(f"âš ï¸ Engine doesn't have play_file method!")
                
        except Exception as e:
            print(f"Error playing file: {e}")
            traceback.print_exc()
    
    def on_playlist_changed(self, playlist_name):
        """Handle playlist change"""
        try:
            if hasattr(self, 'playback_controller'):
                if hasattr(self.playback_controller, 'on_playlist_changed'):
                    self.playback_controller.on_playlist_changed(playlist_name)
        except Exception as e:
            print(f"Error handling playlist change: {e}")
    
    def on_playback_started(self):
        """Handle playback started event"""
        try:
            if hasattr(self.player_window, 'on_playback_started'):
                self.player_window.on_playback_started()
            
            # Notify tray
            if hasattr(self.tray_notifications, 'playback_state_changed'):
                self.tray_notifications.playback_state_changed(True)
        except Exception as e:
            print(f"Error in playback started: {e}")
    
    def on_playback_stopped(self):
        """Handle playback stopped event"""
        try:
            if hasattr(self.player_window, 'on_playback_stopped'):
                self.player_window.on_playback_stopped()
            
            # Notify tray
            if hasattr(self.tray_notifications, 'playback_state_changed'):
                self.tray_notifications.playback_state_changed(False)
        except Exception as e:
            print(f"Error in playback stopped: {e}")
    
    def eventFilter(self, obj, event):
        """Handle global keyboard events"""
        if event.type() == QEvent.Type.KeyPress:
            if self.keyboard_handler.handle_key_event(event):
                return True
        return super().eventFilter(obj, event)
    
    def changeEvent(self, event):
        """Handle window state changes"""
        super().changeEvent(event)
        
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and self.tray_settings.get("minimize_to_tray", False):
                QTimer.singleShot(0, self.minimize_to_tray)
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.tray_settings.get("close_to_tray", False):
            event.ignore()
            self.hide()
            if hasattr(self.tray_notifications, 'running_in_tray'):
                self.tray_notifications.running_in_tray()
            return
        
        if self.engine and hasattr(self.engine, 'stop'):
            try:
                self.engine.stop()
            except:
                pass
        
        if hasattr(self.app, 'playlist_manager'):
            try:
                self.app.playlist_manager.save_playlists()
            except:
                pass
        
        self.save_window_state()
        
        if hasattr(self, "tray_icon"):
            try:
                if hasattr(self.tray_icon, 'cleanup'):
                    self.tray_icon.cleanup()
            except:
                pass
        
        event.accept()
    
    def save_window_state(self):
        """Save window state"""
        try:
            # SaÄuvaj normalan geometry (ne maximized)
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                if self.title_bar.is_window_maximized():
                    # Ako je maximized, saÄuvaj normal geometry iz title bar-a
                    if self.title_bar._normal_geometry:
                        geom = self.title_bar._normal_geometry
                        self.config.set("window_geometry", {
                            "x": geom.x(),
                            "y": geom.y(),
                            "width": geom.width(),
                            "height": geom.height()
                        })
                    self.config.set("window_maximized", True)
                else:
                    self.config.set("window_geometry", {
                        "x": self.x(),
                        "y": self.y(),
                        "width": self.width(),
                        "height": self.height()
                    })
                    self.config.set("window_maximized", False)
            else:
                self.config.set("window_geometry", {
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.width(),
                    "height": self.height()
                })
                self.config.set("window_maximized", self.isMaximized())
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def restore_window_state(self):
        """Restore window state"""
        try:
            geometry = self.config.get("window_geometry")
            maximized = self.config.get("window_maximized", False)
            
            if geometry:
                self.setGeometry(
                    geometry.get("x", 100),
                    geometry.get("y", 100),
                    geometry.get("width", 550),
                    geometry.get("height", 650)
                )
            
            if maximized:
                if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                    # Koristi title bar maximize
                    QTimer.singleShot(100, self.title_bar.on_maximize_clicked)
                else:
                    self.showMaximized()
            else:
                self.showNormal()
        except Exception as e:
            print(f"Error restoring state: {e}")
    
    def show_message(self, message, duration=3000):
        """Show message"""
        if hasattr(self.playlist_panel, 'show_message'):
            self.playlist_panel.show_message(message, duration)
        elif hasattr(self.player_window, 'show_message'):
            self.player_window.show_message(message, duration)
        else:
            print(f"{message}")
    
    def toggle_playlist_visibility(self):
        """Toggle playlist visibility (mini mod)"""
        if self.playlist_panel.isVisible():
            # Sakrij playlist - mini mod
            self.playlist_panel.hide()
            
            # IzraÄunaj novu visinu (title bar + player)
            title_bar_height = 40 if self.use_custom_titlebar else 0
            new_height = self.player_window.height() + title_bar_height
            
            self.resize(self.width(), new_height)
            self.show_message("Playlist hidden (F2 to show)", 2000)
            
            # âœ… FIX: Osiguraj da je resize grip vidljiv i pozicioniran
            QTimer.singleShot(50, self._ensure_resize_grip_visible)
        else:
            # PrikaÅ¾i playlist - normalan mod
            self.playlist_panel.show()
            self.resize(self.width(), 650)
            self.show_message("Playlist visible (F2 to hide)", 2000)
            
            # âœ… FIX: Osiguraj da je resize grip vidljiv i pozicioniran
            QTimer.singleShot(50, self._ensure_resize_grip_visible)
    
    def open_settings(self):
        """Open settings"""
        try:
            from ui.windows.settings_dialog import SettingsDialog
            settings_dialog = SettingsDialog(self)
            settings_dialog.settings_saved.connect(self.on_settings_saved)
            settings_dialog.exec()  # ✅ FIX: exec() umesto show_dialog()
        except ImportError:
            try:
                from ui.dialogs.settings_dialog import SettingsDialog
                settings_dialog = SettingsDialog(self)
                settings_dialog.exec()  # ✅ FIX: exec() umesto show()
            except:
                self.show_message("Settings dialog not found")
        except Exception as e:
            print(f"Error opening settings: {e}")
            self.show_message("Could not open settings")
    
    def open_about(self):
        """Open About dialog (preÄica F1)"""
        try:
            from ui.windows.settings_dialog import SettingsDialog
            settings_dialog = SettingsDialog(self)
            settings_dialog.settings_saved.connect(self.on_settings_saved)
            settings_dialog.show_about_tab()
        except Exception as e:
            print(f"Error opening about: {e}")
            self.show_message("Could not open About")
    
    def on_settings_saved(self, settings):
        """Handle saved settings"""
        try:
            # Tray settings
            if isinstance(settings, dict) and "tray" in settings:
                self.config.set_tray_settings(settings["tray"])
                self.tray_settings = settings["tray"]
                
                if hasattr(self.tray_icon, 'reload_from_settings'):
                    self.tray_icon.reload_from_settings()
                
                tray_enabled = settings["tray"].get("enabled", True)
                if tray_enabled:
                    if hasattr(self.tray_icon, 'show'):
                        self.tray_icon.show()
                else:
                    if hasattr(self.tray_icon, 'hide'):
                        self.tray_icon.hide()
            
            # Audio settings
            if isinstance(settings, dict) and 'audio' in settings and 'default_volume' in settings['audio']:
                volume = settings['audio']['default_volume']
                self.engine.set_volume(volume)
                if hasattr(self.player_window, 'volume_widget'):
                    self.player_window.volume_widget.set_volume(volume)
                self.show_message(f"Volume set to {volume}")
            
            # Theme settings
            if isinstance(settings, dict) and 'appearance' in settings and 'theme' in settings['appearance']:
                theme = settings['appearance']['theme']
                self.apply_theme(theme)
            
            self.show_message("Settings applied")
        except Exception as e:
            print(f"Error applying settings: {e}")
    
    def apply_theme(self, theme_name):
        """Apply theme to all components"""
        try:
            print(f"🎨 [UnifiedPlayerWindow] Applying theme: {theme_name}")
            
            # ✅ Koristi ThemeManager iz app ako postoji
            if hasattr(self.app, 'theme_manager') and self.app.theme_manager:
                theme_manager = self.app.theme_manager
                # Primeni na glavni prozor (ovo će primeniti stylesheet)
                theme_manager.apply_theme(self, theme_name)
                print(f"✅ Theme applied via ThemeManager")
            else:
                # Fallback - direktno primeni iz ThemeRegistry
                try:
                    from core.themes.theme_registry import ThemeRegistry
                    theme = ThemeRegistry.get_theme(theme_name)
                    if theme:
                        theme_data = theme.get_theme_data()
                        self.setStyleSheet(theme_data["stylesheet"])
                        print(f"✅ Theme applied via ThemeRegistry fallback")
                except Exception as e:
                    print(f"⚠️ ThemeRegistry fallback failed: {e}")
            
            # ✅ Primeni na player_window (boje za stilove)
            if hasattr(self.player_window, 'apply_theme'):
                self.player_window.apply_theme(theme_name)
            
            # ✅ Primeni na playlist_panel (ikone i boje)
            if hasattr(self.playlist_panel, 'apply_theme'):
                self.playlist_panel.apply_theme(theme_name)
            
            # ✅ Primeni na title bar ako postoji
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                try:
                    from core.themes.theme_registry import ThemeRegistry
                    theme = ThemeRegistry.get_theme(theme_name)
                    if theme and hasattr(self.title_bar, 'update_from_theme'):
                        self.title_bar.update_from_theme(theme)
                except Exception as e:
                    print(f"⚠️ Could not update title bar theme: {e}")
            
            # ✅ Force repaint
            self.repaint()
            QApplication.processEvents()
            
            self.show_message(f"Theme: {theme_name}", 2000)
            
        except Exception as e:
            print(f"❌ Error applying theme: {e}")
            import traceback
            traceback.print_exc()
    
    def quit_application(self):
        """Quit application"""
        self.tray_settings["close_to_tray"] = False
        self.close()
    
    def setup_tray_connections(self):
        """Setup tray connections"""
        try:
            if hasattr(self.tray_icon, 'show_requested'):
                self.tray_icon.show_requested.connect(self.on_tray_show)
            if hasattr(self.tray_icon, 'hide_requested'):
                self.tray_icon.hide_requested.connect(self.on_tray_hide)
            if hasattr(self.tray_icon, 'quit_requested'):
                self.tray_icon.quit_requested.connect(self.on_tray_quit)
            if hasattr(self.tray_icon, 'play_pause_requested'):
                self.tray_icon.play_pause_requested.connect(self.playback_controller.on_play_clicked)
            if hasattr(self.tray_icon, 'next_requested'):
                self.tray_icon.next_requested.connect(self.playback_controller.on_next_clicked)
            if hasattr(self.tray_icon, 'prev_requested'):
                self.tray_icon.prev_requested.connect(self.playback_controller.on_prev_clicked)
            if hasattr(self.tray_icon, 'stop_requested'):
                self.tray_icon.stop_requested.connect(self.playback_controller.on_stop_clicked)
        except Exception as e:
            print(f"Error setting up tray: {e}")
    
    def on_tray_show(self):
        """Show from tray"""
        self.show_from_tray()
    
    def on_tray_hide(self):
        """Hide to tray"""
        self.minimize_to_tray()
    
    def on_tray_quit(self):
        """Quit from tray"""
        self.quit_application()
    
    def show_from_tray(self):
        """Show window from tray"""
        if self.isHidden() or self.isMinimized():
            self.showNormal()
            self.activateWindow()
            self.raise_()
            QTimer.singleShot(50, self.focus_playlist)
            
            # âœ… FIX: Osiguraj resize grip nakon show
            QTimer.singleShot(100, self._ensure_resize_grip_visible)
            
            if hasattr(self.tray_notifications, 'window_restored'):
                self.tray_notifications.window_restored()
        else:
            self.activateWindow()
            self.raise_()
            self.focus_playlist()
    
    def minimize_to_tray(self):
        """Minimize to tray"""
        if self.tray_settings.get("minimize_to_tray", True):
            self.hide()
            if hasattr(self.tray_notifications, 'minimized_to_tray'):
                self.tray_notifications.minimized_to_tray()
        else:
            self.showMinimized()
    # ===== WINDOW GEOMETRY PERSISTENCE =====
    
    def load_window_geometry(self):
        """Load saved window geometry and state"""
        try:
            # Load geometry
            geometry = self.config.get_window_geometry()
            if geometry:
                self.setGeometry(
                    geometry['x'],
                    geometry['y'],
                    geometry['width'],
                    geometry['height']
                )
                print(f"📐 Loaded geometry: {geometry['width']}x{geometry['height']}")
            
            # Load maximized state
            if self.config.is_window_maximized():
                self.showMaximized()
                if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                    self.title_bar._is_maximized = True
                    self.title_bar.update_icons()
                print("🔲 Restored as maximized")
            
            # Load always on top
            if self.config.is_always_on_top():
                flags = self.windowFlags()
                flags |= Qt.WindowType.WindowStaysOnTopHint
                self.setWindowFlags(flags)
                self.show()
                
                if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                    self.title_bar._is_always_on_top = True
                    if hasattr(self.title_bar, 'always_on_top_action'):
                        self.title_bar.always_on_top_action.setChecked(True)
                
                print("📌 Always on top restored")
        
        except Exception as e:
            print(f"⚠️ Error loading geometry: {e}")
    
    def save_window_geometry(self):
        """Save window geometry and state"""
        try:
            # Get maximized state
            is_maximized = self.isMaximized()
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                is_maximized = self.title_bar.is_window_maximized()
            
            # Save geometry (only if not maximized)
            if not is_maximized:
                geom = self.geometry()
                self.config.set_window_geometry({
                    'x': geom.x(),
                    'y': geom.y(),
                    'width': geom.width(),
                    'height': geom.height()
                }, auto_save=False)
                print(f"💾 Saved geometry: {geom.width()}x{geom.height()}")
            
            # Save maximized state
            self.config.set_window_maximized(is_maximized, auto_save=False)
            
            # Save always on top
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                always_on_top = self.title_bar.is_always_on_top()
                self.config.set_always_on_top(always_on_top, auto_save=False)
            
            # Save all
            self.config.save()
            print("✅ Window state saved")
        
        except Exception as e:
            print(f"⚠️ Error saving geometry: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        print("👋 Closing window...")
        
        # Save window state
        self.save_window_geometry()
        
        # Check close to tray
        if self.tray_settings.get("close_to_tray", True):
            event.ignore()
            self.minimize_to_tray()
            return
        
        # Cleanup
        try:
            self.config.set_tray_settings(self.tray_settings, auto_save=False)
            self.config.save()
            
            if hasattr(self.tray_icon, 'cleanup'):
                self.tray_icon.cleanup()
            
            if hasattr(self.engine, 'cleanup'):
                self.engine.cleanup()
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        
        event.accept()
        print("✅ Closed")
    
    def moveEvent(self, event):
        """Handle window move - debounced save"""
        super().moveEvent(event)
        
        if not hasattr(self, '_geometry_save_timer'):
            self._geometry_save_timer = QTimer()
            self._geometry_save_timer.setSingleShot(True)
            self._geometry_save_timer.timeout.connect(self._save_geometry_debounced)
        
        self._geometry_save_timer.stop()
        self._geometry_save_timer.start(1000)
    
    def _save_geometry_debounced(self):
        """Save geometry after delay"""
        try:
            if not self.isMaximized():
                geom = self.geometry()
                self.config.set_window_geometry({
                    'x': geom.x(),
                    'y': geom.y(),
                    'width': geom.width(),
                    'height': geom.height()
                })
        except Exception as e:
            print(f"⚠️ Debounced save error: {e}")