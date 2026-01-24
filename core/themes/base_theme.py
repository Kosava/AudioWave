# -*- coding: utf-8 -*-
# core/themes/base_theme.py - COMPLETE WITH MINIMAL STYLE - FIXED LINE VISIBILITY

"""Base theme class and common style components"""

from abc import ABC, abstractmethod
from typing import Dict


class BaseTheme(ABC):
    """Base class for all themes"""
    
    def __init__(self, name: str, font_family: str = "Arial", font_size: int = 13):
        self.name = name
        self.font_family = font_family
        self.font_size = font_size
    
    @abstractmethod
    def get_stylesheet(self) -> str:
        """Return complete stylesheet"""
        pass
    
    def get_theme_data(self) -> Dict:
        """Return theme data dict"""
        return {
            "stylesheet": self.get_stylesheet(),
            "font_family": self.font_family,
            "font_size": self.font_size
        }


class StyleComponents:
    """Reusable style components - DRY principle"""
    
    @staticmethod
    def get_complete_theme(primary: str, secondary: str, bg: str, text_color: str, 
                          accent: str = None, title_color: str = None, artist_color: str = None,
                          label_style: str = "minimal") -> str:
        """
        Kompletna tema - PODRŽAVA: minimal, glass, clean, subtle
        """
        if accent is None:
            accent = primary
        if title_color is None:
            title_color = text_color
        if artist_color is None:
            artist_color = text_color
        
        print(f"🎨 [Theme] Applying label_style: {label_style}")
        
        # ===== MINIMAL STYLE - FIXED! Smanjen padding/margin =====
        if label_style == "minimal":
            title_style = f"""
                QLabel#playerTitleLabel {{ 
                    font-size: 18px; 
                    font-weight: 300; 
                    color: white;
                    background: transparent;
                    border: none;
                    border-bottom: 3px solid rgba(255, 255, 255, 0.9);
                    border-radius: 0px;
                    padding: 4px 16px 6px 16px;
                    margin: 2px 8px 4px 8px;
                    letter-spacing: 2px;
                }}
            """
            artist_style = f"""
                QLabel#playerArtistLabel {{ 
                    font-size: 12px;
                    font-weight: 300;
                    color: rgba(255, 255, 255, 0.85);
                    background: transparent;
                    border: none;
                    padding: 2px 16px;
                    margin: 0px 8px 2px 8px;
                    letter-spacing: 2px;
                    text-transform: uppercase;
                }}
            """
        
        # ===== GLASS STYLE =====
        elif label_style == "glass":
            title_style = f"""
                QLabel#playerTitleLabel {{ 
                    font-size: 20px; 
                    font-weight: bold; 
                    color: white;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 0.4),
                        stop:1 rgba(255, 255, 255, 0.2));
                    border: 2px solid rgba(255, 255, 255, 0.5);
                    border-radius: 15px;
                    padding: 14px 28px;
                    margin: 8px 12px;
                }}
            """
            artist_style = f"""
                QLabel#playerArtistLabel {{ 
                    font-size: 14px;
                    color: white;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(255, 255, 255, 0.3),
                        stop:1 rgba(255, 255, 255, 0.15));
                    border: 2px solid rgba(255, 255, 255, 0.4);
                    border-radius: 12px;
                    padding: 10px 28px;
                    margin: 6px 12px;
                }}
            """
        
        # ===== CLEAN STYLE =====
        elif label_style == "clean":
            title_style = f"""
                QLabel#playerTitleLabel {{ 
                    font-size: 20px; 
                    font-weight: bold; 
                    color: white;
                    background: transparent;
                    border: none;
                    padding: 6px 12px;
                    margin: 2px 0px;
                }}
            """
            artist_style = f"""
                QLabel#playerArtistLabel {{ 
                    font-size: 14px;
                    color: white; 
                    background: transparent;
                    border: none;
                    padding: 4px 12px;
                    margin: 0px;
                }}
            """
        
        # ===== SUBTLE STYLE (default) =====
        else:
            title_style = f"""
                QLabel#playerTitleLabel {{ 
                    font-size: 20px; 
                    font-weight: bold; 
                    color: white;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(0, 0, 0, 0.4),
                        stop:0.5 rgba(0, 0, 0, 0.25),
                        stop:1 rgba(0, 0, 0, 0.4));
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 12px;
                    padding: 12px 24px;
                    margin: 6px 10px;
                }}
            """
            artist_style = f"""
                QLabel#playerArtistLabel {{ 
                    font-size: 14px;
                    color: white; 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(0, 0, 0, 0.3),
                        stop:0.5 rgba(0, 0, 0, 0.2),
                        stop:1 rgba(0, 0, 0, 0.3));
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 10px;
                    padding: 8px 24px;
                    margin: 4px 10px;
                }}
            """
        
        play_btn = StyleComponents.get_play_button(primary, secondary, accent)
        control_btns = StyleComponents.get_control_buttons(primary, accent, text_color)
        
        list_widget = f"""
            QListWidget#playlistFileList {{
                background-color: rgba(255, 255, 255, 0.5);
                border: 1px solid {primary};
                border-radius: 10px;
                padding: 6px;
                color: {text_color};
                font-size: 13px;
                outline: none;
            }}
            
            QListWidget#playlistFileList::item {{
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px 0;
            }}
            
            QListWidget#playlistFileList::item:hover {{
                background-color: rgba(255, 255, 255, 0.3);
            }}
            
            QListWidget#playlistFileList::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {primary}, 
                    stop:0.5 {secondary},
                    stop:1 {primary});
                color: white;
                font-weight: 600;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
            }}
        """
        
        scrollbar = StyleComponents.get_scrollbar(primary)
        search = StyleComponents.get_search_box(primary)
        
        return f"""
            * {{ outline: none; }}
            
            QWidget {{ 
                background-color: {bg}; 
                color: {text_color}; 
                font-family: 'Arial', sans-serif; 
                font-size: 13px; 
            }}
            
            QMainWindow {{ 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {bg}, stop:1 {bg}); 
            }}
            
            QFrame#playerTopSection {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {primary}, stop:0.3 {secondary}, stop:0.7 {primary}, stop:1 {secondary}); 
                border: none;
                border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            }}
            
            QFrame#playerTopSection > QWidget,
            QFrame#playerTopSection > QFrame,
            QFrame#playerTopSection QWidget,
            QFrame#playerTopSection QFrame {{
                background: none;
                background-color: transparent;
                border: none;
            }}
            
            QFrame#playerTopSection QLabel {{
                background: none;
                background-color: transparent;
                border: none;
            }}
            
            {title_style}
            {artist_style}
            
            QLabel#playerTimeLabel,
            QLabel#playerCurrentTimeLabel,
            QLabel#playerTotalTimeLabel {{
                color: {text_color};
                background: none;
                background-color: transparent;
                border: none;
                font-size: 12px;
                font-weight: 500;
                padding: 2px 4px;
            }}
            
            QFrame#playerControlsSection {{ background-color: rgba(255, 255, 255, 0.1); border: none; }}
            QFrame#playerVolumeSection {{ background-color: rgba(255, 255, 255, 0.1); border: none; }}
            
            QProgressBar {{
                background-color: rgba(0, 0, 0, 0.1);
                border: none;
                border-radius: 4px;
                text-align: center;
                color: {text_color};
                font-size: 11px;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary});
                border-radius: 4px;
            }}
            
            QSlider::groove:horizontal {{
                background-color: rgba(0, 0, 0, 0.15);
                height: 6px;
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {primary}, stop:1 {secondary});
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 2px solid white;
            }}
            
            QSlider::handle:horizontal:hover {{
                background-color: {primary};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary});
                border-radius: 3px;
            }}
            
            QSlider::add-page:horizontal {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 3px;
            }}
            
            {play_btn}
            {control_btns}
            
            QWidget#playlist_panel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {bg}, stop:1 {bg});
            }}
            
            {search}
            {list_widget}
            {scrollbar}
            
            QPushButton#playlistAddButton,
            QPushButton#playlistClearButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.2), stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid {primary};
                border-radius: 7px;
                color: {text_color};
                font-size: 12px;
                font-weight: 500;
                padding: 8px 14px;
            }}
            
            QPushButton#playlistAddButton:hover,
            QPushButton#playlistClearButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.3), stop:1 rgba(255, 255, 255, 0.1));
                border: 1px solid {accent};
            }}
            
            QPushButton#playlistSettingsButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(255, 255, 255, 0.2), stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid {accent};
                border-radius: 7px;
                color: {text_color};
                font-size: 12px;
                padding: 8px 14px;
            }}
        """
    
    @staticmethod
    def get_play_button(color1: str, color2: str, border: str) -> str:
        return f"""
            QPushButton#playerPlayButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {color1}, stop:1 {color2});
                border: 3px solid {border};
                border-radius: 30px;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton#playerPlayButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {color1}, stop:1 {color2});
                opacity: 0.9;
            }}
        """
    
    @staticmethod
    def get_control_buttons(bg_color: str, border_color: str, text_color: str = "white") -> str:
        return f"""
            QPushButton#playerPrevButton,
            QPushButton#playerNextButton,
            QPushButton#playerStopButton,
            QPushButton#playerPlaylistButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.25), stop:1 rgba(255, 255, 255, 0.15));
                border: 2px solid {border_color};
                border-radius: 22px;
                color: {text_color};
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton#playerPrevButton:hover,
            QPushButton#playerNextButton:hover,
            QPushButton#playerStopButton:hover,
            QPushButton#playerPlaylistButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.4), stop:1 rgba(255, 255, 255, 0.25));
            }}
        """
    
    @staticmethod
    def get_scrollbar(color: str) -> str:
        return f"""
            QScrollBar:vertical {{
                background-color: rgba(255, 255, 255, 0.03);
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {color};
                border-radius: 4px;
                min-height: 30px;
            }}
        """
    
    @staticmethod
    def get_search_box(border_color: str) -> str:
        return f"""
            QLineEdit#playlistSearchBox {{
                background-color: rgba(255, 255, 255, 0.6);
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QLineEdit#playlistSearchBox:focus {{
                border: 1px solid {border_color};
                background-color: rgba(255, 255, 255, 0.8);
            }}
        """
    
    @staticmethod
    def get_list_widget(bg_color: str, border_color: str, selected_color: str, text_color: str = "white") -> str:
        return ""
    
    @staticmethod
    def get_menu(bg_color: str, border_color: str, selected_color: str) -> str:
        return ""