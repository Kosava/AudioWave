#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# audiowave.py - AudioWave Player sa ThemeManager integracijom
# Version 0.4.5 - FIXED: Auto-play next track issues

import sys
import os
from pathlib import Path

# ===== Stabilan import path (radi i iz /usr/lib/audiowave) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication, QMessageBox, QStyleFactory
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, Qt
from PyQt6.QtGui import QPalette, QColor

from core.config import Config
from core.playlist import PlaylistManager
from core.theme_manager import ThemeManager
from core.url_stream_helper import patch_gstreamer_play_file, is_stream_url
from ui.windows.unified_player_window import UnifiedPlayerWindow


# ========== ENGINE FACTORY ==========
# Koristi GStreamer ako je dostupan, inače Qt Multimedia

def create_audio_engine():
    """
    Kreiraj audio engine - preferira GStreamer zbog EQ podrške.
    """
    # Prvo probaj učitati sačuvanu preferenciju
    try:
        from core.engine_factory import load_engine_preference, create_engine
        preferred = load_engine_preference()
        print(f"🔍 Preferred engine from settings: {preferred}")

        if preferred == "gstreamer":
            engine = create_engine("gstreamer")
            if engine:
                print("✅ Using GStreamer engine (with EQ support)")
                return engine
    except ImportError:
        pass

    # Probaj GStreamer direktno
    try:
        from core.gstreamer_engine import GStreamerEngine, GSTREAMER_AVAILABLE
        if GSTREAMER_AVAILABLE:
            engine = GStreamerEngine()
            print("🔊 Audio engine initialized with GStreamer (EQ supported)")
            return engine
    except ImportError as e:
        print(f"⚠️ GStreamer not available: {e}")
    except Exception as e:
        print(f"⚠️ GStreamer init failed: {e}")

    # Fallback na Qt Multimedia
    from core.engine import AudioEngine
    engine = AudioEngine()
    print("🔊 Audio engine initialized with Qt Multimedia (no EQ support)")
    return engine


class ApplicationSignals(QObject):
    """Centralni signali za aplikaciju"""
    theme_apply_requested = pyqtSignal(str)
    playback_state_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    shutdown_requested = pyqtSignal()


