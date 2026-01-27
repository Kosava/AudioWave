# -*- coding: utf-8 -*-
# core/themes/base_theme.py - COMPLETE WITH MINIMAL STYLE - FIXED DROPDOWN

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
                background: qlineargradient(x1:0, y1:0, x2:0, y2=1, 
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
                background: qlineargradient(x1:0, y1:0, x2:0, y2=1, stop:0 {color1}, stop:1 {color2});
                border: 3px solid {border};
                border-radius: 30px;
                color: white;
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton#playerPlayButton:hover {{
                background: qlineargradient(x1:0, y1=0, x2:0, y2=1, stop:0 {color1}, stop:1 {color2});
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
                background: qlineargradient(x1:0, y1=0, x2:0, y2=1,
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
                background: qlineargradient(x1:0, y1=0, x2:0, y2=1,
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
    def get_settings_dialog_stylesheet(primary: str, bg_main: str, bg_secondary: str, text_color: str, is_dark: bool = True) -> str:
        """Generate settings dialog stylesheet - theme-aware with FIXED WHITE DROPDOWN"""
        # NEZAVISNO OD TEME - dropdown UVJEK bijela pozadina, crni tekst
        DROPDOWN_BG = "#ffffff"      # UVJEK bijela
        DROPDOWN_TEXT = "#333333"    # UVJEK tamno siva
        DROPDOWN_BORDER = "#cccccc"
        
        if is_dark:
            border_color = "#555"
            disabled_color = "#888"
        else:
            border_color = "#ccc"
            disabled_color = "#999"
        
        return f"""
            /* Dialog */
            QDialog {{
                background-color: {bg_main}; 
                color: {text_color}; 
                font-family: 'Arial', sans-serif;
                font-size: 13px;
            }}
            
            /* Tab widget */
            QTabWidget::pane {{
                background-color: {bg_main}; 
                border: 1px solid {border_color}; 
                border-radius: 8px;
                padding: 10px;
            }}
            
            QTabBar::tab {{
                background-color: {bg_secondary}; 
                color: {disabled_color}; 
                padding: 10px 20px; 
                border-top-left-radius: 8px; 
                border-top-right-radius: 8px; 
                margin-right: 2px;
                border: 1px solid {border_color};
                border-bottom: none;
            }}
            
            QTabBar::tab:selected {{
                background-color: {primary}; 
                color: white; 
                font-weight: bold;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: rgba({primary.replace('#', '')}, 0.2);
            }}
            
            /* Labels */
            QLabel {{
                color: {text_color}; 
                background: transparent;
            }}
            
            /* ComboBox - MAIN */
            QComboBox {{
                background-color: {bg_secondary}; 
                color: {text_color}; 
                border: 1px solid {border_color}; 
                border-radius: 6px; 
                padding: 8px 12px;
                min-width: 200px;
            }}
            
            QComboBox:hover {{
                border-color: {primary};
            }}
            
            QComboBox:focus {{
                border-color: {primary};
                border-width: 2px;
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid {border_color};
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: {primary};
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid white;
                width: 0;
                height: 0;
            }}
            
            /* ComboBox Dropdown - FIXED: UVJEK bijela pozadina, crni tekst */
            QComboBox QAbstractItemView {{
                background-color: {DROPDOWN_BG};
                color: {DROPDOWN_TEXT};
                border: 1px solid {DROPDOWN_BORDER};
                border-radius: 6px;
                margin: 0px;
                padding: 4px;
                selection-background-color: {primary};
                selection-color: white;
            }}
            
            QComboBox QAbstractItemView::item {{
                padding: 8px 12px;
                border-radius: 4px;
                margin: 1px 0;
            }}
            
            QComboBox QAbstractItemView::item:hover {{
                background-color: rgba({primary.replace('#', '')}, 0.1);
            }}
            
            QComboBox QAbstractItemView::item:selected {{
                background-color: {primary};
                color: white;
                font-weight: bold;
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {primary}; 
                color: white; 
                border: none; 
                border-radius: 6px; 
                padding: 10px 20px; 
                font-weight: bold;
                min-width: 100px;
            }}
            
            QPushButton:hover {{
                background-color: rgba({primary.replace('#', '')}, 0.9);
            }}
            
            QPushButton:pressed {{
                background-color: rgba({primary.replace('#', '')}, 0.7);
            }}
            
            /* Checkboxes */
            QCheckBox {{
                color: {text_color}; 
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 18px; 
                height: 18px; 
                border: 2px solid {border_color}; 
                border-radius: 4px; 
                background-color: {bg_secondary};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {primary}; 
                border-color: {primary};
                image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12"><path fill="white" d="M10.28 3.28L4.5 9.06 1.72 6.28 1 7l3.5 3.5 6.5-6.5z"/></svg>');
            }}
            
            QCheckBox::indicator:checked:hover {{
                background-color: rgba({primary.replace('#', '')}, 0.9);
            }}
            
            /* Sliders */
            QSlider::groove:horizontal {{
                background: {bg_secondary}; 
                height: 6px; 
                border-radius: 3px;
                border: 1px solid {border_color};
            }}
            
            QSlider::handle:horizontal {{
                background: {primary}; 
                width: 16px; 
                height: 16px; 
                margin: -5px 0; 
                border-radius: 8px; 
                border: 2px solid white;
            }}
            
            QSlider::handle:horizontal:hover {{
                background: rgba({primary.replace('#', '')}, 0.9); 
                width: 18px; 
                height: 18px; 
                margin: -6px 0; 
                border-radius: 9px;
            }}
            
            QSlider::sub-page:horizontal {{
                background: {primary}; 
                border-radius: 3px;
            }}
            
            /* Group boxes */
            QGroupBox {{
                border: 1px solid {border_color}; 
                border-radius: 8px; 
                font-weight: bold; 
                color: {text_color};
                margin-top: 12px;
                padding-top: 20px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 4px 12px;
                background-color: {primary};
                color: white;
                border-radius: 4px;
            }}
            
            /* Scrollbars */
            QScrollBar:vertical {{
                background: {bg_secondary}; 
                width: 12px; 
                border-radius: 6px; 
                border: 1px solid {border_color};
            }}
            
            QScrollBar::handle:vertical {{
                background: {primary}; 
                border-radius: 6px; 
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: rgba({primary.replace('#', '')}, 0.9);
            }}
            
            /* Plugin cards */
            QFrame#pluginCard {{
                background-color: rgba({primary.replace('#', '')}, 0.1); 
                border: 1px solid rgba({primary.replace('#', '')}, 0.3);
                border-radius: 8px; 
            }}
            
            QFrame#pluginCard:hover {{
                background-color: rgba({primary.replace('#', '')}, 0.15); 
                border-color: rgba({primary.replace('#', '')}, 0.5);
            }}
            
            /* Separator lines */
            QFrame[frameShape="4"] {{
                background-color: {border_color}; 
                max-height: 1px;
            }}
        """
    @staticmethod
    def get_settings_dialog_stylesheet(primary: str, bg_main: str, bg_secondary: str, 
                                       text_color: str, is_dark: bool = True) -> str:
        """Generate settings dialog stylesheet - FIXED for light themes!"""
        
        if is_dark:
            border_color = "#555"
            disabled_color = "#888"
            hover_bg = "#2a2a4a"
            selection_text = "white"
        else:
            border_color = "#ccc"
            disabled_color = "#666"
            hover_bg = "rgba(0, 0, 0, 0.05)"
            selection_text = "white"
        
        return f"""
            QDialog {{ background-color: {bg_main}; color: {text_color}; }}
            QTabWidget::pane {{ background-color: {bg_main}; border: 1px solid {border_color}; border-radius: 8px; }}
            QTabBar::tab {{ background-color: {bg_secondary}; color: {disabled_color}; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; }}
            QTabBar::tab:selected {{ background-color: {bg_secondary}; color: {text_color}; font-weight: bold; }}
            QTabBar::tab:hover {{ background-color: {hover_bg}; }}
            QLabel {{ color: {text_color}; background: transparent; }}
            QComboBox {{ background-color: {bg_secondary}; color: {text_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 8px 12px; min-width: 150px; }}
            QComboBox:hover {{ border-color: {primary}; background-color: {hover_bg}; }}
            QComboBox::drop-down {{ border: none; width: 30px; }}
            QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid {text_color}; margin-right: 10px; }}
            QComboBox QAbstractItemView {{ background-color: {bg_secondary}; color: {text_color}; border: 1px solid {border_color}; selection-background-color: {primary}; selection-color: {selection_text}; outline: none; }}
            QPushButton {{ background-color: {primary}; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {primary}DD; }}
            QPushButton:pressed {{ background-color: {primary}AA; }}
            QPushButton:disabled {{ background-color: {disabled_color}; color: #999; }}
            QCheckBox {{ color: {text_color}; spacing: 8px; }}
            QCheckBox::indicator {{ width: 20px; height: 20px; border: 2px solid {border_color}; border-radius: 4px; background-color: {bg_secondary}; }}
            QCheckBox::indicator:checked {{ background-color: {primary}; border-color: {primary}; }}
            QCheckBox::indicator:hover {{ border-color: {primary}; }}
            QSlider::groove:horizontal {{ background: {bg_secondary}; height: 6px; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background: {primary}; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }}
            QSlider::handle:horizontal:hover {{ background: {primary}DD; }}
            QSlider::sub-page:horizontal {{ background: {primary}; border-radius: 3px; }}
            QGroupBox {{ border: 1px solid {border_color}; border-radius: 8px; margin-top: 12px; padding-top: 12px; font-weight: bold; color: {text_color}; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 4px 8px; background-color: {primary}; color: white; border-radius: 4px; }}
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: {bg_secondary}; width: 12px; border-radius: 6px; }}
            QScrollBar::handle:vertical {{ background: {primary}; border-radius: 6px; min-height: 30px; }}
            QScrollBar::handle:vertical:hover {{ background: {primary}DD; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QFrame {{ background: transparent; }}
            QFrame[frameShape="4"] {{ background-color: {border_color}; max-height: 1px; }}
            QFrame[frameShape="5"] {{ background-color: {border_color}; max-width: 1px; }}
        """