# -*- coding: utf-8 -*-
# core/gstreamer_engine.py
"""
GStreamer Audio Engine - Sa pravom EQ podrškom

Alternativni audio engine koji koristi GStreamer umesto Qt Multimedia.
Prednosti:
- Pravi 10-band equalizer
- Više audio formata
- Bolji audio processing pipeline

Zahteva:
- PyGObject (gi)
- GStreamer 1.0 sa plugins-good i plugins-bad
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Proveri da li je GStreamer dostupan
GSTREAMER_AVAILABLE = False
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst, GLib
    Gst.init(None)
    GSTREAMER_AVAILABLE = True
    print("✅ GStreamer engine available")
except ImportError as e:
    print(f"⚠️ GStreamer not available: {e}")
except Exception as e:
    print(f"⚠️ GStreamer init error: {e}")


class GStreamerEngine(QObject):
    """
    Audio engine baziran na GStreamer-u sa EQ podrškom.
    
    Pipeline:
    filesrc -> decodebin -> audioconvert -> equalizer-10bands -> 
    volume -> autoaudiosink
    """
    
    # Signali (isti kao Qt Multimedia engine za kompatibilnost)
    metadata_changed = pyqtSignal(dict)
    position_changed = pyqtSignal(int)  # milisekunde
    volume_changed = pyqtSignal(int)    # 0-100
    playback_started = pyqtSignal(str)
    playback_stopped = pyqtSignal()
    playback_paused = pyqtSignal()
    playback_resumed = pyqtSignal()
    playback_ended = pyqtSignal()
    duration_changed = pyqtSignal(int)  # milisekunde
    error_occurred = pyqtSignal(str)
    eq_changed = pyqtSignal(list)       # EQ vrednosti
    
    # EQ frekvencije (Hz)
    EQ_BANDS = [29, 59, 119, 237, 474, 947, 1889, 3770, 7523, 15011]
    
    def __init__(self):
        super().__init__()
        
        if not GSTREAMER_AVAILABLE:
            raise RuntimeError("GStreamer is not available. Install PyGObject and GStreamer.")
        
        self._volume = 70
        self._playing = False
        self._paused = False
        self.current_file: Optional[str] = None
        self.app = None
        self.is_cleaning_up = False
        
        # EQ vrednosti (-12 do +12 dB za svaki band)
        self._eq_values = [0.0] * 10
        self._eq_enabled = True
        
        # GStreamer komponente
        self.pipeline = None
        self.equalizer = None
        self.volume_element = None
        
        # Position timer
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.setInterval(100)
        
        # Kreiraj pipeline
        self._create_pipeline()
        
        print("🎛️ GStreamer engine initialized with 10-band EQ")
    
    def _create_pipeline(self):
        """Kreiraj GStreamer pipeline sa EQ-om"""
        try:
            # Kreiraj elemente
            self.pipeline = Gst.Pipeline.new("audiowave-pipeline")
            
            # Source (će se postaviti kada se učita fajl)
            self.filesrc = Gst.ElementFactory.make("filesrc", "source")
            
            # Decoder
            self.decodebin = Gst.ElementFactory.make("decodebin", "decoder")
            self.decodebin.connect("pad-added", self._on_pad_added)
            
            # Audio convert (za format kompatibilnost)
            self.audioconvert = Gst.ElementFactory.make("audioconvert", "convert")
            
            # Equalizer - 10 bands!
            self.equalizer = Gst.ElementFactory.make("equalizer-10bands", "equalizer")
            if not self.equalizer:
                print("⚠️ equalizer-10bands not found, trying equalizer-nbands")
                self.equalizer = Gst.ElementFactory.make("equalizer-nbands", "equalizer")
                if self.equalizer:
                    self.equalizer.set_property("num-bands", 10)
            
            if not self.equalizer:
                print("❌ No equalizer element available!")
            
            # Volume control
            self.volume_element = Gst.ElementFactory.make("volume", "volume")
            
            # Audio resample (za kompatibilnost)
            self.audioresample = Gst.ElementFactory.make("audioresample", "resample")
            
            # Output sink
            self.audiosink = Gst.ElementFactory.make("autoaudiosink", "sink")
            
            # Dodaj elemente u pipeline
            for element in [self.filesrc, self.decodebin, self.audioconvert, 
                           self.equalizer, self.volume_element, 
                           self.audioresample, self.audiosink]:
                if element:
                    self.pipeline.add(element)
            
            # Poveži elemente (osim decodebin koji se povezuje dinamički)
            self.filesrc.link(self.decodebin)
            
            # Poveži audio chain
            if self.equalizer:
                self.audioconvert.link(self.equalizer)
                self.equalizer.link(self.volume_element)
            else:
                self.audioconvert.link(self.volume_element)
            
            self.volume_element.link(self.audioresample)
            self.audioresample.link(self.audiosink)
            
            # Postavi početni volume
            if self.volume_element:
                self.volume_element.set_property("volume", self._volume / 100.0)
            
            # Bus za poruke
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_bus_message)
            
            print("✅ GStreamer pipeline created successfully")
            
        except Exception as e:
            print(f"❌ Error creating GStreamer pipeline: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_pad_added(self, element, pad):
        """Callback kada decodebin doda pad"""
        caps = pad.get_current_caps()
        if caps:
            struct = caps.get_structure(0)
            if struct.get_name().startswith("audio"):
                sink_pad = self.audioconvert.get_static_pad("sink")
                if not sink_pad.is_linked():
                    pad.link(sink_pad)
                    print("🔗 Audio pad linked")
    
    def _on_bus_message(self, bus, message):
        """Obradi GStreamer poruke"""
        if self.is_cleaning_up:
            return
        
        t = message.type
        
        if t == Gst.MessageType.EOS:
            # End of stream
            print("📚 End of stream")
            self._playing = False
            self.position_timer.stop()
            self.playback_ended.emit()
            
            # Auto-play next
            QTimer.singleShot(100, self._auto_play_next)
        
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"❌ GStreamer error: {err.message}")
            self.error_occurred.emit(str(err.message))
            self.stop()
        
        elif t == Gst.MessageType.DURATION_CHANGED:
            # Duration se promenio
            success, duration = self.pipeline.query_duration(Gst.Format.TIME)
            if success:
                duration_ms = duration // Gst.MSECOND
                self.duration_changed.emit(duration_ms)
        
        elif t == Gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline:
                old, new, pending = message.parse_state_changed()
                if new == Gst.State.PLAYING:
                    # Dobij duration kada počne playback
                    success, duration = self.pipeline.query_duration(Gst.Format.TIME)
                    if success:
                        duration_ms = duration // Gst.MSECOND
                        self.duration_changed.emit(duration_ms)
        
        elif t == Gst.MessageType.TAG:
            # Metadata tags
            tags = message.parse_tag()
            self._extract_tags(tags)
    
    def _extract_tags(self, tags):
        """Izvuci metadata iz GStreamer tag-ova"""
        metadata = {}
        
        def get_tag(tag_name):
            success, value = tags.get_string(tag_name)
            return value if success else None
        
        def get_tag_uint(tag_name):
            success, value = tags.get_uint(tag_name)
            return value if success else None
        
        metadata['title'] = get_tag(Gst.TAG_TITLE) or Path(self.current_file).stem if self.current_file else "Unknown"
        metadata['artist'] = get_tag(Gst.TAG_ARTIST) or "Unknown Artist"
        metadata['album'] = get_tag(Gst.TAG_ALBUM) or "Unknown Album"
        metadata['genre'] = get_tag(Gst.TAG_GENRE)
        metadata['year'] = get_tag_uint(Gst.TAG_DATE_TIME)
        
        self.metadata_changed.emit(metadata)
    
    def _update_position(self):
        """Update position timer callback"""
        if self.pipeline and self._playing and not self._paused:
            success, position = self.pipeline.query_position(Gst.Format.TIME)
            if success:
                position_ms = position // Gst.MSECOND
                self.position_changed.emit(position_ms)
    
    def _auto_play_next(self):
        """Auto-play sledeća pesma nakon završetka"""
        if self.is_cleaning_up:
            return
        
        if self.app and hasattr(self.app, 'playlist_manager'):
            try:
                if self.app.playlist_manager.repeat == "one":
                    if self.current_file:
                        self.play_file(self.current_file)
                else:
                    self.play_next(auto_play=True)
            except Exception as e:
                print(f"❌ Auto-play error: {e}")
                import traceback
                traceback.print_exc()
    
    # ========== PLAYBACK CONTROL ==========
    
    def play_file(self, filepath: str):
        """Pusti audio fajl"""
        if self.is_cleaning_up:
            return
        
        if not os.path.exists(filepath):
            self.error_occurred.emit(f"File not found: {filepath}")
            return
        
        print(f"🎵 GStreamer playing: {Path(filepath).name}")
        
        try:
            # Zaustavi prethodni playback
            self.stop()
            
            # Postavi fajl
            self.current_file = filepath
            self.filesrc.set_property("location", filepath)
            
            # Pokreni playback
            self.pipeline.set_state(Gst.State.PLAYING)
            self._playing = True
            self._paused = False
            
            self.playback_started.emit(filepath)
            self.position_timer.start()
            
        except Exception as e:
            print(f"❌ Error playing file: {e}")
            self.error_occurred.emit(str(e))
    
    def play(self):
        """Resume playback"""
        if self.pipeline and self._paused:
            self.pipeline.set_state(Gst.State.PLAYING)
            self._playing = True
            self._paused = False
            self.position_timer.start()
            self.playback_resumed.emit()
    
    def pause(self):
        """Pause playback"""
        if self.pipeline and self._playing:
            self.pipeline.set_state(Gst.State.PAUSED)
            self._paused = True
            self.position_timer.stop()
            self.playback_paused.emit()
    
    def stop(self):
        """Stop playback"""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self._playing = False
            self._paused = False
            self.position_timer.stop()
            self.playback_stopped.emit()
    
    def toggle_play_pause(self):
        """Toggle play/pause"""
        if self._playing and not self._paused:
            self.pause()
        elif self._paused:
            self.play()
        elif self.current_file:
            self.play_file(self.current_file)
    
    # ========== SEEK & POSITION ==========
    
    def seek_to_position(self, position_ms: int):
        """Seek na poziciju (milisekunde)"""
        if self.pipeline:
            position_ns = position_ms * Gst.MSECOND
            self.pipeline.seek_simple(
                Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                position_ns
            )
    
    def get_position(self) -> int:
        """Dobij trenutnu poziciju (milisekunde)"""
        if self.pipeline:
            success, position = self.pipeline.query_position(Gst.Format.TIME)
            if success:
                return position // Gst.MSECOND
        return 0
    
    def get_duration(self) -> int:
        """Dobij trajanje (milisekunde)"""
        if self.pipeline:
            success, duration = self.pipeline.query_duration(Gst.Format.TIME)
            if success:
                return duration // Gst.MSECOND
        return 0
    
    # ========== VOLUME ==========
    
    def set_volume(self, volume: int):
        """Postavi volume (0-100)"""
        self._volume = max(0, min(100, volume))
        if self.volume_element:
            self.volume_element.set_property("volume", self._volume / 100.0)
        self.volume_changed.emit(self._volume)
    
    def get_volume(self) -> int:
        """Dobij volume (0-100)"""
        return self._volume
    
    # ========== EQUALIZER ==========
    
    def set_equalizer(self, values: List[float]):
        """
        Postavi EQ vrednosti za sve bandove.
        
        Args:
            values: Lista od 10 vrednosti (-12.0 do +12.0 dB)
        """
        if not self.equalizer:
            print("⚠️ Equalizer not available")
            return
        
        if len(values) != 10:
            print(f"⚠️ Expected 10 EQ values, got {len(values)}")
            return
        
        self._eq_values = values
        
        # GStreamer equalizer-10bands koristi band0, band1, ... band9
        for i, value in enumerate(values):
            gain = max(-24.0, min(12.0, float(value)))  # Clamp vrednosti
            self.equalizer.set_property(f"band{i}", gain)
        
        self.eq_changed.emit(values)
        print(f"🎛️ EQ set: {values}")
    
    def get_equalizer(self) -> List[float]:
        """Dobij trenutne EQ vrednosti"""
        return self._eq_values.copy()
    
    def set_equalizer_band(self, band: int, value: float):
        """
        Postavi jedan EQ band.
        
        Args:
            band: Index banda (0-9)
            value: Vrednost (-12.0 do +12.0 dB)
        """
        if not self.equalizer or band < 0 or band > 9:
            return
        
        gain = max(-24.0, min(12.0, float(value)))
        self._eq_values[band] = gain
        self.equalizer.set_property(f"band{band}", gain)
    
    def enable_equalizer(self, enabled: bool):
        """Uključi/isključi EQ"""
        self._eq_enabled = enabled
        if not enabled:
            # Reset na flat
            flat = [0.0] * 10
            self.set_equalizer(flat)
    
    def is_equalizer_enabled(self) -> bool:
        """Da li je EQ uključen"""
        return self._eq_enabled
    
    # ========== STATE ==========
    
    def is_playing(self) -> bool:
        return self._playing and not self._paused
    
    def is_paused(self) -> bool:
        return self._paused
    
    def is_stopped(self) -> bool:
        return not self._playing
    
    # ========== PLAYLIST INTEGRATION ==========
    
    def play_next(self, auto_play: bool = False):
        """Pusti sledeću pesmu"""
        if self.app and hasattr(self.app, 'playlist_manager'):
            # ISPRAVKA: Koristi next() umesto get_next()
            next_file = self.app.playlist_manager.next()
            if next_file:
                self.play_file(next_file)
    
    def play_previous(self):
        """Pusti prethodnu pesmu"""
        if self.app and hasattr(self.app, 'playlist_manager'):
            # ISPRAVKA: Koristi prev() umesto get_previous()
            prev_file = self.app.playlist_manager.prev()
            if prev_file:
                self.play_file(prev_file)
    
    # ========== CLEANUP ==========
    
    def cleanup(self):
        """Očisti resurse"""
        self.is_cleaning_up = True
        self.position_timer.stop()
        
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
        
        print("🎛️ GStreamer engine cleaned up")
    
    def __del__(self):
        self.cleanup()


# ========== HELPER ==========

def is_gstreamer_available() -> bool:
    """Proveri da li je GStreamer dostupan"""
    return GSTREAMER_AVAILABLE


def get_gstreamer_version() -> str:
    """Dobij GStreamer verziju"""
    if GSTREAMER_AVAILABLE:
        return f"{Gst.VERSION_MAJOR}.{Gst.VERSION_MINOR}.{Gst.VERSION_MICRO}"
    return "Not available"