class AudioWaveApp:
    """Glavna aplikacija sa objedinjenim prozorom"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("AudioWave")
        self.app.setOrganizationName("AudioWave")
        self.app.setOrganizationDomain("audiowave.example.com")
        
        # Postavi visok DPI support - koristi Qt enumove
        try:
            self.app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            self.app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
            print("🔍 High DPI scaling enabled")
        except AttributeError:
            print("⚠️ DPI scaling attributes not available in this Qt version")

        # Postavi Fusion style kao osnovni
        available_styles = QStyleFactory.keys()
        if "Fusion" in available_styles:
            self.app.setStyle("Fusion")
            print(f"🎨 Using Fusion style (available: {available_styles})")
        else:
            print(f"⚠️ Fusion style not available, using default (available: {available_styles})")

        # Centralni signali
        self.signals = ApplicationSignals()

        # ===== CORE KOMPONENTE =====
        print("🔍 Initializing core components...")
        
        # ✅ 1. Config se učitava PRVO (sa load() metodom)
        self.config = Config()
        print(f"📁 Config loaded from: {self.config.get_config_path()}")
        
        # ✅ 2. Engine
        self.engine = create_audio_engine()
        
        # ✅ 2.1 Patch engine za URL streaming podršku
        try:
            from core.gstreamer_engine import GStreamerEngine
            if isinstance(self.engine, GStreamerEngine):
                patch_gstreamer_play_file(self.engine)
                print("✅ URL streaming support enabled")
        except Exception as e:
            print(f"⚠️ URL streaming patch failed: {e}")
        
        # ✅ 3. Playlist Manager
        self.playlist_manager = PlaylistManager()

        # ===== THEME MANAGER SA CONFIG INTEGRATION =====
        print("🎨 Initializing theme manager...")
        
        # ✅ Pass config to ThemeManager
        self.theme_manager = ThemeManager(self.config)
        
        # Povezi engine sa app
        self.engine.app = self

        # ===== MAIN WINDOW =====
        print("🪟 Creating unified window...")
        self.main_window = UnifiedPlayerWindow(self)

        # Poveži aplikaciju sa prozorom za globalni pristup
        self.app.main_window = self.main_window  # OVO JE DODATA LINIJA

        # Atributi za kompatibilnost
        self.window = self.main_window
        self.unified_window = self.main_window

        # Postavi objectName za lakše theming
        self._setup_object_names()

        # ===== LOAD SAVED THEME =====
        print("🎨 Loading saved theme...")
        saved_theme = self.config.get_theme()
        print(f"📋 Saved theme: {saved_theme}")
        
        # ✅ Apply saved theme (without re-saving)
        self.theme_manager.load_saved_theme(self.main_window)
        
        print(f"✅ Applied theme: {self.theme_manager.current_theme}")

        # Verifikacija teme
        print("🎨 Theme system verification:")
        print(f"   Available themes: {len(self.theme_manager.get_available_themes())} themes")
        print(f"   Current theme: {self.theme_manager.current_theme}")
        print(f"   Is dark: {self.theme_manager.is_dark_theme()}")

        # Učitaj prethodno stanje
        self._load_application_state()

        # Poveži signale
        self.setup_connections()

        # Učitaj demo muziku samo ako je prazna playlist
        if not self.playlist_manager.current_playlist:
            self.setup_test_music()

        print("✅ Application initialized")
        print("=" * 50)

    def _setup_object_names(self):
        """Postavi objectName za glavne komponente"""
        try:
            if hasattr(self.main_window, "player_window"):
                self.main_window.player_window.setObjectName("player_window")
                print("🎭 Set objectName for player_window")
            
            if hasattr(self.main_window, "playlist_panel"):
                self.main_window.playlist_panel.setObjectName("playlist_panel")
                print("🎭 Set objectName for playlist_panel")
            
            if hasattr(self.main_window, "title_bar"):
                self.main_window.title_bar.setObjectName("title_bar")
                print("🎭 Set objectName for title_bar")
            
            if hasattr(self.main_window, "controls_panel"):
                self.main_window.controls_panel.setObjectName("controls_panel")
                print("🎭 Set objectName for controls_panel")
                
        except Exception as e:
            print(f"⚠️ Error setting object names: {e}")

    def _load_application_state(self):
        """Učitaj prethodno sačuvano stanje aplikacije"""
        try:
            # Učitaj volume
            saved_volume = self.config.get_volume()
            if saved_volume is not None:
                self.engine.set_volume(saved_volume)
                print(f"🔊 Restored volume: {saved_volume}")
            
            # Učitaj window geometry
            geometry = self.config.get_window_geometry()
            if geometry:
                self.main_window.setGeometry(
                    geometry.get('x', 100),
                    geometry.get('y', 100),
                    geometry.get('width', 900),
                    geometry.get('height', 600)
                )
                print(f"📐 Restored window geometry: {geometry}")
            
            # Učitaj playlist state ako postoji
            if hasattr(self.playlist_manager, 'load_state'):
                self.playlist_manager.load_state(self.config)
                
        except Exception as e:
            print(f"⚠️ Error loading application state: {e}")

    def setup_connections(self):
        """Poveži signale između komponenti"""
        try:
            # Engine -> UI (preko unified window)
            self.engine.playback_started.connect(self.on_playback_started)
            self.engine.playback_ended.connect(self.on_playback_ended)  # OVO JE BITNO
            self.engine.error_occurred.connect(self.show_error)
            
            # OBAVEŠTENJE: position_changed može slati samo position ili (position, duration)
            # Prilagodite se na osnovu engine implementacije
            if hasattr(self.engine, 'position_changed'):
                try:
                    # Probaj da povežeš oba formata
                    self.engine.position_changed.connect(self.on_position_changed)
                except Exception:
                    # Ako ne radi, probaj alternativni način
                    pass
            
            # Poveži volume signal ako postoji
            if hasattr(self.engine, 'volume_changed'):
                self.engine.volume_changed.connect(self.on_volume_changed)

            # Ako unified window ima kontrolne signale, poveži ih
            if hasattr(self.main_window, "next_clicked"):
                self.main_window.next_clicked.connect(self.engine.play_next)

            if hasattr(self.main_window, "prev_clicked"):
                self.main_window.prev_clicked.connect(self.engine.play_prev)

            if hasattr(self.main_window, "volume_changed"):
                self.main_window.volume_changed.connect(self.engine.set_volume)

            # Playlist manager signale poveži sa window-om
            if hasattr(self.playlist_manager, "playlist_changed"):
                self.playlist_manager.playlist_changed.connect(
                    self.on_playlist_changed
                )
            
            # ✅ Theme changed signal
            self.theme_manager.theme_changed.connect(self.on_theme_changed)
            
            # Centralni signali
            self.signals.theme_apply_requested.connect(self.on_theme_requested)
            self.signals.error_occurred.connect(self.show_error)
            self.signals.shutdown_requested.connect(self.shutdown)

        except Exception as e:
            print(f"⚠️ Error setting up connections: {e}")

    def on_playlist_changed(self):
        """Obrada promene playliste"""
        try:
            if hasattr(self.main_window, "show_message"):
                count = len(self.playlist_manager.current_playlist)
                self.main_window.show_message(f"Playlist updated ({count} tracks)")
            
            # Ažuriraj UI ako postoji playlist panel
            if hasattr(self.main_window, 'refresh_playlist_display'):
                self.main_window.refresh_playlist_display()
                
        except Exception as e:
            print(f"⚠️ Error in on_playlist_changed: {e}")
    
    def on_position_changed(self, *args):
        """Ažuriraj progress bar - podržava različite formate signala"""
        try:
            if len(args) == 1:
                # Samo position
                position = args[0]
                duration = None
            elif len(args) >= 2:
                # position i duration
                position = args[0]
                duration = args[1]
            else:
                print(f"⚠️ Unexpected position_changed signal format: {args}")
                return
                
            if hasattr(self.main_window, 'update_progress'):
                self.main_window.update_progress(position, duration)
        except Exception as e:
            print(f"⚠️ Error in on_position_changed: {e}, args: {args}")
    
    def on_volume_changed(self, volume):
        """Ažuriraj UI za volume"""
        try:
            if hasattr(self.main_window, 'update_volume_display'):
                self.main_window.update_volume_display(volume)
        except Exception as e:
            print(f"⚠️ Error in on_volume_changed: {e}")

    def on_theme_changed(self, theme_name: str):
        """Called when theme changes"""
        print(f"🎨 Theme changed to: {theme_name}")
        print(f"💾 Theme saved to config")
        
        # Sačuvaj u config
        self.config.set_theme(theme_name)
        
        # Ažuriraj sve UI komponente
        self._refresh_all_ui_components()
        
        # Objavi poruku
        if hasattr(self.main_window, 'show_message'):
            self.main_window.show_message(f"Theme applied: {theme_name}")

    def on_theme_requested(self, theme_name: str):
        """Zahtev za primenu teme iz bilo kog dela aplikacije"""
        print(f"🎨 Theme apply requested: {theme_name}")
        self.theme_manager.apply_theme(theme_name, self.main_window)

    def _refresh_all_ui_components(self):
        """Osveži sve UI komponente nakon promene teme"""
        try:
            # Osveži palette aplikacije
            if self.theme_manager.current_theme in ["dark", "midnight", "slate"]:
                dark_palette = QPalette()
                dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
                dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
                dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
                dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
                dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
                dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
                dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
                dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
                dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
                dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
                dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
                dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
                dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
                self.app.setPalette(dark_palette)
            else:
                self.app.setPalette(self.app.style().standardPalette())

            # Osveži sve widgete
            if hasattr(self.main_window, 'refresh_theme'):
                self.main_window.refresh_theme()
            
            # Force repaint svih widgeta
            self.main_window.repaint()
            for widget in self.main_window.findChildren(QObject):
                if hasattr(widget, 'repaint'):
                    widget.repaint()
            
            # Process events za odmah ažuriranje
            QApplication.processEvents()
            
            print("✅ UI components refreshed after theme change")
            
        except Exception as e:
            print(f"⚠️ Error refreshing UI components: {e}")

    def on_playback_started(self, filepath):
        """Ažuriraj stanje kada pesma krene"""
        try:
            if hasattr(self, "playlist_manager"):
                if filepath in self.playlist_manager.current_playlist:
                    index = self.playlist_manager.current_playlist.index(filepath)
                    self.playlist_manager.current_index = index
                    print(f"📁 Playing: {Path(filepath).name}")

                    # Obavesti unified window
                    if hasattr(self.main_window, "show_message"):
                        self.main_window.show_message(
                            f"Playing: {Path(filepath).name}"
                        )
                    
                    # Ažuriraj playlist display
                    if hasattr(self.main_window, 'update_current_track'):
                        self.main_window.update_current_track(index)
                        
        except Exception as e:
            print(f"⚠️ Error in on_playback_started: {e}")

    def on_playback_ended(self):
        """Obrada završetka pesme"""
        try:
            print("📢 Playback ended (UI notified)")
            # NE pozivaj engine.play_next() ovde!
            # Engine će sam hendlovati auto-next
        except Exception as e:
            print(f"⚠️ Error in on_playback_ended: {e}")

    def show_error(self, error_msg):
        """Prikaži grešku"""
        try:
            QMessageBox.warning(self.main_window, "AudioWave Error", error_msg)
        except Exception as e:
            print(f"⚠️ Error showing error message: {e}")

    def setup_test_music(self):
        """Automatsko skeniranje muzike - dodaj demo pesme"""
        try:
            # Prvo proveri da li postoje realne pesme u Music folderu
            music_dir = Path.home() / "Music"
            audio_extensions = [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"]
            
            real_files = []
            if music_dir.exists():
                for ext in audio_extensions:
                    real_files.extend(list(music_dir.glob(f"*{ext}")))
                    real_files.extend(list(music_dir.glob(f"**/*{ext}")))
            
            if real_files:
                # Uzmi prvih 5 realnih fajlova
                files_to_add = [str(f) for f in real_files[:5]]
                self.playlist_manager.add_files(files_to_add)
                print(f"🎵 Added {len(files_to_add)} real tracks from Music folder")
            else:
                # Koristi demo placeholdere
                demo_files = [
                    "Summer Vibes.mp3",
                    "Chill Night.flac",
                    "Electronic Dreams.ogg",
                ]
                for demo_file in demo_files:
                    self.playlist_manager.add_files([demo_file])
                print(f"🎵 Added {len(demo_files)} demo tracks to playlist")

        except Exception as e:
            print(f"⚠️ Error setting up test music: {e}")

    def add_real_music(self):
        """Ovu funkciju sada možeš pozivati direktno iz Unified prozora"""
        from PyQt6.QtWidgets import QFileDialog

        try:
            files, _ = QFileDialog.getOpenFileNames(
                self.main_window,
                "Select Audio Files",
                str(Path.home() / "Music"),
                "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;All Files (*)"
            )
            if files:
                self.playlist_manager.add_files(files)

                # Obavesti korisnika
                if hasattr(self.main_window, "show_message"):
                    self.main_window.show_message(f"Added {len(files)} tracks")

                # Ako nije ništa puštano, pusti prvu
                if len(self.playlist_manager.current_playlist) > 0:
                    if self.engine.current_file is None:
                        self.engine.play_file(
                            self.playlist_manager.current_playlist[0]
                        )

        except Exception as e:
            print(f"⚠️ Error adding music: {e}")
    
    def save_state_periodically(self):
        """Periodično čuvanje stanja (može se pozvati iz timera)"""
        try:
            # Sačuvaj trenutni volume
            if hasattr(self.engine, 'volume'):
                self.config.set_volume(self.engine.volume())
            
            # Sačuvaj playlist stanje ako postoji metoda
            if hasattr(self.playlist_manager, 'save_state'):
                self.playlist_manager.save_state(self.config)
            
            print("💾 Periodic state saved")
            
        except Exception as e:
            print(f"⚠️ Error in periodic save: {e}")

    def shutdown(self):
        """Clean shutdown - save state"""
        print("💾 Saving application state...")
        
        try:
            # Save window geometry
            if hasattr(self.main_window, 'geometry'):
                geom = self.main_window.geometry()
                self.config.set_window_geometry({
                    'x': geom.x(),
                    'y': geom.y(),
                    'width': geom.width(),
                    'height': geom.height()
                })
            
            # Save volume
            if hasattr(self.engine, 'volume'):
                self.config.set_volume(self.engine.volume())
            
            # Save current theme
            self.config.set_theme(self.theme_manager.current_theme)
            
            # Final config save
            self.config.save()
            print("✅ Application state saved")
            
        except Exception as e:
            print(f"⚠️ Error saving state: {e}")
        
        # DELAYED ENGINE CLEANUP - posle svih drugih cleanup-a
        try:
            if hasattr(self, 'engine'):
                QTimer.singleShot(100, self._delayed_engine_cleanup)
        except:
            pass

    def _delayed_engine_cleanup(self):
        """Cleanup engine sa delay-om da izbegneš segfault"""
        try:
            if hasattr(self, 'engine'):
                self.engine.cleanup()
                print("🔧 Engine cleanup completed")
        except Exception as e:
            print(f"⚠️ Error in delayed engine cleanup: {e}")

    def run(self):
        """Pokreni aplikaciju"""
        print("▶️ Starting main window...")
        self.main_window.show()

        # Postavi timer za periodično čuvanje stanja
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_state_periodically)
        self.save_timer.start(30000)  # Svakih 30 sekundi

        # Final UI refresh
        self.main_window.repaint()
        QApplication.processEvents()

        return self.app.exec()


def debug_eq_info(player):
    """Debug info o EQ podršci"""
    print("\n" + "=" * 50)
    print("🎛️ EQ DEBUG INFO")
    print("=" * 50)

    engine = player.engine
    engine_type = type(engine).__name__
    engine_module = type(engine).__module__

    print(f"   Engine type: {engine_type}")
    print(f"   Engine module: {engine_module}")

    is_gstreamer = "GStreamer" in engine_type or "gstreamer" in engine_module
    print(f"   Is GStreamer: {is_gstreamer}")

    has_eq = hasattr(engine, "set_equalizer") and hasattr(engine, "equalizer")
    print(f"   Has EQ support: {has_eq}")

    if has_eq:
        has_eq_element = getattr(engine, "equalizer", None) is not None
        print(f"   EQ element exists: {has_eq_element}")

    if is_gstreamer and has_eq:
        print("\n   ✅ EQ SHOULD WORK!")
        print("   Otvori EQ sa F3 i testiraj.")
    elif not is_gstreamer:
        print("\n   ❌ Qt Multimedia - EQ neće raditi!")
        print("   Promeni u ~/.audiowave/audio_settings.json:")
        print('   {"preferred_engine": "gstreamer"}')

    print("=" * 50 + "\n")


def debug_theme_info(player):
    """Debug info o theme persistence"""
    print("\n" + "=" * 50)
    print("🎨 THEME PERSISTENCE DEBUG")
    print("=" * 50)
    
    print(f"   Config file: {player.config.get_config_path()}")
    print(f"   Config exists: {player.config.get_config_path().exists()}")
    print(f"   Saved theme: {player.config.get_theme()}")
    print(f"   Current theme: {player.theme_manager.current_theme}")
    print(f"   Themes match: {player.config.get_theme() == player.theme_manager.current_theme}")
    
    # Proveri da li su sve komponente pravilno postavljene
    print("\n   Component objectNames:")
    if hasattr(player.main_window, 'player_window'):
        print(f"   - player_window: {player.main_window.player_window.objectName()}")
    if hasattr(player.main_window, 'playlist_panel'):
        print(f"   - playlist_panel: {player.main_window.playlist_panel.objectName()}")
    
    if player.config.get_theme() == player.theme_manager.current_theme:
        print("\n   ✅ THEME PERSISTENCE WORKING!")
    else:
        print("\n   ⚠️ Theme mismatch - check integration")
    
    print("=" * 50 + "\n")


def debug_app_info(player):
    """Opšti debug info o aplikaciji"""
    print("\n" + "=" * 50)
    print("🔍 APPLICATION DEBUG INFO")
    print("=" * 50)
    
    print(f"   Playlist tracks: {len(player.playlist_manager.current_playlist)}")
    print(f"   Current index: {player.playlist_manager.current_index}")
    print(f"   Engine ready: {player.engine is not None}")
    print(f"   Window visible: {player.main_window.isVisible()}")
    print(f"   Config loaded: {player.config.config is not None}")
    
    # Proveri da li su signali dostupni (pojednostavljena verzija za PyQt6)
    engine_signals = []
    if hasattr(player.engine, 'playback_started'):
        engine_signals.append("playback_started")
    if hasattr(player.engine, 'playback_ended'):
        engine_signals.append("playback_ended")
    if hasattr(player.engine, 'error_occurred'):
        engine_signals.append("error_occurred")
    if hasattr(player.engine, 'position_changed'):
        engine_signals.append("position_changed")
    if hasattr(player.engine, 'volume_changed'):
        engine_signals.append("volume_changed")
    
    print(f"   Engine signals available: {engine_signals}")
    print("=" * 50 + "\n")


def main():
    """Glavna funkcija aplikacije"""
    player = None
    try:
        print("=" * 50)
        print("🚀 Starting AudioWave...")
        print("=" * 50)

        player = AudioWaveApp()

        exit_code = player.run()

        print("=" * 50)
        print("👋 Shutting down AudioWave...")
        print("=" * 50)

    except KeyboardInterrupt:
        exit_code = 0
    except Exception as e:
        print(f"❌ Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        if player:
            try:
                player.shutdown()
            except Exception:
                pass

        sys.exit(exit_code)


if __name__ == "__main__":
    main()