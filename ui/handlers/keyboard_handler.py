# -*- coding: utf-8 -*-
# ui/handlers/keyboard_handler.py
"""
Keyboard Handler - Handles all keyboard shortcuts for AudioWave

Includes shortcuts for:
- Playback control
- Volume control
- Navigation
- Plugins (Equalizer, Lyrics)
- Settings and About
"""

from PyQt6.QtCore import Qt, QObject, QEvent
from PyQt6.QtWidgets import QMessageBox, QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox

# Import Plugin Manager
try:
    from plugins.plugin_manager import get_plugin_manager
    PLUGIN_MANAGER_AVAILABLE = True
except ImportError:
    PLUGIN_MANAGER_AVAILABLE = False


class KeyboardHandler(QObject):
    """Handles keyboard shortcuts for the main window"""
    
    # Tipovi widgeta koji primaju text input
    TEXT_INPUT_TYPES = (QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox)
    
    def __init__(self, window):
        super().__init__()
        self.window = window
        
        # Plugin manager - koristimo ga samo za proveru statusa
        if PLUGIN_MANAGER_AVAILABLE:
            try:
                self.plugin_manager = get_plugin_manager()
                print("✅ PluginManager initialized")
            except Exception as e:
                print(f"❌ Failed to get PluginManager: {e}")
                self.plugin_manager = None
        else:
            self.plugin_manager = None
            print("⚠️ PluginManager not available")
        
        print("⌨️ KeyboardHandler initialized")
    
    def _is_text_input_focused(self) -> bool:
        """
        Proveri da li je fokus na text input widgetu.
        
        Returns:
            True ako je fokus na QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, 
            QDoubleSpinBox ili QComboBox (sa editable=True)
        """
        from PyQt6.QtWidgets import QApplication
        
        focused_widget = QApplication.focusWidget()
        if focused_widget is None:
            return False
        
        # Proveri da li je fokusirani widget neki od text input tipova
        if isinstance(focused_widget, self.TEXT_INPUT_TYPES):
            # Za QComboBox, proveri da li je editable
            if isinstance(focused_widget, QComboBox):
                return focused_widget.isEditable()
            return True
        
        # Proveri da li je parent od fokusiranog widgeta text input
        # (npr. za QComboBox lineEdit)
        parent = focused_widget.parent()
        while parent is not None:
            if isinstance(parent, self.TEXT_INPUT_TYPES):
                if isinstance(parent, QComboBox):
                    return parent.isEditable()
                return True
            parent = parent.parent()
        
        return False
    
    def handle_key_event(self, event) -> bool:
        """
        Handle keyboard events - ONLY KeyPress, ignore KeyRelease
        
        Returns:
            True ako je event obrađen, False ako treba da prođe dalje
        """
        
        # ✅ Only handle KeyPress events, ignore KeyRelease
        if event.type() != QEvent.Type.KeyPress:
            return False
        
        # ✅ Ignore auto-repeat events (holding key down)
        if event.isAutoRepeat():
            return False
        
        key = event.key()
        modifiers = event.modifiers()
        
        # ✅ NOVO: Proveri da li je fokus na text input polju
        # Ako jeste, propusti većinu tastera da idu u text input
        if self._is_text_input_focused():
            # Dozvoli samo GLOBALNE shortcutte koji imaju modifier (Ctrl, Alt)
            # ili function keys koji ne utiču na tekst
            has_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
            has_alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)
            
            # Function keys su OK čak i u text inputu
            is_function_key = Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12
            
            # Ako nema modifiera i nije function key, propusti event
            if not has_ctrl and not has_alt and not is_function_key:
                return False  # Propusti Space, M, Enter, itd. u text input
            
            # Za Ctrl+A u text inputu, propusti (Select All u text inputu)
            if has_ctrl and key == Qt.Key.Key_A:
                return False
            
            # Za Ctrl+C, Ctrl+V, Ctrl+X u text inputu, propusti
            if has_ctrl and key in (Qt.Key.Key_C, Qt.Key.Key_V, Qt.Key.Key_X, Qt.Key.Key_Z):
                return False
            
            # Escape u text inputu - propusti (može da služi za zatvaranje dijaloga)
            if key == Qt.Key.Key_Escape:
                return False
            
            # Enter u text inputu - propusti (potvrda dijaloga)
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                return False
        
        # ===== FUNCTION KEYS =====
        
        # F1 - About dialog
        if key == Qt.Key.Key_F1:
            self._show_about()
            return True
        
        # F2 - Toggle playlist
        if key == Qt.Key.Key_F2:
            self._toggle_playlist()
            return True
        
        # F3 - Equalizer (plugin)
        if key == Qt.Key.Key_F3:
            self._show_equalizer()
            return True
        
        # F4 - Lyrics (plugin)
        if key == Qt.Key.Key_F4:
            self._show_lyrics()
            return True
        
        # F5 - Refresh
        if key == Qt.Key.Key_F5:
            self._refresh_playlist()
            return True
        
        # ===== PLAYBACK CONTROLS =====
        
        # Space - Play/Pause
        if key == Qt.Key.Key_Space:
            if hasattr(self.window, 'playback_controller') and self.window.playback_controller:
                self.window.playback_controller.on_play_clicked()
            return True
        
        # M - Mute
        if key == Qt.Key.Key_M:
            self._toggle_mute()
            return True
        
        # Enter - Play selected
        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self._play_selected()
            return True
        
        # Escape - Stop
        if key == Qt.Key.Key_Escape:
            if hasattr(self.window, 'playback_controller') and self.window.playback_controller:
                self.window.playback_controller.on_stop_clicked()
            return True
        
        # Delete - Remove selected
        if key == Qt.Key.Key_Delete:
            self._remove_selected()
            return True
        
        # ===== VOLUME CONTROLS =====
        
        # Ctrl + Up/Down - Volume ±5%
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Up:
                self._adjust_volume(5)
                return True
            elif key == Qt.Key.Key_Down:
                self._adjust_volume(-5)
                return True
        
        # Alt + Up/Down - Volume ±10%
        if modifiers & Qt.KeyboardModifier.AltModifier:
            if key == Qt.Key.Key_Up:
                self._adjust_volume(10)
                return True
            elif key == Qt.Key.Key_Down:
                self._adjust_volume(-10)
                return True
        
        # ===== SEEK CONTROLS =====
        
        # Ctrl + Left/Right - Seek ±10 seconds
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Left:
                self._seek_relative(-10000)
                return True
            elif key == Qt.Key.Key_Right:
                self._seek_relative(10000)
                return True
        
        # Alt + Left/Right - Previous/Next track
        if modifiers & Qt.KeyboardModifier.AltModifier:
            if key == Qt.Key.Key_Left:
                if hasattr(self.window, 'playback_controller') and self.window.playback_controller:
                    self.window.playback_controller.on_prev_clicked()
                return True
            elif key == Qt.Key.Key_Right:
                if hasattr(self.window, 'playback_controller') and self.window.playback_controller:
                    self.window.playback_controller.on_next_clicked()
                return True
        
        # Plain Left/Right - Seek ±5 seconds
        if key == Qt.Key.Key_Left and not modifiers:
            self._seek_relative(-5000)
            return True
        elif key == Qt.Key.Key_Right and not modifiers:
            self._seek_relative(5000)
            return True
        
        # Up/Down - Navigate playlist (without modifiers)
        if key == Qt.Key.Key_Up and not modifiers:
            self._navigate_playlist(-1)
            return True
        elif key == Qt.Key.Key_Down and not modifiers:
            self._navigate_playlist(1)
            return True
        
        # ===== CTRL SHORTCUTS =====
        
        # Ctrl+A - Select all
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_A:
            self._select_all()
            return True
        
        # Ctrl+O - Open files
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_O:
            self._open_files()
            return True
        
        # Ctrl+L - Clear playlist
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_L:
            self._clear_playlist()
            return True
        
        # Ctrl+S - Settings
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S:
            self._open_settings()
            return True
        
        # Ctrl+E - Equalizer (alternativna prečica)
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_E:
            self._show_equalizer()
            return True
        
        # Ctrl+H - Show shortcuts help
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_H:
            self._show_shortcuts()
            return True
        
        # Ctrl+P - Plugins settings
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_P:
            self._show_plugins_settings()
            return True
        
        # Ctrl+Q - Quit
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Q:
            self.window.close()
            return True
        
        return False
    
    def _get_player_window(self):
        """Safely get player_window or None"""
        if hasattr(self.window, 'player_window') and self.window.player_window:
            return self.window.player_window
        return None
    
    def _get_engine(self):
        """Safely get audio engine"""
        if hasattr(self.window, 'app') and hasattr(self.window.app, 'engine'):
            return self.window.app.engine
        return None
    
    # ===== PLUGIN SHORTCUTS =====
    
    def _show_equalizer(self):
        """Show Equalizer dialog (F3)"""
        print(f"🎛️ F3 pressed - Equalizer shortcut triggered")
        
        # Proveri da li je plugin omogućen (ako je plugin manager dostupan)
        if self.plugin_manager:
            if not self.plugin_manager.is_enabled("equalizer"):
                self._show_message("⚠️ Equalizer plugin is disabled. Enable it in Settings → Plugins")
                return
        
        # Direktan poziv - zaobilazimo plugin manager jer šalje extra argumente
        try:
            from plugins.equalizer.equalizer_plugin import EqualizerDialog
            engine = self._get_engine()
            
            # Pozovi dijalog sa tačno onim argumentima koje očekuje
            dialog = EqualizerDialog(self.window, engine=engine)
            dialog.exec()
            print("✅ Equalizer opened successfully")
        except ImportError as e:
            print(f"❌ Equalizer plugin not found: {e}")
            self._show_message("Equalizer plugin not available")
        except TypeError as e:
            # Ako EqualizerDialog ne prihvata engine argument, pokušaj bez njega
            print(f"⚠️ EqualizerDialog TypeError: {e}. Trying without engine...")
            try:
                from plugins.equalizer.equalizer_plugin import EqualizerDialog
                dialog = EqualizerDialog(self.window)
                dialog.exec()
                print("✅ Equalizer opened without engine argument")
            except Exception as e2:
                print(f"❌ Error opening equalizer: {e2}")
                self._show_message(f"Error opening equalizer: {str(e2)}")
        except Exception as e:
            print(f"❌ Error opening equalizer: {e}")
            self._show_message(f"Error opening equalizer: {str(e)}")
    
    def _show_lyrics(self):
        """Show Lyrics dialog (F4)"""
        print(f"🎵 F4 pressed - Lyrics shortcut triggered")
        
        # Proveri da li je plugin omogućen (ako je plugin manager dostupan)
        if self.plugin_manager:
            if not self.plugin_manager.is_enabled("lyrics"):
                self._show_message("⚠️ Lyrics plugin is disabled. Enable it in Settings → Plugins")
                return
        
        # Direktan poziv - zaobilazimo plugin manager jer šalje extra argumente
        try:
            from plugins.lyrics.lyrics_plugin import LyricsDialog
            
            # Dobij metapodatke za trenutnu pesmu (ako postoji)
            artist = ""
            title = ""
            
            engine = self._get_engine()
            if engine and hasattr(engine, 'current_metadata'):
                metadata = engine.current_metadata
                if metadata:
                    artist = metadata.get('artist', '')
                    title = metadata.get('title', '')
            
            print(f"🔍 Searching lyrics for: {artist} - {title}")
            
            # Pozovi dijalog sa minimalnim argumentima
            dialog = LyricsDialog(self.window, artist=artist, title=title)
            dialog.exec()
            print("✅ Lyrics opened successfully")
        except ImportError as e:
            print(f"❌ Lyrics plugin not found: {e}")
            self._show_message("Lyrics plugin not available")
        except TypeError as e:
            # Ako LyricsDialog ne prihvata artist/title, pokušaj bez njih
            print(f"⚠️ LyricsDialog TypeError: {e}. Trying without artist/title...")
            try:
                from plugins.lyrics.lyrics_plugin import LyricsDialog
                dialog = LyricsDialog(self.window)
                dialog.exec()
                print("✅ Lyrics opened without artist/title arguments")
            except Exception as e2:
                print(f"❌ Error opening lyrics: {e2}")
                self._show_message(f"Error opening lyrics: {str(e2)}")
        except Exception as e:
            print(f"❌ Error opening lyrics: {e}")
            self._show_message(f"Error opening lyrics: {str(e)}")
    
    def _show_plugins_settings(self):
        """Show Plugins tab in Settings (Ctrl+P)"""
        try:
            from ui.windows.settings_dialog import show_plugins
            show_plugins(self.window)
        except ImportError:
            self._show_message("Settings dialog not available")
    
    # ===== ABOUT & HELP =====
    
    def _show_about(self):
        """Show About dialog (F1)"""
        if hasattr(self.window, 'open_about'):
            self.window.open_about()
        else:
            try:
                from ui.windows.settings_dialog import show_about
                show_about(self.window)
            except ImportError:
                self._show_message("About dialog not available")
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts help (Ctrl+H)"""
        shortcuts = """
