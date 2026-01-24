"""
Playback controller - handles auto-play, shuffle, repeat logic.
FIXED: Removed duplicate auto-play (engine handles it)
"""

import random
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QPushButton


class PlaybackController:
    """Controller for playback logic (auto-play, shuffle, repeat)."""
    
    def __init__(self, app, window):
        self.app = app
        self.window = window
        self.engine = app.engine
        self.playlist_manager = app.playlist_manager
        
        # State
        self.auto_play_enabled = True
        self.is_closing = False
        
        # UI references
        self.btn_auto_play = None
        self.btn_shuffle = None
        self.btn_repeat = None
        self.status_label = None
    
    def set_ui_references(self, btn_auto_play, btn_shuffle, btn_repeat, status_label):
        """Set references to UI elements."""
        self.btn_auto_play = btn_auto_play
        self.btn_shuffle = btn_shuffle
        self.btn_repeat = btn_repeat
        self.status_label = status_label
        
        # Connect UI signals
        if self.btn_auto_play:
            self.btn_auto_play.toggled.connect(self.toggle_auto_play)
        
        if self.btn_shuffle:
            self.btn_shuffle.toggled.connect(self.toggle_shuffle)
        
        if self.btn_repeat:
            self.btn_repeat.clicked.connect(self.cycle_repeat)
    
    def set_auto_play(self, enabled):
        """Set auto-play mode."""
        if self.is_closing:
            return
            
        self.auto_play_enabled = enabled
        if self.btn_auto_play:
            self.btn_auto_play.setChecked(enabled)
        
        if enabled:
            self.show_message("Auto-play: ON")
        else:
            self.show_message("Auto-play: OFF")
            # If auto-play is off, disable repeat
            self.playlist_manager.set_repeat("none")
            if self.btn_repeat:
                self.btn_repeat.setText("🔀")
                self.btn_repeat.setToolTip("Repeat: None")
    
    def toggle_auto_play(self, enabled):
        """Toggle auto-play mode."""
        self.set_auto_play(enabled)
    
    def toggle_shuffle(self, enabled):
        """Toggle shuffle mode."""
        if self.is_closing:
            return
            
        self.playlist_manager.set_shuffle(enabled)
        self.show_message(f"Shuffle {'ON' if enabled else 'OFF'}")
    
    def cycle_repeat(self):
        """Cycle repeat mode."""
        if self.is_closing:
            return
            
        modes = ["none", "one", "all"]
        icons = {"none": "🔀", "one": "🔂", "all": "🔄"}
        
        current = self.playlist_manager.repeat
        next_mode = modes[(modes.index(current) + 1) % 3]
        
        self.playlist_manager.set_repeat(next_mode)
        
        if self.btn_repeat:
            self.btn_repeat.setText(icons[next_mode])
            self.btn_repeat.setToolTip(f"Repeat: {next_mode.title()}")
        
        self.show_message(f"Repeat: {next_mode}")
    
    def on_play_clicked(self):
        """Handle play/pause click - kompatibilno sa GStreamerEngine."""
        if self.is_closing:
            return
        
        print("🎵 Play/pause clicked")
        
        try:
            # Debug info
            print(f"🔍 Engine type: {type(self.engine).__name__}")
            print(f"🔍 Engine methods: play={hasattr(self.engine, 'play')}, "
                  f"pause={hasattr(self.engine, 'pause')}, "
                  f"is_playing={hasattr(self.engine, 'is_playing')}, "
                  f"is_paused={hasattr(self.engine, 'is_paused')}")
            
            # Proveri stanje
            is_playing = False
            is_paused = False
            
            if hasattr(self.engine, 'is_playing'):
                is_playing = self.engine.is_playing()
            
            if hasattr(self.engine, 'is_paused'):
                is_paused = self.engine.is_paused()
            
            print(f"🔍 State: is_playing={is_playing}, is_paused={is_paused}")
            
            if is_playing and not is_paused:
                # Pauziraj
                print("⏸️ Pausing playback")
                if hasattr(self.engine, 'pause'):
                    self.engine.pause()
                elif hasattr(self.engine, 'toggle_play_pause'):
                    self.engine.toggle_play_pause()
                else:
                    print("⚠️ No pause method available")
                    return
                
                # Tray notifikacija
                if hasattr(self.app, 'tray_icon'):
                    self.app.tray_icon.notifications.paused()
                
            else:
                # Pokreni ili nastavi
                if is_paused:
                    # Nastavi sa pauze
                    print("▶️ Resuming playback")
                    if hasattr(self.engine, 'play'):
                        self.engine.play()
                    elif hasattr(self.engine, 'toggle_play_pause'):
                        self.engine.toggle_play_pause()
                    else:
                        print("⚠️ No play/resume method available")
                        return
                    
                    # Tray notifikacija
                    if hasattr(self.app, 'tray_icon'):
                        metadata = self.engine.current_metadata if hasattr(self.engine, 'current_metadata') else {}
                        title = metadata.get('title', 'Unknown Track')
                        artist = metadata.get('artist', 'Unknown Artist')
                        self.app.tray_icon.notifications.now_playing(title, artist)
                    
                else:
                    # Nije playing ni paused - pokreni nešto
                    print("▶️ Starting playback")
                    self.play_something()
        
        except Exception as e:
            print(f"❌ Play/pause error: {e}")
            import traceback
            traceback.print_exc()
    
    def on_stop_clicked(self):
        """Handle stop click."""
        if self.is_closing:
            return
            
        self.engine.stop()
    
    def on_next_clicked(self):
        """Handle next click - MANUAL next only (user clicked)."""
        if self.is_closing:
            return
        
        # ✅ Use engine's play_next which has debounce protection
        if hasattr(self.engine, 'play_next'):
            self.engine.play_next(auto_play=False)
            self.show_message("Next track")
        else:
            # Fallback: manual implementation
            next_file = self.playlist_manager.next()
            if next_file and hasattr(self.engine, 'play_file'):
                self.engine.play_file(next_file)
                self.show_message("Next track")
            else:
                self.show_message("End of playlist")
                self.engine.stop()
    
    def on_prev_clicked(self):
        """Handle previous click."""
        if self.is_closing:
            return
        
        # ✅ Use engine's play_previous which has debounce protection
        if hasattr(self.engine, 'play_previous'):
            self.engine.play_previous()
            self.show_message("Previous track")
        else:
            # Fallback: manual implementation
            prev_file = self.playlist_manager.prev()
            if prev_file and hasattr(self.engine, 'play_file'):
                self.engine.play_file(prev_file)
                self.show_message("Previous track")
    
    def play_something(self):
        """Play something (current or demo)."""
        if self.is_closing:
            return
            
        current_file = self.playlist_manager.get_current_file()
        if current_file and hasattr(self.engine, 'play_file'):
            self.engine.play_file(current_file)
        else:
            # Play demo
            demo_files = ["Summer Vibes.mp3", "Chill Beats.flac"]
            demo = random.choice(demo_files)
            self.playlist_manager.add_files([demo])
            if hasattr(self.engine, 'play_file'):
                self.engine.play_file(demo)
            self.show_message("Playing (demo)")
    
    def on_track_ended(self):
        """
        Handle track ended - UI UPDATE ONLY!
        
        ✅ FIXED: Engine handles auto-play via _auto_play_next().
        This method should ONLY update UI, NOT trigger next track.
        Calling next here would cause DUPLICATE playback!
        """
        if self.is_closing:
            return
        
        # ✅ Only update UI status - DO NOT call on_next_clicked()!
        self.show_message("Track ended")
        
        # ❌ REMOVED - This was causing duplicate auto-play:
        # if self.auto_play_enabled:
        #     QTimer.singleShot(100, self.on_next_clicked)
    
    def on_seek_requested(self, position_ms):
        """Handle seek request."""
        if self.is_closing:
            return
            
        print(f"🎯 Seeking to: {position_ms}ms")
        self.show_message(f"Seeking to {position_ms//1000}s")
        
        try:
            if hasattr(self.engine, 'seek'):
                success = self.engine.seek(position_ms)
                if success:
                    print(f"✅ Seek successful")
                else:
                    print(f"❌ Seek failed")
            elif hasattr(self.engine, 'seek_to_position'):
                self.engine.seek_to_position(position_ms)
                print(f"✅ Seek via seek_to_position")
            elif hasattr(self.engine, 'player') and hasattr(self.engine.player, 'setPosition'):
                self.engine.player.setPosition(position_ms)
                print(f"✅ Seek via player.setPosition")
            else:
                print(f"⚠️ No seek method available")
        except Exception as e:
            print(f"❌ Seek error: {e}")
            self.show_message(f"Seek error: {str(e)[:20]}")
        
        # Reset status
        QTimer.singleShot(2000, lambda: self.show_message("Ready"))
    
    def show_message(self, message):
        """Show message in status."""
        if self.status_label:
            self.status_label.setText(f"✓ {message}")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Ready") if self.status_label else None)