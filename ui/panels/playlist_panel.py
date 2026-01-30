# -*- coding: utf-8 -*-
# ui/panels/playlist_panel.py
# KOORDINATOR - Glavni playlist panel koji integriše sve module

import json
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QLineEdit,
    QFileDialog, QMessageBox, QMenu, QFrame, QComboBox,
    QInputDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QRect, QEvent, QUrl
from PyQt6.QtGui import QAction, QFont, QPainter, QColor, QDragEnterEvent, QDropEvent, QPalette, QBrush
from pathlib import Path
import threading

from .playlist_delegate import WinampPlaylistItemDelegate
from .playlist_search import PlaylistSearchManager
from .playlist_operations import PlaylistOperationsManager
from .playlist_context_menu import PlaylistContextMenuManager

# Import SVG Icon Manager
try:
    from ui.utils.svg_icon_manager import get_themed_icon
    SVG_ICONS_AVAILABLE = True
except ImportError:
    SVG_ICONS_AVAILABLE = False
    print('Ã¢šÂ Ã¯Â¸Â SVG Icon Manager not available, using text fallback')

# Import audio utils
try:
    from core.audio_utils import get_audio_duration, format_duration, is_audio_file
    AUDIO_UTILS_AVAILABLE = True
except ImportError as e:
    AUDIO_UTILS_AVAILABLE = False
    print(f'Ã¢šÂ Ã¯Â¸Â Audio utils not available: {e}')

# Import MetadataReader
try:
    from core.metadata_reader import MetadataReader, read_metadata, read_basic_metadata
    METADATA_READER_AVAILABLE = True
except ImportError as e:
    METADATA_READER_AVAILABLE = False
    print(f'Ã¢šÂ Ã¯Â¸Â MetadataReader not available: {e}')


