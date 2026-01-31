# -*- coding: utf-8 -*-
# core/engine_factory.py
"""
Engine Factory - Kreira odgovarajući audio engine na osnovu korisničkog izbora

Podržani backend-ovi:
- gstreamer: GStreamer sa 10-band EQ (DEFAULT)
- qt_multimedia: PyQt6 QMediaPlayer (bez EQ podrške)
- null: Null output za testiranje
"""

from typing import Optional, Dict, Any, Type
from PyQt6.QtCore import QObject
import json
from pathlib import Path


# Registar dostupnih engine-a
ENGINE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "gstreamer": {
        "name": "GStreamer",
        "description": "GStreamer with 10-band equalizer (recommended)",
        "has_eq": True,
        "module": "core.gstreamer_engine",
        "class": "GStreamerEngine",
        "available": None  # Proveri runtime
    },
    "qt_multimedia": {
        "name": "Qt Multimedia",
        "description": "Qt6 audio engine (no EQ support)",
        "has_eq": False,
        "module": "core.engine",
        "class": "AudioEngine",
        "available": True  # Uvek dostupan
    },
    "null": {
        "name": "Null Output",
        "description": "Silent output for testing",
        "has_eq": False,
        "module": None,
        "class": None,
        "available": True
    }
}

# Default engine - GStreamer zbog EQ podrške
DEFAULT_ENGINE = "gstreamer"


def check_engine_availability(engine_id: str) -> bool:
    """
    Proveri da li je engine dostupan na sistemu.
    """
    if engine_id not in ENGINE_REGISTRY:
        return False
    
    info = ENGINE_REGISTRY[engine_id]
    
    # Ako je već provereno
    if info["available"] is not None:
        return info["available"]
    
    # Proveri GStreamer
    if engine_id == "gstreamer":
        try:
            from core.gstreamer_engine import is_gstreamer_available
            available = is_gstreamer_available()
            ENGINE_REGISTRY[engine_id]["available"] = available
            return available
        except ImportError:
            ENGINE_REGISTRY[engine_id]["available"] = False
            return False
    
    return info.get("available", False)


def get_available_engines() -> Dict[str, Dict[str, Any]]:
    """
    Dobij listu dostupnih engine-a.
    """
    available = {}
    
    for engine_id, info in ENGINE_REGISTRY.items():
        is_available = check_engine_availability(engine_id)
        available[engine_id] = {
            **info,
            "available": is_available
        }
    
    return available


def create_engine(engine_id: str = None) -> Optional[QObject]:
    """
    Kreiraj audio engine na osnovu ID-a.
    
    Args:
        engine_id: ID engine-a ('gstreamer', 'qt_multimedia', 'null')
                   Ako je None, koristi DEFAULT_ENGINE
    
    Returns:
        Audio engine instance ili None ako nije dostupan
    """
    if engine_id is None:
        engine_id = DEFAULT_ENGINE
    
    print(f"🔧 Creating audio engine: {engine_id}")
    
    # Proveri da li je dostupan
    if not check_engine_availability(engine_id):
        print(f"⚠️ Engine '{engine_id}' is not available, falling back to qt_multimedia")
        engine_id = "qt_multimedia"
    
    info = ENGINE_REGISTRY.get(engine_id)
    if not info:
        print(f"❌ Unknown engine: {engine_id}")
        return None
    
    # Null engine
    if engine_id == "null":
        return _create_null_engine()
    
    # Dinamički import
    try:
        module_name = info["module"]
        class_name = info["class"]
        
        import importlib
        module = importlib.import_module(module_name)
        engine_class = getattr(module, class_name)
        
        engine = engine_class()
        print(f"✅ Engine '{engine_id}' created successfully")
        
        return engine
        
    except ImportError as e:
        print(f"❌ Failed to import engine '{engine_id}': {e}")
        
        # Fallback na Qt Multimedia
        if engine_id != "qt_multimedia":
            print("⚠️ Falling back to Qt Multimedia")
            return create_engine("qt_multimedia")
        
        return None
        
    except Exception as e:
        print(f"❌ Error creating engine '{engine_id}': {e}")
        import traceback
        traceback.print_exc()
        return None


