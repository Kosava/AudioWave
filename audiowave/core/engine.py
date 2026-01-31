# -*- coding: utf-8 -*-
# core/engine.py
"""
Audio Engine - Pravi audio playback sa PyQt6 QMediaPlayer
Complete implementation with seek support and auto-play next
"""

import os
import random
import time
import traceback
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimedia import QMediaMetaData

# Dodaj import za MetadataReader
from core.metadata_reader import MetadataReader  # ✔ NOVO: Importuj napredni reader

class AudioEngine(QObject):
    """Audio engine sa pravim audio playbackom i seek funkcionalnoscu"""
    
    # Signali
    metadata_changed = pyqtSignal(dict)
    position_changed = pyqtSignal(int)
    volume_changed = pyqtSignal(int)
    playback_started = pyqtSignal(str)
    playback_stopped = pyqtSignal()
    playback_paused = pyqtSignal()
    playback_resumed = pyqtSignal()
    playback_ended = pyqtSignal()
    duration_changed = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Kreiraj audio komponente
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        
        # Postavi pocetne vrednosti
        self._volume = 70
        self.audio_output.setVolume(self._volume / 100.0)
        self._playing = False
        self._paused = False
        self.current_file = None
        self.app = None
        self._last_next_time = 0  # Za debounce
        self._is_auto_play_in_progress = False  # Flag za auto-play
        
        # Zaštita od duplih poziva
        self._last_play_file_time = 0
        self._is_loading_file = False
        
        # Timer za azuriranje poziciju
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.position_timer.setInterval(100)
        
        # Povezi signale
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.errorOccurred.connect(self.on_player_error)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.metaDataChanged.connect(self.on_metadata_changed)
        
        print("🔊 Audio engine initialized with real audio playback")
        
        # Flag za pracenje unistavanja
        self.is_cleaning_up = False
        
        # ✔ NOVO: Instanciraj MetadataReader
        self.metadata_reader = MetadataReader()
    
    # ========== CLEANUP ==========
    
    def cleanup(self):
        """Ocisti resurse"""
        self.is_cleaning_up = True
        
        try:
            self.stop()
            self.position_timer.stop()
            
            # Diskonektuj sve signale
            if self.player:
                try:
                    self.player.playbackStateChanged.disconnect()
                    self.player.mediaStatusChanged.disconnect()
                    self.player.errorOccurred.disconnect()
                    self.player.durationChanged.disconnect()
                    self.player.positionChanged.disconnect()
                    self.player.metaDataChanged.disconnect()
                except:
                    pass
                
                self.player.setSource(QUrl())
                self.player.deleteLater()
            
            # Zaustavi timer
            self.position_timer.deleteLater()
            
            print("🔊 Audio engine cleaned up")
        except:
            pass
    
    def __del__(self):
        """Destruktor za cisto brisanje"""
        self.cleanup()
    
    # ========== PLAYBACK CONTROL ==========
    
    def play_file(self, filepath):
        """Pusti stvarni audio fajl"""
        if self.is_cleaning_up:
            return
        
        print(f"\n{'='*60}")
        print(f"🐛 [DEBUG engine] play_file() called: {Path(filepath).name}")
        print(f"{'='*60}")
        
        # ZAŠTITA OD DUPLIH POZIVA
        current_time = time.time()
        if current_time - self._last_play_file_time < 0.5:
            print(f"⚠️ play_file() called too quickly ({current_time - self._last_play_file_time:.2f}s), ignoring duplicate")
            print(f"{'='*60}\n")
            return
        
        self._last_play_file_time = current_time
        
        if self._is_loading_file:
            print(f"⚠️ Already loading a file, ignoring duplicate call")
            print(f"{'='*60}\n")
            return
        
        self._is_loading_file = True
        
        if not os.path.exists(filepath):
            # Ako fajl ne postoji, koristi demo
            print(f"⚠️ File not found: {filepath}, using demo")
            self._is_loading_file = False
            self.play_demo(filepath)
            return
        
        try:
            # Zaustavi prethodni playback
            self.stop()
            
            # Postavi fajl
            self.current_file = filepath
            url = QUrl.fromLocalFile(filepath)
            self.player.setSource(url)
            
            # Pokreni playback
            self.player.play()
            self._playing = True
            self._paused = False
            
            # Emituj signale
            self.playback_started.emit(filepath)
            self.position_timer.start()
            
            # ✔ IZMENJENO: Koristi MetadataReader umesto prostog parsovanja
            self.extract_metadata(filepath)
            
            print(f"🎵 Playing: {Path(filepath).name}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            self.error_occurred.emit(f"Error playing file: {str(e)}")
            print(f"❌ Error: {e}")
            # Fallback na demo
            self._is_loading_file = False
            self.play_demo(filepath)
        finally:
            # Resetuj flag nakon kratkog vremena
            QTimer.singleShot(500, lambda: setattr(self, '_is_loading_file', False))
    
    def play_demo(self, filename):
        """Simuliraj playback za demo fajlove"""
        if self.is_cleaning_up:
            return
        
        print(f"\n{'='*60}")
        print(f"🐛 [DEBUG engine] play_demo() called: {filename}")
        print(f"{'='*60}")
        
        self.stop()
        
        self.current_file = filename
        self._playing = True
        self._paused = False
        
        # Emituj signale za demo
        self.playback_started.emit(filename)
        self.position_timer.start()
        
        # Generisi demo metadata
        filename_display = Path(filename).name
        metadata = {
            "title": filename_display.replace(".mp3", "").replace(".flac", "").replace("_", " ").title(),
            "artist": random.choice(["Demo Artist", "Test Band", "Sample Musician"]),
            "album": random.choice(["Demo Album", "Test Tracks", "Samples"]),
            "duration": 180000,  # 3 minuta
            "filename": filename_display,
            "bitrate": "320 kbps",
            "year": "2024"
        }
        self.metadata_changed.emit(metadata)
        self.duration_changed.emit(180000)
        
        print(f"🎵 Playing (demo): {filename_display}")
        print(f"{'='*60}\n")
    
    def toggle_play_pause(self):
        """Toggle play/pause"""
        if self.is_cleaning_up:
            return
        
        print(f"🐛 [DEBUG engine] toggle_play_pause() - playing={self._playing}, paused={self._paused}")
        
        if self._playing:
            if self._paused:
                self.resume()
            else:
                self.pause()
        elif self.current_file:
            # Nije playing, ali imamo fajl - pokreni
            self.play_file(self.current_file)
    
    def play(self):
        """Play (resume ako je pauzirano)"""
        if self.is_cleaning_up:
            return
        
        if self._paused:
            self.resume()
        elif self.current_file and not self._playing:
            self.play_file(self.current_file)
    
    def stop(self):
        """Zaustavi playback"""
        if self.is_cleaning_up:
            return
        
        try:
            print(f"🐛 [DEBUG engine] stop() called")
            self.player.stop()
            self._playing = False
            self._paused = False
            self.position_timer.stop()
            self._is_auto_play_in_progress = False  # Reset auto-play
            self.playback_stopped.emit()
            print("⏹ Stopped")
        except:
            pass
    
    def pause(self):
        """Pauziraj playback"""
        if self.is_cleaning_up:
            return
        
        if self._playing and not self._paused:
            try:
                print(f"🐛 [DEBUG engine] pause() called")
                self.player.pause()
                self._paused = True
                self.position_timer.stop()
                self._is_auto_play_in_progress = False  # Prekini auto-play
                self.playback_paused.emit()
                print("⏸ Paused")
            except:
                pass
    
    def resume(self):
        """Nastavi playback"""
        if self.is_cleaning_up:
            return
        
        if self._playing and self._paused:
            try:
                print(f"🐛 [DEBUG engine] resume() called")
                self.player.play()
                self._paused = False
                self.position_timer.start()
                self.playback_resumed.emit()
                print("▶ Resumed")
            except:
                pass
    
    # ========== SEEK FUNCTIONALITY ==========
    
    def seek_to_position(self, position_ms):
        """
        Seek na određenu poziciju u pesmi
        
        Args:
            position_ms: Poziciju u milisekundama
        """
        if self.is_cleaning_up:
            return
        
        try:
            if self.player and self._playing:
                # Ogranici poziciju na validne vrednosti
                duration = self.get_duration()
                position_ms = max(0, min(duration, position_ms))
                
                # Postavi poziciju u QMediaPlayer
                self.player.setPosition(position_ms)
                
                print(f"⏩ Seek to: {position_ms}ms")
        except:
            pass
    
    # ========== VOLUME CONTROL ==========
    
    def set_volume(self, volume):
        """Postavi volumen"""
        if self.is_cleaning_up:
            return
        
        volume = max(0, min(100, volume))
        self._volume = volume
        self.audio_output.setVolume(volume / 100.0)
        self.volume_changed.emit(volume)
        print(f"🔊 Volume set to {volume}%")
    
    def get_volume(self):
        """Dobavi trenutni volumen"""
        return self._volume
    
    def get_position(self):
        """Dobavi trenutnu poziciju u ms"""
        if self.player:
            return self.player.position()
        return 0
    
    def get_duration(self):
        """Dobavi duzinu trake u ms"""
        if self.player:
            return self.player.duration()
        return 0
    
    def is_playing(self):
        """Da li se reprodukuje"""
        return self._playing and not self._paused
    
    def is_paused(self):
        """Da li je pauzirano"""
        return self._paused
    
    def is_stopped(self):
        """Da li je zaustavljeno"""
        return not self._playing
    
    def play_next(self, auto_play=False):
        """Pusti sledecu pesmu iz playliste"""
        if self.is_cleaning_up:
            return
        
        print(f"🐛 [DEBUG engine] play_next() called, auto_play={auto_play}")
        
        current_time = time.time()
        if current_time - self._last_next_time < 0.5:
            print(f"⚠️ Next too quick ({current_time - self._last_next_time:.2f}s), ignoring")
            return
        
        self._last_next_time = current_time
        
        if auto_play:
            self._is_auto_play_in_progress = True
        
        try:
            if self.app and hasattr(self.app, 'playlist_manager'):
                next_file = self.app.playlist_manager.next()
                if next_file:
                    print(f"➡️ Playing next: {Path(next_file).name}")
                    self.play_file(next_file)
                else:
                    print("📚 End of playlist")
                    self.stop()
        finally:
            if auto_play:
                self._is_auto_play_in_progress = False
    
    def play_previous(self):
        """Pusti prethodnu pesmu iz playliste"""
        if self.is_cleaning_up:
            return
        
        print(f"🐛 [DEBUG engine] play_previous() called")
        
        if self.app and hasattr(self.app, 'playlist_manager'):
            prev_file = self.app.playlist_manager.prev()
            if prev_file:
                print(f"⬅️ Playing previous: {Path(prev_file).name}")
                self.play_file(prev_file)
            else:
                print("⏮ Start of playlist")
    
    # ========== METADATA ==========
    
    def extract_metadata(self, filepath):
        """✔ IZMENJENO: Koristi MetadataReader za čitanje stvarnih tagova iz fajla"""
        if self.is_cleaning_up:
            return
        
        try:
            # Koristi napredni reader za metadata
            metadata = self.metadata_reader.read_metadata(filepath)
            
            # Ako nema tagova, fallback na filename parsovanje
            if metadata.get('error') or not metadata.get('title'):
                print("⚠️ No tags found, falling back to filename parsing")
                filename = Path(filepath).name
                base_name = filename.split('.')[0]
                
                if ' - ' in base_name:
                    parts = base_name.split(' - ', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                else:
                    artist = "Unknown Artist"
                    title = base_name.replace('_', ' ').title()
                
                metadata['title'] = title
                metadata['artist'] = artist
            
            # Dodaj dodatne informacije
            metadata.update({
                "album": metadata.get('album', "Unknown Album"),
                "duration": metadata.get('duration', self.player.duration() or 180000),
                "filename": Path(filepath).name,
                "bitrate": metadata.get('bitrate', "Unknown"),
                "year": metadata.get('date', "Unknown")
            })
            
            print(f"🐛 [DEBUG engine] Extracted metadata: {metadata['title']} - {metadata['artist']}")
            self.metadata_changed.emit(metadata)
            
        except Exception as e:
            print(f"⚠️ Metadata extraction failed: {e}")
    
    # ========== TIMER & SIGNAL HANDLERS ==========
    
    def update_position(self):
        """Azuriraj poziciju za demo playback"""
        if self.is_cleaning_up:
            self.position_timer.stop()
            return
        
        try:
            if self._playing and not self._paused:
                # Proveri da li je playback zavrsen
                if self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
                    # Ako je stvarni player zaustavljen, emituj kraj
                    self._playing = False
                    self.position_timer.stop()
                    
                    # Ova logika je sada u on_media_status_changed
                    # Ostaje samo za demo playback
                    if not self.player.source().isValid():
                        print(f"🐛 [DEBUG engine] update_position: player stopped, no valid source")
                        self.playback_ended.emit()
        except RuntimeError:
            # Objekti su unisteni, ignorisi
            self.position_timer.stop()
    
    def on_playback_state_changed(self, state):
        """Obradi promenu stanja playbacka"""
        if self.is_cleaning_up:
            return
        
        try:
            state_names = {
                QMediaPlayer.PlaybackState.StoppedState: "Stopped",
                QMediaPlayer.PlaybackState.PlayingState: "Playing",
                QMediaPlayer.PlaybackState.PausedState: "Paused"
            }
            state_name = state_names.get(state, 'Unknown')
            print(f"🐛 [DEBUG engine] Playback state changed to: {state_name}")
            
            if state == QMediaPlayer.PlaybackState.StoppedState:
                self._playing = False
                self._paused = False
                self._is_auto_play_in_progress = False  # Reset auto-play
            elif state == QMediaPlayer.PlaybackState.PlayingState:
                self._playing = True
                self._paused = False
            elif state == QMediaPlayer.PlaybackState.PausedState:
                self._paused = True
        except Exception as e:
            print(f"❌ Error in playback_state_changed: {e}")
    
    def on_media_status_changed(self, status):
        """Obradi promenu statusa media"""
        if self.is_cleaning_up:
            return
        
        # DEBUG ispis za status
        status_names = {
            QMediaPlayer.MediaStatus.NoMedia: "NoMedia",
            QMediaPlayer.MediaStatus.LoadingMedia: "LoadingMedia",
            QMediaPlayer.MediaStatus.LoadedMedia: "LoadedMedia",
            QMediaPlayer.MediaStatus.BufferingMedia: "BufferingMedia",
            QMediaPlayer.MediaStatus.BufferedMedia: "BufferedMedia",
            QMediaPlayer.MediaStatus.EndOfMedia: "EndOfMedia",
            QMediaPlayer.MediaStatus.InvalidMedia: "InvalidMedia"
        }
        status_name = status_names.get(status, 'Unknown')
        print(f"🐛 [DEBUG engine] Media status: {status_name}")
        
        # Auto-play sledece pesme kada se trenutna zavrsi
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print(f"📚 Track ended (duration: {self.get_duration()}ms, position: {self.get_position()}ms)")
            print(f"🐛 [DEBUG engine] Current file at end: {self.current_file}")
            
            # Emituj signal da je playback zavrsen
            self.playback_ended.emit()
            
            # Samo ako nismo vec u auto-play modu
            if not self._is_auto_play_in_progress:
                print(f"🐛 [DEBUG engine] Not in auto-play, triggering auto-play next")
                # Automatski pusti sledecu pesmu iz playliste
                # Koristi QTimer.singleShot da bi UI imao vremena da se azurira
                QTimer.singleShot(100, self._auto_play_next)
    
    def _auto_play_next(self):
        """Interna metoda za auto-play sledece pesme"""
        if self.is_cleaning_up:
            return
        
        print(f"\n{'='*60}")
        print(f"🐛 [DEBUG engine] _auto_play_next() called")
        print(f"{'='*60}")
        
        # Proveri da li je UI auto-play ukljucen
        if self.app and hasattr(self.app, 'unified_window'):
            if not self.app.unified_window.auto_play_enabled:
                print("⏸ UI auto-play disabled, stopping")
                return
        
        try:
            if self.app and hasattr(self.app, 'playlist_manager'):
                # Proveri repeat mode
                print(f"🐛 [DEBUG engine] Repeat mode: {self.app.playlist_manager.repeat}")
                
                if self.app.playlist_manager.repeat == "one":
                    # Ponovi istu pesmu
                    if self.current_file:
                        print("🔄 Repeating same track")
                        self.play_file(self.current_file)
                    else:
                        print("⚠️ No current file to repeat")
                    return
                elif self.app.playlist_manager.repeat == "all":
                    # Auto-play sledecu (PlaylistManager ce obraditi loop)
                    print("🔄 Auto-play next (repeat all)")
                    self.play_next(auto_play=True)
                else:  # "none" ili bilo koji drugi
                    # Auto-play sledecu pesmu
                    print("➡️ Auto-play next (repeat none)")
                    self.play_next(auto_play=True)
        except Exception as e:
            print(f"❌ Auto-play error: {e}")
            traceback.print_exc()
    
    def on_player_error(self, error, error_string=""):
        """Obradi greske playera"""
        if self.is_cleaning_up:
            return
        
        try:
            print(f"❌ Player error: {error_string}")
            self.error_occurred.emit(f"Player error: {error_string}")
            
            # Ako je error i nismo u auto-play, pokusaj sledecu pesmu
            if not self._is_auto_play_in_progress:
                print("⚠️ Trying next track after error")
                QTimer.singleShot(100, lambda: self.play_next(auto_play=True))
        except Exception as e:
            print(f"❌ Error in player_error handler: {e}")
    
    def on_duration_changed(self, duration):
        """Obradi promenu dužine"""
        if self.is_cleaning_up:
            return
        
        try:
            if duration > 0:
                print(f"🐛 [DEBUG engine] Duration changed: {duration}ms ({duration//1000}s)")
                self.duration_changed.emit(duration)
        except Exception as e:
            print(f"❌ Error in duration_changed: {e}")
    
    def on_position_changed(self, position):
        """Obradi promenu pozicije"""
        if self.is_cleaning_up:
            return
        
        try:
            self.position_changed.emit(position)
        except:
            pass
    
    def on_metadata_changed(self):
        """Obradi promenu metadata"""
        if self.is_cleaning_up:
            return
        
        # PyQt6 automatski cita metadata za podrzane formate
        # Ovde mozes dodati custom handling ako zelis
        pass
    
    # ========== UTILITY METHODS ==========
    
    def get_state_info(self):
        """
        Dobavi informacije o trenutnom stanju
        
        Returns:
            Dict sa informacijama o stanju
        """
        return {
            "playing": self.is_playing(),
            "paused": self.is_paused(),
            "stopped": self.is_stopped(),
            "position": self.get_position(),
            "duration": self.get_duration(),
            "volume": self.get_volume(),
            "current_file": self.current_file,
        }
    
    def format_time(self, milliseconds):
        """
        Formatiraj vreme u MM:SS format
        
        Args:
            milliseconds: Vreme u milisekundama
            
        Returns:
            Formatiran string
        """
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"