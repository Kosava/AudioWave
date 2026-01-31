# -*- coding: utf-8 -*-
"""
Configuration Manager with Persistence
core/config.py

FEATURES:
✅ Load/Save configuration to JSON file
✅ Theme persistence (remembers last selected theme)
✅ Window geometry persistence
✅ Volume and playback state persistence
✅ Tray settings persistence
✅ Auto-save on changes
✅ Resume playback position persistence
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


class Config:
    """Configuration manager with file persistence"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Config filename (default: config.json)
        """
        # Config directory: ~/.config/audiowave/
        self.config_dir = Path.home() / ".config" / "audiowave"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / config_file
        
        # Default configuration
        self.defaults = {
            "version": "0.3.5",
            
            # ✅ Theme settings - PERSISTENT
            "theme": "Dark Modern",  # Default theme
            
            # Volume settings
            "volume": 70,
            "muted": False,
            
            # Library settings
            "library_path": str(Path.home() / "Music"),
            
            # Window settings
            "show_on_startup": True,
            "window_geometry": None,  # {"x": int, "y": int, "width": int, "height": int}
            "window_maximized": False,
            "always_on_top": False,
            
            # Playback settings
            "last_file": None,
            "auto_play": True,
            
            # ✅ NOVO: Resume playback settings
            "resume_playback": {
                "enabled": False,           # Da li je opcija uključena
                "last_track_path": None,    # Putanja do poslednje pesme
                "last_position_ms": 0,      # Pozicija u milisekundama
                "last_playlist_index": 0    # Index u playlisti
            },
            
            # Tray settings - ✅ AŽURIRANO: minimize_to_tray je sada checkbox opcija
            "tray": {
                "enabled": True,
                "close_to_tray": True,      # ✅ Ovo je sada kontrolisano iz Settings
                "minimize_to_tray": True,   # ✅ NOVO: Minimize on X click
                "notifications": True,
                "icon_theme": "auto"        # auto | light | dark
            },
            
            # Player style
            "player_style": "Modern",  # Modern | Classic | Minimal | Compact
        }
        
        # Load config from file (or use defaults)
        self.config = self.load()
        
        print(f"📋 Config loaded from: {self.config_file}")
        print(f"🎨 Current theme: {self.config.get('theme', 'Dark Modern')}")
    
    def load(self) -> dict:
        """
        Load configuration from JSON file.
        
        Returns:
            dict: Configuration dictionary
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults (in case new keys were added)
                config = self.defaults.copy()
                
                # Deep merge za nested dictionaries
                for key, value in loaded_config.items():
                    if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                        # Merge nested dict
                        config[key] = {**config[key], **value}
                    else:
                        config[key] = value
                
                print(f"✅ Config loaded successfully")
                return config
                
            except Exception as e:
                print(f"⚠️ Error loading config: {e}")
                print(f"   Using default configuration")
                return self.defaults.copy()
        else:
            print(f"ℹ️ No config file found, using defaults")
            return self.defaults.copy()
    
    def save(self) -> bool:
        """
        Save configuration to JSON file.
        
        Returns:
            bool: True if saved successfully
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            print(f"💾 Config saved to: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            auto_save: Automatically save to file (default: True)
        """
        self.config[key] = value
        
        if auto_save:
            self.save()
    
    # ===== THEME METHODS =====
    
    def get_theme(self) -> str:
        """
        Get current theme name.
        
        Returns:
            str: Theme name
        """
        return self.config.get("theme", "Dark Modern")
    
    def set_theme(self, theme_name: str, auto_save: bool = True) -> None:
        """
        Set current theme and save.
        
        Args:
            theme_name: Theme name to set
            auto_save: Automatically save to file (default: True)
        """
        self.config["theme"] = theme_name
        print(f"🎨 Theme changed to: {theme_name}")
        
        if auto_save:
            self.save()
    
    # ===== TRAY METHODS =====
    
    def get_tray_settings(self) -> dict:
        """
        Get tray settings.
        
        Returns:
            dict: Tray settings
        """
        tray = self.config.get("tray")
        if not isinstance(tray, dict):
            tray = {
                "enabled": True,
                "close_to_tray": True,
                "minimize_to_tray": True,
                "notifications": True,
                "icon_theme": "auto"
            }
            self.config["tray"] = tray
        
        # Osiguraj da postoje svi ključevi (za stare config fajlove)
        if "minimize_to_tray" not in tray:
            tray["minimize_to_tray"] = True
        
        return tray
    
    def set_tray_settings(self, tray_settings: dict, auto_save: bool = True) -> None:
        """
        Set tray settings.
        
        Args:
            tray_settings: Tray settings dictionary
            auto_save: Automatically save to file (default: True)
        """
        self.config["tray"] = tray_settings
        
        if auto_save:
            self.save()
    
    # ===== RESUME PLAYBACK METHODS =====
    
    def get_resume_playback_settings(self) -> dict:
        """
        Get resume playback settings.
        
        Returns:
            dict: Resume playback settings
        """
        resume = self.config.get("resume_playback")
        if not isinstance(resume, dict):
            resume = {
                "enabled": False,
                "last_track_path": None,
                "last_position_ms": 0,
                "last_playlist_index": 0
            }
            self.config["resume_playback"] = resume
        print(f"🔍 [DEBUG] get_resume_playback_settings() = {resume}")
        return resume
    
    def set_resume_playback_settings(self, settings: dict, auto_save: bool = True) -> None:
        """
        Set resume playback settings.
        
        Args:
            settings: Resume playback settings dictionary
            auto_save: Automatically save to file (default: True)
        """
        self.config["resume_playback"] = settings
        
        if auto_save:
            self.save()
    
    def is_resume_playback_enabled(self) -> bool:
        """Check if resume playback is enabled"""
        resume = self.get_resume_playback_settings()
        enabled = resume.get("enabled", False)
        print(f"🔍 [DEBUG] is_resume_playback_enabled() = {enabled}")
        print(f"🔍 [DEBUG] resume_playback config: {resume}")
        return enabled
    
    def set_resume_playback_enabled(self, enabled: bool, auto_save: bool = True) -> None:
        """Set resume playback enabled state"""
        print(f"🔧 [DEBUG] set_resume_playback_enabled({enabled}, auto_save={auto_save})")
        resume = self.get_resume_playback_settings()
        resume["enabled"] = enabled
        self.config["resume_playback"] = resume
        print(f"🔧 [DEBUG] resume_playback after set: {self.config['resume_playback']}")
        
        if auto_save:
            self.save()
            print(f"🔧 [DEBUG] Config saved after set_resume_playback_enabled")
    
    def save_playback_position(self, track_path: str, position_ms: int, 
                                playlist_index: int = 0, auto_save: bool = True) -> None:
        """
        Sačuvaj trenutnu poziciju pesme za resume.
        
        Args:
            track_path: Putanja do pesme
            position_ms: Pozicija u milisekundama
            playlist_index: Index u playlisti
            auto_save: Automatski sačuvaj
        """
        resume = self.get_resume_playback_settings()
        resume["last_track_path"] = track_path
        resume["last_position_ms"] = position_ms
        resume["last_playlist_index"] = playlist_index
        self.config["resume_playback"] = resume
        
        if auto_save:
            self.save()
        
        print(f"💾 Saved playback position: {position_ms}ms for {track_path}")
    
    def get_saved_playback_position(self) -> tuple:
        """
        Vrati sačuvanu poziciju za resume.
        
        Returns:
            tuple: (track_path, position_ms, playlist_index)
        """
        resume = self.get_resume_playback_settings()
        return (
            resume.get("last_track_path"),
            resume.get("last_position_ms", 0),
            resume.get("last_playlist_index", 0)
        )
    
    def clear_playback_position(self, auto_save: bool = True) -> None:
        """Obriši sačuvanu poziciju"""
        resume = self.get_resume_playback_settings()
        resume["last_track_path"] = None
        resume["last_position_ms"] = 0
        resume["last_playlist_index"] = 0
        self.config["resume_playback"] = resume
        
        if auto_save:
            self.save()
    
    # ===== WINDOW GEOMETRY METHODS =====
    
    def get_window_geometry(self) -> Optional[dict]:
        """
        Get saved window geometry.
        
        Returns:
            dict or None: Window geometry {x, y, width, height}
        """
        return self.config.get("window_geometry")
    
    def set_window_geometry(self, geometry: dict, auto_save: bool = True) -> None:
        """
        Set window geometry.
        
        Args:
            geometry: Dictionary with x, y, width, height
            auto_save: Automatically save to file (default: True)
        """
        self.config["window_geometry"] = geometry
        
        if auto_save:
            self.save()
    
    def is_window_maximized(self) -> bool:
        """Check if window was maximized"""
        return self.config.get("window_maximized", False)
    
    def set_window_maximized(self, maximized: bool, auto_save: bool = True) -> None:
        """Set window maximized state"""
        self.config["window_maximized"] = maximized
        
        if auto_save:
            self.save()
    
    # ===== ALWAYS ON TOP =====
    
    def is_always_on_top(self) -> bool:
        """Check if always on top is enabled"""
        return self.config.get("always_on_top", False)
    
    def set_always_on_top(self, enabled: bool, auto_save: bool = True) -> None:
        """Set always on top state"""
        self.config["always_on_top"] = enabled
        
        if auto_save:
            self.save()
    
    # ===== VOLUME METHODS =====
    
    def get_volume(self) -> int:
        """Get saved volume (0-100)"""
        return self.config.get("volume", 70)
    
    def set_volume(self, volume: int, auto_save: bool = True) -> None:
        """Set volume (0-100)"""
        self.config["volume"] = max(0, min(100, volume))
        
        if auto_save:
            self.save()
    
    # ===== PLAYER STYLE =====
    
    def get_player_style(self) -> str:
        """Get player style"""
        return self.config.get("player_style", "Modern")
    
    def set_player_style(self, style: str, auto_save: bool = True) -> None:
        """Set player style"""
        self.config["player_style"] = style
        
        if auto_save:
            self.save()
    
    # ===== UTILITY METHODS =====
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = self.defaults.copy()
        self.save()
        print("🔄 Configuration reset to defaults")
    
    def get_config_path(self) -> Path:
        """Get config file path"""
        return self.config_file
    
    def export_config(self, export_path: Path) -> bool:
        """Export config to a different location"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"📤 Config exported to: {export_path}")
            return True
        except Exception as e:
            print(f"❌ Error exporting config: {e}")
            return False
    
    def import_config(self, import_path: Path) -> bool:
        """Import config from a different location"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge with defaults
            self.config = self.defaults.copy()
            self.config.update(imported_config)
            
            self.save()
            print(f"📥 Config imported from: {import_path}")
            return True
        except Exception as e:
            print(f"❌ Error importing config: {e}")
            return False


# ===== USAGE EXAMPLE =====
if __name__ == "__main__":
    # Initialize config
    config = Config()
    
    # Get theme
    current_theme = config.get_theme()
    print(f"Current theme: {current_theme}")
    
    # Test resume playback
    print(f"\nResume playback enabled: {config.is_resume_playback_enabled()}")
    
    # Test tray settings
    tray = config.get_tray_settings()
    print(f"Minimize to tray: {tray.get('minimize_to_tray', True)}")
    
    # Change theme
    config.set_theme("Nordic Light")
    
    # Get theme again
    print(f"New theme: {config.get_theme()}")
    
    # Check if saved
    config2 = Config()
    print(f"Theme after reload: {config2.get_theme()}")  # Should be "Nordic Light"