def _create_null_engine():
    """Kreiraj null engine za testiranje"""
    from PyQt6.QtCore import QObject, pyqtSignal
    
    class NullEngine(QObject):
        """Null engine - ne pušta zvuk, samo emituje signale"""
        
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
            self._volume = 70
            self._playing = False
            self._paused = False
            self.current_file = None
            self.app = None
            self.is_cleaning_up = False
        
        def play_file(self, filepath):
            print(f"🔇 [NULL] Playing: {filepath}")
            self.current_file = filepath
            self._playing = True
            self.playback_started.emit(filepath)
            self.duration_changed.emit(180000)  # 3 min dummy
        
        def play(self):
            self._playing = True
            self._paused = False
            self.playback_resumed.emit()
        
        def pause(self):
            self._paused = True
            self.playback_paused.emit()
        
        def stop(self):
            self._playing = False
            self._paused = False
            self.playback_stopped.emit()
        
        def toggle_play_pause(self):
            if self._playing and not self._paused:
                self.pause()
            else:
                self.play()
        
        def set_volume(self, volume):
            self._volume = volume
            self.volume_changed.emit(volume)
        
        def get_volume(self):
            return self._volume
        
        def get_position(self):
            return 0
        
        def get_duration(self):
            return 180000
        
        def seek_to_position(self, pos):
            pass
        
        def is_playing(self):
            return self._playing and not self._paused
        
        def is_paused(self):
            return self._paused
        
        def is_stopped(self):
            return not self._playing
        
        def set_equalizer(self, values):
            print(f"🔇 [NULL] EQ set: {values}")
        
        def get_equalizer(self):
            return [0] * 10
        
        def cleanup(self):
            self.is_cleaning_up = True
    
    return NullEngine()


# ========== SETTINGS PERSISTENCE ==========

SETTINGS_FILE = Path.home() / ".audiowave" / "audio_settings.json"


def save_engine_preference(engine_id: str):
    """Sačuvaj preferiran engine"""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        settings = {}
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
        
        settings["preferred_engine"] = engine_id
        
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        
        print(f"💾 Saved engine preference: {engine_id}")
        
    except Exception as e:
        print(f"⚠️ Could not save engine preference: {e}")


def load_engine_preference() -> str:
    """
    Učitaj preferiran engine.
    Default je GStreamer zbog EQ podrške.
    """
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                return settings.get("preferred_engine", DEFAULT_ENGINE)
    except Exception as e:
        print(f"⚠️ Could not load engine preference: {e}")
    
    # Default: GStreamer (ima EQ podršku)
    return DEFAULT_ENGINE


def create_preferred_engine() -> Optional[QObject]:
    """Kreiraj engine prema sačuvanoj preferenciji"""
    preferred = load_engine_preference()
    return create_engine(preferred)


# ========== INFO ==========

def get_engine_info(engine_id: str) -> Dict[str, Any]:
    """Dobij info o engine-u"""
    if engine_id in ENGINE_REGISTRY:
        info = ENGINE_REGISTRY[engine_id].copy()
        info["available"] = check_engine_availability(engine_id)
        return info
    return {}


def print_available_engines():
    """Ispiši dostupne engine-e"""
    print("\n📊 Available Audio Engines:")
    print("-" * 50)
    
    for engine_id, info in get_available_engines().items():
        status = "✅" if info["available"] else "❌"
        eq = "🎛️" if info["has_eq"] else ""
        default = "(default)" if engine_id == DEFAULT_ENGINE else ""
        print(f"  {status} {info['name']} {eq} {default}")
        print(f"     ID: {engine_id}")
        print(f"     {info['description']}")
    
    print("-" * 50)