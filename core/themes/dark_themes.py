# core/themes/dark_themes.py - FIXED: Dodao bg_main i bg_secondary za SVE teme

"""All dark theme implementations"""

from .base_theme import BaseTheme, StyleComponents


class DarkModernTheme(BaseTheme):
    """Dark Modern theme - Default"""
    
    def __init__(self):
        super().__init__("Dark Modern", "Arial", 13)
        self.primary = "#667eea"
        self.secondary = "#764ba2"
        self.bg_main = "#0f172a"
        self.bg_secondary = "#1e293b"
    
    def get_stylesheet(self) -> str:
        play_btn = StyleComponents.get_play_button(
            f"{self.primary}80", f"{self.secondary}80", f"{self.primary}CC"
        )
        control_btns = StyleComponents.get_control_buttons(self.primary, self.primary)
        list_widget = StyleComponents.get_list_widget(
            "rgba(30, 25, 45, 0.6)",
            f"{self.primary}33",
            f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self.primary}66, stop:1 #a88bfa66)"
        )
        scrollbar = StyleComponents.get_scrollbar(f"{self.primary}66")
        menu = StyleComponents.get_menu("rgba(30, 25, 45, 0.95)", f"{self.primary}4D", f"{self.primary}4D")
        search = StyleComponents.get_search_box("rgba(255, 255, 255, 0.08)", f"{self.primary}40", f"{self.primary}80")
        
        return f"""
            /* === GLOBAL === */
            QWidget {{
                background-color: {self.bg_main};
                color: #e2e8f0;
                font-family: '{self.font_family}', sans-serif;
                font-size: {self.font_size}px;
            }}
            
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.bg_main}, stop:1 {self.bg_secondary});
            }}
            
            /* === PLAYER WINDOW === */
            QFrame#playerTopSection {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.primary}26, stop:1 {self.bg_secondary}CC);
                border: none;
            }}
            
            QLabel#playerTitleLabel {{
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: transparent;
                border: none;
                padding: 2px;
            }}
            
            QLabel#playerArtistLabel {{
                font-size: 13px;
                color: rgba(255, 255, 255, 0.75);
                background: transparent;
                border: none;
                padding: 2px;
            }}
            
            QFrame#playerControlsSection {{
                background-color: rgba(30, 41, 59, 0.6);
                border: none;
            }}
            
            QFrame#playerVolumeSection {{
                background-color: rgba(30, 41, 59, 0.4);
                border: none;
            }}
            
            /* === BUTTONS === */
            {play_btn}
            {control_btns}
            
            /* === LISTS === */
            {list_widget}
            
            /* === SEARCH === */
            {search}
            
            /* === PLAYLIST BUTTONS === */
            QPushButton#playlistAddButton,
            QPushButton#playlistClearButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.primary}33, stop:1 {self.primary}1A);
                border: 1px solid {self.primary}4D;
                border-radius: 7px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                padding: 8px 14px;
                min-width: 80px;
            }}
            
            QPushButton#playlistAddButton:hover,
            QPushButton#playlistClearButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.primary}4D, stop:1 {self.primary}33);
                border: 1px solid {self.primary}80;
            }}
            
            QPushButton#playlistSettingsButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a88bfa33, stop:1 #a88bfa1A);
                border: 1px solid #a88bfa4D;
                border-radius: 7px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                padding: 8px 14px;
                min-width: 80px;
            }}
            
            QPushButton#playlistSettingsButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a88bfa4D, stop:1 #a88bfa33);
                border: 1px solid #a88bfa80;
            }}
            
            QLabel#playlistStatusLabel {{
                color: rgba(255, 255, 255, 0.6);
                font-size: 11px;
                background: rgba(255, 255, 255, 0.03);
                padding: 6px 10px;
                border-radius: 6px;
            }}
            
            /* === SCROLLBARS & MENUS === */
            {scrollbar}
            {menu}
        """


class OceanTheme(BaseTheme):
    """Ocean theme"""
    
    def __init__(self):
        super().__init__("Ocean", "Arial", 13)
        self.primary = "#0a9396"
        self.secondary = "#005f73"
        self.bg_main = "#001219"
        self.bg_secondary = "#003845"
    
    def get_stylesheet(self) -> str:
        play_btn = StyleComponents.get_play_button(self.primary, self.secondary, self.primary)
        control_btns = StyleComponents.get_control_buttons(self.primary, self.primary, "#90e0ef")
        list_widget = StyleComponents.get_list_widget(
            "rgba(0, 31, 38, 0.8)", f"{self.primary}4D", f"{self.primary}66", "#90e0ef"
        )
        
        return f"""
            QWidget {{
                background-color: {self.bg_main};
                color: #90e0ef;
            }}
            
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.bg_main}, stop:1 {self.bg_secondary});
            }}
            
            QFrame#playerTopSection {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.primary}33, stop:1 {self.bg_main}80);
            }}
            
            QLabel#playerTitleLabel {{
                font-size: 18px;
                font-weight: bold;
                color: #caf0f8;
                background: transparent;
                border: none;
            }}
            
            QLabel#playerArtistLabel {{
                color: #90e0ef;
                background: transparent;
                border: none;
            }}
            
            {play_btn}
            {control_btns}
            {list_widget}
        """