🎹 <b>AudioWave - Keyboard Shortcuts</b>

<b>Playback:</b>
• Space - Play/Pause
• Enter - Play selected
• Esc - Stop
• M - Toggle Mute

<b>Navigation:</b>
• ↑/↓ - Navigate playlist
• Alt+← / Alt+→ - Previous/Next track
• ← / → - Seek ±5 seconds
• Ctrl+← / Ctrl+→ - Seek ±10 seconds

<b>Volume:</b>
• Ctrl+↑ / Ctrl+↓ - Volume ±5%
• Alt+↑ / Alt+↓ - Volume ±10%

<b>Playlist:</b>
• Ctrl+A - Select all
• Del - Remove selected
• Ctrl+O - Open files
• Ctrl+L - Clear playlist
• F2 - Toggle playlist visibility
• F5 - Refresh

<b>Plugins:</b>
• F3 / Ctrl+E - Equalizer
• F4 - Lyrics
• Ctrl+P - Plugin settings

<b>Other:</b>
• Ctrl+S - Settings
• F1 - About
• Ctrl+H - Show shortcuts
• Ctrl+Q - Quit
        """
        
        QMessageBox.information(
            self.window,
            "Keyboard Shortcuts",
            shortcuts.strip()
        )
    
    # ===== PLAYLIST CONTROLS =====
    
    def _toggle_playlist(self):
        """Toggle playlist visibility (F2)"""
        if hasattr(self.window, 'toggle_playlist_visibility'):
            self.window.toggle_playlist_visibility()
        elif hasattr(self.window, 'playlist_panel') and self.window.playlist_panel:
            if self.window.playlist_panel.isVisible():
                self.window.playlist_panel.hide()
                self._show_message("Playlist hidden (F2 to show)")
            else:
                self.window.playlist_panel.show()
                self._show_message("Playlist visible (F2 to hide)")
    
    def _refresh_playlist(self):
        """Refresh playlist (F5)"""
        if hasattr(self.window, 'playlist_panel') and self.window.playlist_panel:
            if hasattr(self.window.playlist_panel, 'load_current_playlist'):
                self.window.playlist_panel.load_current_playlist()
            self._show_message("Playlist refreshed")
    
    def _play_selected(self):
        """Play selected track"""
        if hasattr(self.window, 'playlist_panel') and self.window.playlist_panel:
            if hasattr(self.window.playlist_panel, 'play_selected'):
                self.window.playlist_panel.play_selected()
    
    def _remove_selected(self):
        """Remove selected tracks"""
        if hasattr(self.window, 'playlist_panel') and self.window.playlist_panel:
            if hasattr(self.window.playlist_panel, 'remove_selected'):
                self.window.playlist_panel.remove_selected()
    
    def _select_all(self):
        """Select all in playlist"""
        if hasattr(self.window, 'playlist_panel') and self.window.playlist_panel:
            if hasattr(self.window.playlist_panel, 'file_list'):
                self.window.playlist_panel.file_list.selectAll()
    
    def _open_files(self):
        """Open files dialog"""
        if hasattr(self.window, 'playlist_panel') and self.window.playlist_panel:
            if hasattr(self.window.playlist_panel, 'add_files'):
                self.window.playlist_panel.add_files()
    
    def _clear_playlist(self):
        """Clear playlist"""
        if hasattr(self.window, 'playlist_panel') and self.window.playlist_panel:
            if hasattr(self.window.playlist_panel, 'clear_playlist'):
                self.window.playlist_panel.clear_playlist()
    
    def _navigate_playlist(self, direction):
        """Navigate playlist up/down"""
        if hasattr(self.window, 'playlist_panel') and self.window.playlist_panel:
            if hasattr(self.window.playlist_panel, 'file_list'):
                file_list = self.window.playlist_panel.file_list
                current_row = file_list.currentRow()
                new_row = current_row + direction
                
                if 0 <= new_row < file_list.count():
                    file_list.setCurrentRow(new_row)
    
    # ===== AUDIO CONTROLS =====
    
    def _toggle_mute(self):
        """Toggle mute"""
        player = self._get_player_window()
        if player:
            if hasattr(player, 'toggle_mute'):
                player.toggle_mute()
            volume = player.get_volume() if hasattr(player, 'get_volume') else 0
            self._show_message(f"{'Muted' if volume == 0 else f'Volume: {volume}%'}")
    
    def _adjust_volume(self, delta):
        """Adjust volume by delta"""
        player = self._get_player_window()
        if player:
            current = player.get_volume() if hasattr(player, 'get_volume') else 50
            new_volume = max(0, min(100, current + delta))
            
            if hasattr(player, 'set_volume'):
                player.set_volume(new_volume)
            
            # Emit signal to engine
            engine = self._get_engine()
            if engine:
                engine.set_volume(new_volume)
            
            self._show_message(f"Volume: {new_volume}%", 1000)
    
    def _seek_relative(self, delta_ms):
        """Seek relative to current position"""
        engine = self._get_engine()
        if engine:
            if hasattr(engine, 'get_position') and hasattr(engine, 'seek_to_position'):
                current_pos = engine.get_position()
                new_pos = max(0, current_pos + delta_ms)
                engine.seek_to_position(new_pos)
                
                direction = "→" if delta_ms > 0 else "←"
                seconds = abs(delta_ms) // 1000
                self._show_message(f"Seek {direction} {seconds}s", 1000)
    
    # ===== SETTINGS =====
    
    def _open_settings(self):
        """Open settings dialog"""
        if hasattr(self.window, 'open_settings'):
            self.window.open_settings()
        else:
            try:
                from ui.windows.settings_dialog import show_settings
                show_settings(self.window)
            except ImportError:
                self._show_message("Settings dialog not available")
    
    # ===== UTILITY =====
    
    def _show_message(self, text, duration=2000):
        """Show status message if available"""
        if hasattr(self.window, 'show_message'):
            self.window.show_message(text, duration)
        else:
            print(f"ℹ️ {text}")