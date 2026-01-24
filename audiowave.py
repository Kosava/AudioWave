#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# audiowave.py - AudioWave Player sa ThemeManager integracijom
# Version 0.3.1 - Sa GStreamer EQ podrškom

import sys
import os
from pathlib import Path

# ===== Stabilan import path (radi i iz /usr/lib/audiowave) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

from core.config import Config
from core.playlist import PlaylistManager
from core.theme_manager import ThemeManager
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
        print(f"🔧 Preferred engine from settings: {preferred}")

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


class AudioWaveApp:
    """Glavna aplikacija sa objedinjenim prozorom"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("AudioWave")
        self.app.setStyle("Fusion")

        # (profi detalj za Wayland / GNOME)
        try:
            self.app.setDesktopFileName("audiowave.desktop")
        except Exception:
            pass

        # Core komponente
        print("🔧 Initializing core components...")
        self.config = Config()

        # ✅ KORISTI FACTORY ZA ENGINE (GStreamer ako je dostupan)
        self.engine = create_audio_engine()

        self.playlist_manager = PlaylistManager()

        # Theme Manager
        print("🎨 Initializing theme manager...")
        self.theme_manager = ThemeManager()

        # Poveži engine sa app
        self.engine.app = self

        print("🪟 Creating unified window...")
        # Inicijalizuj samo UnifiedPlayerWindow
        self.main_window = UnifiedPlayerWindow(self)

        # Dodaj window atribut za kompatibilnost
        self.window = self.main_window

        # Atribut za unified_window kompatibilnost
        self.unified_window = self.main_window

        # Verifikacija teme
        print("🎨 Theme system verification:")
        print(f"   Available themes: {self.theme_manager.get_available_themes()}")
        print(f"   Current theme: {self.theme_manager.current_theme}")

        # Testiraj temu direktno
        print("🎨 Testing theme application...")
        if hasattr(self.theme_manager, "apply_to_all_windows"):
            print("🎨 Using apply_to_all_windows method")
            self.theme_manager.apply_to_all_windows(self.main_window, "Ocean")
        else:
            print("🎨 Using apply_theme method")
            self.theme_manager.apply_theme(self.main_window, "Ocean")

        print("✅ Theme test completed")

        # Refresh UI
        self.main_window.repaint()
        QApplication.processEvents()

        # Postavi objectName za lakše theming
        if hasattr(self.main_window, "player_window"):
            try:
                self.main_window.player_window.setObjectName("player_window")
                print("🎯 Set objectName for player_window")
            except Exception:
                pass

        if hasattr(self.main_window, "playlist_panel"):
            try:
                self.main_window.playlist_panel.setObjectName("playlist_panel")
                print("🎯 Set objectName for playlist_panel")
            except Exception:
                pass

        # Poveži signale
        self.setup_connections()

        # Učitaj demo muziku
        self.setup_test_music()

        print("✅ Application initialized")
        print("=" * 50)

    def setup_connections(self):
        """Poveži signale između komponenti"""
        try:
            # Engine -> UI (preko unified window)
            self.engine.playback_started.connect(self.on_playback_started)
            self.engine.playback_ended.connect(self.on_playback_ended)
            self.engine.error_occurred.connect(self.show_error)

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
                    lambda: self.main_window.show_message("Playlist updated")
                )

        except Exception as e:
            print(f"⚠️ Error setting up connections: {e}")

    def on_playback_started(self, filepath):
        """Ažuriraj stanje kada pesma krene"""
        try:
            if hasattr(self, "playlist_manager"):
                if filepath in self.playlist_manager.current_playlist:
                    index = self.playlist_manager.current_playlist.index(filepath)
                    self.playlist_manager.current_index = index
                    print(f"📋 Playing: {Path(filepath).name}")

                    # Obavesti unified window
                    if hasattr(self.main_window, "show_message"):
                        self.main_window.show_message(
                            f"Playing: {Path(filepath).name}"
                        )
        except Exception as e:
            print(f"⚠️ Error in on_playback_started: {e}")

    def on_playback_ended(self):
        """Auto-play sledeće pesme"""
        try:
            if hasattr(self, "playlist_manager"):
                if self.playlist_manager.repeat != "one":
                    # Delay za stabilnost
                    QTimer.singleShot(500, self.engine.play_next)
        except Exception as e:
            print(f"⚠️ Error in on_playback_ended: {e}")

    def show_error(self, error_msg):
        """Prikaži grešku"""
        try:
            QMessageBox.warning(self.main_window, "Playback Error", error_msg)
        except Exception as e:
            print(f"⚠️ Error showing error message: {e}")

    def setup_test_music(self):
        """Automatsko skeniranje muzike - dodaj demo pesme"""
        try:
            demo_files = [
                "Summer Vibes.mp3",
                "Chill Night.flac",
                "Electronic Dreams.ogg",
            ]

            # Dodaj u playlist kao placeholder
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
                "Select Audio",
                str(Path.home() / "Music"),
                "Audio (*.mp3 *.wav *.flac)",
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

    def run(self):
        """Pokreni aplikaciju"""
        print("🎬 Starting main window...")
        self.main_window.show()

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


def main():
    """Glavna funkcija sa sigurnim zatvaranjem"""
    try:
        print("=" * 50)
        print("🚀 Starting AudioWave...")
        print("=" * 50)

        player = AudioWaveApp()

        # ✅ DEBUG: Prikaži EQ info
        debug_eq_info(player)

        exit_code = player.run()

        print("=" * 50)
        print("👋 Shutting down AudioWave...")
        print("=" * 50)

        # Čisto zatvaranje
        if hasattr(player, "engine"):
            try:
                player.engine.cleanup()
            except Exception:
                pass

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt - shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unhandled exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
