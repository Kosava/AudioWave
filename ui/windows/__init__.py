# ui/windows/__init__.py
"""
Windows module - UPDATED
PlaylistPanel has been moved to ui.panels
"""

print("📁 Loading windows module...")
print("⚠️ PlaylistPanel is now in ui.panels.playlist_panel")

# PlayerWindow removed - using UnifiedPlayerWindow instead
# PlaylistPanel is now in ui.panels, NOT here!
# Do NOT import PlaylistPanel from here

from .unified_player_window import UnifiedPlayerWindow
from .settings_dialog import SettingsDialog

print("✅ Windows module loaded - UnifiedPlayerWindow and SettingsDialog only")