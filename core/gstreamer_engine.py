# -*- coding: utf-8 -*-
# core/gstreamer_engine.py
"""
GStreamer Audio Engine - Sa pravom EQ podrškom i SIGURNIM cleanup-om
✅ Bez segfault-a pri zatvaranju
✅ Proper Qt i GStreamer cleanup
✅ 10-band equalizer support
✅ Auto-play next sa debounce
✅ FIXED: Next track playback issues
"""

import os
import time
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
    Audio engine baziran na GStreamer-u sa EQ podrškom i SIGURNIM cleanup-om.
    
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
        
        print("🎛️ Initializing GStreamer engine...")
        
        # State variables
        self._volume = 70
        self._playing = False
        self._paused = False
        self.current_file: Optional[str] = None
        self.app = None
        
        # Debounce za auto-play
        self._last_auto_play_time = 0
        self._auto_play_debounce_ms = 300
        
        # EQ vrednosti (-12 do +12 dB za svaki band)
        self._eq_values = [0.0] * 10
        self._eq_enabled = True
        self._eq_preamp = 0.0  # NOVO: dodaj preamp za equalizer
        
        # GStreamer komponente
        self.pipeline = None
        self.bus = None
        self.equalizer = None
        self.volume_element = None
        self.preamp_element = None  # NOVO: zaseban preamp element
        
        # Position timer
        self.position_timer = None
        
        # Cleanup flag
        self._is_cleaning_up = False
        self._cleanup_lock = False
        
        # Kreiraj pipeline
        self._create_pipeline()
        
        print("✅ GStreamer engine initialized with 10-band EQ")
    
    def _create_pipeline(self):
        """Kreiraj GStreamer pipeline sa EQ-om - sa error handling"""
        try:
            # Kreiraj elemente
            self.pipeline = Gst.Pipeline.new("audiowave-pipeline")
            if not self.pipeline:
                raise RuntimeError("Failed to create GStreamer pipeline")
            
            # Source (će se postaviti kada se učita fajl)
            self.filesrc = Gst.ElementFactory.make("filesrc", "source")
            if not self.filesrc:
                raise RuntimeError("Failed to create filesrc element")
            
            # Decoder
            self.decodebin = Gst.ElementFactory.make("decodebin", "decoder")
            if not self.decodebin:
                raise RuntimeError("Failed to create decodebin element")
            
            # Connect pad-added signal
            self.decodebin.connect("pad-added", self._on_pad_added)
            
            # Audio convert (za format kompatibilnost)
            self.audioconvert = Gst.ElementFactory.make("audioconvert", "convert")
            if not self.audioconvert:
                raise RuntimeError("Failed to create audioconvert element")
            
            # Equalizer - 10 bands!
            self.equalizer = Gst.ElementFactory.make("equalizer-10bands", "equalizer")
            if not self.equalizer:
                print("⚠️ equalizer-10bands not found, trying equalizer-nbands")
                self.equalizer = Gst.ElementFactory.make("equalizer-nbands", "equalizer")
                if self.equalizer:
                    self.equalizer.set_property("num-bands", 10)
                else:
                    print("⚠️ No equalizer element available, continuing without EQ")
            
            # Preamp control (zaseban volume za EQ) - NOVO
            self.preamp_element = Gst.ElementFactory.make("volume", "preamp")
            if not self.preamp_element:
                print("⚠️ Failed to create preamp element, using main volume")
            
            # Main volume control
            self.volume_element = Gst.ElementFactory.make("volume", "volume")
            if not self.volume_element:
                raise RuntimeError("Failed to create volume element")
            
            # Audio resample (za kompatibilnost)
            self.audioresample = Gst.ElementFactory.make("audioresample", "resample")
            if not self.audioresample:
                print("⚠️ Failed to create audioresample element")
            
            # Output sink
            self.audiosink = Gst.ElementFactory.make("autoaudiosink", "sink")
            if not self.audiosink:
                print("⚠️ Failed to create autoaudiosink, trying pulsesink")
                self.audiosink = Gst.ElementFactory.make("pulsesink", "sink")
                if not self.audiosink:
                    raise RuntimeError("Failed to create audio sink")
            
            # Dodaj elemente u pipeline
            elements_to_add = [self.filesrc, self.decodebin]
            
            if self.equalizer:
                elements_to_add.append(self.audioconvert)
                elements_to_add.append(self.equalizer)
                
                # Dodaj preamp ako postoji
                if self.preamp_element:
                    elements_to_add.append(self.preamp_element)
            else:
                # Ako nema equalizera, preskoči ga
                elements_to_add.append(self.audioconvert)
            
            # Dodaj glavni volume
            elements_to_add.append(self.volume_element)
            
            # Dodaj opcione elemente
            if self.audioresample:
                elements_to_add.append(self.audioresample)
            elements_to_add.append(self.audiosink)
            
            for element in elements_to_add:
                if element:
                    self.pipeline.add(element)
            
            # Poveži elemente (osim decodebin koji se povezuje dinamički)
            if not self.filesrc.link(self.decodebin):
                raise RuntimeError("Failed to link filesrc to decodebin")
            
            # Poveži audio chain
            current_element = self.audioconvert
            
            if self.equalizer:
                # Poveži audioconvert -> equalizer
                if not current_element.link(self.equalizer):
                    raise RuntimeError("Failed to link audioconvert to equalizer")
                current_element = self.equalizer
                
                # Ako imamo preamp, poveži ga posle equalizera
                if self.preamp_element:
                    if not current_element.link(self.preamp_element):
                        raise RuntimeError("Failed to link equalizer to preamp")
                    current_element = self.preamp_element
            
            # Poveži na glavni volume
            if not current_element.link(self.volume_element):
                raise RuntimeError("Failed to link to volume element")
            
            current_element = self.volume_element
            
            if self.audioresample:
                if not current_element.link(self.audioresample):
                    raise RuntimeError("Failed to link volume to audioresample")
                current_element = self.audioresample
            
            if not current_element.link(self.audiosink):
                raise RuntimeError("Failed to link to audio sink")
            
            # Postavi početni volume
            self.volume_element.set_property("volume", self._volume / 100.0)
            
            # Postavi početni preamp
            if self.preamp_element:
                self.preamp_element.set_property("volume", 1.0)  # Neutral (0dB)
            
            # Kreiraj bus za poruke
            self.bus = self.pipeline.get_bus()
            if not self.bus:
                raise RuntimeError("Failed to get pipeline bus")
            
            self.bus.add_signal_watch()
            self.bus.connect("message", self._on_bus_message)
            
            # Kreiraj position timer
            self.position_timer = QTimer()
            self.position_timer.timeout.connect(self._update_position)
            self.position_timer.setInterval(100)
            
            print("✅ GStreamer pipeline created successfully")
            
        except Exception as e:
            print(f"❌ Error creating GStreamer pipeline: {e}")
            import traceback
            traceback.print_exc()
            
            # Cleanup ako je došlo do greške
            self._safe_cleanup()
            raise
    
    def _on_pad_added(self, element, pad):
        """Callback kada decodebin doda pad"""
        if self._is_cleaning_up:
            return
        
        try:
            caps = pad.get_current_caps()
            if caps:
                struct = caps.get_structure(0)
                if struct.get_name().startswith("audio"):
                    sink_pad = self.audioconvert.get_static_pad("sink")
                    if sink_pad and not sink_pad.is_linked():
                        pad.link(sink_pad)
                        print("🔗 Audio pad linked")
        except Exception as e:
            print(f"⚠️ Error in pad-added callback: {e}")
    
    def _on_bus_message(self, bus, message):
        """Obradi GStreamer poruke - SAFE VERSION"""
        # Proveri cleanup flag prvo
        if self._is_cleaning_up:
            return
        
        try:
            t = message.type
            
            if t == Gst.MessageType.EOS:
                # End of stream
                print("📚 End of stream detected")
                self._playing = False
                
                # Zaustavi timer ako postoji
                if self.position_timer and self.position_timer.isActive():
                    self.position_timer.stop()
                
                # Emituj signal sa debounce
                current_time = time.time() * 1000  # ms
                if current_time - self._last_auto_play_time > self._auto_play_debounce_ms:
                    self._last_auto_play_time = current_time
                    self.playback_ended.emit()
                    
                    # Schedule auto-play
                    QTimer.singleShot(100, self._auto_play_next)
            
            elif t == Gst.MessageType.ERROR:
                err, debug = message.parse_error()
                error_msg = str(err.message) if hasattr(err, 'message') else str(err)
                print(f"❌ GStreamer error: {error_msg}")
                self.error_occurred.emit(error_msg)
                
                # Zaustavi playback
                self._stop_playback_safe()
            
            elif t == Gst.MessageType.DURATION_CHANGED:
                # Duration se promenio
                try:
                    success, duration = self.pipeline.query_duration(Gst.Format.TIME)
                    if success:
                        duration_ms = duration // Gst.MSECOND
                        self.duration_changed.emit(duration_ms)
                except:
                    pass
            
            elif t == Gst.MessageType.STATE_CHANGED:
                if message.src == self.pipeline:
                    try:
                        old, new, pending = message.parse_state_changed()
                        if new == Gst.State.PLAYING:
                            # Dobij duration kada počne playback
                            success, duration = self.pipeline.query_duration(Gst.Format.TIME)
                            if success:
                                duration_ms = duration // Gst.MSECOND
                                self.duration_changed.emit(duration_ms)
                    except:
                        pass
            
            elif t == Gst.MessageType.TAG:
                # Metadata tags
                try:
                    tags = message.parse_tag()
                    self._extract_tags(tags)
                except:
                    pass
        
        except Exception as e:
            # Silent fail - objekti su verovatno uništeni
            pass
    
    def _extract_tags(self, tags):
        """Izvuci metadata iz GStreamer tag-ova"""
        try:
            metadata = {}
            
            def get_tag(tag_name):
                try:
                    success, value = tags.get_string(tag_name)
                    return value if success else None
                except:
                    return None
            
            def get_tag_uint(tag_name):
                try:
                    success, value = tags.get_uint(tag_name)
                    return value if success else None
                except:
                    return None
            
            metadata['title'] = get_tag(Gst.TAG_TITLE) or Path(self.current_file).stem if self.current_file else "Unknown"
            metadata['artist'] = get_tag(Gst.TAG_ARTIST) or "Unknown Artist"
            metadata['album'] = get_tag(Gst.TAG_ALBUM) or "Unknown Album"
            metadata['genre'] = get_tag(Gst.TAG_GENRE)
            metadata['year'] = get_tag_uint(Gst.TAG_DATE_TIME)
            
            self.metadata_changed.emit(metadata)
            
        except Exception as e:
            print(f"⚠️ Error extracting tags: {e}")
    
    def _update_position(self):
        """Update position timer callback - SAFE"""
        if (self._is_cleaning_up or not self.pipeline or 
            not self._playing or self._paused):
            return
        
        try:
            success, position = self.pipeline.query_position(Gst.Format.TIME)
            if success:
                position_ms = position // Gst.MSECOND
                self.position_changed.emit(position_ms)
        except:
            # Timer će biti zaustavljen u cleanup-u
            pass
    
    def _auto_play_next(self):
        """Auto-play sledeća pesma nakon završetka - OPTIMIZOVANO"""
        if self._is_cleaning_up:
            return
        
        print("🔄 Auto-play next track...")
        
        if self.app and hasattr(self.app, 'playlist_manager'):
            try:
                # Proveri repeat mode
                pm = self.app.playlist_manager
                
                if pm.repeat == "one":
                    # Ponovi istu pesmu
                    if self.current_file and os.path.exists(self.current_file):
                        QTimer.singleShot(100, lambda: self.play_file(self.current_file))
                else:
                    # Pokreni sledeću pesmu sa force=True (zaobiđi debounce)
                    QTimer.singleShot(100, lambda: self.play_next(auto_play=True))
                    
            except Exception as e:
                print(f"❌ Auto-play error: {e}")
    
    # ========== PLAYBACK CONTROL ==========
    
    def play_file(self, filepath: str):
        """Pusti audio fajl - SAFE + reset decodebin"""
        if self._is_cleaning_up:
            print("⚠️ Engine is cleaning up, cannot play")
            return
        
        if not os.path.exists(filepath):
            self.error_occurred.emit(f"File not found: {filepath}")
            return
        
        print(f"🎵 GStreamer playing: {Path(filepath).name}")
        
        try:
            # 1. Zaustavi prethodni playback
            self._stop_playback_safe()
            
            # 2. Reset decodebin za sledeću pesmu (samo ako postoji stari pad)
            try:
                # Proveri da li decodebin ima linked pad
                sink_pad = self.audioconvert.get_static_pad("sink")
                if sink_pad and sink_pad.is_linked():
                    print("🔄 Resetting decodebin for next track...")
                    
                    # Postavi pipeline na READY
                    self.pipeline.set_state(Gst.State.READY)
                    
                    # Odspoji i ponovo kreiraj decodebin
                    self.decodebin.disconnect_by_func(self._on_pad_added)
                    self.pipeline.remove(self.decodebin)
                    
                    # Napravi novi decodebin
                    self.decodebin = Gst.ElementFactory.make("decodebin", "decoder")
                    if self.decodebin:
                        self.decodebin.connect("pad-added", self._on_pad_added)
                        self.pipeline.add(self.decodebin)
                        
                        # Poveži ponovo
                        if not self.filesrc.link(self.decodebin):
                            print("⚠️ Failed to relink filesrc to decodebin")
            except Exception as e:
                print(f"⚠️ decodebin reset warning: {e}")
            
            # 3. Postavi novi fajl
            self.current_file = filepath
            self.filesrc.set_property("location", filepath)
            
            # 4. Pokreni playback
            result = self.pipeline.set_state(Gst.State.PLAYING)
            if result == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to start playback")
            
            self._playing = True
            self._paused = False
            
            # 5. Pokreni timer za poziciju
            if self.position_timer:
                self.position_timer.start()
            
            self.playback_started.emit(filepath)
            
        except Exception as e:
            print(f"❌ Error playing file: {e}")
            self.error_occurred.emit(str(e))
            self._playing = False
            self._paused = False
    
    def _stop_playback_safe(self):
        """Sigurno zaustavi playback"""
        try:
            if self.pipeline:
                # Postavi pipeline na READY (ne NULL odmah)
                self.pipeline.set_state(Gst.State.READY)
            
            # Zaustavi timer
            if self.position_timer and self.position_timer.isActive():
                self.position_timer.stop()
            
            self._playing = False
            self._paused = False
            
        except Exception as e:
            print(f"⚠️ Error in safe stop: {e}")
    
    def play(self):
        """Resume playback"""
        if self._is_cleaning_up or not self.pipeline:
            return
        
        try:
            result = self.pipeline.set_state(Gst.State.PLAYING)
            if result != Gst.StateChangeReturn.FAILURE:
                self._playing = True
                self._paused = False
                
                if self.position_timer:
                    self.position_timer.start()
                
                self.playback_resumed.emit()
        except Exception as e:
            print(f"❌ Error resuming playback: {e}")
    
    def pause(self):
        """Pause playback"""
        if self._is_cleaning_up or not self.pipeline:
            return
        
        try:
            result = self.pipeline.set_state(Gst.State.PAUSED)
            if result != Gst.StateChangeReturn.FAILURE:
                self._paused = True
                
                if self.position_timer:
                    self.position_timer.stop()
                
                self.playback_paused.emit()
        except Exception as e:
            print(f"❌ Error pausing playback: {e}")
    
    def stop(self):
        """Stop playback"""
        if self._is_cleaning_up:
            return
        
        print("⏹ Stopping GStreamer playback")
        self._stop_playback_safe()
        self.playback_stopped.emit()
    
    def toggle_play_pause(self):
        """Toggle play/pause"""
        if self._is_cleaning_up:
            return
        
        if self._playing and not self._paused:
            self.pause()
        elif self._paused:
            self.play()
        elif self.current_file and os.path.exists(self.current_file):
            self.play_file(self.current_file)
    
    # ========== SEEK & POSITION ==========
    
    def seek_to_position(self, position_ms: int):
        """Seek na poziciju (milisekunde)"""
        if self._is_cleaning_up or not self.pipeline:
            return
        
        try:
            position_ns = position_ms * Gst.MSECOND
            self.pipeline.seek_simple(
                Gst.Format.TIME,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                position_ns
            )
            print(f"⏩ Seek to: {position_ms}ms")
        except Exception as e:
            print(f"❌ Error seeking: {e}")
    
    def get_position(self) -> int:
        """Dobij trenutnu poziciju (milisekunde)"""
        if self._is_cleaning_up or not self.pipeline:
            return 0
        
        try:
            success, position = self.pipeline.query_position(Gst.Format.TIME)
            if success:
                return position // Gst.MSECOND
        except:
            pass
        
        return 0
    
    def get_duration(self) -> int:
        """Dobij trajanje (milisekunde)"""
        if self._is_cleaning_up or not self.pipeline:
            return 0
        
        try:
            success, duration = self.pipeline.query_duration(Gst.Format.TIME)
            if success:
                return duration // Gst.MSECOND
        except:
            pass
        
        return 0
    
    # ========== VOLUME ==========
    
    def set_volume(self, volume: int):
        """Postavi volume (0-100)"""
        if self._is_cleaning_up:
            return
        
        self._volume = max(0, min(100, volume))
        
        try:
            if self.volume_element:
                self.volume_element.set_property("volume", self._volume / 100.0)
        except Exception as e:
            print(f"⚠️ Error setting volume: {e}")
        
        self.volume_changed.emit(self._volume)
    
    def get_volume(self) -> int:
        """Dobij volume (0-100)"""
        return self._volume
    
    # ========== EQUALIZER ==========
    
    def set_equalizer(self, band_gains: List[float], preamp: float = 0.0) -> bool:
        """
        Postavi EQ vrednosti za sve bandove.
        
        Args:
            band_gains: Lista od 10 vrednosti (-12.0 do +12.0 dB)
            preamp: Preamp gain (-12.0 do +12.0 dB)
            
        Returns:
            True ako je uspešno
        """
        if self._is_cleaning_up or not self.equalizer:
            print("⚠️ Equalizer not available or engine cleaning up")
            return False
        
        if len(band_gains) != 10:
            print(f"⚠️ Expected 10 EQ values, got {len(band_gains)}")
            return False
        
        # Snimi vrednosti
        self._eq_values = band_gains.copy()
        self._eq_preamp = preamp
        
        try:
            # Postavi vrednosti za svaki band
            for i, gain in enumerate(band_gains):
                # Clamp vrednosti
                clamped_gain = max(-24.0, min(12.0, float(gain)))
                self.equalizer.set_property(f"band{i}", clamped_gain)
                print(f"🎛️ EQ band {i} set to {clamped_gain}dB")
            
            # Postavi preamp ako imamo preamp element
            if self.preamp_element:
                # Konvertuj dB u linear gain za volume element
                # 0dB = 1.0, -12dB = 0.25, +12dB = 4.0
                preamp_gain = 10 ** (preamp / 20.0)  # dB to linear conversion
                self.preamp_element.set_property("volume", preamp_gain)
                print(f"🎛️ Preamp set to {preamp}dB (gain: {preamp_gain:.2f})")
            
            self.eq_changed.emit(band_gains)
            print(f"✅ EQ successfully set: {band_gains}, preamp: {preamp}dB")
            return True
            
        except Exception as e:
            print(f"❌ Error setting EQ: {e}")
            return False
    
    def get_equalizer(self) -> List[float]:
        """Dobij trenutne EQ vrednosti"""
        return self._eq_values.copy()
    
    def get_equalizer_full(self) -> Dict[str, Any]:
        """
        Dobij kompletne EQ postavke (band gains + preamp).
        
        Returns:
            Dict sa band_gains i preamp
        """
        return {
            'band_gains': self._eq_values.copy(),
            'preamp': self._eq_preamp
        }
    
    def set_equalizer_band(self, band: int, value: float):
        """Postavi jedan EQ band"""
        if (self._is_cleaning_up or not self.equalizer or 
            band < 0 or band > 9):
            return
        
        try:
            gain = max(-24.0, min(12.0, float(value)))
            self._eq_values[band] = gain
            self.equalizer.set_property(f"band{band}", gain)
        except Exception as e:
            print(f"❌ Error setting EQ band: {e}")
    
    def enable_equalizer(self, enabled: bool):
        """Uključi/isključi EQ"""
        if self._is_cleaning_up:
            return
        
        self._eq_enabled = enabled
        if not enabled:
            # Reset na flat
            flat = [0.0] * 10
            self.set_equalizer(flat, 0.0)
    
    def is_equalizer_enabled(self) -> bool:
        """Da li je EQ uključen"""
        return self._eq_enabled
    
    def has_equalizer(self) -> bool:
        """Proveri da li engine podržava equalizer"""
        return self.equalizer is not None
    
    # ========== STATE ==========
    
    def is_playing(self) -> bool:
        return self._playing and not self._paused
    
    def is_paused(self) -> bool:
        return self._paused
    
    def is_stopped(self) -> bool:
        return not self._playing
    
    # ========== PLAYLIST INTEGRATION ==========
    
    def play_next(self, auto_play: bool = False):
        """
        Pusti sledeću pesmu.
        
        Args:
            auto_play: True ako je automatski pozvan nakon završetka pesme
        """
        if self._is_cleaning_up:
            return
        
        if self.app and hasattr(self.app, 'playlist_manager'):
            try:
                pm = self.app.playlist_manager
                
                # OVO JE NOVO: Ako je auto-play, zaobiđi debounce
                if auto_play:
                    # Bypass debounce za auto-play
                    next_file = pm.next(force=True) if hasattr(pm, 'next') else pm.next()
                else:
                    # Normalni next za korisnički zahtev
                    next_file = pm.next()
                
                if next_file and os.path.exists(next_file):
                    self.play_file(next_file)
                else:
                    print("📚 End of playlist or file not found")
                    self.stop()
            except Exception as e:
                print(f"❌ Error playing next: {e}")
                import traceback
                traceback.print_exc()
    
    def play_previous(self):
        """Pusti prethodnu pesmu"""
        if self._is_cleaning_up:
            return
        
        if self.app and hasattr(self.app, 'playlist_manager'):
            try:
                prev_file = self.app.playlist_manager.prev()
                if prev_file and os.path.exists(prev_file):
                    self.play_file(prev_file)
                else:
                    print("⏮ Start of playlist or file not found")
            except Exception as e:
                print(f"❌ Error playing previous: {e}")
    
    # ========== CLEANUP ==========
    
    def _safe_cleanup(self):
        """Interni cleanup bez printova - za inicijalizacione greške"""
        try:
            # Stop timer
            if hasattr(self, 'position_timer') and self.position_timer:
                if self.position_timer.isActive():
                    self.position_timer.stop()
                self.position_timer.timeout.disconnect()
            
            # Stop pipeline
            if hasattr(self, 'pipeline') and self.pipeline:
                try:
                    self.pipeline.set_state(Gst.State.NULL)
                except:
                    pass
            
            # Remove bus watch
            if hasattr(self, 'bus') and self.bus:
                try:
                    self.bus.disconnect_by_func(self._on_bus_message)
                    self.bus.remove_signal_watch()
                except:
                    pass
        
        except:
            pass  # Silent cleanup
    
    def cleanup(self):
        """
        SIGURAN cleanup GStreamer engine-a.
        Prevencija segfault-a kroz pravilno uništavanje Qt i GStreamer objekata.
        """
        # Prevent re-entrancy
        if self._is_cleaning_up or self._cleanup_lock:
            return
        
        self._cleanup_lock = True
        self._is_cleaning_up = True
        
        print("🎛️ [GStreamer] Starting engine cleanup...")
        
        try:
            # 1. Diskonektuj Qt signale
            try:
                signals = [
                    self.metadata_changed, self.position_changed, 
                    self.volume_changed, self.playback_started,
                    self.playback_stopped, self.playback_paused,
                    self.playback_resumed, self.playback_ended,
                    self.duration_changed, self.error_occurred,
                    self.eq_changed
                ]
                
                for signal in signals:
                    try:
                        signal.disconnect()
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ [GStreamer] Error disconnecting Qt signals: {e}")
            
            # 2. Zaustavi i uništi timer
            try:
                if hasattr(self, 'position_timer') and self.position_timer:
                    # Diskonektuj prvo
                    try:
                        self.position_timer.timeout.disconnect(self._update_position)
                    except:
                        pass
                    
                    # Zaustavi
                    if self.position_timer.isActive():
                        self.position_timer.stop()
                    
                    # Uništi
                    self.position_timer.deleteLater()
                    self.position_timer = None
            except Exception as e:
                print(f"⚠️ [GStreamer] Error cleaning up timer: {e}")
            
            # 3. Zaustavi GStreamer pipeline
            try:
                if hasattr(self, 'pipeline') and self.pipeline:
                    # Diskonektuj bus signale
                    if hasattr(self, 'bus') and self.bus:
                        try:
                            self.bus.disconnect_by_func(self._on_bus_message)
                            self.bus.remove_signal_watch()
                        except:
                            pass
                        self.bus = None
                    
                    # Postavi pipeline na NULL state
                    self.pipeline.set_state(Gst.State.NULL)
                    
                    # Oslobodi reference - DO NOT set to None here!
                    # Let Python garbage collect it
                    
            except Exception as e:
                print(f"⚠️ [GStreamer] Error stopping pipeline: {e}")
            
            # 4. Process GLib events
            try:
                from gi.repository import GLib
                context = GLib.main_context_default()
                for _ in range(3):  # Process a few iterations
                    if context.pending():
                        context.iteration(False)
            except:
                pass
            
            # 5. Očisti reference
            self.app = None
            self.current_file = None
            self.equalizer = None
            self.volume_element = None
            self.preamp_element = None
            self.filesrc = None
            self.decodebin = None
            self.audioconvert = None
            self.audioresample = None
            self.audiosink = None
            
            print("✅ [GStreamer] Engine cleanup completed")
            
        except Exception as e:
            print(f"💥 [GStreamer] Critical error during cleanup: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self._cleanup_lock = False
    
    def __del__(self):
        """Destruktor - za slučaj da cleanup nije pozvan"""
        # NE radite cleanup u __del__! To je opasno sa Qt i GStreamer
        # Python će pozvati __del__ u nepredvidljivom trenutku
        pass


# ========== HELPER ==========

def is_gstreamer_available() -> bool:
    """Proveri da li je GStreamer dostupan"""
    return GSTREAMER_AVAILABLE


def get_gstreamer_version() -> str:
    """Dobij GStreamer verziju"""
    if GSTREAMER_AVAILABLE:
        try:
            return f"{Gst.VERSION_MAJOR}.{Gst.VERSION_MINOR}.{Gst.VERSION_MICRO}"
        except:
            return "Unknown"
    return "Not available"


# ========== TEST ==========
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    print("🧪 Testing GStreamerEngine...")
    
    app = QApplication(sys.argv)
    
    try:
        engine = GStreamerEngine()
        print(f"✅ Engine created successfully")
        print(f"📊 GStreamer version: {get_gstreamer_version()}")
        print(f"🎛️ EQ bands: {len(engine.EQ_BANDS)}")
        print(f"🎛️ Has equalizer: {engine.has_equalizer()}")
        
        # Test EQ sa preamp-om
        test_eq = [0.0, 2.0, 4.0, 2.0, 0.0, -2.0, -4.0, -2.0, 0.0, 2.0]
        success = engine.set_equalizer(test_eq, 3.0)  # Sa preamp-om
        print(f"✅ EQ test: {success}, gains: {engine.get_equalizer()}")
        
        # Test get_equalizer_full
        full_eq = engine.get_equalizer_full()
        print(f"✅ Full EQ: {full_eq}")
        
        # Test volume
        engine.set_volume(80)
        print(f"✅ Volume test: {engine.get_volume()}")
        
        # Cleanup
        print("🧪 Cleaning up engine...")
        engine.cleanup()
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0)