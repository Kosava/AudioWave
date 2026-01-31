# -*- coding: utf-8 -*-
"""
Unified Player Window - SA CUSTOM TITLE BAR
ui/windows/unified_player_window.py

AudioWave - Modern desktop music player
Version 0.3.3 - Tray improvements & Resume playback

FEATURES:
- Custom title bar with theme support
- Minimize to tray on close (configurable in Settings)
- Show/Hide window toggle from tray menu
- Resume playback position on startup (configurable in Settings)
- Radio Browser integration
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication, QSizeGrip, QMessageBox
from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon
import traceback
import sys
import os
import logging

# ISPRAVNI IMPORTI
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
        def is_resume_playback_enabled(self): return False
        def get_saved_playback_position(self): return (None, 0, 0)
        def save_playback_position(self, *args, **kwargs): pass
        def clear_playback_position(self): pass

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

# Import custom title bar
try:
    from ui.widgets.title_bar import TitleBar
    TITLE_BAR_AVAILABLE = True
except ImportError:
    TITLE_BAR_AVAILABLE = False
    print('[WARN] Custom TitleBar not available, using system title bar')

# Import plugin manager
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../"))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from plugins.plugin_manager import get_plugin_manager
    PLUGIN_MANAGER_AVAILABLE = True
    print("[OK] [PluginManager] Import successful")
except ImportError as e:
    PLUGIN_MANAGER_AVAILABLE = False
    print(f'[WARN] Plugin manager not available: {e}')
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "plugin_manager", 
            os.path.join(project_root, "plugins", "plugin_manager.py")
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["plugin_manager"] = module
            spec.loader.exec_module(module)
            from plugin_manager import get_plugin_manager
            PLUGIN_MANAGER_AVAILABLE = True
            print("[OK] [PluginManager] Direct import successful")
    except Exception as e2:
        print(f'[WARN] Direct import also failed: {e2}')


class UnifiedPlayerWindow(QMainWindow):
    """Glavni prozor - SA CUSTOM TITLE BAR + RADIO BROWSER INTEGRATION"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.engine = app.engine
        
        # Setup logger za debugging
        self.logger = logging.getLogger(__name__)
        
        # Track last highlighted file to prevent duplicates
        self._last_highlighted_file = None
        
        # Auto-play enabled by default
        self.auto_play_enabled = True
        
        # System Tray
        self.config = app.config
        self.tray_settings = self.config.get_tray_settings()
        self.tray_icon = TrayIcon(app, self)
        self.tray_notifications = TrayNotifications(self.tray_icon)
        
        # Proveri da li koristimo custom title bar
        self.use_custom_titlebar = TITLE_BAR_AVAILABLE
        
        # Ako koristimo custom title bar, iskljuci sistemski
        if self.use_custom_titlebar:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.Window
            )
            print("[TitleBar] Custom title bar enabled")
        
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
        
        # Plugin Manager
        self.plugin_manager = None
        self.radio_browser_widget = None
        
        if PLUGIN_MANAGER_AVAILABLE:
            try:
                self.plugin_manager = get_plugin_manager()
                self.logger.info("[PluginManager] Plugin manager initialized")
                print("[OK] [UnifiedPlayerWindow] Plugin manager initialized successfully")
                
                if self.plugin_manager:
                    rb_plugin = self.plugin_manager.get_plugin("radio_browser")
                    if rb_plugin:
                        print(f"[OK] [DEBUG] Radio Browser plugin found: {rb_plugin.name}")
                    else:
                        print("[WARN] [DEBUG] Radio Browser plugin NOT found")
                        
            except Exception as e:
                print(f"[ERR] Error initializing plugin manager: {e}")
                traceback.print_exc()
        else:
            print("[WARN] Plugin manager not available")
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Dodaj custom title bar ako je dostupan
        if self.use_custom_titlebar:
            self.title_bar = TitleBar(self)
            layout.addWidget(self.title_bar)
            print("[TitleBar] Title bar widget added to layout")
        
        # Dodaj player i playlist
        layout.addWidget(self.player_window)
        layout.addWidget(self.playlist_panel, 1)
        
        # Resize grip
        self._central_widget = central_widget
        self.size_grip = None
        self.add_resize_grip()
        
        # Setup
        self.setup_connections()
        self.setup_tray_connections()
        self.setup_theme_connections()
        self.setup_plugin_connections()
        
        # Keyboard
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        QApplication.instance().installEventFilter(self)
        
        # Focus
        QTimer.singleShot(50, self.focus_playlist)
        
        # Show tray icon
        if self.tray_settings.get("enabled", True):
            if hasattr(self.tray_icon, 'show'):
                self.tray_icon.show()
        
        # Primeni inicijalnu temu na title bar
        if self.use_custom_titlebar:
            QTimer.singleShot(100, self.apply_initial_theme_to_titlebar)
        
        # Load saved window geometry
        QTimer.singleShot(150, self.load_window_geometry)
        
        # DEBUG: Testiraj plugin manager
        QTimer.singleShot(200, self._debug_plugin_manager)
        
        # NOVO: Restore playback position ako je enabled
        QTimer.singleShot(500, self._restore_playback_position)
    
    def _debug_plugin_manager(self):
        """Debug funkcija za proveru plugin managera"""
        print("\n[DEBUG] Plugin Manager Status:")
        print(f"   PLUGIN_MANAGER_AVAILABLE: {PLUGIN_MANAGER_AVAILABLE}")
        print(f"   self.plugin_manager: {self.plugin_manager}")
        
        if self.plugin_manager:
            plugins = self.plugin_manager.get_all_plugins()
            print(f"   Total plugins: {len(plugins)}")
            for plugin in plugins:
                status = "[ON]" if plugin.enabled else "[OFF]"
                print(f"   {status} {plugin.icon} {plugin.name} (ID: {plugin.id})")
        print("[DEBUG END]\n")
    
    def add_resize_grip(self):
        """Dodaj resize grip u donji desni ugao."""
        if self.size_grip is not None:
            self.size_grip.show()
            self._update_resize_grip_position()
            return
        
        self.size_grip = QSizeGrip(self._central_widget)
        self.size_grip.setObjectName("resizeGrip")
        self.size_grip.setFixedSize(16, 16)
        self.size_grip.setStyleSheet("""
            QSizeGrip {
                background: transparent;
                width: 16px;
                height: 16px;
            }
        """)
        self._update_resize_grip_position()
        self.size_grip.show()
        self.size_grip.raise_()
        print("[OK] Resize grip created")
    
    def _update_resize_grip_position(self):
        """Update poziciju resize grip-a"""
        if self.size_grip and self._central_widget:
            grip_size = self.size_grip.size()
            self.size_grip.move(
                self._central_widget.width() - grip_size.width(),
                self._central_widget.height() - grip_size.height()
            )
    
    def resizeEvent(self, event):
        """Update resize grip position kada se prozor resize-uje."""
        super().resizeEvent(event)
        self._update_resize_grip_position()
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        QTimer.singleShot(50, self._ensure_resize_grip_visible)
    
    def _ensure_resize_grip_visible(self):
        """Osiguraj da je resize grip vidljiv i pravilno pozicioniran."""
        if self.size_grip:
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
        """Callback kada se stanje prozora promeni (maximize/restore)."""
        if self.size_grip:
            if maximized:
                self.size_grip.hide()
            else:
                self.size_grip.show()
                self.size_grip.raise_()
                self._update_resize_grip_position()
    
    def focus_playlist(self):
        """Focus playlist"""
        if hasattr(self.playlist_panel, 'file_list'):
            self.playlist_panel.file_list.setFocus()
    
    def setup_connections(self):
        """Setup all connections"""
        # Player -> Controller
        self.player_window.play_clicked.connect(self.playback_controller.on_play_clicked)
        self.player_window.stop_clicked.connect(self.playback_controller.on_stop_clicked)
        self.player_window.next_clicked.connect(self.playback_controller.on_next_clicked)
        self.player_window.prev_clicked.connect(self.playback_controller.on_prev_clicked)
        self.player_window.volume_changed.connect(self.engine.set_volume)
        self.player_window.toggle_playlist_requested.connect(self.toggle_playlist_visibility)
        self.player_window.seek_requested.connect(self.playback_controller.on_seek_requested)
        
        # Playlist -> Controller
        self.playlist_panel.play_requested.connect(self.on_playlist_play_requested)
        self.playlist_panel.settings_requested.connect(self.open_settings)
        self.playlist_panel.playlist_changed.connect(self.on_playlist_changed)
        
        # Engine -> Player
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
        """Setup theme manager connections"""
        if hasattr(self.app, 'theme_manager'):
            self.app.theme_manager.theme_changed.connect(self.on_theme_changed)
            print("[Theme] Theme manager connected")
    
    def setup_plugin_connections(self):
        """Setup plugin manager connections"""
        if not self.plugin_manager:
            return
        
        try:
            if hasattr(self.plugin_manager, 'add_radio_to_playlist'):
                self.plugin_manager.add_radio_to_playlist.connect(self.on_radio_station_add)
            
            from PyQt6.QtGui import QShortcut, QKeySequence
            self.radio_browser_shortcut = QShortcut(QKeySequence("F5"), self)
            self.radio_browser_shortcut.activated.connect(self.open_radio_browser)
            
            self._add_radio_browser_to_context_menu()
        except Exception as e:
            print(f"[WARN] Error setting up plugins: {e}")
    
    def _add_radio_browser_to_context_menu(self):
        """Dodaje Radio Browser opciju u kontekstni meni"""
        try:
            if hasattr(self.player_window, 'current_style_widget'):
                style_widget = self.player_window.current_style_widget
                if style_widget and hasattr(style_widget, 'hamburger_menu'):
                    style_widget.hamburger_menu.addSeparator()
                    from PyQt6.QtGui import QAction
                    radio_action = QAction("Radio Browser (F5)", self)
                    radio_action.triggered.connect(self.open_radio_browser)
                    style_widget.hamburger_menu.addAction(radio_action)
        except Exception as e:
            print(f"[WARN] Could not add Radio Browser to context menu: {e}")
    
    def apply_initial_theme_to_titlebar(self):
        """Primeni inicijalnu temu na title bar"""
        if not self.use_custom_titlebar:
            return
        
        if hasattr(self.app, 'theme_manager'):
            current_theme_name = self.app.theme_manager.current_theme
            theme = self.app.theme_manager.registry.get_theme(current_theme_name)
            if hasattr(self, 'title_bar'):
                self.title_bar.update_from_theme(theme)
    
    def on_theme_changed(self, theme_name: str):
        """Callback kada se tema promeni"""
        if not self.use_custom_titlebar:
            return
        try:
            theme = self.app.theme_manager.registry.get_theme(theme_name)
            if hasattr(self, 'title_bar'):
                self.title_bar.update_from_theme(theme)
        except Exception as e:
            print(f"[ERR] Error updating title bar theme: {e}")
    
    # ===== RADIO BROWSER PLUGIN METHODS =====
    
    def open_radio_browser(self):
        """Otvara Radio Browser plugin"""
        if not self.plugin_manager:
            QMessageBox.warning(self, "Plugin Manager nedostupan",
                "Plugin manager nije ucitan. Radio Browser nije dostupan.")
            return
        
        plugin = self.plugin_manager.get_plugin("radio_browser")
        if not plugin:
            QMessageBox.warning(self, "Plugin nije pronadjen",
                "Radio Browser plugin nije instaliran.")
            return
        
        if not plugin.enabled:
            reply = QMessageBox.question(self, "Plugin nije omogucen",
                "Radio Browser plugin nije omogucen. Zelite li ga omoguciti?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.plugin_manager.enable_plugin("radio_browser")
            else:
                return
        
        if not self.radio_browser_widget or not hasattr(self.radio_browser_widget, 'isVisible'):
            try:
                self.radio_browser_widget = self.plugin_manager.show_plugin_widget(
                    "radio_browser", parent=self)
                if not self.radio_browser_widget:
                    QMessageBox.critical(self, "Greska",
                        "Nije moguce kreirati Radio Browser widget.")
                    return
                if hasattr(self.radio_browser_widget, 'add_to_playlist'):
                    self.radio_browser_widget.add_to_playlist.connect(self.on_radio_station_add)
            except Exception as e:
                QMessageBox.critical(self, "Greska", f"Greska: {str(e)}")
                return
        
        if hasattr(self.radio_browser_widget, 'setWindowTitle'):
            self.radio_browser_widget.setWindowTitle("Radio Browser - AudioWave")
        if hasattr(self.radio_browser_widget, 'resize'):
            self.radio_browser_widget.resize(900, 600)
        if hasattr(self.radio_browser_widget, 'show'):
            self.radio_browser_widget.show()
        if hasattr(self.radio_browser_widget, 'raise_'):
            self.radio_browser_widget.raise_()
        if hasattr(self.radio_browser_widget, 'activateWindow'):
            self.radio_browser_widget.activateWindow()
    
    @pyqtSlot(str, str)
    def on_radio_station_add(self, name: str, url: str):
        """Handler za dodavanje radio stanice u playlist."""
        try:
            if hasattr(self.app, 'playlist_manager'):
                playlist_manager = self.app.playlist_manager
                if hasattr(playlist_manager, 'add_files'):
                    playlist_manager.add_files([url])
                    if hasattr(self.playlist_panel, 'refresh_playlist'):
                        self.playlist_panel.refresh_playlist()
                    self.show_message(f"Dodato: {name}", 3000)
            elif hasattr(self.playlist_panel, 'add_stream'):
                self.playlist_panel.add_stream(name, url)
                self.show_message(f"Dodato: {name}", 3000)
            elif hasattr(self.playlist_panel, 'add_url'):
                self.playlist_panel.add_url(name, url)
                self.show_message(f"Dodato: {name}", 3000)
            else:
                QMessageBox.information(self, "Radio stanica",
                    f"Radio stanica '{name}' je spremna.\nURL: {url}")
        except Exception as e:
            QMessageBox.critical(self, "Greska", f"Greska: {str(e)}")
    
    def on_playlist_play_requested(self, file_path):
        """Handle play request from playlist"""
        try:
            if self._last_highlighted_file != file_path:
                if hasattr(self.playlist_panel, 'highlight_file'):
                    self.playlist_panel.highlight_file(file_path)
                self._last_highlighted_file = file_path
            
            if hasattr(self.engine, 'play_file'):
                self.engine.play_file(file_path)
        except Exception as e:
            print(f"Error playing file: {e}")
    
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
            if hasattr(self.tray_notifications, 'playback_state_changed'):
                self.tray_notifications.playback_state_changed(True)
            # NOVO: Azuriraj tray menu Play/Pause tekst
            self._update_tray_menu_playing_state(True)
        except Exception as e:
            print(f"Error in playback started: {e}")
    
    def on_playback_stopped(self):
        """Handle playback stopped event"""
        try:
            if hasattr(self.player_window, 'on_playback_stopped'):
                self.player_window.on_playback_stopped()
            if hasattr(self.tray_notifications, 'playback_state_changed'):
                self.tray_notifications.playback_state_changed(False)
            # NOVO: Azuriraj tray menu Play/Pause tekst
            self._update_tray_menu_playing_state(False)
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
        """Handle close event - AZURIRANO za minimize_to_tray opciju"""
        print("[Window] Closing window...")
        
        # Save window state
        self.save_window_geometry()
        
        # NOVO: Sacuvaj playback poziciju ako je resume enabled
        self._save_playback_position_for_resume()
        
        # AZURIRANO: Koristi minimize_to_tray umesto close_to_tray
        if self.tray_settings.get("minimize_to_tray", True):
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
            print(f"[WARN] Cleanup error: {e}")
        
        event.accept()
        print("[OK] Closed")
    
    def save_window_state(self):
        """Save window state"""
        try:
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                if self.title_bar.is_window_maximized():
                    if self.title_bar._normal_geometry:
                        geom = self.title_bar._normal_geometry
                        self.config.set("window_geometry", {
                            "x": geom.x(), "y": geom.y(),
                            "width": geom.width(), "height": geom.height()
                        })
                    self.config.set("window_maximized", True)
                else:
                    self.config.set("window_geometry", {
                        "x": self.x(), "y": self.y(),
                        "width": self.width(), "height": self.height()
                    })
                    self.config.set("window_maximized", False)
            else:
                self.config.set("window_geometry", {
                    "x": self.x(), "y": self.y(),
                    "width": self.width(), "height": self.height()
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
                    geometry.get("x", 100), geometry.get("y", 100),
                    geometry.get("width", 550), geometry.get("height", 650)
                )
            
            if maximized:
                if self.use_custom_titlebar and hasattr(self, 'title_bar'):
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
            self.playlist_panel.hide()
            title_bar_height = 40 if self.use_custom_titlebar else 0
            new_height = self.player_window.height() + title_bar_height
            self.resize(self.width(), new_height)
            self.show_message("Playlist hidden (F2 to show)", 2000)
            QTimer.singleShot(50, self._ensure_resize_grip_visible)
        else:
            self.playlist_panel.show()
            self.resize(self.width(), 650)
            self.show_message("Playlist visible (F2 to hide)", 2000)
            QTimer.singleShot(50, self._ensure_resize_grip_visible)
    
    def open_settings(self):
        """Open settings"""
        try:
            from ui.windows.settings_dialog import SettingsDialog
            settings_dialog = SettingsDialog(self)
            settings_dialog.settings_saved.connect(self.on_settings_saved)
            settings_dialog.exec()
        except ImportError:
            try:
                from ui.dialogs.settings_dialog import SettingsDialog
                settings_dialog = SettingsDialog(self)
                settings_dialog.exec()
            except:
                self.show_message("Settings dialog not found")
        except Exception as e:
            print(f"Error opening settings: {e}")
    
    def open_about(self):
        """Open About dialog"""
        try:
            from ui.windows.settings_dialog import SettingsDialog
            settings_dialog = SettingsDialog(self)
            settings_dialog.settings_saved.connect(self.on_settings_saved)
            settings_dialog.show_about_tab()
        except Exception as e:
            print(f"Error opening about: {e}")
    
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
            
            # NOVO: Azuriraj tray_settings iz playback opcija
            if isinstance(settings, dict) and "playback" in settings:
                if "minimize_to_tray" in settings["playback"]:
                    self.tray_settings["minimize_to_tray"] = settings["playback"]["minimize_to_tray"]
            
            # Audio settings
            if isinstance(settings, dict) and 'audio' in settings:
                if 'default_volume' in settings['audio']:
                    volume = settings['audio']['default_volume']
                    self.engine.set_volume(volume)
                    if hasattr(self.player_window, 'volume_widget'):
                        self.player_window.volume_widget.set_volume(volume)
            
            # Theme settings
            if isinstance(settings, dict) and 'appearance' in settings:
                if 'theme' in settings['appearance']:
                    theme = settings['appearance']['theme']
                    self.apply_theme(theme)
            
            self.show_message("Settings applied")
        except Exception as e:
            print(f"Error applying settings: {e}")
    
    def apply_theme(self, theme_name):
        """Apply theme to all components"""
        try:
            if hasattr(self.app, 'theme_manager') and self.app.theme_manager:
                self.app.theme_manager.apply_theme(self, theme_name)
            else:
                try:
                    from core.themes.theme_registry import ThemeRegistry
                    theme = ThemeRegistry.get_theme(theme_name)
                    if theme:
                        theme_data = theme.get_theme_data()
                        self.setStyleSheet(theme_data["stylesheet"])
                except Exception as e:
                    print(f"[WARN] ThemeRegistry fallback failed: {e}")
            
            if hasattr(self.player_window, 'apply_theme'):
                self.player_window.apply_theme(theme_name)
            if hasattr(self.playlist_panel, 'apply_theme'):
                self.playlist_panel.apply_theme(theme_name)
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                try:
                    from core.themes.theme_registry import ThemeRegistry
                    theme = ThemeRegistry.get_theme(theme_name)
                    if theme and hasattr(self.title_bar, 'update_from_theme'):
                        self.title_bar.update_from_theme(theme)
                except:
                    pass
            
            self.repaint()
            QApplication.processEvents()
            self.show_message(f"Theme: {theme_name}", 2000)
        except Exception as e:
            print(f"[ERR] Error applying theme: {e}")
    
    def quit_application(self):
        """Quit application - AZURIRANO"""
        # NOVO: Sacuvaj poziciju pre izlaska
        self._save_playback_position_for_resume()
        # Postavi flag da ne ide u tray
        self.tray_settings["minimize_to_tray"] = False
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
        """Show window from tray - AZURIRANO za tray menu update"""
        if self.isHidden() or self.isMinimized():
            self.showNormal()
            self.activateWindow()
            self.raise_()
            QTimer.singleShot(50, self.focus_playlist)
            QTimer.singleShot(100, self._ensure_resize_grip_visible)
            if hasattr(self.tray_notifications, 'window_restored'):
                self.tray_notifications.window_restored()
            # NOVO: Azuriraj tray menu da prikazuje "Hide Window"
            self._update_tray_menu_window_state(True)
        else:
            self.activateWindow()
            self.raise_()
            self.focus_playlist()
    
    def minimize_to_tray(self):
        """Minimize to tray - AZURIRANO za tray menu update"""
        if self.tray_settings.get("minimize_to_tray", True):
            self.hide()
            if hasattr(self.tray_notifications, 'minimized_to_tray'):
                self.tray_notifications.minimized_to_tray()
            # NOVO: Azuriraj tray menu da prikazuje "Show Window"
            self._update_tray_menu_window_state(False)
        else:
            self.showMinimized()
    
    # ===== NOVE METODE ZA TRAY MENU I RESUME PLAYBACK =====
    
    def _update_tray_menu_window_state(self, is_visible: bool):
        """NOVO: Azuriraj tray menu Show/Hide Window tekst"""
        try:
            if hasattr(self.tray_icon, '_menu_manager') and self.tray_icon._menu_manager:
                if hasattr(self.tray_icon._menu_manager, 'update_window_state'):
                    self.tray_icon._menu_manager.update_window_state(is_visible)
        except Exception as e:
            print(f"[WARN] Could not update tray menu: {e}")
    
    def _update_tray_menu_playing_state(self, is_playing: bool):
        """NOVO: Azuriraj tray menu Play/Pause tekst"""
        try:
            if hasattr(self.tray_icon, '_menu_manager') and self.tray_icon._menu_manager:
                if hasattr(self.tray_icon._menu_manager, 'set_playing_state'):
                    self.tray_icon._menu_manager.set_playing_state(is_playing)
        except Exception as e:
            print(f"[WARN] Could not update tray menu playing state: {e}")
    
    def _save_playback_position_for_resume(self):
        """NOVO: Sacuvaj trenutnu poziciju pesme za resume"""
        try:
            if not self.config.is_resume_playback_enabled():
                return
            
            if not hasattr(self.engine, 'get_position') or not hasattr(self.engine, 'current_file'):
                return
            
            current_file = getattr(self.engine, 'current_file', None)
            if not current_file:
                return
            
            position_ms = self.engine.get_position()
            playlist_index = 0
            if hasattr(self.playlist_panel, 'get_current_index'):
                playlist_index = self.playlist_panel.get_current_index()
            
            self.config.save_playback_position(
                track_path=current_file,
                position_ms=position_ms,
                playlist_index=playlist_index,
                auto_save=False
            )
            print(f"[OK] Resume position saved: {position_ms}ms")
        except Exception as e:
            print(f"[WARN] Error saving resume position: {e}")
    
    def _restore_playback_position(self):
        """NOVO: Ucitaj sacuvanu poziciju i nastavi sa reprodukcijom"""
        print("🔄 [DEBUG] _restore_playback_position() CALLED!")

        if not self.config or not self.config.is_resume_playback_enabled():
            print("🔄 Resume playback disabled or no config")
            return

        track, position, index = self.config.get_saved_playback_position()

        if not track:
            print("⚠️ No saved track")
            return

        print(f"▶️ Restoring: {track} @ {position}ms")

        # ▶️ Pusti fajl DIREKTNO preko engine-a
        if hasattr(self.engine, "play_file"):
            self.engine.play_file(track)
        else:
            print("❌ Engine has no play_file()")
            return

        # ▶️ Seek tek kad playback krene
        QTimer.singleShot(
            400,
            lambda: hasattr(self.engine, "seek") and self.engine.seek(position)
        )
    
    def _seek_to_resume_position(self, position_ms: int):
        """NOVO: Seek na sacuvanu poziciju i pauziraj"""
        try:
            if hasattr(self.engine, 'seek'):
                self.engine.seek(position_ms)
            
            if hasattr(self.engine, 'pause'):
                self.engine.pause()
                self.show_message("Resumed from last position - Press Play to continue", 5000)
        except Exception as e:
            print(f"[WARN] Error seeking to resume position: {e}")
    
    # ===== WINDOW GEOMETRY PERSISTENCE =====
    
    def load_window_geometry(self):
        """Load saved window geometry and state"""
        try:
            geometry = self.config.get_window_geometry()
            if geometry:
                self.setGeometry(
                    geometry['x'], geometry['y'],
                    geometry['width'], geometry['height']
                )
            
            if self.config.is_window_maximized():
                self.showMaximized()
                if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                    self.title_bar._is_maximized = True
                    self.title_bar.update_icons()
            
            if self.config.is_always_on_top():
                flags = self.windowFlags()
                flags |= Qt.WindowType.WindowStaysOnTopHint
                self.setWindowFlags(flags)
                self.show()
                if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                    self.title_bar._is_always_on_top = True
                    if hasattr(self.title_bar, 'always_on_top_action'):
                        self.title_bar.always_on_top_action.setChecked(True)
        except Exception as e:
            print(f"[WARN] Error loading geometry: {e}")
    
    def save_window_geometry(self):
        """Save window geometry and state"""
        try:
            is_maximized = self.isMaximized()
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                is_maximized = self.title_bar.is_window_maximized()
            
            if not is_maximized:
                geom = self.geometry()
                self.config.set_window_geometry({
                    'x': geom.x(), 'y': geom.y(),
                    'width': geom.width(), 'height': geom.height()
                }, auto_save=False)
            
            self.config.set_window_maximized(is_maximized, auto_save=False)
            
            if self.use_custom_titlebar and hasattr(self, 'title_bar'):
                always_on_top = self.title_bar.is_always_on_top()
                self.config.set_always_on_top(always_on_top, auto_save=False)
            
            self.config.save()
        except Exception as e:
            print(f"[WARN] Error saving geometry: {e}")
    
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
                    'x': geom.x(), 'y': geom.y(),
                    'width': geom.width(), 'height': geom.height()
                })
        except Exception as e:
            print(f"[WARN] Debounced save error: {e}")