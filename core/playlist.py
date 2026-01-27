# core/playlist.py - OPTIMIZOVANA VERZIJA SA BOLJIM CACHE-OM
"""
Playlist manager with tab support and duration cache - OPTIMIZED VERSION
"""

import json
import os
import random
import threading
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Import our duration cache
from .duration_cache import DurationCache
# Import audio utils
from .audio_utils import get_audio_duration, format_duration


class PlaylistManager(QObject):
    """Menadžer za playliste sa tabovima i duration cache-om - OPTIMIZOVANA VERZIJA"""
    
    playlist_changed = pyqtSignal(str)  # playlist_name
    current_playlist_changed = pyqtSignal()
    current_index_changed = pyqtSignal(int)
    playlists_updated = pyqtSignal(dict)  # Svi playlisti
    duration_loaded = pyqtSignal(str, int)  # filepath, duration
    
    def __init__(self):
        super().__init__()
        self.playlists = {}  # name -> list of files
        self.current_playlist_name = "default"
        self.current_playlist = []
        self.current_index = -1
        self.shuffle = False
        self.repeat = "none"  # "none", "one", "all"
        
        # ✅ DODAJ DEBOUNCE ZAŠTITU:
        self._last_next_time = 0  # Debounce zaštita
        self._last_prev_time = 0  # Debounce zaštita
        
        # Debug info
        self.debug_mode = True
        self.init_time = time.time()
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "background_loads": 0,
            "total_load_time": 0,
            "sql_queries": 0,
            "prefetch_calls": 0,
            "prefetch_loaded": 0
        }
        
        # Duration cache
        print(f"🎵 Initializing DurationCache...")
        cache_start = time.time()
        self.duration_cache = DurationCache()
        cache_init_time = time.time() - cache_start
        print(f"✅ DurationCache initialized in {cache_init_time:.2f}s")
        
        # Cache za total duration po playlisti
        self._total_duration_cache = {}  # cache_key -> (timestamp, value)
        
        # Background loading
        self.background_loading = False
        self.loading_thread = None
        self.stop_loading = threading.Event()
        
        # Timer za periodic cache cleanup
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_cache)
        self.cleanup_timer.start(24 * 60 * 60 * 1000)  # Svakih 24 sata
        
        # Timer za debug info - svakih 30 sekundi umesto 10
        self.debug_timer = QTimer()
        self.debug_timer.timeout.connect(self.print_debug_info)
        if self.debug_mode:
            self.debug_timer.start(30000)  # Svakih 30 sekundi
        
        # Učitaj playliste iz fajla
        print(f"📋 Loading playlists from file...")
        self.load_playlists()
        
        # Start background loading za trenutnu playlistu sa delay-om
        QTimer.singleShot(3000, self.start_background_loading)
        
        print(f"✅ PlaylistManager initialized in {time.time() - self.init_time:.2f}s")
    
    def print_debug_info(self):
        """Print debug informacija - OPTIMIZOVANO"""
        if not self.debug_mode:
            return
        
        print(f"\n=== PLAYLIST MANAGER DEBUG INFO ===")
        print(f"Uptime: {time.time() - self.init_time:.1f}s")
        print(f"Current playlist: {self.current_playlist_name} ({len(self.current_playlist)} tracks)")
        print(f"Total playlists: {len(self.playlists)}")
        
        # Cache efektivnost
        total_access = self.stats['cache_hits'] + self.stats['cache_misses']
        if total_access > 0:
            hit_rate = (self.stats['cache_hits'] / total_access) * 100
            print(f"Cache stats: Hits={self.stats['cache_hits']:,}, Misses={self.stats['cache_misses']:,}, Rate={hit_rate:.1f}%")
        
        print(f"Background loads: {self.stats['background_loads']:,}")
        print(f"Prefetch: {self.stats['prefetch_loaded']:,} loaded in {self.stats['prefetch_calls']:,} calls")
        
        if self.stats['total_load_time'] > 0:
            avg_load_time = self.stats['total_load_time'] / total_access if total_access > 0 else 0
            print(f"Total/avg load time: {self.stats['total_load_time']:.2f}s / {avg_load_time:.3f}s")
        
        # Cache DB info sa boljim podacima
        try:
            cache_path = Path.home() / ".config" / "traywave" / "duration_cache.db"
            if cache_path.exists():
                size_mb = cache_path.stat().st_size / (1024 * 1024)
                print(f"Cache DB size: {size_mb:.2f} MB")
                
                conn = sqlite3.connect(str(cache_path))
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM duration_cache')
                cache_count = cursor.fetchone()[0]
                
                # Cache coverage za trenutnu playlistu
                if self.current_playlist:
                    coverage = (cache_count / len(self.current_playlist) * 100)
                    print(f"Cache coverage: {coverage:.1f}% ({cache_count:,}/{len(self.current_playlist):,})")
                
                # Get recent access stats
                cursor.execute('SELECT COUNT(*) FROM duration_cache WHERE last_accessed > ?', 
                             (time.time() - 3600,))  # Last hour
                recent_access = cursor.fetchone()[0]
                
                # Get hit rate iz cache-a
                cache_stats = self.duration_cache.get_stats()
                if isinstance(cache_stats, dict) and 'hit_rate' in cache_stats:
                    print(f"Cache hit rate: {cache_stats['hit_rate']}")
                
                conn.close()
                
                if recent_access > 0:
                    print(f"Recent access: {recent_access:,} in last hour")
        except Exception as e:
            if self.debug_mode:
                print(f"Error reading cache stats: {e}")
        
        # Background loading status
        if self.background_loading:
            print(f"Background loading: ACTIVE")
        else:
            print(f"Background loading: INACTIVE")
        
        print("=" * 40)
    
    def load_playlists(self):
        """Učitaj playliste iz JSON fajla"""
        start_time = time.time()
        
        playlist_file = Path.home() / ".config" / "traywave" / "playlists.json"
        playlist_file.parent.mkdir(parents=True, exist_ok=True)
        
        if playlist_file.exists():
            try:
                with open(playlist_file, 'r') as f:
                    self.playlists = json.load(f)
                if self.debug_mode:
                    print(f"📁 Loaded {len(self.playlists)} playlists from {playlist_file}")
            except Exception as e:
                print(f"❌ Error loading playlists: {e}")
                self.playlists = {}
        else:
            self.playlists = {}
            if self.debug_mode:
                print(f"📁 Created new playlists file: {playlist_file}")
        
        # Default playlist
        if "default" not in self.playlists:
            self.playlists["default"] = []
            self.save_playlists()
        
        # Postavi trenutnu playlistu
        if self.current_playlist_name in self.playlists:
            self.current_playlist = self.playlists[self.current_playlist_name].copy()
        
        load_time = time.time() - start_time
        if self.debug_mode and load_time > 0.1:
            print(f"⏱️ load_playlists took {load_time:.3f}s")
        
        self.playlists_updated.emit(self.playlists)
        
        # Emituj signal da se playlista promenila - ovo omogucava UI-u da ucita sadrzaj
        # Koristi QTimer.singleShot da damo vremena UI-u da se inicijalizuje
        QTimer.singleShot(500, lambda: self.current_playlist_changed.emit())
    
    def save_playlists(self):
        """Sačuvaj playliste u JSON fajl"""
        playlist_file = Path.home() / ".config" / "traywave" / "playlists.json"
        playlist_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(playlist_file, 'w') as f:
                json.dump(self.playlists, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving playlists: {e}")
    
    # ========== DURATION CACHE METHODS - OPTIMIZOVANO ==========
    
    def get_duration(self, filepath: str) -> Optional[int]:
        """Vrati trajanje iz cache-a - OPTIMIZOVANO"""
        start_time = time.time()
        
        # PRVO proveri memory cache direktno
        if hasattr(self.duration_cache, 'memory_cache'):
            if filepath in self.duration_cache.memory_cache:
                cached = self.duration_cache.memory_cache[filepath]
                try:
                    path = Path(filepath)
                    if path.exists() and path.stat().st_size == cached.get("filesize"):
                        self.stats["cache_hits"] += 1
                        load_time = time.time() - start_time
                        self.stats["total_load_time"] += load_time
                        return cached.get("duration")
                except:
                    pass
        
        # ONDA proveri kroz duration_cache metodu
        if hasattr(self, 'duration_cache'):
            duration = self.duration_cache.get_duration(filepath)
            
            if duration is not None:
                self.stats["cache_hits"] += 1
            else:
                self.stats["cache_misses"] += 1
            
            load_time = time.time() - start_time
            self.stats["total_load_time"] += load_time
            
            # Debug slow loads
            if self.debug_mode and load_time > 0.1:
                print(f"🌐 SLOW cache get: {Path(filepath).name} - {load_time:.3f}s")
            
            return duration
        
        return None
    
    def get_batch_durations(self, filepaths: List[str]) -> Dict[str, Optional[int]]:
        """Vrati trajanja za batch fajlova - OPTIMIZOVANO"""
        if not hasattr(self, 'duration_cache'):
            return {fp: None for fp in filepaths}
        
        results = {}
        
        # Prvo proveri memory cache za sve
        for filepath in filepaths:
            if filepath in self.duration_cache.memory_cache:
                cached = self.duration_cache.memory_cache[filepath]
                try:
                    path = Path(filepath)
                    if path.exists() and path.stat().st_size == cached.get("filesize"):
                        results[filepath] = cached.get("duration")
                        self.stats["cache_hits"] += 1
                        continue
                except:
                    pass
        
        # Za preostale, koristi DB batch
        remaining = [fp for fp in filepaths if fp not in results]
        if remaining:
            db_results = self.duration_cache.get_batch_durations(remaining)
            results.update(db_results)
            
            # Update stats
            for filepath, duration in db_results.items():
                if duration is not None:
                    self.stats["cache_hits"] += 1
                else:
                    self.stats["cache_misses"] += 1
        
        # Ensure all filepaths are in results
        for filepath in filepaths:
            if filepath not in results:
                results[filepath] = None
        
        return results
    
    def get_total_duration(self, playlist_name: str = None) -> Tuple[int, int]:
        """
        Vrati ukupno trajanje playliste - OPTIMIZOVANO
        Returns: (known_duration, unknown_count)
        """
        name = playlist_name or self.current_playlist_name
        playlist = self.playlists.get(name, [])
        
        if not playlist:
            return 0, 0
        
        # Koristi batch query za sve fajlove odjednom
        start_time = time.time()
        durations = self.get_batch_durations(playlist)
        
        total = 0
        unknown_count = 0
        
        for filepath in playlist:
            duration = durations.get(filepath)
            if duration is not None:
                total += duration
            else:
                unknown_count += 1
        
        calc_time = time.time() - start_time
        if self.debug_mode and calc_time > 0.1:
            print(f"⏱️ get_total_duration for '{name}' took {calc_time:.3f}s")
        
        return total, unknown_count
    
    def get_formatted_total_duration(self, playlist_name: str = None) -> str:
        """Vrati formatirano ukupno trajanje playliste - CACHED"""
        name = playlist_name or self.current_playlist_name
        
        # Koristi cached vrednost ako postoji
        cache_key = f"total_dur_{name}"
        current_time = time.time()
        
        if cache_key in self._total_duration_cache:
            cached_time, cached_value = self._total_duration_cache[cache_key]
            if current_time - cached_time < 5:  # Cache 5 sekundi
                return cached_value
        
        # Ako nema u cache-u, izračunaj
        total_duration, unknown_count = self.get_total_duration(name)
        
        if unknown_count > 0:
            result = f"{format_duration(total_duration)} ({unknown_count} unknown)"
        else:
            result = format_duration(total_duration)
        
        # Store u cache
        self._total_duration_cache[cache_key] = (current_time, result)
        
        return result
    
    def store_duration(self, filepath: str, duration: int):
        """Store duration in cache"""
        if hasattr(self, 'duration_cache'):
            success = self.duration_cache.store_duration(filepath, duration)
            
            if success:
                self.duration_loaded.emit(filepath, duration)
                
                # Invalidate total duration cache za sve playliste koje sadrže ovaj fajl
                for playlist_name, files in self.playlists.items():
                    if filepath in files:
                        cache_key = f"total_dur_{playlist_name}"
                        self._total_duration_cache.pop(cache_key, None)
    
    # ========== PLAYLIST MANAGEMENT ==========
    
    def create_playlist(self, name: str):
        """Kreiraj novu playlistu"""
        if name and name not in self.playlists:
            self.playlists[name] = []
            self.save_playlists()
            self.playlists_updated.emit(self.playlists)
            return True
        return False
    
    def delete_playlist(self, name: str):
        """Obriši playlistu"""
        if name in self.playlists and name != "default":
            del self.playlists[name]
            
            # Ako je trenutna playlista obrisana, prebaci na default
            if self.current_playlist_name == name:
                self.switch_to_playlist("default")
            
            self.save_playlists()
            self.playlists_updated.emit(self.playlists)
            return True
        return False
    
    def rename_playlist(self, old_name: str, new_name: str):
        """Preimenuj playlistu"""
        if old_name in self.playlists and new_name not in self.playlists:
            self.playlists[new_name] = self.playlists[old_name]
            del self.playlists[old_name]
            
            if self.current_playlist_name == old_name:
                self.current_playlist_name = new_name
            
            self.save_playlists()
            self.playlists_updated.emit(self.playlists)
            return True
        return False
    
    def add_to_playlist(self, playlist_name: str, filepath: str):
        """Dodaj fajl u playlistu"""
        if playlist_name in self.playlists:
            if filepath not in self.playlists[playlist_name]:
                self.playlists[playlist_name].append(filepath)
                self.save_playlists()
                
                # Invalidate total duration cache
                cache_key = f"total_dur_{playlist_name}"
                self._total_duration_cache.pop(cache_key, None)
                
                # Ako je trenutna playlista, ažuriraj
                if playlist_name == self.current_playlist_name:
                    self.current_playlist = self.playlists[playlist_name].copy()
                    self.playlist_changed.emit(playlist_name)
                
                return True
        return False
    
    def remove_from_playlist(self, playlist_name: str, filepath: str):
        """Ukloni fajl iz playliste"""
        if playlist_name in self.playlists:
            if filepath in self.playlists[playlist_name]:
                self.playlists[playlist_name].remove(filepath)
                self.save_playlists()
                
                # Invalidate total duration cache
                cache_key = f"total_dur_{playlist_name}"
                self._total_duration_cache.pop(cache_key, None)
                
                # Ako je trenutna playlista, ažuriraj
                if playlist_name == self.current_playlist_name:
                    self.current_playlist = self.playlists[playlist_name].copy()
                    self.playlist_changed.emit(playlist_name)
                    # Podesi index
                    if self.current_index >= len(self.current_playlist):
                        self.current_index = max(0, len(self.current_playlist) - 1)
                        self.current_index_changed.emit(self.current_index)
                
                return True
        return False
    
    def switch_to_playlist(self, playlist_name: str):
        """Prebaci na drugu playlistu"""
        if playlist_name in self.playlists:
            self.current_playlist_name = playlist_name
            self.current_playlist = self.playlists[playlist_name].copy()
            self.current_index = 0 if self.current_playlist else -1
            self.playlist_changed.emit(playlist_name)
            self.current_index_changed.emit(self.current_index)
            
            # Start background loading za novu playlistu sa delay-om
            QTimer.singleShot(1000, self.start_background_loading)
            return True
        return False
    
    def get_current_playlist_name(self) -> str:
        """Vrati ime trenutne playliste"""
        return self.current_playlist_name
    
    def get_playlist_names(self) -> List[str]:
        """Vrati listu imena playlisti"""
        return list(self.playlists.keys())
    
    def add_files(self, filepaths: List[str], playlist_name: str = None):
        """Dodaj fajlove u playlistu"""
        start_time = time.time()
        
        target_playlist = playlist_name or self.current_playlist_name
        
        if target_playlist not in self.playlists:
            self.create_playlist(target_playlist)
        
        added_count = 0
        for filepath in filepaths:
            if filepath not in self.playlists[target_playlist]:
                self.playlists[target_playlist].append(filepath)
                added_count += 1
        
        if added_count > 0:
            self.save_playlists()
            
            # Invalidate total duration cache
            cache_key = f"total_dur_{target_playlist}"
            self._total_duration_cache.pop(cache_key, None)
            
            # Ako je trenutna playlista, ažuriraj
            if target_playlist == self.current_playlist_name:
                self.current_playlist = self.playlists[target_playlist].copy()
                self.playlist_changed.emit(target_playlist)
                
                if self.current_index == -1 and self.current_playlist:
                    self.current_index = 0
                    self.current_index_changed.emit(0)
            
            # Start background loading za nove fajlove sa delay-om
            QTimer.singleShot(2000, self.start_background_loading)
            
            add_time = time.time() - start_time
            if self.debug_mode:
                print(f"📥 Added {added_count:,} files to '{target_playlist}' in {add_time:.2f}s")
            
            return True
        
        return False
    
    def remove_files(self, filepaths: List[str], playlist_name: str = None):
        """Ukloni fajlove iz playliste"""
        target_playlist = playlist_name or self.current_playlist_name
        
        if target_playlist in self.playlists:
            removed = False
            for filepath in filepaths:
                if filepath in self.playlists[target_playlist]:
                    self.playlists[target_playlist].remove(filepath)
                    removed = True
            
            if removed:
                self.save_playlists()
                
                # Invalidate total duration cache
                cache_key = f"total_dur_{target_playlist}"
                self._total_duration_cache.pop(cache_key, None)
                
                # Ako je trenutna playlista, ažuriraj
                if target_playlist == self.current_playlist_name:
                    self.current_playlist = self.playlists[target_playlist].copy()
                    self.playlist_changed.emit(target_playlist)
                    
                    # Podesi index
                    if self.current_index >= len(self.current_playlist):
                        self.current_index = max(0, len(self.current_playlist) - 1)
                        self.current_index_changed.emit(self.current_index)
                
                return True
        return False
    
    def clear_current_playlist(self):
        """Očisti trenutnu playlistu"""
        if self.current_playlist_name in self.playlists:
            self.playlists[self.current_playlist_name] = []
            self.current_playlist = []
            self.current_index = -1
            
            # Clear total duration cache
            cache_key = f"total_dur_{self.current_playlist_name}"
            self._total_duration_cache[cache_key] = (time.time(), "0:00")
            
            self.save_playlists()
            self.playlist_changed.emit(self.current_playlist_name)
            self.current_index_changed.emit(-1)
            return True
        return False
    
    def clear_playlist(self, playlist_name: str):
        """Očisti određenu playlistu"""
        if playlist_name in self.playlists:
            self.playlists[playlist_name] = []
            
            # Clear total duration cache
            cache_key = f"total_dur_{playlist_name}"
            self._total_duration_cache[cache_key] = (time.time(), "0:00")
            
            if playlist_name == self.current_playlist_name:
                self.current_playlist = []
                self.current_index = -1
                self.current_index_changed.emit(-1)
            
            self.save_playlists()
            self.playlist_changed.emit(playlist_name)
            return True
        return False
    
    # ========== PLAYBACK NAVIGATION ==========
    
    def get_current_file(self) -> Optional[str]:
        """Vrati trenutni fajl"""
        if 0 <= self.current_index < len(self.current_playlist):
            return self.current_playlist[self.current_index]
        return None
    
    def set_current_index(self, index: int):
        """Postavi trenutni index"""
        if 0 <= index < len(self.current_playlist):
            self.current_index = index
            self.current_index_changed.emit(index)
            return True
        return False
    
    def find_file_index(self, filepath: str) -> int:
        """Pronađi index fajla u trenutnoj playlisti"""
        try:
            return self.current_playlist.index(filepath)
        except ValueError:
            return -1
    
    def next(self, force: bool = False) -> Optional[str]:
        """Idi na sledeću pesmu - SA DEBOUNCE ZAŠTITOM I FORCE PARAMETROM"""
        import time
        
        # ✅ Omogući force za auto-play (ignoriši debounce)
        if not force:
            current_time = time.time()
            if current_time - self._last_next_time < 0.5:  # 500ms debounce za normalne pozive
                print(f"⚠️ [PlaylistManager] next() called too quickly ({current_time - self._last_next_time:.3f}s), ignoring")
                return None
        
        self._last_next_time = time.time()
        
        if not self.current_playlist:
            return None
        
        if self.shuffle:
            # Shuffle mode
            if len(self.current_playlist) > 1:
                new_index = self.current_index
                while new_index == self.current_index:
                    new_index = random.randint(0, len(self.current_playlist) - 1)
                self.current_index = new_index
            else:
                pass  # Ostani na istoj ako je samo jedna pesma
        else:
            # Normal mode
            if self.repeat == "one":
                pass  # Ostani na istoj pesmi
            elif self.current_index < len(self.current_playlist) - 1:
                self.current_index += 1
            else:
                if self.repeat == "all":
                    self.current_index = 0
                else:
                    return None  # Kraj playliste
        
        self.current_index_changed.emit(self.current_index)
        return self.get_current_file()
    
    def prev(self) -> Optional[str]:
        """Idi na prethodnu pesmu - SA DEBOUNCE ZAŠTITOM"""
        import time
        
        # ✅ DODAJ DEBOUNCE:
        current_time = time.time()
        if current_time - self._last_prev_time < 0.5:  # 500ms
            print(f"⚠️ [PlaylistManager] prev() called too quickly, ignoring")
            return None
        
        self._last_prev_time = current_time
        
        if not self.current_playlist:
            return None
        
        if self.shuffle:
            if len(self.current_playlist) > 1:
                new_index = self.current_index
                while new_index == self.current_index:
                    new_index = random.randint(0, len(self.current_playlist) - 1)
                self.current_index = new_index
            else:
                pass
        else:
            if self.repeat == "one":
                pass
            elif self.current_index > 0:
                self.current_index -= 1
            else:
                if self.repeat == "all":
                    self.current_index = len(self.current_playlist) - 1
                else:
                    self.current_index = 0
        
        self.current_index_changed.emit(self.current_index)
        return self.get_current_file()
    
    def set_repeat(self, mode: str):
        """Postavi repeat mode"""
        if mode in ["none", "one", "all"]:
            self.repeat = mode
    
    def set_shuffle(self, shuffle: bool):
        """Postavi shuffle mode"""
        self.shuffle = shuffle
    
    # ========== BACKGROUND LOADING ==========
    
    def start_background_loading(self):
        """Pokreni background thread za učitavanje duration-a - OPTIMIZOVANO"""
        if self.background_loading or not self.current_playlist:
            return
        
        # Proveri da li već imamo dovoljno u cache-u
        cache_stats = self.get_duration_stats()
        if isinstance(cache_stats, dict) and 'database_entries' in cache_stats:
            db_entries = cache_stats['database_entries']
            current_count = len(self.current_playlist)
            
            # Ako već imamo preko 80% fajlova u cache-u, preskoči
            if current_count > 0 and db_entries > current_count * 0.8:
                if self.debug_mode:
                    print(f"🎵 Skipping background loading - {db_entries:,}/{current_count:,} already cached ({db_entries/current_count*100:.1f}%)")
                return
        
        self.stop_loading.clear()
        self.background_loading = True
        
        def load_durations():
            playlist = self.current_playlist.copy()
            total_files = len(playlist)
            
            if self.debug_mode:
                print(f"🎵 Starting background loading for {total_files:,} files...")
            
            start_time = time.time()
            
            # Koristi batch loading za bolje performance
            batch_size = 100
            loaded_count = 0
            cached_count = 0
            
            for i in range(0, total_files, batch_size):
                if self.stop_loading.is_set():
                    if self.debug_mode:
                        print(f"⏹️ Background loading stopped by user after {i:,} files")
                    break
                
                batch = playlist[i:i+batch_size]
                
                # Get durations for batch
                batch_durations = self.get_batch_durations(batch)
                
                # Load missing durations
                for filepath in batch:
                    duration = batch_durations.get(filepath)
                    if duration is None:
                        try:
                            duration = get_audio_duration(filepath)
                            if duration is not None:
                                self.store_duration(filepath, duration)
                                loaded_count += 1
                                self.stats["background_loads"] += 1
                        except Exception as e:
                            if self.debug_mode and i % 500 == 0:
                                print(f"⚠️ Error loading duration for {Path(filepath).name}: {e}")
                    else:
                        cached_count += 1
                
                # Progress report svakih 500 fajlova umesto 100
                if i % 500 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    if self.debug_mode:
                        print(f"  Background: {i:,}/{total_files:,} files, "
                              f"{loaded_count:,} loaded, {cached_count:,} cached, "
                              f"{rate:.1f} files/sec")
            
            total_time = time.time() - start_time
            if self.debug_mode:
                print(f"✅ Background loading complete: {loaded_count:,} loaded, "
                      f"{cached_count:,} cached in {total_time:.1f}s "
                      f"({total_files/total_time:.1f} files/sec)")
            
            self.background_loading = False
        
        self.loading_thread = threading.Thread(target=load_durations, daemon=True)
        self.loading_thread.start()
    
    def stop_background_loading(self):
        """Zaustavi background loading"""
        self.stop_loading.set()
        if self.loading_thread and self.loading_thread.is_alive():
            self.loading_thread.join(timeout=2)
        self.background_loading = False
    
    def prefetch_durations(self, filepaths: List[str]):
        """Prefetch durations for files (background) - MANJE AGRESIVNO"""
        if not filepaths or not hasattr(self, 'duration_cache') or self.stop_loading.is_set():
            return
        
        # Ograniči na 50 fajlova odjednom
        if len(filepaths) > 50:
            filepaths = filepaths[:50]
        
        self.stats["prefetch_calls"] += 1
        
        if self.debug_mode:
            print(f"🚀 Prefetching {len(filepaths)} durations...")
        
        def prefetch():
            # Dodaj mali delay da ne preopteretimo sistem
            time.sleep(0.1)
            
            start_time = time.time()
            
            # Koristi batch query
            batch_durations = self.duration_cache.get_batch_durations(filepaths)
            
            loaded = 0
            for filepath in filepaths:
                if self.stop_loading.is_set():
                    break
                
                if batch_durations.get(filepath) is None:
                    try:
                        duration = get_audio_duration(filepath)
                        if duration is not None:
                            self.duration_cache.store_duration(filepath, duration)
                            loaded += 1
                            self.stats["prefetch_loaded"] += 1
                    except:
                        pass
            
            total_time = time.time() - start_time
            if self.debug_mode and loaded > 0:
                print(f"✅ Prefetch complete: {loaded} loaded in {total_time:.2f}s")
        
        thread = threading.Thread(target=prefetch, daemon=True)
        thread.start()
    
    # ========== UTILITY METHODS ==========
    
    def get_playlist_info(self, playlist_name: str = None) -> Dict:
        """Vrati informacije o playlisti"""
        name = playlist_name or self.current_playlist_name
        playlist = self.playlists.get(name, [])
        
        return {
            "name": name,
            "files": playlist.copy(),
            "current_index": self.current_index if name == self.current_playlist_name else -1,
            "shuffle": self.shuffle if name == self.current_playlist_name else False,
            "repeat": self.repeat if name == self.current_playlist_name else "none",
            "total": len(playlist)
        }
    
    def get_all_playlists_info(self) -> Dict[str, Dict]:
        """Vrati informacije o svim playlistama"""
        return {
            name: {
                "name": name,
                "files": files.copy(),
                "total": len(files)
            }
            for name, files in self.playlists.items()
        }
    
    def cleanup_old_cache(self):
        """Očisti stari cache"""
        if self.debug_mode:
            print(f"🧹 Starting cache cleanup...")
        
        if hasattr(self, 'duration_cache'):
            deleted = self.duration_cache.cleanup_old_entries(30)
            
            if self.debug_mode and deleted > 0:
                print(f"🧹 Cleaned {deleted:,} old cache entries")
        
        # Clear total duration cache
        self._total_duration_cache.clear()
    
    def clear_duration_cache(self):
        """Obriši celu duration cache"""
        if self.debug_mode:
            print(f"🧹 Clearing entire duration cache...")
        
        if hasattr(self, 'duration_cache'):
            self.duration_cache.clear_cache()
        self._total_duration_cache.clear()
        
        if self.debug_mode:
            print(f"🧹 Duration cache cleared")
    
    def get_duration_stats(self) -> Dict:
        """Vrati statistiku o duration cache-u"""
        if hasattr(self, 'duration_cache'):
            stats = self.duration_cache.get_stats()
            
            # Dodaj naše statove
            if isinstance(stats, dict):
                stats.update({
                    "playlist_manager_hits": self.stats["cache_hits"],
                    "playlist_manager_misses": self.stats["cache_misses"],
                    "playlist_manager_background_loads": self.stats["background_loads"],
                    "playlist_manager_prefetch_calls": self.stats["prefetch_calls"],
                    "playlist_manager_prefetch_loaded": self.stats["prefetch_loaded"],
                    "playlist_manager_total_load_time": self.stats["total_load_time"],
                    "playlist_manager_sql_queries": self.stats["sql_queries"],
                    "current_playlist_files": len(self.current_playlist),
                    "total_playlists": len(self.playlists),
                    "background_loading_active": self.background_loading
                })
            return stats
        return {"error": "No duration cache available"}