class PlaylistPanel(QWidget):
    play_requested = pyqtSignal(str)
    playlist_changed = pyqtSignal(str)
    new_playlist_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.playlist_manager = app.playlist_manager
        self.setObjectName("playlist_panel")
        
        # Optimizacije
        self.start_time = time.time()
        self.load_times = []
        self.debug_mode = False
        
        # Theme tracking za SVG ikone
        self.current_theme_color = "#667eea"  # Default primary color
        self.is_dark_theme = True
        
        # Managers
        self.search_manager = PlaylistSearchManager(self)
        self.operations_manager = PlaylistOperationsManager(self)
        self.context_menu_manager = PlaylistContextMenuManager(self)
        
        # Debounce timers
        self._last_status_update = 0
        self._last_scroll_time = 0
        self._scroll_timer = QTimer()
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(300)
        
        # Visible items optimization
        self._visible_items_timer = QTimer()
        self._visible_items_timer.setSingleShot(True)
        self._visible_items_timer.setInterval(100)
        
        # Metadata preloading
        self._metadata_preload_timer = QTimer()
        self._metadata_preload_timer.setSingleShot(True)
        self._metadata_preload_timer.setInterval(500)
        
        # State
        self._is_loading = False
        self._pending_refresh = False
        self._current_highlighted_file = None
        
        # Ã¢Å“â€ Highlight debounce - prevents rapid duplicate highlights
        self._highlight_debounce_timer = QTimer()
        self._highlight_debounce_timer.setSingleShot(True)
        self._highlight_debounce_timer.setInterval(50)  # 50ms debounce
        self._pending_highlight_file = None
        self._last_highlight_time = 0
        
        self.setAcceptDrops(True)
        
        self.setup_ui()
        self.setup_connections()
        self.load_playlists()
        
        if self.debug_mode:
            self.debug_timer = QTimer()
            self.debug_timer.timeout.connect(self.print_debug_info)
            self.debug_timer.start(30000)
        
        QTimer.singleShot(100, self.force_load_playlist)
    
    def _get_icon(self, icon_name: str, size: int = 24):
        """
        Helper metoda za dobijanje SVG ikone prema trenutnoj temi.
        Fallback na text ako SVG nije dostupan.
        """
        if SVG_ICONS_AVAILABLE:
            return get_themed_icon(icon_name, self.current_theme_color, self.is_dark_theme, size)
        return None

    def print_debug_info(self):
        """Print debug information"""
        if not self.debug_mode:
            return
        
        if hasattr(self, 'delegate'):
            stats = self.delegate.get_stats()
            print(f"\n♪ PLAYLIST DELEGATE STATS:")
            print(f"   Duration: Hits={stats['cache_hits']}, Misses={stats['cache_misses']}")
            print(f"   Metadata: Hits={stats['metadata_hits']}, Misses={stats['metadata_misses']}")
            print(f"   Display: Hits={stats['display_name_hits']}, Misses={stats['display_name_misses']}")
            print(f"   Async Loads: {stats['async_loads']}, Total Time: {stats['total_load_time']:.3f}s")

    def setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 5, 12, 10)
        layout.setSpacing(10)

        # Toolbar
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("playlistToolbar")
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(0, 5, 0, 5)
        toolbar_layout.setSpacing(8)
        
        self.new_playlist_btn = QPushButton()
        self.new_playlist_btn.setObjectName("newPlaylistButton")
        self.new_playlist_btn.setFixedSize(32, 32)
        self.new_playlist_btn.setToolTip("Create New Playlist")
        self.new_playlist_btn.clicked.connect(self.create_new_playlist)
        icon = self._get_icon('add', 20)
        if icon:
            self.new_playlist_btn.setIcon(icon)
            self.new_playlist_btn.setIconSize(QSize(20, 20))
        else:
            self.new_playlist_btn.setText("+")
        
        self.playlist_selector = QComboBox()
        self.playlist_selector.setObjectName("playlistSelector")
        self.playlist_selector.setMinimumWidth(200)
        self.playlist_selector.setEditable(False)
        self.playlist_selector.currentTextChanged.connect(self.on_playlist_selected)
        
        self.delete_playlist_btn = QPushButton()
        self.delete_playlist_btn.setObjectName("deletePlaylistButton")
        self.delete_playlist_btn.setFixedSize(32, 32)
        self.delete_playlist_btn.setToolTip("Delete Current Playlist")
        self.delete_playlist_btn.clicked.connect(self.delete_current_playlist)
        self.delete_playlist_btn.setEnabled(False)
        icon = self._get_icon('delete', 20)
        if icon:
            self.delete_playlist_btn.setIcon(icon)
            self.delete_playlist_btn.setIconSize(QSize(20, 20))
        else:
            self.delete_playlist_btn.setText("ÃƒÆ’Ã¢â‚¬â€")
        
        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("settingsButton")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        icon = self._get_icon('settings', 20)
        if icon:
            self.settings_btn.setIcon(icon)
            self.settings_btn.setIconSize(QSize(20, 20))
        else:
            self.settings_btn.setText("Ã¢šâ„¢")
        
        toolbar_layout.addWidget(self.new_playlist_btn)
        toolbar_layout.addWidget(self.playlist_selector, 1)
        toolbar_layout.addWidget(self.delete_playlist_btn)
        toolbar_layout.addWidget(self.settings_btn)
        
        layout.addWidget(toolbar_frame)

        # Search
        self.search_box = QLineEdit()
        self.search_box.setObjectName("playlistSearch")
        self.search_box.setPlaceholderText("Search tracks...")
        layout.addWidget(self.search_box)

        # List
        self.file_list = QListWidget()
        self.file_list.setObjectName("winampPlaylistList")
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.file_list.setAcceptDrops(True)
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
        # Optimizovani delegate
        self.delegate = WinampPlaylistItemDelegate(self.file_list)
        self.delegate.set_playlist_panel(self)
        self.file_list.setItemDelegate(self.delegate)
        
        layout.addWidget(self.file_list, 1)

        # Bottom
        bottom_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Music")
        self.add_btn.setObjectName("addMusicButton")
        icon = self._get_icon("add", 18)
        if icon:
            self.add_btn.setIcon(icon)
            self.add_btn.setIconSize(QSize(18, 18))
        else:
            self.add_btn.setText("+ Add Music")
        add_menu = QMenu(self.add_btn)
        add_menu.addAction("Add Files", self.add_files)
        add_menu.addAction("Add Folder", self.add_folder)
        add_menu.addAction("Add URL (Stream)", self.add_url)
        self.add_btn.setMenu(add_menu)
        
        self.clear_btn = QPushButton("Clear Playlist")
        self.clear_btn.setObjectName("clearPlaylistButton")
        icon_clear = self._get_icon("delete", 18)
        if icon_clear:
            self.clear_btn.setIcon(icon_clear)
            self.clear_btn.setIconSize(QSize(18, 18))
        else:
            self.clear_btn.setText("ÃƒÆ’Ã¢â‚¬â€ Clear Playlist")
        self.clear_btn.clicked.connect(self.clear_playlist)
        
        self.status_label = QLabel("Ready • 0 tracks • 0:00")
        self.status_label.setObjectName("playlistStatus")
        
        bottom_layout.addWidget(self.add_btn)
        bottom_layout.addWidget(self.clear_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.status_label)
        
        layout.addLayout(bottom_layout)

        # Install event filters
        self.file_list.viewport().installEventFilter(self)
        self.file_list.verticalScrollBar().valueChanged.connect(self.on_scroll)

    def eventFilter(self, obj, event):
        if obj == self.file_list.viewport():
            if event.type() == QEvent.Type.Resize:
                self._scroll_timer.start(200)
        return super().eventFilter(obj, event)

    def on_scroll(self):
        """Optimized scroll handler"""
        current_time = time.time()
        if current_time - self._last_scroll_time < 0.1:
            return
        self._last_scroll_time = current_time
        
        self._scroll_timer.stop()
        self._scroll_timer.start(200)
        
        self._visible_items_timer.stop()
        self._visible_items_timer.start(100)

    def setup_connections(self):
        """Setup all signal connections"""
        self.file_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        
        self.search_manager.setup_search_connections()
        
        self._scroll_timer.timeout.connect(self.load_visible_metadata)
        self._visible_items_timer.timeout.connect(self.load_visible_durations)
        self._metadata_preload_timer.timeout.connect(self.preload_metadata)
        
        if self.playlist_manager:
            if hasattr(self.playlist_manager, 'playlist_changed'):
                self.playlist_manager.playlist_changed.connect(self.on_external_playlist_changed)
            if hasattr(self.playlist_manager, 'playlists_updated'):
                self.playlist_manager.playlists_updated.connect(self.on_playlists_updated)
            if hasattr(self.playlist_manager, 'duration_loaded'):
                self.playlist_manager.duration_loaded.connect(self.on_duration_loaded)
            if hasattr(self.playlist_manager, 'current_playlist_changed'):
                self.playlist_manager.current_playlist_changed.connect(self.on_current_playlist_changed)
            if hasattr(self.playlist_manager, 'current_index_changed'):
                self.playlist_manager.current_index_changed.connect(self.on_current_index_changed)

    def load_visible_metadata(self):
        """Load metadata for visible items"""
        viewport = self.file_list.viewport()
        start_index = self.file_list.indexAt(viewport.rect().topLeft())
        end_index = self.file_list.indexAt(viewport.rect().bottomRight())
        
        if not start_index.isValid():
            return
        
        start_row = max(0, start_index.row() - 5)
        end_row = min(self.file_list.count() - 1, end_index.row() + 10)
        
        for row in range(start_row, end_row + 1):
            item = self.file_list.item(row)
            if item:
                filepath = item.data(Qt.ItemDataRole.UserRole)
                if filepath and METADATA_READER_AVAILABLE:
                    self.delegate.get_display_name_cached(filepath)

    def load_visible_durations(self):
        """Load durations for visible items"""
        if not self.playlist_manager:
            return
        
        viewport = self.file_list.viewport()
        start_index = self.file_list.indexAt(viewport.rect().topLeft())
        end_index = self.file_list.indexAt(viewport.rect().bottomRight())
        
        if not start_index.isValid():
            return
        
        start_row = max(0, start_index.row() - 3)
        end_row = min(self.file_list.count() - 1, end_index.row() + 6)
        
        filepaths_to_load = []
        for row in range(start_row, end_row + 1):
            item = self.file_list.item(row)
            if item:
                filepath = item.data(Qt.ItemDataRole.UserRole)
                if filepath:
                    filepaths_to_load.append(filepath)
        
        if filepaths_to_load:
            for filepath in filepaths_to_load:
                self.delegate.get_duration(filepath)

    def preload_metadata(self):
        """Preload metadata for upcoming items"""
        if not self.playlist_manager or self.file_list.count() == 0:
            return
        
        current_row = self.file_list.currentRow()
        if current_row < 0:
            current_row = 0
        
        preload_start = current_row + 1
        preload_end = min(self.file_list.count() - 1, current_row + 20)
        
        for row in range(preload_start, preload_end + 1):
            item = self.file_list.item(row)
            if item:
                filepath = item.data(Qt.ItemDataRole.UserRole)
                if filepath and METADATA_READER_AVAILABLE:
                    self.delegate.get_display_name_cached(filepath)

    def force_load_playlist(self):
        """Force load playlist with optimizations"""
        if self._is_loading:
            self._pending_refresh = True
            return
        
        self._is_loading = True
        
        if self.playlist_manager:
            self.delegate.clear_cache()
            # Direktno uÃƒâ€žÃ‚ÂÃƒâ€šÃ‚Âitaj listu umesto poziva refresh_list koji proverava _is_loading
            self._do_refresh_list(self.playlist_manager.current_playlist)
            self.update_status_bar()
            self._metadata_preload_timer.start(1000)
        
        self._is_loading = False
        
        if self._pending_refresh:
            self._pending_refresh = False
            QTimer.singleShot(100, self.force_load_playlist)

    def refresh_list(self, playlist):
        """Optimized list refresh"""
        if self._is_loading:
            self._pending_refresh = True
            return
        
        self._is_loading = True
        self._do_refresh_list(playlist)
        self._is_loading = False
        self.update_status_bar()
        
        QTimer.singleShot(50, self.load_visible_metadata)
    
    def _do_refresh_list(self, playlist):
        """Internal: Actually populate the list - no locking check"""
        self.file_list.clear()
        
        if playlist:
            for filepath in playlist:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, filepath)
                # Tooltip uklonjen - nije potrebno prikazivati putanju fajla
                self.file_list.addItem(item)

    def update_status_bar(self):
        """Optimized status bar update with throttling"""
        current_time = time.time()
        if current_time - self._last_status_update < 0.5:
            return
        
        self._last_status_update = current_time
        
        if not self.playlist_manager:
            return
        
        current_playlist = self.playlist_selector.currentText().replace("♪ ", "")
        total_tracks = self.file_list.count()
        
        if hasattr(self.playlist_manager, 'get_formatted_total_duration'):
            total_duration_str = self.playlist_manager.get_formatted_total_duration(current_playlist)
        else:
            total_duration_str = "Calculating..."
        
        self.status_label.setText(f"{current_playlist} • {total_tracks} tracks • {total_duration_str}")

    def on_item_double_clicked(self, item):
        """Handle double-click on playlist item"""
        filepath = item.data(Qt.ItemDataRole.UserRole)
        if filepath:
            self.highlight_current_track(filepath)
            
            if self.playlist_manager:
                index = self.playlist_manager.find_file_index(filepath)
                if index >= 0:
                    self.playlist_manager.set_current_index(index)
                    self._metadata_preload_timer.stop()
                    self._metadata_preload_timer.start(500)
            
            self.play_requested.emit(filepath)

    def highlight_current_track(self, filepath=None):
        """Highlight the currently playing track - WITH DEBOUNCE"""
        import os
        
        # Normalize filepath for comparison
        if filepath:
            filepath = os.path.normpath(os.path.abspath(filepath))
        
        # Skip if same file already highlighted
        if filepath == self._current_highlighted_file:
            return
        
        # Ã¢Å“â€ Debounce: If called too quickly, schedule for later
        current_time = time.time()
        if current_time - self._last_highlight_time < 0.05:  # 50ms
            self._pending_highlight_file = filepath
            self._highlight_debounce_timer.stop()
            # Safely disconnect if connected
            try:
                if self._highlight_debounce_timer.receivers(self._highlight_debounce_timer.timeout) > 0:
                    self._highlight_debounce_timer.timeout.disconnect()
            except:
                pass
            self._highlight_debounce_timer.timeout.connect(lambda: self._do_highlight(self._pending_highlight_file))
            self._highlight_debounce_timer.start()
            return
        
        self._do_highlight(filepath)
    
    def _do_highlight(self, filepath):
        """Actually perform the highlight - internal method"""
        import os
        
        # Normalize again just in case
        if filepath:
            filepath = os.path.normpath(os.path.abspath(filepath))
        
        # Double-check we're not highlighting the same file
        if filepath == self._current_highlighted_file:
            return
        
        self._last_highlight_time = time.time()
        
        # Clear all highlights
        for row in range(self.file_list.count()):
            item = self.file_list.item(row)
            if item:
                item.setBackground(QBrush())
                item.setForeground(QBrush())
        
        # Update current highlighted file
        self._current_highlighted_file = filepath
        
        # Find and highlight current track
        if filepath:
            for row in range(self.file_list.count()):
                item = self.file_list.item(row)
                if item:
                    item_path = item.data(Qt.ItemDataRole.UserRole)
                    if item_path:
                        # Normalize item path for comparison
                        item_path_normalized = os.path.normpath(os.path.abspath(item_path))
                        if item_path_normalized == filepath:
                            # Apply highlight color
                            highlight_color = QColor(74, 110, 224, 80)
                            item.setBackground(QBrush(highlight_color))
                            item.setForeground(QBrush(QColor(255, 255, 255)))
                            
                            # NO SCROLL - user controls scroll position!
                            # NO setCurrentRow - don't change selection!
                            
                            # Update status
                            track_name = Path(filepath).stem
                            if hasattr(self, 'delegate'):
                                display_name = self.delegate.get_display_name_cached(filepath)
                                if display_name:
                                    track_name = display_name
                            
                            self.status_label.setText(f"▶ Playing: {track_name}")
                            QTimer.singleShot(3000, self.update_status_bar)
                            break
    
    def on_current_index_changed(self, index):
        """Handle current index change from playlist manager"""
        if index >= 0 and hasattr(self.playlist_manager, 'current_playlist'):
            if index < len(self.playlist_manager.current_playlist):
                filepath = self.playlist_manager.current_playlist[index]
                self.highlight_current_track(filepath)

    def on_tags_updated(self, filepath, metadata):
        """Handle tag updates with cache invalidation"""
        try:
            self.delegate.clear_cache_for_file(filepath)
            self.file_list.viewport().update()
            
            track_name = Path(filepath).stem
            if 'title' in metadata and metadata['title']:
                track_name = metadata['title']
            
            self.show_status_message(f"Ã¢Å“â€ Tags saved: {track_name}", 3000)
            
            if hasattr(self.app, 'engine'):
                if self.app.engine.current_file == filepath:
                    if hasattr(self.app.engine, 'metadata_updated'):
                        self.app.engine.metadata_updated.emit(filepath, metadata)
        except Exception as e:
            print(f"X Error in on_tags_updated: {e}")

    # Delegate methods to managers
    def dragEnterEvent(self, event: QDragEnterEvent):
        self.operations_manager.dragEnterEvent(event)
    
    def dragLeaveEvent(self, event):
        self.operations_manager.dragLeaveEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        self.operations_manager.dropEvent(event)
    
    def add_files(self):
        self.operations_manager.add_files()
    
    def add_folder(self):
        self.operations_manager.add_folder()
    
    def add_url(self):
        self.operations_manager.add_url()
    
    def clear_playlist(self):
        self.operations_manager.clear_playlist()
    
    def remove_selected(self):
        self.operations_manager.remove_selected()
    
    def play_selected(self):
        """Play the currently selected item (called from keyboard handler - Enter key)"""
        items = self.file_list.selectedItems()
        if items:
            # Play first selected item
            item = items[0]
            filepath = item.data(Qt.ItemDataRole.UserRole)
            if filepath:
                self.highlight_current_track(filepath)
                
                if self.playlist_manager:
                    index = self.playlist_manager.find_file_index(filepath)
                    if index >= 0:
                        self.playlist_manager.set_current_index(index)
                        self._metadata_preload_timer.stop()
                        self._metadata_preload_timer.start(500)
                
                self.play_requested.emit(filepath)
    
    def show_context_menu(self, pos):
        self.context_menu_manager.show_context_menu(pos)
    
    def edit_tags(self):
        self.context_menu_manager.edit_tags()
    
    def show_in_folder(self):
        self.context_menu_manager.show_in_folder()
    
    def show_file_info(self):
        self.context_menu_manager.show_file_info()

    # Playlist management
    def load_playlists(self):
        self.playlist_selector.clear()
        
        if self.playlist_manager and hasattr(self.playlist_manager, 'get_playlist_names'):
            playlists = self.playlist_manager.get_playlist_names()
            for playlist in playlists:
                self.playlist_selector.addItem(f"♪ {playlist}")
        else:
            self.playlist_selector.addItem("♪ Default Playlist")
        
        if self.playlist_manager and hasattr(self.playlist_manager, 'get_current_playlist_name'):
            current = self.playlist_manager.get_current_playlist_name()
            index = self.playlist_selector.findText(f"♪ {current}")
            if index >= 0:
                self.playlist_selector.setCurrentIndex(index)

    def on_playlist_selected(self, playlist_name):
        if not playlist_name:
            return
            
        clean_name = playlist_name.replace("♪ ", "")
        
        if self.playlist_manager and hasattr(self.playlist_manager, 'switch_to_playlist'):
            success = self.playlist_manager.switch_to_playlist(clean_name)
            
            if success:
                self.playlist_changed.emit(clean_name)
                self.delete_playlist_btn.setEnabled(clean_name != "Default Playlist")

    def create_new_playlist(self):
        playlist_name, ok = QInputDialog.getText(
            self, "New Playlist", "Enter playlist name:", text="My Playlist"
        )
        
        if ok and playlist_name:
            existing_playlists = []
            if self.playlist_manager and hasattr(self.playlist_manager, 'get_playlist_names'):
                existing_playlists = self.playlist_manager.get_playlist_names()
            
            if playlist_name in existing_playlists:
                QMessageBox.warning(self, "Duplicate Name", 
                    f"A playlist named '{playlist_name}' already exists.")
                return
            
            if self.playlist_manager and hasattr(self.playlist_manager, 'create_playlist'):
                success = self.playlist_manager.create_playlist(playlist_name)
                if success:
                    self.playlist_selector.addItem(f"♪ {playlist_name}")
                    index = self.playlist_selector.findText(f"♪ {playlist_name}")
                    if index >= 0:
                        self.playlist_selector.setCurrentIndex(index)
                    self.show_status_message(f"Created playlist: {playlist_name}")

    def delete_current_playlist(self):
        current_playlist = self.playlist_selector.currentText().replace("♪ ", "")
        
        if current_playlist == "Default Playlist":
            QMessageBox.warning(self, "Cannot Delete", 
                "The Default Playlist cannot be deleted.")
            return
        
        reply = QMessageBox.question(
            self, "Delete Playlist",
            f"Are you sure you want to delete the playlist '{current_playlist}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.playlist_manager and hasattr(self.playlist_manager, 'delete_playlist'):
                success = self.playlist_manager.delete_playlist(current_playlist)
                if success:
                    index = self.playlist_selector.currentIndex()
                    self.playlist_selector.removeItem(index)
                    if self.playlist_selector.count() > 0:
                        self.playlist_selector.setCurrentIndex(0)
                    self.show_status_message(f"Deleted playlist: {current_playlist}")

    def on_external_playlist_changed(self, playlist_name):
        """
        Handle external playlist changes (from PlaylistManager signals).
        This is called when tracks are added/removed or playlist content changes.
        """
        index = self.playlist_selector.findText(f"♪ {playlist_name}")
        if index >= 0:
            self.playlist_selector.setCurrentIndex(index)
            self.delete_playlist_btn.setEnabled(playlist_name != "Default Playlist")
        
        # KRITIÃ„Å’NO: OsveÃ…Â¾i listu da prikaÃ…Â¾e promene (npr. obrisane pesme)
        self.load_current_playlist()

    def on_current_playlist_changed(self):
        self.load_current_playlist()

    def on_playlists_updated(self, playlists):
        self.load_playlists()

    def on_duration_loaded(self, filepath, duration):
        for row in range(self.file_list.count()):
            item = self.file_list.item(row)
            if item and item.data(Qt.ItemDataRole.UserRole) == filepath:
                self.file_list.viewport().update(self.file_list.visualItemRect(item))
                break

    def load_current_playlist(self):
        if self.playlist_manager and hasattr(self.playlist_manager, 'current_playlist'):
            self.refresh_list(self.playlist_manager.current_playlist)

    def show_status_message(self, message, duration=3000):
        """Show temporary status message"""
        self.status_label.setText(message)
        if duration > 0:
            QTimer.singleShot(duration, self.update_status_bar)
    
    def get_current_highlighted_file(self):
        """Get the currently highlighted file"""
        return self._current_highlighted_file
    def apply_theme(self, theme_name: str = None):
        """
        AÃƒâ€¦Ã‚Â¾urira ikone prema trenutnoj temi.
        Poziva se kada se tema promeni.
        """
        # Detektuj boju iz teme
        try:
            from core.themes.theme_registry import ThemeRegistry
            if theme_name:
                theme = ThemeRegistry.get_theme(theme_name)
                if theme and hasattr(theme, 'primary'):
                    self.current_theme_color = theme.primary
                if theme and hasattr(theme, 'bg_main'):
                    from PyQt6.QtGui import QColor
                    self.is_dark_theme = QColor(theme.bg_main).lightness() < 128
        except:
            pass
        
        # AÃƒâ€¦Ã‚Â¾uriraj sve ikone
        self._update_button_icons()
    
    def _update_button_icons(self):
        """AÃƒâ€¦Ã‚Â¾urira ikone na svim dugmadima."""
        if not SVG_ICONS_AVAILABLE:
            return
        
        # New playlist button
        icon = self._get_icon('add', 20)
        if icon and hasattr(self, 'new_playlist_btn'):
            self.new_playlist_btn.setIcon(icon)
        
        # Delete playlist button
        icon = self._get_icon('delete', 20)
        if icon and hasattr(self, 'delete_playlist_btn'):
            self.delete_playlist_btn.setIcon(icon)
        
        # Settings button
        icon = self._get_icon('settings', 20)
        if icon and hasattr(self, 'settings_btn'):
            self.settings_btn.setIcon(icon)
        
        # Add music button
        icon = self._get_icon('add', 18)
        if icon and hasattr(self, 'add_btn'):
            self.add_btn.setIcon(icon)
        
        # Clear playlist button
        icon = self._get_icon('delete', 18)
        if icon and hasattr(self, 'clear_btn'):
            self.clear_btn.setIcon(icon)