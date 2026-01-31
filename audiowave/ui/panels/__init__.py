# ui/panels/__init__.py
"""
Playlist panels module - refactored into logical components
"""

from .playlist_panel import PlaylistPanel
from .playlist_delegate import WinampPlaylistItemDelegate
from .playlist_cache import PlaylistCacheManager
from .playlist_search import PlaylistSearchManager
from .playlist_operations import PlaylistOperationsManager
from .playlist_context_menu import PlaylistContextMenuManager

__all__ = [
    'PlaylistPanel',
    'WinampPlaylistItemDelegate',
    'PlaylistCacheManager',
    'PlaylistSearchManager',
    'PlaylistOperationsManager',
    'PlaylistContextMenuManager'
]