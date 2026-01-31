# ui/panels/playlist_search.py
# Search and filtering functionality za playlist

import time
from pathlib import Path
from PyQt6.QtCore import QTimer


class PlaylistSearchManager:
    """Manager za search i filtering operacije"""
    
    def __init__(self, playlist_panel):
        self.playlist_panel = playlist_panel
        self._current_search = ""
        
        # Search debounce timer
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)  # 200ms debounce
        
        # State
        self._is_searching = False
    
    def setup_search_connections(self):
        """Setup search-related signal connections"""
        self.playlist_panel.search_box.textChanged.connect(self._on_search_changed_debounced)
        self._search_timer.timeout.connect(self._perform_search)
    
    def _on_search_changed_debounced(self, text):
        """Debounced search handler"""
        self._current_search = text
        self._search_timer.stop()
        self._search_timer.start(200)
    
    def _perform_search(self):
        """Perform actual search after debounce"""
        if self._is_searching:
            return
        
        self._is_searching = True
        
        try:
            if self.playlist_panel.playlist_manager and hasattr(self.playlist_panel.playlist_manager, 'current_playlist'):
                search_text = self._current_search.lower()
                current_playlist = self.playlist_panel.playlist_manager.current_playlist
                
                if not search_text:
                    self.playlist_panel.refresh_list(current_playlist)
                else:
                    # Optimized search
                    filtered = []
                    for f in current_playlist:
                        # Quick filename check first (fastest)
                        if search_text in Path(f).stem.lower():
                            filtered.append(f)
                            continue
                        
                        # Check full path if needed
                        if search_text in f.lower():
                            filtered.append(f)
                    
                    self.playlist_panel.refresh_list(filtered)
        finally:
            self._is_searching = False
    
    def get_current_search(self):
        """Get current search text"""
        return self._current_search
    
    def clear_search(self):
        """Clear current search"""
        self._current_search = ""
        self._search_timer.stop()
        if self.playlist_panel.search_box:
            self.playlist_panel.search_box.clear()
    
    def search_tracks(self, search_text):
        """Programmatically search tracks"""
        self._current_search = search_text
        if self.playlist_panel.search_box:
            self.playlist_panel.search_box.setText(search_text)
        self._perform_search()