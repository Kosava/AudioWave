# -*- coding: utf-8 -*-
# core/theme_manager.py

"""
Centralized Theme Manager with Config Integration
✅ Loads saved theme on startup
✅ Saves theme when changed
✅ Clean & Modular
"""

import json
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from .themes.theme_registry import ThemeRegistry
from .themes.base_theme import BaseTheme


class ThemeManager(QObject):
    """Manages application themes with persistence"""
    
    theme_changed = pyqtSignal(str)
    theme_applied = pyqtSignal(str, bool)
    
    def __init__(self, config=None):
        """
        Initialize ThemeManager.
        
        Args:
            config: Config instance (optional, for theme persistence)
        """
        super().__init__()
        self.config = config
        self.registry = ThemeRegistry
        
        # Load saved theme from config (or use default)
        if self.config:
            self.current_theme = self.config.get_theme()
            print(f"🎨 Loading saved theme: {self.current_theme}")
        else:
            self.current_theme = "Dark Modern"
            print(f"⚠️ No config provided, using default theme")
        
        # Load custom themes from JSON if exists
        self._load_custom_themes()
        
        available_count = len(self.registry.get_theme_names())
        print(f"🎨 ThemeManager initialized with {available_count} themes")
        print(f"📋 Available themes: {', '.join(self.registry.get_theme_names())}")
    
    def _load_custom_themes(self):
        """Load custom themes from JSON file"""
        try:
            themes_file = Path(__file__).parent.parent / "ui" / "themes" / "themes.json"
            if themes_file.exists():
                with open(themes_file, 'r', encoding='utf-8') as f:
                    custom_themes = json.load(f)
                    # TODO: Implement custom theme loading from JSON
                    # For now, we only use Python-defined themes
                    print(f"ℹ️  Custom themes file found (not yet implemented)")
        except Exception as e:
            print(f"⚠️  Could not load custom themes: {e}")
    
    def get_available_themes(self) -> list:
        """Return list of available themes"""
        return self.registry.get_theme_names()
    
    def is_dark_theme(self, theme_name: str = None) -> bool:
        """Check if theme is dark"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.registry.is_dark_theme(theme_name)
    
    def apply_theme(self, widget, theme_name: str, save_to_config: bool = True) -> bool:
        """
        Apply theme to a widget.
        
        Args:
            widget: Widget to apply theme to
            theme_name: Name of theme to apply
            save_to_config: Save theme selection to config (default: True)
        
        Returns:
            bool: True if successful
        """
        try:
            theme = self.registry.get_theme(theme_name)
            theme_data = theme.get_theme_data()
            
            print(f"🎨 [ThemeManager] Applying '{theme_name}' to {widget.__class__.__name__}")
            
            # Apply to QApplication (global)
            app = QApplication.instance()
            if app:
                app_font = QFont(theme_data["font_family"], theme_data["font_size"])
                app.setFont(app_font)
                app.setStyleSheet(theme_data["stylesheet"])
            
            # Apply to widget (local)
            widget.setStyleSheet(theme_data["stylesheet"])
            
            # Update current theme
            self.current_theme = theme_name
            
            # ✅ SAVE TO CONFIG
            if save_to_config and self.config:
                self.config.set_theme(theme_name)
                print(f"💾 Theme '{theme_name}' saved to config")
            
            # Emit signals
            self.theme_changed.emit(theme_name)
            self.theme_applied.emit(theme_name, True)
            
            # Force UI refresh
            widget.repaint()
            QApplication.processEvents()
            
            print(f"✅ Theme '{theme_name}' applied successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error applying theme '{theme_name}': {e}")
            import traceback
            traceback.print_exc()
            self.theme_applied.emit(theme_name, False)
            return False
    
    def apply_to_all_windows(self, main_window, theme_name: str, save_to_config: bool = True) -> bool:
        """Apply theme to all windows"""
        return self.apply_theme(main_window, theme_name, save_to_config)
    
    def get_current_theme(self) -> str:
        """Get currently applied theme name"""
        return self.current_theme
    
    def reload_themes(self):
        """Reload all themes (useful for development)"""
        print("🔄 Reloading themes...")
        self._load_custom_themes()
        print(f"✅ Themes reloaded: {len(self.registry.get_theme_names())} available")
    
    def load_saved_theme(self, widget) -> bool:
        """
        Load and apply saved theme from config.
        
        Args:
            widget: Widget to apply theme to
            
        Returns:
            bool: True if successful
        """
        if not self.config:
            print("⚠️ No config available, cannot load saved theme")
            return False
        
        saved_theme = self.config.get_theme()
        print(f"📖 Loading saved theme: {saved_theme}")
        
        # Apply without saving again (avoid redundant save)
        return self.apply_theme(widget, saved_theme, save_to_config=False)


# ============================================================
# USAGE EXAMPLE:
# ============================================================
"""
from core.config import Config
from core.theme_manager import ThemeManager

# Initialize with config
config = Config()
theme_mgr = ThemeManager(config)

# Load saved theme on startup
theme_mgr.load_saved_theme(main_window)

# User changes theme
theme_mgr.apply_theme(main_window, "Nordic Light")  # Automatically saved!

# Next startup
config2 = Config()
theme_mgr2 = ThemeManager(config2)
# theme_mgr2.current_theme will be "Nordic Light"
"""
