# -*- coding: utf-8 -*-
# core/themes/emergency_theme.py

"""
Emergency fallback themes for when things go wrong.
Minimal themes designed to NEVER fail.
"""

from .base_theme import BaseTheme, StyleComponents


class EmergencyTheme(BaseTheme):
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


class SafeTheme(BaseTheme):
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


# ===== TEST =====
if __name__ == "__main__":
    print("🧪 Testing Emergency Themes...")
    
    emergency = EmergencyTheme()
    safe = SafeTheme()
    
    print(f"\n✅ EmergencyTheme:")
    print(f"   Name: {emergency.name}")
    print(f"   Dark: {emergency.is_dark}")
    
    print(f"\n✅ SafeTheme:")
    print(f"   Name: {safe.name}")
    print(f"   Dark: {safe.is_dark}")
    
    print(f"\n✅ Both themes created successfully!")