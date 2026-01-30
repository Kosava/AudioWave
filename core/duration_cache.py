# core/duration_cache.py - ISPRAVLJEN SA MIGRACIJOM
"""
SQLite cache za audio trajanja - ISPRAVLJENA VERZIJA SA MIGRACIJOM
"""

import sqlite3
import threading
from pathlib import Path
import time
import json
import hashlib
from typing import Optional, Dict, List, Tuple
from collections import OrderedDict


class DurationCache:
    """SQLite cache za audio trajanja - OPTIMIZOVANA VERZIJA SA LRU CACHE-OM"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / ".config" / "traywave" / "duration_cache.db")
        
        self.db_path = db_path
        self.db_path_parent = Path(db_path).parent
        self.db_path_parent.mkdir(parents=True, exist_ok=True)
        
        self.lock = threading.RLock()  # Reentrant lock za thread safety
        
        # Debug stats
        self.debug_mode = True
        self.stats = {
            "db_hits": 0,
            "db_misses": 0,
            "memory_hits": 0,
            "memory_misses": 0,
            "queries": 0,
            "inserts": 0,
            "updates": 0,
            "total_query_time": 0,
            "cache_cleans": 0
        }
        
        self.init_database()
        
        # LRU Memory cache za brži pristup - koristi OrderedDict
        self.memory_cache_max = 5000  # Povećano sa 1000 na 5000
        self.memory_cache = OrderedDict()  # Koristi OrderedDict za LRU
        
        # Brojač za čišćenje - čistimo samo kada pređe prag
        self.access_counter = 0
        self.cleanup_threshold = 100  # Čistimo svakih 100 pristupa
        
        if self.debug_mode:
            print(f"💾 DurationCache initialized at {db_path}")
            print(f"💾 Memory cache size: {self.memory_cache_max}")
    
    def init_database(self):
        """Inicijalizuj SQLite bazu sa migracijom"""
        start_time = time.time()
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # PRVO: Proveri da li postoji tabela i njene kolone
            cursor.execute("PRAGMA table_info(duration_cache)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Kreiraj tabelu ako ne postoji
            if not columns:
                cursor.execute('''
                    CREATE TABLE duration_cache (
                        filepath TEXT PRIMARY KEY,
                        duration INTEGER,
                        filesize INTEGER,
                        modified_time REAL,
                        last_accessed REAL,
                        format TEXT,
                        bitrate INTEGER,
                        file_hash TEXT
                    )
                ''')
                if self.debug_mode:
                    print(f"💿 Created new duration_cache table")
            else:
                # Migracija: dodaj file_hash kolonu ako ne postoji
                if 'file_hash' not in column_names:
                    cursor.execute('''
                        ALTER TABLE duration_cache 
                        ADD COLUMN file_hash TEXT
                    ''')
                    if self.debug_mode:
                        print(f"💿 Added file_hash column to existing table")
            
            # PRAGMA optimizacije za bolje performance
            cursor.execute('PRAGMA journal_mode = WAL')
            cursor.execute('PRAGMA synchronous = NORMAL')
            cursor.execute('PRAGMA cache_size = -2000')  # 2MB cache
            cursor.execute('PRAGMA temp_store = MEMORY')
            cursor.execute('PRAGMA busy_timeout = 30000')  # 30 sekundi timeout
            
            # Kreiraj indekse ako ne postoje
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_accessed 
                ON duration_cache(last_accessed)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_filepath 
                ON duration_cache(filepath)
            ''')
            
            # Kreiraj indeks za file_hash samo ako kolona postoji
            cursor.execute("PRAGMA table_info(duration_cache)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'file_hash' in column_names:
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_file_hash 
                    ON duration_cache(file_hash)
                ''')
            else:
                if self.debug_mode:
                    print(f"⚠️ file_hash column not found, skipping index creation")
            
            conn.commit()
            conn.close()
        
        init_time = time.time() - start_time
        if self.debug_mode:
            print(f"💿 Database initialized in {init_time:.3f}s")
    
    def get_file_hash(self, filepath: str) -> Optional[str]:
        """Napravi hash fajla za validaciju - OPTIMIZOVANO"""
        try:
            path = Path(filepath)
            if not path.exists():
                return None
            
            stat = path.stat()
            # Koristimo kombinaciju filesize i modified time
            file_info = f"{filepath}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(file_info.encode()).hexdigest()
        except:
            return None
    
    def get_duration(self, filepath: str) -> Optional[int]:
        """
        Vrati trajanje iz cache-a - OPTIMIZOVANO
        Returns: duration in seconds or None if not in cache
        """
        query_start = time.time()
        
        # Prvo proveri memory cache sa LRU logikom
        if filepath in self.memory_cache:
            cached = self.memory_cache[filepath]
            
            # Proveri da li je cache validan
            if self.is_cache_valid(cached, filepath):
                # Move to end (most recently used)
                self.memory_cache.move_to_end(filepath)
                cached["last_accessed"] = time.time()
                self.stats["memory_hits"] += 1
                
                query_time = time.time() - query_start
                self.stats["total_query_time"] += query_time
                
                return cached["duration"]
            else:
                # Remove invalid cache entry
                del self.memory_cache[filepath]
                self.stats["memory_misses"] += 1
        
        # Onda proveri database cache
        with self.lock:
            try:
                file_hash = self.get_file_hash(filepath)
                if not file_hash:
                    self.stats["db_misses"] += 1
                    return None
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                self.stats["queries"] += 1
                
                # Proveri prvo po file_hash, pa po filepath
                cursor.execute('''
                    SELECT duration, filesize, modified_time, last_accessed, file_hash 
                    FROM duration_cache 
                    WHERE file_hash = ? OR filepath = ?
                    ORDER BY CASE 
                        WHEN file_hash = ? THEN 1 
                        WHEN filepath = ? THEN 2 
                        ELSE 3 
                    END
                    LIMIT 1
                ''', (file_hash, filepath, file_hash, filepath))
                
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    duration, cached_filesize, cached_mtime, last_accessed, cached_hash = result
                    
                    # Proveri hash umesto samo filesize-a
                    if file_hash == cached_hash or filepath == filepath:
                        # Update last accessed
                        self.update_last_accessed(filepath)
                        
                        # Update file_hash ako je stari unos
                        if cached_hash != file_hash:
                            self.update_file_hash(filepath, file_hash)
                        
                        # Store in memory cache
                        cache_entry = {
                            "duration": duration,
                            "filesize": cached_filesize,
                            "modified_time": cached_mtime,
                            "last_accessed": time.time(),
                            "file_hash": file_hash
                        }
                        
                        # Add to memory cache (LRU)
                        self.memory_cache[filepath] = cache_entry
                        if len(self.memory_cache) > self.memory_cache_max:
                            # Remove least recently used
                            self.memory_cache.popitem(last=False)
                        
                        self.stats["db_hits"] += 1
                        
                        query_time = time.time() - query_start
                        self.stats["total_query_time"] += query_time
                        
                        return duration
                
                self.stats["db_misses"] += 1
                return None
                
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ DB query error for {Path(filepath).name}: {e}")
                self.stats["db_misses"] += 1
                return None
    
    def update_file_hash(self, filepath: str, file_hash: str):
        """Update file_hash u bazi"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE duration_cache 
                    SET file_hash = ?, last_accessed = ? 
                    WHERE filepath = ?
                ''', (file_hash, time.time(), filepath))
                conn.commit()
                conn.close()
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ Error updating file_hash: {e}")
    
    def is_cache_valid(self, cache_entry: Dict, filepath: str) -> bool:
        """Proveri da li je cache entry validan - sa hash proverom"""
        try:
            current_hash = self.get_file_hash(filepath)
            if not current_hash:
                return False
            
            cached_hash = cache_entry.get("file_hash")
            return current_hash == cached_hash
        except:
            return False
    
    def update_last_accessed(self, filepath: str):
        """Update last accessed time u bazi"""
        with self.lock:
            try:
                current_time = time.time()
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE duration_cache 
                    SET last_accessed = ? 
                    WHERE filepath = ?
                ''', (current_time, filepath))
                conn.commit()
                conn.close()
                self.stats["updates"] += 1
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ Error updating last accessed: {e}")
    
    def store_duration(self, filepath: str, duration: int, 
                      format: str = None, bitrate: int = None):
        """Store duration in cache - OPTIMIZOVANO"""
        store_start = time.time()
        
        with self.lock:
            try:
                file_hash = self.get_file_hash(filepath)
                if not file_hash or duration is None:
                    return False
                
                path = Path(filepath)
                stat = path.stat()
                filepath_abs = str(path.absolute())
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Proveri da li file_hash kolona postoji
                cursor.execute("PRAGMA table_info(duration_cache)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'file_hash' in column_names:
                    cursor.execute('''
                        INSERT OR REPLACE INTO duration_cache 
                        (filepath, duration, filesize, modified_time, last_accessed, 
                         format, bitrate, file_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        filepath_abs, 
                        duration, 
                        stat.st_size, 
                        stat.st_mtime, 
                        time.time(),
                        format,
                        bitrate,
                        file_hash
                    ))
                else:
                    # Fallback za staru verziju bez file_hash
                    cursor.execute('''
                        INSERT OR REPLACE INTO duration_cache 
                        (filepath, duration, filesize, modified_time, last_accessed, 
                         format, bitrate)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        filepath_abs, 
                        duration, 
                        stat.st_size, 
                        stat.st_mtime, 
                        time.time(),
                        format,
                        bitrate
                    ))
                
                conn.commit()
                conn.close()
                self.stats["inserts"] += 1
                
                # Store in memory cache too
                cache_entry = {
                    "duration": duration,
                    "filesize": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "last_accessed": time.time(),
                    "format": format,
                    "bitrate": bitrate,
                    "file_hash": file_hash
                }
                
                # Add to LRU cache
                self.memory_cache[filepath] = cache_entry
                if len(self.memory_cache) > self.memory_cache_max:
                    # Remove least recently used
                    self.memory_cache.popitem(last=False)
                
                store_time = time.time() - store_start
                if self.debug_mode and store_time > 0.1:
                    print(f"💾 SLOW store: {Path(filepath).name} - {store_time:.3f}s")
                
                return True
                
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ Error storing duration: {e}")
                return False
    
    def get_batch_durations(self, filepaths: List[str]) -> Dict[str, Optional[int]]:
        """Vrati trajanja za batch fajlova - OPTIMIZOVANO"""
        results = {}
        
        with self.lock:
            try:
                # Prvo proveri memory cache za sve
                for filepath in filepaths:
                    if filepath in self.memory_cache:
                        cached = self.memory_cache[filepath]
                        if self.is_cache_valid(cached, filepath):
                            # Move to end (most recently used)
                            self.memory_cache.move_to_end(filepath)
                            results[filepath] = cached["duration"]
                            self.stats["memory_hits"] += 1
                        else:
                            # Remove invalid cache entry
                            del self.memory_cache[filepath]
                            self.stats["memory_misses"] += 1
                
                # Za preostale proveri DB
                remaining = [fp for fp in filepaths if fp not in results]
                if remaining:
                    # Prepare hashes for remaining files
                    file_hashes = {}
                    valid_files = {}
                    
                    for fp in remaining:
                        file_hash = self.get_file_hash(fp)
                        if file_hash:
                            file_hashes[fp] = file_hash
                            valid_files[fp] = fp
                    
                    # Batch query za sve hash-ove odjednom
                    if file_hashes:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        
                        # Proveri da li file_hash kolona postoji
                        cursor.execute("PRAGMA table_info(duration_cache)")
                        columns = cursor.fetchall()
                        column_names = [col[1] for col in columns]
                        
                        if 'file_hash' in column_names and file_hashes:
                            # Query po hash-u
                            placeholders = ','.join(['?'] * len(file_hashes))
                            hashes_list = list(file_hashes.values())
                            
                            cursor.execute(f'''
                                SELECT file_hash, duration, filesize, modified_time 
                                FROM duration_cache 
                                WHERE file_hash IN ({placeholders})
                            ''', hashes_list)
                            
                            db_results = cursor.fetchall()
                            
                            # Map results back to filepaths
                            hash_to_data = {}
                            for file_hash, duration, filesize, modified_time in db_results:
                                hash_to_data[file_hash] = {
                                    "duration": duration,
                                    "filesize": filesize,
                                    "modified_time": modified_time
                                }
                            
                            for fp, fh in file_hashes.items():
                                if fh in hash_to_data:
                                    data = hash_to_data[fh]
                                    results[fp] = data["duration"]
                                    self.stats["db_hits"] += 1
                                    
                                    # Store in memory cache
                                    self.memory_cache[fp] = {
                                        "duration": data["duration"],
                                        "filesize": data["filesize"],
                                        "modified_time": data["modified_time"],
                                        "last_accessed": time.time(),
                                        "file_hash": fh
                                    }
                        else:
                            # Fallback: query po filepath
                            for fp in remaining:
                                cursor.execute('''
                                    SELECT duration, filesize, modified_time 
                                    FROM duration_cache 
                                    WHERE filepath = ?
                                ''', (fp,))
                                
                                result = cursor.fetchone()
                                if result:
                                    duration, filesize, modified_time = result
                                    results[fp] = duration
                                    self.stats["db_hits"] += 1
                                    
                                    # Store in memory cache
                                    self.memory_cache[fp] = {
                                        "duration": duration,
                                        "filesize": filesize,
                                        "modified_time": modified_time,
                                        "last_accessed": time.time(),
                                        "file_hash": self.get_file_hash(fp) or ""
                                    }
                        
                        conn.close()
                
                # Ensure all filepaths are in results
                for filepath in filepaths:
                    if filepath not in results:
                        results[filepath] = None
                        self.stats["db_misses"] += 1
                
                # Čišćenje memory cache ako je potrebno
                self.maybe_cleanup_memory_cache()
                
                return results
                
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ Error in batch query: {e}")
                # Fallback na individual queries
                for filepath in filepaths:
                    results[filepath] = self.get_duration(filepath)
                return results
    
    def maybe_cleanup_memory_cache(self):
        """Očisti memory cache samo ako pređe prag"""
        self.access_counter += 1
        
        if self.access_counter >= self.cleanup_threshold:
            self.access_counter = 0
            
            # Samo logujemo, ne čistimo agresivno
            if self.debug_mode and len(self.memory_cache) >= self.memory_cache_max:
                self.stats["cache_cleans"] += 1
                # Samo obriši neke stare entryje ako je baš potrebno
                if len(self.memory_cache) > self.memory_cache_max * 1.1:
                    # Remove oldest 10%
                    items_to_remove = len(self.memory_cache) - self.memory_cache_max
                    for _ in range(items_to_remove):
                        self.memory_cache.popitem(last=False)
                    
                    if self.debug_mode:
                        print(f"🧹 Cleaned {items_to_remove} old items from memory cache")
    
    def cleanup_old_entries(self, max_age_days: int = 30):
        """Obriši stare cache unose iz baze"""
        cleanup_start = time.time()
        
        with self.lock:
            try:
                cutoff = time.time() - (max_age_days * 24 * 3600)
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM duration_cache WHERE last_accessed < ?', (cutoff,))
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                # Clear memory cache too
                self.memory_cache.clear()
                
                cleanup_time = time.time() - cleanup_start
                if self.debug_mode:
                    print(f"🧹 Cleaned up {deleted} old cache entries in {cleanup_time:.2f}s")
                
                return deleted
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ Error cleaning up cache: {e}")
                return 0
    
    def clear_cache(self):
        """Obriši celu cache bazu"""
        with self.lock:
            try:
                Path(self.db_path).unlink(missing_ok=True)
                self.memory_cache.clear()
                self.init_database()
                
                if self.debug_mode:
                    print(f"🧹 Cache database cleared")
                
                return True
            except Exception as e:
                if self.debug_mode:
                    print(f"❌ Error clearing cache: {e}")
                return False
    
    def get_stats(self) -> Dict:
        """Vrati statistiku cache-a"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM duration_cache')
                db_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT AVG(duration) FROM duration_cache WHERE duration IS NOT NULL')
                avg_duration = cursor.fetchone()[0] or 0
                conn.close()
                
                total_hits = self.stats["memory_hits"] + self.stats["db_hits"]
                total_access = total_hits + self.stats["db_misses"] + self.stats["memory_misses"]
                
                hit_rate = (total_hits / total_access * 100) if total_access > 0 else 0
                memory_hit_rate = (self.stats["memory_hits"] / total_access * 100) if total_access > 0 else 0
                
                return {
                    "database_entries": db_count,
                    "memory_cache_entries": len(self.memory_cache),
                    "memory_cache_max": self.memory_cache_max,
                    "total_accesses": total_access,
                    "memory_hits": self.stats["memory_hits"],
                    "memory_misses": self.stats["memory_misses"],
                    "db_hits": self.stats["db_hits"],
                    "db_misses": self.stats["db_misses"],
                    "inserts": self.stats["inserts"],
                    "updates": self.stats["updates"],
                    "cache_cleans": self.stats["cache_cleans"],
                    "hit_rate": f"{hit_rate:.1f}%",
                    "memory_hit_rate": f"{memory_hit_rate:.1f}%",
                    "avg_query_time": f"{self.stats['total_query_time']/total_access:.3f}s" if total_access > 0 else "0s",
                    "avg_duration": f"{avg_duration:.1f}s",
                    "db_size_mb": Path(self.db_path).stat().st_size / (1024 * 1024) if Path(self.db_path).exists() else 0
                }
            except Exception as e:
                return {"error": str(e)}