class CyberpunkTheme(BaseTheme):
    """Cyberpunk theme"""
    
    def __init__(self):
        super().__init__("Cyberpunk", "Courier New", 12)
        self.primary = "#c026d3"
        self.secondary = "#9333ea"
        self.bg_main = "#0a0e1a"
        self.bg_secondary = "#1a1030"
    
    def get_stylesheet(self) -> str:
        play_btn = StyleComponents.get_play_button(self.primary, self.secondary, "#d946ef")
        control_btns = StyleComponents.get_control_buttons(self.primary, "#d946ef", "#00ffff")
        
        return f"""
            QWidget {{
                background-color: {self.bg_main};
                color: #00ffff;
                font-family: '{self.font_family}', monospace;
            }}
            
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.bg_main}, stop:1 {self.bg_secondary});
            }}
            
            QLabel#playerTitleLabel {{
                color: #ff00ff;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
            
            QLabel#playerArtistLabel {{
                color: #00ffff;
                background: transparent;
                border: none;
            }}
            
            {play_btn}
            {control_btns}
        """


class RetroWaveTheme(BaseTheme):
    """Retro Wave theme"""
    
    def __init__(self):
        super().__init__("Retro Wave", "Arial", 13)
        self.primary = "#f72585"
        self.secondary = "#7209b7"
        self.bg_main = "#1a0033"
        self.bg_secondary = "#2d0a50"
    
    def get_stylesheet(self) -> str:
        play_btn = StyleComponents.get_play_button(self.primary, self.secondary, self.primary)
        control_btns = StyleComponents.get_control_buttons(self.primary, self.primary, "#ff6ec7")
        
        return f"""
            QWidget {{
                background-color: {self.bg_main};
                color: #ff6ec7;
            }}
            
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.bg_main}, stop:1 {self.bg_secondary});
            }}
            
            QLabel#playerTitleLabel {{
                color: #ff6ec7;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
            
            QLabel#playerArtistLabel {{
                color: #00f5ff;
                background: transparent;
                border: none;
            }}
            
            {play_btn}
            {control_btns}
        """


class ForestTheme(BaseTheme):
    """Forest theme"""
    
    def __init__(self):
        super().__init__("Forest", "Arial", 13)
        self.primary = "#40916c"
        self.secondary = "#2d6a4f"
        self.bg_main = "#0d1b0e"
        self.bg_secondary = "#1b2f1e"
    
    def get_stylesheet(self) -> str:
        play_btn = StyleComponents.get_play_button(self.primary, self.secondary, "#52b788")
        control_btns = StyleComponents.get_control_buttons(self.primary, "#52b788", "#d8f3dc")
        
        return f"""
            QWidget {{
                background-color: {self.bg_main};
                color: #a8e6cf;
            }}
            
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.bg_main}, stop:1 {self.bg_secondary});
            }}
            
            QLabel#playerTitleLabel {{
                color: #d8f3dc;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
            
            QLabel#playerArtistLabel {{
                color: #a8e6cf;
                background: transparent;
                border: none;
            }}
            
            {play_btn}
            {control_btns}
        """


class SolarizedDarkTheme(BaseTheme):
    """Solarized Dark theme"""
    
    def __init__(self):
        super().__init__("Solarized Dark", "Arial", 13)
        self.primary = "#268bd2"
        self.secondary = "#2aa198"
        self.bg_main = "#002b36"
        self.bg_secondary = "#073642"
    
    def get_stylesheet(self) -> str:
        play_btn = StyleComponents.get_play_button(self.primary, self.secondary, self.primary)
        control_btns = StyleComponents.get_control_buttons(self.primary, self.primary, "#93a1a1")
        
        return f"""
            QWidget {{
                background-color: {self.bg_main};
                color: #839496;
            }}
            
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.bg_main}, stop:1 {self.bg_secondary});
            }}
            
            QLabel#playerTitleLabel {{
                color: #eee8d5;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
            
            QLabel#playerArtistLabel {{
                color: #93a1a1;
                background: transparent;
                border: none;
            }}
            
            {play_btn}
            {control_btns}
        """