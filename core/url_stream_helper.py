# -*- coding: utf-8 -*-
# core/url_stream_helper.py
"""
Helper modul za podršku URL streaming-a u AudioWave.
Koristi uridecodebin za streaming URL-ova.
"""

import os
from pathlib import Path

# Import GStreamer za stream kontrolu
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    GST_AVAILABLE = True
except ImportError:
    GST_AVAILABLE = False
    print("⚠️ GStreamer not available for URL streaming")


def is_stream_url(filepath: str) -> bool:
    """
    Proveri da li je filepath zapravo URL stream.
    
    Args:
        filepath: Putanja ili URL
        
    Returns:
        True ako je URL stream, False ako je lokalni fajl
    """
    if not filepath or not isinstance(filepath, str):
        return False
    
    return filepath.startswith(('http://', 'https://', 'mms://', 'rtsp://', 'rtmp://'))


def patch_gstreamer_play_file(engine):
    """
    Patch-uje GStreamer engine play_file metodu da podrži URL streaming.
    Koristi uridecodebin umesto filesrc za URL-ove.
    
    Args:
        engine: GStreamerEngine instanca
    """
    if not GST_AVAILABLE:
        print("⚠️ Cannot patch engine - GStreamer not available")
        return
    
    # Sačuvaj originalnu metodu
    original_play_file = engine.play_file
    
    # Dodaj atribute za URL streaming
    engine._stream_pipeline = None
    engine._stream_source = None
    engine._is_streaming = False
    
    def patched_play_file(filepath: str):
        """Wrapper oko play_file koji dodaje URL podršku"""
        # Proveri da li engine čisti
        if engine._is_cleaning_up:
            print("⚠️ Engine is cleaning up, cannot play")
            return
        
        # Proveri da li je URL ili fajl
        is_url = is_stream_url(filepath)
        
        # Validacija
        if not is_url and not os.path.exists(filepath):
            engine.error_occurred.emit(f"File not found: {filepath}")
            return
        
        # Log
        if is_url:
            print(f"📻 GStreamer streaming: {filepath}")
        else:
            print(f"🎵 GStreamer playing: {Path(filepath).name}")
        
        try:
            # Za URL streaming, koristi playbin (najjednostavnije)
            if is_url:
                _play_stream_url(engine, filepath)
            else:
                # Za lokalne fajlove, koristi originalnu metodu
                # Ali prvo zaustavi stream ako je aktivan
                if engine._is_streaming:
                    _stop_stream(engine)
                original_play_file(filepath)
                
        except Exception as e:
            print(f"❌ Error playing file/stream: {e}")
            import traceback
            traceback.print_exc()
            engine.error_occurred.emit(str(e))
            engine._playing = False
            engine._paused = False
    
    def _play_stream_url(engine, url: str):
        """
        Pusti URL stream koristeći playbin3.
        playbin3 automatski hendluje sve - source, decoding, output.
        """
        # Zaustavi glavni pipeline
        if engine.pipeline:
            engine.pipeline.set_state(Gst.State.NULL)
        
        # Zaustavi prethodni stream ako postoji
        if engine._stream_pipeline:
            _stop_stream(engine)
        
        # Kreiraj playbin za streaming
        engine._stream_pipeline = Gst.ElementFactory.make("playbin", "stream-player")
        if not engine._stream_pipeline:
            # Probaj playbin3
            engine._stream_pipeline = Gst.ElementFactory.make("playbin3", "stream-player")
            if not engine._stream_pipeline:
                raise RuntimeError("Failed to create playbin element for streaming")
        
        # Postavi URI
        engine._stream_pipeline.set_property("uri", url)
        
        # Poveži volume sa stream pipeline-om
        # playbin ima ugrađen volume control
        if hasattr(engine, '_volume'):
            volume_linear = engine._volume / 100.0
            engine._stream_pipeline.set_property("volume", volume_linear)
        
        # Postavi audio sink (koristimo isti kao glavni pipeline)
        if engine.audiosink:
            # Ne možemo ponovo koristiti isti sink, kreiraj novi
            audio_sink = Gst.ElementFactory.make("autoaudiosink", "stream-sink")
            if audio_sink:
                engine._stream_pipeline.set_property("audio-sink", audio_sink)
        
        # Postavi bus za monitoring
        bus = engine._stream_pipeline.get_bus()
        bus.add_signal_watch()
        
        # Handler za bus poruke
        def on_stream_message(bus, message):
            t = message.type
            if t == Gst.MessageType.EOS:
                print("📻 Stream ended")
                engine.playback_ended.emit()
                _stop_stream(engine)
            elif t == Gst.MessageType.ERROR:
                err, debug = message.parse_error()
                print(f"❌ Stream error: {err}, {debug}")
                engine.error_occurred.emit(str(err))
                _stop_stream(engine)
            elif t == Gst.MessageType.STATE_CHANGED:
                if message.src == engine._stream_pipeline:
                    old_state, new_state, pending = message.parse_state_changed()
                    if new_state == Gst.State.PLAYING:
                        print("📻 Stream playing")
        
        bus.connect("message", on_stream_message)
        
        # Pokreni stream
        result = engine._stream_pipeline.set_state(Gst.State.PLAYING)
        if result == Gst.StateChangeReturn.FAILURE:
            raise RuntimeError("Failed to start stream playback")
        
        # Update engine state
        engine.current_file = url
        engine._playing = True
        engine._paused = False
        engine._is_streaming = True
        
        # Pokreni position timer (iako stream možda nema poznatu duration)
        if engine.position_timer:
            engine.position_timer.start()
        
        engine.playback_started.emit(url)
    
    def _stop_stream(engine):
        """Zaustavi stream playback"""
        if engine._stream_pipeline:
            bus = engine._stream_pipeline.get_bus()
            if bus:
                bus.remove_signal_watch()
            
            engine._stream_pipeline.set_state(Gst.State.NULL)
            engine._stream_pipeline = None
        
        engine._is_streaming = False
        engine._playing = False
        engine._paused = False
    
    # Override stop, pause metode da hendluju streaming
    original_stop = engine.stop
    
    def patched_stop():
        if engine._is_streaming:
            _stop_stream(engine)
        else:
            original_stop()
    
    original_pause = engine.pause
    
    def patched_pause():
        if engine._is_streaming and engine._stream_pipeline:
            engine._stream_pipeline.set_state(Gst.State.PAUSED)
            engine._paused = True
            engine.playback_paused.emit()
        else:
            original_pause()
    
    # GStreamerEngine koristi play() za resume, ne resume()
    original_play = engine.play
    
    def patched_play():
        if engine._is_streaming and engine._stream_pipeline:
            engine._stream_pipeline.set_state(Gst.State.PLAYING)
            engine._paused = False
            engine.playback_resumed.emit()
        else:
            original_play()
    
    # Patch volume control
    original_set_volume = engine.set_volume
    
    def patched_set_volume(volume: int):
        original_set_volume(volume)
        # Update stream volume ako je aktivan
        if engine._is_streaming and engine._stream_pipeline:
            volume_linear = volume / 100.0
            engine._stream_pipeline.set_property("volume", volume_linear)
    
    # Patch toggle_play_pause za streaming
    original_toggle = engine.toggle_play_pause
    
    def patched_toggle_play_pause():
        if engine._is_streaming:
            if engine._playing and not engine._paused:
                patched_pause()
            elif engine._paused:
                patched_play()
        else:
            original_toggle()
    
    # Zameni metode sa patched verzijama
    engine.play_file = patched_play_file
    engine.stop = patched_stop
    engine.pause = patched_pause
    engine.play = patched_play  # Za resume funkcionalnost
    engine.set_volume = patched_set_volume
    engine.toggle_play_pause = patched_toggle_play_pause
    
    print("✅ GStreamer engine patched for URL streaming support (using playbin)")


def get_stream_display_name(url: str, custom_name: str = None) -> str:
    """
    Generiši display name za stream URL.
    
    Args:
        url: Stream URL
        custom_name: Korisničko ime (opciono)
        
    Returns:
        Formatiran display name
    """
    if custom_name and custom_name.strip():
        return f"📻 {custom_name.strip()}"
    
    # Pokušaj da ekstraktuješ ime iz URL-a
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or "Stream"
        
        # Ukloni www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Ukloni port broj
        if ':' in domain:
            domain = domain.split(':')[0]
        
        return f"📻 {domain}"
    except:
        return f"📻 Stream"