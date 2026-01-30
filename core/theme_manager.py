# -*- coding: utf-8 -*-
# core/theme_manager.py

"""
Centralized Theme Manager with Config Integration
✅ Loads saved theme on startup
✅ Saves theme when changed
✅ Clean & Modular
✅ Custom theme support from JSON
✅ Robust error handling (prevents segfaults)
✅ Emergency fallback themes
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QColor, QPalette

from .themes.theme_registry import ThemeRegistry, register_custom_theme_from_json
from .themes.base_theme import BaseTheme, StyleComponents


class ThemeManager(QObject):
    """Manages application themes with persistence and robust error handling"""
    
    theme_changed = pyqtSignal(str)
    theme_applied = pyqtSignal(str, bool)
    themes_reloaded = pyqtSignal()  # Emituje kada se teme ponovo učitaju
    
    def __init__(self, config=None):
        """
        Initialize ThemeManager with robust error handling.
        
        Args:
            config: Config instance (optional, for theme persistence)
        """
        super().__init__()
        self.config = config
        self.registry = ThemeRegistry
        
        # Emergency fallback flag
        self.emergency_mode = False
        
        # Učitaj saved theme iz config-a (sa error handling)
        self._load_initial_theme()
        
        # Load custom themes from JSON
        self._load_custom_themes()
        
        # Register emergency themes
        self._register_emergency_themes()
        
        # Log stats
        self._log_theme_stats()
    
    def _load_initial_theme(self):
        """Load initial theme with error handling"""
        try:
            if self.config:
                saved_theme = self.config.get_theme()
                
                # Validacija teme
                if not saved_theme or saved_theme.strip() == "":
                    print(f"⚠️  Empty theme in config, using Dark Modern")
                    self.current_theme = "Dark Modern"
                elif not self.registry.theme_exists(saved_theme):
                    print(f"⚠️  Saved theme '{saved_theme}' not found, using Dark Modern")
                    self.current_theme = "Dark Modern"
                else:
                    self.current_theme = saved_theme
                    print(f"🎨 Loading saved theme: {self.current_theme}")
            else:
                self.current_theme = "Dark Modern"
                print(f"⚠️ No config provided, using default theme: {self.current_theme}")
                
        except Exception as e:
            print(f"❌ Error loading initial theme: {e}")
            self.current_theme = "Dark Modern"
            self.emergency_mode = True
    
    def _load_custom_themes(self):
        """Load custom themes from JSON files - with error handling"""
        try:
            # Kreiraj direktorijum za custom teme
            custom_themes_dir = Path.home() / ".audiowave" / "themes"
            custom_themes_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Looking for custom themes in: {custom_themes_dir}")
            
            # Učitaj custom teme iz JSON fajlova
            json_files = list(custom_themes_dir.glob("*.json"))
            print(f"📄 Found {len(json_files)} custom theme files")
            
            loaded_count = 0
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                    
                    theme_name = theme_data.get("name", json_file.stem)
                    
                    # Proveri validnost JSON-a
                    if not self._validate_theme_json(theme_data):
                        print(f"⚠️  Invalid theme JSON in {json_file.name}")
                        continue
                    
                    print(f"🎨 Loading custom theme: {theme_name}")
                    
                    # Kreiraj dinamičku temu
                    if self._create_dynamic_theme(theme_data):
                        loaded_count += 1
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  Invalid JSON in {json_file}: {e}")
                except Exception as e:
                    print(f"⚠️  Could not load custom theme {json_file}: {e}")
            
            if loaded_count > 0:
                print(f"✅ Loaded {loaded_count} custom themes")
            elif json_files:
                print(f"⚠️  Found {len(json_files)} theme files but couldn't load any")
            else:
                print(f"ℹ️  No custom themes found. Use Theme Creator to create some!")
                
        except Exception as e:
            print(f"⚠️  Could not load custom themes: {e}")
            import traceback
            traceback.print_exc()
    
    def _validate_theme_json(self, theme_data: Dict) -> bool:
        """Validate theme JSON data"""
        try:
            required_fields = ["name", "type", "primary", "secondary", "bg_main"]
            
            for field in required_fields:
                if field not in theme_data:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Proveri tip
            theme_type = theme_data.get("type", "").lower()
            if theme_type not in ["dark", "light"]:
                print(f"❌ Invalid theme type: {theme_type}. Must be 'dark' or 'light'")
                return False
            
            # Proveri boje
            color_fields = ["primary", "secondary", "bg_main", "bg_secondary", "text_color"]
            for field in color_fields:
                if field in theme_data:
                    color = theme_data[field]
                    if not isinstance(color, str) or not color.startswith("#"):
                        print(f"❌ Invalid color format for {field}: {color}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ Theme validation error: {e}")
            return False
    
    def _create_dynamic_theme(self, theme_data: Dict) -> bool:
        """
        Create a dynamic theme class from JSON data.
        
        Args:
            theme_data: Dictionary with theme configuration
            
        Returns:
            bool: True if successful
        """
        try:
            theme_name = theme_data.get("name", "Custom Theme")
            
            # Proveri da li tema već postoji
            if theme_name in self.registry.get_theme_names():
                print(f"ℹ️  Theme '{theme_name}' already exists, skipping...")
                return False
            
            # Koristi utility funkciju iz theme_registry
            success = register_custom_theme_from_json(theme_data)
            
            if success:
                print(f"✨ Successfully registered custom theme: {theme_name}")
                return True
            else:
                print(f"❌ Failed to register custom theme: {theme_name}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create dynamic theme: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _register_emergency_themes(self):
        """Register emergency fallback themes"""
        try:
            # Kreiraj dinamičke emergency teme
            emergency_theme_class = self._create_emergency_theme_class()
            safe_theme_class = self._create_safe_theme_class()
            
            # Registruj emergency teme samo ako ne postoje
            if not self.registry.theme_exists("Emergency Fallback"):
                self.registry.register_dynamic_theme(emergency_theme_class)
                print(f"🆘 Registered emergency fallback theme")
            
            if not self.registry.theme_exists("Safe Mode"):
                self.registry.register_dynamic_theme(safe_theme_class)
                print(f"🛡️  Registered safe mode theme")
                
        except Exception as e:
            print(f"⚠️  Could not register emergency themes: {e}")
    
    def _create_emergency_theme_class(self):
        """Kreiraj emergency theme class dinamički"""
        class EmergencyFallbackTheme(BaseTheme):
            """Ultra-simple emergency fallback theme"""
            
            def __init__(self):
                super().__init__()
                self.name = "Emergency Fallback"
                self.is_dark = False
                
                # Ultra-simplified colors
                self.primary = "#cccccc"
                self.secondary = "#999999"
                self.bg_main = "#ffffff"
                self.bg_secondary = "#f0f0f0"
                self.text_color = "#000000"
                
                # Minimal fonts
                self.font_family = "Arial"
                self.font_size = 12
                
            def get_theme_data(self) -> dict:
                """Get theme data dictionary"""
                return {
                    "name": self.name,
                    "type": "light",
                    "primary": self.primary,
                    "secondary": self.secondary,
                    "bg_main": self.bg_main,
                    "bg_secondary": self.bg_secondary,
                    "text_color": self.text_color,
                    "font_family": self.font_family,
                    "font_size": self.font_size,
                    "stylesheet": self._generate_stylesheet()
                }
            
            def _generate_stylesheet(self) -> str:
                """Generate ultra-simple stylesheet that should NEVER fail"""
                return """
                    /* Emergency Fallback Theme - Ultra Simple */
                    * {
                        background-color: #ffffff;
                        color: #000000;
                        font-family: Arial;
                        font-size: 12px;
                        border: none;
                        margin: 0;
                        padding: 0;
                    }
                    
                    QMainWindow {
                        background-color: #ffffff;
                    }
                    
                    QWidget {
                        background-color: #ffffff;
                    }
                    
                    QPushButton {
                        background-color: #cccccc;
                        border: 1px solid #999999;
                        border-radius: 3px;
                        padding: 5px 10px;
                        color: #000000;
                    }
                    
                    QPushButton:hover {
                        background-color: #bbbbbb;
                    }
                    
                    QPushButton:pressed {
                        background-color: #aaaaaa;
                    }
                    
                    QLabel {
                        color: #000000;
                        background-color: transparent;
                    }
                    
                    QLineEdit, QTextEdit, QPlainTextEdit {
                        background-color: #f8f8f8;
                        border: 1px solid #cccccc;
                        border-radius: 3px;
                        padding: 5px;
                        color: #000000;
                    }
                    
                    QListWidget, QTreeWidget, QTableWidget {
                        background-color: #f8f8f8;
                        border: 1px solid #cccccc;
                        border-radius: 3px;
                        color: #000000;
                        alternate-background-color: #eeeeee;
                    }
                    
                    QScrollBar {
                        background-color: #f0f0f0;
                        border: 1px solid #cccccc;
                        width: 12px;
                    }
                    
                    QScrollBar::handle {
                        background-color: #cccccc;
                        border-radius: 5px;
                    }
                    
                    QScrollBar::handle:hover {
                        background-color: #bbbbbb;
                    }
                    
                    QProgressBar {
                        border: 1px solid #cccccc;
                        border-radius: 3px;
                        text-align: center;
                    }
                    
                    QProgressBar::chunk {
                        background-color: #cccccc;
                        border-radius: 2px;
                    }
                    
                    QSlider::groove:horizontal {
                        border: 1px solid #999999;
                        height: 6px;
                        background: #f0f0f0;
                        border-radius: 3px;
                    }
                    
                    QSlider::handle:horizontal {
                        background: #cccccc;
                        border: 1px solid #999999;
                        width: 16px;
                        height: 16px;
                        margin: -6px 0;
                        border-radius: 8px;
                    }
                """
        
        return EmergencyFallbackTheme
    
    def _create_safe_theme_class(self):
        """Kreiraj safe mode theme class dinamički"""
        class SafeModeTheme(BaseTheme):
            """Safe mode theme - slightly nicer than emergency but still simple"""
            
            def __init__(self):
                super().__init__()
                self.name = "Safe Mode"
                self.is_dark = True
                
                # Safe colors
                self.primary = "#2c3e50"
                self.secondary = "#34495e"
                self.bg_main = "#1a1a2e"
                self.bg_secondary = "#16213e"
                self.text_color = "#ecf0f1"
                
                # Safe fonts
                self.font_family = "Segoe UI, Arial, sans-serif"
                self.font_size = 12
                
            def get_theme_data(self) -> dict:
                """Get theme data dictionary"""
                return {
                    "name": self.name,
                    "type": "dark",
                    "primary": self.primary,
                    "secondary": self.secondary,
                    "bg_main": self.bg_main,
                    "bg_secondary": self.bg_secondary,
                    "text_color": self.text_color,
                    "font_family": self.font_family,
                    "font_size": self.font_size,
                    "stylesheet": self._generate_stylesheet()
                }
            
            def _generate_stylesheet(self) -> str:
                """Generate safe mode stylesheet"""
                return f"""
                    /* Safe Mode Theme - Stable & Reliable */
                    * {{
                        color: {self.text_color};
                        font-family: {self.font_family};
                        font-size: {self.font_size}px;
                        outline: none;
                    }}
                    
                    QMainWindow {{
                        background-color: {self.bg_main};
                    }}
                    
                    QWidget {{
                        background-color: {self.bg_main};
                    }}
                    
                    QPushButton {{
                        background-color: {self.primary};
                        border: 1px solid {self.secondary};
                        border-radius: 4px;
                        padding: 6px 12px;
                        color: {self.text_color};
                    }}
                    
                    QPushButton:hover {{
                        background-color: {self.secondary};
                    }}
                    
                    QPushButton:pressed {{
                        background-color: #1a252f;
                    }}
                    
                    QPushButton:disabled {{
                        background-color: #7f8c8d;
                        color: #95a5a6;
                    }}
                    
                    QLabel {{
                        color: {self.text_color};
                        background-color: transparent;
                    }}
                    
                    QLineEdit, QTextEdit, QPlainTextEdit {{
                        background-color: {self.bg_secondary};
                        border: 1px solid {self.secondary};
                        border-radius: 4px;
                        padding: 6px;
                        color: {self.text_color};
                        selection-background-color: {self.primary};
                        selection-color: white;
                    }}
                    
                    QListWidget, QTreeWidget, QTableWidget {{
                        background-color: {self.bg_secondary};
                        border: 1px solid {self.secondary};
                        border-radius: 4px;
                        color: {self.text_color};
                        alternate-background-color: #1e2a3e;
                    }}
                    
                    QListWidget::item:selected, 
                    QTreeWidget::item:selected,
                    QTableWidget::item:selected {{
                        background-color: {self.primary};
                        color: white;
                    }}
                    
                    QHeaderView::section {{
                        background-color: {self.primary};
                        color: {self.text_color};
                        padding: 5px;
                        border: none;
                    }}
                    
                    QScrollBar {{
                        background-color: {self.bg_secondary};
                        border: 1px solid {self.secondary};
                        width: 14px;
                    }}
                    
                    QScrollBar::handle {{
                        background-color: {self.secondary};
                        border-radius: 6px;
                        min-height: 20px;
                    }}
                    
                    QScrollBar::handle:hover {{
                        background-color: #3d4f66;
                    }}
                    
                    QScrollBar::add-line, QScrollBar::sub-line {{
                        background-color: {self.primary};
                        border: none;
                    }}
                    
                    QProgressBar {{
                        border: 1px solid {self.secondary};
                        border-radius: 4px;
                        text-align: center;
                        background-color: {self.bg_secondary};
                    }}
                    
                    QProgressBar::chunk {{
                        background-color: {self.primary};
                        border-radius: 3px;
                    }}
                    
                    QSlider::groove:horizontal {{
                        border: 1px solid {self.secondary};
                        height: 8px;
                        background: {self.bg_secondary};
                        border-radius: 4px;
                    }}
                    
                    QSlider::handle:horizontal {{
                        background: {self.primary};
                        border: 1px solid {self.secondary};
                        width: 18px;
                        height: 18px;
                        margin: -6px 0;
                        border-radius: 9px;
                    }}
                    
                    QSlider::groove:vertical {{
                        border: 1px solid {self.secondary};
                        width: 8px;
                        background: {self.bg_secondary};
                        border-radius: 4px;
                    }}
                    
                    QSlider::handle:vertical {{
                        background: {self.primary};
                        border: 1px solid {self.secondary};
                        width: 18px;
                        height: 18px;
                        margin: 0 -6px;
                        border-radius: 9px;
                    }}
                    
                    QTabWidget::pane {{
                        border: 1px solid {self.secondary};
                        background-color: {self.bg_main};
                    }}
                    
                    QTabBar::tab {{
                        background-color: {self.bg_secondary};
                        border: 1px solid {self.secondary};
                        padding: 8px 16px;
                        margin-right: 2px;
                    }}
                    
                    QTabBar::tab:selected {{
                        background-color: {self.primary};
                        color: white;
                    }}
                    
                    QTabBar::tab:hover {{
                        background-color: {self.secondary};
                    }}
                    
                    QMenu {{
                        background-color: {self.bg_secondary};
                        border: 1px solid {self.secondary};
                    }}
                    
                    QMenu::item {{
                        padding: 6px 24px 6px 12px;
                    }}
                    
                    QMenu::item:selected {{
                        background-color: {self.primary};
                    }}
                    
                    QMenu::separator {{
                        height: 1px;
                        background-color: {self.secondary};
                        margin: 4px 8px;
                    }}
                """
        
        return SafeModeTheme
    
    def _log_theme_stats(self):
        """Log theme statistics"""
        try:
            all_themes = self.registry.get_theme_names()
            builtin_count = len(self.registry.get_builtin_theme_names())
            dynamic_count = len(self.registry.get_dynamic_theme_names())
            dark_count = len([t for t in all_themes if self.registry.is_dark_theme(t)])
            light_count = len(all_themes) - dark_count
            
            print(f"\n🎨 Theme Manager Statistics:")
            print(f"   📦 Built-in themes: {builtin_count}")
            print(f"   ✨ Dynamic themes: {dynamic_count}")
            print(f"   🌌 Dark themes: {dark_count}")
            print(f"   🌞 Light themes: {light_count}")
            print(f"   🎯 Total: {len(all_themes)} themes")
            
            if dynamic_count > 0:
                dynamic_names = self.registry.get_dynamic_theme_names()
                print(f"   📋 Custom themes: {', '.join(dynamic_names)}")
                
        except Exception as e:
            print(f"⚠️  Could not log theme stats: {e}")
    
    def get_available_themes(self) -> list:
        """
        Return list of all available themes.
        
        Returns:
            list: Sorted list of theme names
        """
        try:
            return self.registry.get_theme_names()
        except Exception as e:
            print(f"⚠️  Error getting available themes: {e}")
            return ["Dark Modern", "Safe Mode"]
    
    def is_dark_theme(self, theme_name: str = None) -> bool:
        """
        Check if theme is dark.
        
        Args:
            theme_name: Theme name (uses current if None)
            
        Returns:
            bool: True if theme is dark
        """
        try:
            if theme_name is None:
                theme_name = self.current_theme
            
            if not theme_name:
                return True  # Default to dark
            
            return self.registry.is_dark_theme(theme_name)
            
        except Exception as e:
            print(f"⚠️  Error checking if theme is dark: {e}")
            return True  # Default to dark on error
    
    def apply_theme(self, widget, theme_name: str, save_to_config: bool = True) -> bool:
        """
        Apply theme to a widget with robust error handling.
        
        Args:
            widget: Widget to apply theme to
            theme_name: Name of theme to apply
            save_to_config: Save theme selection to config
            
        Returns:
            bool: True if successful
        """
        # Sačuvaj originalni theme_name za error reporting
        original_theme_name = theme_name
        
        try:
            # ✅ VALIDACIJA INPUT-A
            if not theme_name or not isinstance(theme_name, str) or theme_name.strip() == "":
                print(f"⚠️  Invalid theme name: '{theme_name}'")
                theme_name = "Dark Modern"
            
            # Proveri da li widget postoji
            if widget is None:
                print(f"❌ Cannot apply theme to None widget")
                return False
            
            # ✅ PROVERI DA LI TEMA POSTOJI
            if not self.registry.theme_exists(theme_name):
                print(f"❌ Theme '{theme_name}' not found in registry!")
                
                # Pokušaj da pronadžeš sličnu temu
                similar = self._find_similar_theme(theme_name)
                if similar and similar != theme_name:
                    print(f"   Using similar theme: {similar}")
                    theme_name = similar
                else:
                    print(f"   Falling back to 'Dark Modern'")
                    theme_name = "Dark Modern"
            
            # ✅ DOBÍJ TEMU SA ERROR HANDLING-OM
            try:
                theme = self.registry.get_theme(theme_name)
                theme_data = theme.get_theme_data()
            except Exception as theme_error:
                print(f"❌ Error getting theme data for '{theme_name}': {theme_error}")
                
                # Pokušaj sa Safe Mode
                if theme_name != "Safe Mode":
                    print(f"   Trying Safe Mode...")
                    return self.apply_theme(widget, "Safe Mode", save_to_config=False)
                else:
                    # Apsolutni fallback
                    return self._apply_emergency_theme(widget)
            
            print(f"🎨 [ThemeManager] Applying '{theme_name}' to {widget.__class__.__name__}")
            
            # ✅ PRIMENI TEMU NA QAPPLICATION
            app = QApplication.instance()
            if app:
                try:
                    app_font = QFont(theme_data["font_family"], theme_data["font_size"])
                    app.setFont(app_font)
                    app.setStyleSheet(theme_data["stylesheet"])
                except Exception as app_error:
                    print(f"⚠️  Error applying theme to QApplication: {app_error}")
            
            # ✅ PRIMENI TEMU NA WIDGET
            try:
                widget.setStyleSheet(theme_data["stylesheet"])
            except Exception as widget_error:
                print(f"❌ Error applying stylesheet to widget: {widget_error}")
                return False
            
            # ✅ AŽURIRAJ TRENUTNU TEMU
            old_theme = self.current_theme
            self.current_theme = theme_name
            
            # ✅ SAČUVAJ U CONFIG
            if save_to_config and self.config:
                try:
                    self.config.set_theme(theme_name)
                    print(f"💾 Theme '{theme_name}' saved to config")
                except Exception as config_error:
                    print(f"⚠️  Error saving theme to config: {config_error}")
            
            # ✅ EMITUJ SIGNALE
            self.theme_changed.emit(theme_name)
            self.theme_applied.emit(theme_name, True)
            
            # ✅ OSVEŽI UI
            try:
                widget.repaint()
                if app:
                    QApplication.processEvents()
            except Exception as refresh_error:
                print(f"⚠️  Error refreshing UI: {refresh_error}")
            
            # ✅ LOG SUCCESS
            if original_theme_name != theme_name:
                print(f"✅ Theme '{original_theme_name}' → '{theme_name}' applied successfully")
            else:
                print(f"✅ Theme '{theme_name}' applied successfully")
            
            # Reset emergency mode ako je uspešno
            if self.emergency_mode and theme_name != "Emergency Fallback":
                self.emergency_mode = False
                print(f"🔄 Exited emergency mode")
            
            return True
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR applying theme '{original_theme_name}': {e}")
            import traceback
            traceback.print_exc()
            
            # Pokušaj emergency fallback
            try:
                if not self.emergency_mode:
                    print(f"🆘 Entering emergency mode...")
                    self.emergency_mode = True
                    return self._apply_emergency_theme(widget)
            except Exception as emergency_error:
                print(f"💥 DOUBLE FAULT: Emergency theme also failed: {emergency_error}")
            
            self.theme_applied.emit(original_theme_name, False)
            return False
    
    def _apply_emergency_theme(self, widget) -> bool:
        """Apply emergency fallback theme"""
        try:
            print(f"🆘 Applying emergency fallback theme")
            
            # Veoma jednostavna tema koja nikad neće fail-ovati
            emergency_stylesheet = """
                * {
                    background-color: white;
                    color: black;
                    font-family: Arial;
                    font-size: 12px;
                    border: none;
                }
                QPushButton {
                    background-color: #cccccc;
                    border: 1px solid #999999;
                    border-radius: 3px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #bbbbbb;
                }
                QLabel {
                    color: #333333;
                }
            """
            
            app = QApplication.instance()
            if app:
                app.setStyleSheet(emergency_stylesheet)
                app.setFont(QFont("Arial", 12))
            
            if widget:
                widget.setStyleSheet(emergency_stylesheet)
                widget.repaint()
                if app:
                    QApplication.processEvents()
            
            self.current_theme = "Emergency Fallback"
            print(f"✅ Emergency theme applied")
            return True
            
        except Exception as e:
            print(f"💥 CRITICAL: Emergency theme failed: {e}")
            return False
    
    def _find_similar_theme(self, theme_name: str) -> Optional[str]:
        """
        Find a similar theme name using fuzzy matching.
        
        Args:
            theme_name: Theme name to find similar for
            
        Returns:
            Optional[str]: Similar theme name or None
        """
        try:
            available = self.registry.get_theme_names()
            if not available:
                return None
            
            theme_lower = theme_name.lower().strip()
            
            # 1. Exact match (case insensitive)
            for theme in available:
                if theme.lower() == theme_lower:
                    return theme
            
            # 2. Contains match
            for theme in available:
                theme_lower_available = theme.lower()
                if (theme_lower in theme_lower_available or 
                    theme_lower_available in theme_lower):
                    return theme
            
            # 3. Common typos/corrections
            corrections = {
                "darkmodern": "Dark Modern",
                "dark modern": "Dark Modern",
                "darkmodern theme": "Dark Modern",
                "nordic": "Nordic Light",
                "nordiclight": "Nordic Light",
                "cyber": "Cyberpunk",
                "cyberpunk theme": "Cyberpunk",
                "ocean theme": "Ocean",
                "forest theme": "Forest",
                "solarized": "Solarized Dark",
                "solarizeddark": "Solarized Dark",
                "retro": "Retro Wave",
                "retrowave": "Retro Wave",
                "lava": "Molten Lava",
                "molten": "Molten Lava",
                "neon": "Neon Pulse",
                "sunset": "Sunset Glow",
                "aurora": "Arctic Aurora",
                "champagne": "Champagne Sparkle",
                "modern": "Dark Modern",
                "light": "Nordic Light",
                "blue": "Electric Blue",
                "pink": "Hot Pink Blast",
                "green": "Mint Fresh",
                "purple": "Violet Storm",
                "orange": "Sunburst Orange",
            }
            
            for typo, correction in corrections.items():
                if typo in theme_lower and correction in available:
                    return correction
            
            # 4. First theme with matching first letter
            if theme_lower:
                first_char = theme_lower[0]
                for theme in available:
                    if theme.lower().startswith(first_char):
                        return theme
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error finding similar theme: {e}")
            return None
    
    def apply_to_all_windows(self, main_window, theme_name: str, save_to_config: bool = True) -> bool:
        """
        Apply theme to all windows.
        
        Args:
            main_window: Main window widget
            theme_name: Name of theme to apply
            save_to_config: Save theme selection to config
            
        Returns:
            bool: True if successful
        """
        return self.apply_theme(main_window, theme_name, save_to_config)
    
    def get_current_theme(self) -> str:
        """
        Get currently applied theme name.
        
        Returns:
            str: Current theme name
        """
        return self.current_theme
    
    def get_current_theme_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about current theme.
        
        Returns:
            Optional[Dict]: Theme information or None
        """
        try:
            return self.registry.get_theme_info(self.current_theme)
        except Exception as e:
            print(f"⚠️  Error getting current theme info: {e}")
            return None
    
    def reload_themes(self, widget=None) -> bool:
        """
        Reload all themes (useful for adding new custom themes).
        
        Args:
            widget: Optional widget to re-apply current theme to
            
        Returns:
            bool: True if successful
        """
        try:
            print("🔄 Reloading themes...")
            
            # Sačuvaj trenutnu temu
            current_theme = self.current_theme
            
            # Clear dynamic themes
            self.registry.clear_dynamic_themes()
            
            # Reload custom teme
            self._load_custom_themes()
            
            # Re-register emergency themes
            self._register_emergency_themes()
            
            # Pokušaj da vratiš trenutnu temu
            theme_still_exists = self.registry.theme_exists(current_theme)
            
            if theme_still_exists:
                print(f"✅ Themes reloaded. Current theme '{current_theme}' still available.")
                
                # Re-apply tema ako je widget prosleđen
                if widget:
                    QTimer.singleShot(100, lambda: self.apply_theme(
                        widget, current_theme, save_to_config=False
                    ))
            else:
                print(f"⚠️  Current theme '{current_theme}' no longer available.")
                self.current_theme = "Dark Modern"
                
                # Apply default temu ako je widget prosleđen
                if widget:
                    QTimer.singleShot(100, lambda: self.apply_theme(
                        widget, "Dark Modern", save_to_config=False
                    ))
            
            # Emit signal
            self.themes_reloaded.emit()
            
            # Log nova statistika
            self._log_theme_stats()
            
            return True
            
        except Exception as e:
            print(f"❌ Error reloading themes: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
        
        try:
            saved_theme = self.config.get_theme()
            print(f"📖 Loading saved theme: {saved_theme}")
            
            # Apply without saving again
            return self.apply_theme(widget, saved_theme, save_to_config=False)
            
        except Exception as e:
            print(f"❌ Error loading saved theme: {e}")
            return False
    
    def get_custom_themes_dir(self) -> Path:
        """
        Get the directory where custom themes are stored.
        
        Returns:
            Path to custom themes directory
        """
        return Path.home() / ".audiowave" / "themes"
    
    def scan_for_new_themes(self) -> int:
        """
        Scan for new theme JSON files and load them.
        
        Returns:
            int: Number of new themes found and loaded
        """
        try:
            print("🔍 Scanning for new custom themes...")
            
            # Prebroj postojeće dynamic teme
            before_count = len(self.registry.get_dynamic_theme_names())
            
            # Učitaj custom teme
            self._load_custom_themes()
            
            # Izračunaj koliko je novih
            after_count = len(self.registry.get_dynamic_theme_names())
            new_count = after_count - before_count
            
            if new_count > 0:
                print(f"✨ Found {new_count} new custom themes!")
                self.themes_reloaded.emit()
            else:
                print("ℹ️  No new themes found.")
            
            return new_count
            
        except Exception as e:
            print(f"⚠️  Error scanning for new themes: {e}")
            return 0
    
    def delete_custom_theme(self, theme_name: str) -> bool:
        """
        Delete a custom theme.
        
        Args:
            theme_name: Name of theme to delete
            
        Returns:
            bool: True if successful
        """
        try:
            # Proveri da li je tema built-in
            if theme_name in self.registry.get_builtin_theme_names():
                print(f"❌ Cannot delete built-in theme: {theme_name}")
                return False
            
            # Proveri da li je tema dynamic
            if not self.registry.is_dynamic_theme(theme_name):
                print(f"❌ Theme '{theme_name}' is not a custom theme")
                return False
            
            # Proveri da li je trenutno primenjena
            if theme_name == self.current_theme:
                print(f"⚠️  Cannot delete currently applied theme: {theme_name}")
                return False
            
            # Pronađi i obriši JSON fajl
            custom_themes_dir = self.get_custom_themes_dir()
            deleted_file = False
            
            for json_file in custom_themes_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                    
                    if theme_data.get("name") == theme_name:
                        # Backup fajl
                        backup_file = json_file.with_suffix('.json.backup')
                        import shutil
                        shutil.copy2(json_file, backup_file)
                        
                        # Obriši original
                        json_file.unlink()
                        deleted_file = True
                        print(f"🗑️  Deleted theme file: {json_file.name}")
                        print(f"💾 Backup saved to: {backup_file.name}")
                        break
                        
                except Exception as e:
                    print(f"⚠️  Error processing {json_file}: {e}")
                    continue
            
            if not deleted_file:
                print(f"⚠️  Theme file for '{theme_name}' not found")
                # Ipak pokušaj da unregister tema
                pass
            
            # Unregister temu iz registry
            success = self.registry.unregister_theme(theme_name)
            
            if success:
                print(f"✅ Custom theme '{theme_name}' deleted successfully")
                self.themes_reloaded.emit()
                return True
            else:
                print(f"⚠️  Could not unregister theme '{theme_name}' from registry")
                return False
            
        except Exception as e:
            print(f"❌ Error deleting theme '{theme_name}': {e}")
            return False
    
    def export_theme_to_json(self, theme_name: str, file_path: Path = None) -> bool:
        """
        Export a theme to JSON file.
        
        Args:
            theme_name: Name of theme to export
            file_path: Path to save JSON (None for default location)
            
        Returns:
            bool: True if successful
        """
        try:
            # Proveri da li tema postoji
            if not self.registry.theme_exists(theme_name):
                print(f"❌ Theme '{theme_name}' not found")
                return False
            
            # Dobij temu
            theme = self.registry.get_theme(theme_name)
            theme_data = theme.get_theme_data()
            
            # Dodaj dodatne informacije
            export_data = {
                "name": theme_name,
                "type": "dark" if self.registry.is_dark_theme(theme_name) else "light",
                "exported_at": datetime.now().isoformat(),
                "exported_from": "AudioWave Theme Manager",
                "theme_data": theme_data
            }
            
            # Dodaj boje ako postoje kao atribute
            if hasattr(theme, 'primary'):
                export_data.update({
                    "primary": theme.primary,
                    "secondary": theme.secondary,
                    "bg_main": getattr(theme, 'bg_main', ''),
                    "bg_secondary": getattr(theme, 'bg_secondary', ''),
                    "text_color": getattr(theme, 'text_color', ''),
                })
            
            # Odredi file path
            if file_path is None:
                themes_dir = self.get_custom_themes_dir()
                themes_dir.mkdir(exist_ok=True)
                safe_name = "".join(c if c.isalnum() else "_" for c in theme_name)
                file_path = themes_dir / f"{safe_name}.json"
            
            # Sačuvaj JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Exported theme '{theme_name}' to {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting theme '{theme_name}': {e}")
            return False


# ===== UTILITY FUNCTIONS =====

def create_theme_manager(config=None) -> ThemeManager:
    """
    Create and initialize a ThemeManager instance.
    
    Args:
        config: Optional config instance
        
    Returns:
        ThemeManager: Initialized theme manager
    """
    try:
        return ThemeManager(config)
    except Exception as e:
        print(f"💥 CRITICAL: Failed to create ThemeManager: {e}")
        # Return minimal working manager
        manager = ThemeManager.__new__(ThemeManager)
        manager.current_theme = "Dark Modern"
        manager.emergency_mode = True
        manager.registry = ThemeRegistry
        return manager


# ===== TEST =====
if __name__ == "__main__":
    print("🧪 Testing ThemeManager...")
    
    # Mock config
    class MockConfig:
        def get_theme(self):
            return "Dark Modern"
        def set_theme(self, theme):
            print(f"MockConfig: Would save theme '{theme}'")
    
    # Test
    config = MockConfig()
    tm = ThemeManager(config)
    
    print(f"\n✅ ThemeManager test successful!")
    print(f"   Current theme: {tm.get_current_theme()}")
    print(f"   Available themes: {len(tm.get_available_themes())}")
    print(f"   Emergency mode: {tm.emergency_mode}")