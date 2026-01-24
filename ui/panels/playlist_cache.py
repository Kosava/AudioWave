# ui/panels/playlist_cache.py
# Thread-safe cache manager za playlist

import time
import threading
from pathlib import Path
from PyQt6.QtCore import QTimer

try:
    from core.audio_utils import get_audio_duration, format_duration
    from core.metadata_reader import read_basic_metadata
    METADATA_READER_AVAILABLE = True
except ImportError as e:
    METADATA_READER_AVAILABLE = False
    print(f'⚠️ Metadata utilities not available: {e}')


class PlaylistCacheManager:
    """Thread-safe cache manager za playlist metadata i duration"""
    
    def __init__(self, playlist_panel=None):
        self.playlist_panel = playlist_panel
        
        # Thread-safe caches
        self.duration_cache = {}
        self.metadata_cache = {}
        self.display_name_cache = {}
        
        # Loading flags
        self.loading_durations = set()
        self.loading_metadata = set()
        
        # Threading locks
        self._cache_lock = threading.Lock()
        self._loading_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "async_loads": 0,
            "total_load_time": 0,
            "metadata_hits": 0,
            "metadata_misses": 0,
            "display_name_hits": 0,
            "display_name_misses": 0
        }
    
    def get_duration(self, filepath):
        """Thread-safe duration getter"""
        start_time = time.time()
        
        with self._cache_lock:
            if filepath in self.duration_cache:
                self.stats["cache_hits"] += 1
                return self.duration_cache[filepath]
        
        self.stats["cache_misses"] += 1
        
        # Check if already loading
        with self._loading_lock:
            if filepath in self.loading_durations:
                return "..."
        
        # Try to get from playlist manager cache
        if (self.playlist_panel and 
            hasattr(self.playlist_panel, 'app') and 
            hasattr(self.playlist_panel.app, 'playlist_manager')):
            
            pm = self.playlist_panel.app.playlist_manager
            duration = pm.get_duration(filepath)
            if duration is not None:
                duration_str = format_duration(duration)
                with self._cache_lock:
                    self.duration_cache[filepath] = duration_str
                load_time = time.time() - start_time
                self.stats["total_load_time"] += load_time
                return duration_str
        
        # Start async load
        with self._loading_lock:
            self.loading_durations.add(filepath)
        
        self.stats["async_loads"] += 1
        
        # Use thread pool for async loading
        QTimer.singleShot(0, lambda: self.load_duration_async(filepath))
        
        return "..."
    
    def get_display_name(self, filepath):
        """Get display name with optimized caching"""
        with self._cache_lock:
            if filepath in self.display_name_cache:
                self.stats["display_name_hits"] += 1
                return self.display_name_cache[filepath]
        
        self.stats["display_name_misses"] += 1
        
        # Get from metadata cache or load
        with self._cache_lock:
            if filepath in self.metadata_cache:
                metadata = self.metadata_cache[filepath]
                display_name = self._format_display_name(metadata, filepath)
                self.display_name_cache[filepath] = display_name
                return display_name
        
        # Start async metadata load
        with self._loading_lock:
            if filepath not in self.loading_metadata:
                self.loading_metadata.add(filepath)
                QTimer.singleShot(0, lambda: self.load_metadata_async(filepath))
        
        # Return filename as fallback while loading
        return Path(filepath).stem
    
    def _format_display_name(self, metadata, filepath):
        """Format display name from metadata"""
        try:
            title = metadata.get('title', '').strip()
            artist = metadata.get('artist', '').strip()
            
            if artist and title and artist != 'Unknown Artist' and title != 'Unknown':
                return f"{artist} - {title}"
            elif title and title != 'Unknown':
                return title
            elif artist and artist != 'Unknown Artist':
                return artist
        except:
            pass
        
        return Path(filepath).stem
    
    def load_duration_async(self, filepath):
        """Load duration in background"""
        start_time = time.time()
        try:
            duration = get_audio_duration(filepath)
            duration_str = format_duration(duration) if duration else "0:00"
            
            with self._cache_lock:
                self.duration_cache[filepath] = duration_str
            
            with self._loading_lock:
                self.loading_durations.discard(filepath)
            
            self.stats["total_load_time"] += time.time() - start_time
            
            # Update playlist manager cache
            if (self.playlist_panel and 
                hasattr(self.playlist_panel, 'app') and 
                hasattr(self.playlist_panel.app, 'playlist_manager')):
                
                pm = self.playlist_panel.app.playlist_manager
                if duration is not None:
                    pm.store_duration(filepath, duration)
            
            # Schedule UI update
            if self.playlist_panel and hasattr(self.playlist_panel, 'file_list'):
                QTimer.singleShot(0, lambda: self.playlist_panel.file_list.viewport().update())
                
        except Exception as e:
            with self._cache_lock:
                self.duration_cache[filepath] = "0:00"
            
            with self._loading_lock:
                self.loading_durations.discard(filepath)
    
    def load_metadata_async(self, filepath):
        """Load metadata in background"""
        try:
            if not METADATA_READER_AVAILABLE:
                return
            
            metadata = read_basic_metadata(filepath)
            
            with self._cache_lock:
                self.metadata_cache[filepath] = metadata
                # Update display name cache
                self.display_name_cache[filepath] = self._format_display_name(metadata, filepath)
            
            with self._loading_lock:
                self.loading_metadata.discard(filepath)
            
            # Schedule UI update
            if self.playlist_panel and hasattr(self.playlist_panel, 'file_list'):
                QTimer.singleShot(0, lambda: self.playlist_panel.file_list.viewport().update())
                
        except Exception as e:
            with self._loading_lock:
                self.loading_metadata.discard(filepath)
    
    def clear_cache(self):
        """Clear all caches"""
        with self._cache_lock:
            self.duration_cache.clear()
            self.metadata_cache.clear()
            self.display_name_cache.clear()
        
        with self._loading_lock:
            self.loading_durations.clear()
            self.loading_metadata.clear()
        
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "async_loads": 0,
            "total_load_time": 0,
            "metadata_hits": 0,
            "metadata_misses": 0,
            "display_name_hits": 0,
            "display_name_misses": 0
        }
    
    def clear_cache_for_file(self, filepath):
        """Clear cache for specific file"""
        with self._cache_lock:
            if filepath in self.duration_cache:
                del self.duration_cache[filepath]
            if filepath in self.metadata_cache:
                del self.metadata_cache[filepath]
            if filepath in self.display_name_cache:
                del self.display_name_cache[filepath]
        
        with self._loading_lock:
            self.loading_durations.discard(filepath)
            self.loading_metadata.discard(filepath)
    
    def get_stats(self):
        """Get cache statistics"""
        return self.stats.copy()