# -*- coding: utf-8 -*-
# ui/tray/tray_icon.py

"""
SIGURAN System Tray Icon za AudioWave
✅ Bez segfault-a pri zatvaranju
✅ Proper cleanup Qt objekata
✅ Handle za mouse i keyboard interakcije
✅ Theme-aware ikone
"""

import os
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QSystemTrayIcon, QMainWindow, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from core.config import Config
from .tray_menu import TrayMenu


class TrayIcon(QObject):
    """
    QSystemTrayIcon wrapper sa sigurnim cleanup-om.
    Prevencija segfault-a kroz pravilno uništavanje Qt objekata.
    """
    
    # Signali
    show_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    play_pause_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    
    def __init__(self, app, parent=None):
        super().__init__(parent)
        print("🔧 Initializing TrayIcon...")
        
        self._app = app
        self._parent_window = parent
        self._is_cleaning_up = False
        self._tray = None
        self._menu_manager = None
        
        # Config
        self._config = Config()
        self._tray_settings = self._config.get_tray_settings()
        
        # Kreiraj tray icon samo ako je enabled u settings
        if self._tray_settings.get("enabled", True):
            self._initialize_tray()
        else:
            print("⚪ Tray disabled by settings")
    
    def _get_tray_theme_icon(self) -> QIcon:
        """Helper metoda za dobijanje theme-based tray ikone"""
        return QIcon.fromTheme(
            "audiowave-tray",
            QIcon("/usr/share/icons/hicolor/22x22/apps/audiowave-tray.png")
        )
    
    def _initialize_tray(self):
        """Initialize tray icon - sa error handling"""
        try:
            # Koristi theme-based icon sa fallback-om
            icon = self._get_tray_theme_icon()
            
            # Kreiraj QSystemTrayIcon
            self._tray = QSystemTrayIcon(icon, self._parent_window)
            self._tray.setToolTip("AudioWave Player")
            
            # Kreiraj context menu
            self._menu_manager = TrayMenu(self)
            self._tray.setContextMenu(self._menu_manager.menu)
            
            # Poveži signale
            self._tray.activated.connect(self._on_activated)
            
            # Prikaži tray icon
            self._tray.show()
            
            print("✅ Tray icon initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize tray icon: {e}")
            import traceback
            traceback.print_exc()
            self._tray = None
    
    def _load_icon(self) -> QIcon:
        """
        Učitaj tray icon prema trenutnoj temi.
        
        Returns:
            QIcon: Tray icon ili prazan icon
        """
        try:
            theme = self._tray_settings.get("icon_theme", "auto")
            
            # Odredi koji icon file koristiti
            if theme == "light":
                icon_file = "audiowave_tray_light.png"
            elif theme == "dark":
                icon_file = "audiowave_tray_dark.png"
            else:  # auto
                # Proveri da li je trenutna tema dark
                current_theme = self._config.get_theme()
                from core.themes.theme_registry import ThemeRegistry
                if ThemeRegistry.is_dark_theme(current_theme):
                    icon_file = "audiowave_tray_dark.png"
                else:
                    icon_file = "audiowave_tray_light.png"
            
            # Pokušaj da nađeš icon u različitim lokacijama
            icon_paths = [
                Path("resources/icons") / icon_file,
                Path("icons") / icon_file,
                Path.cwd() / "icons" / icon_file,
                Path.home() / ".audiowave" / "icons" / icon_file,
                Path("/usr/share/audiowave/icons") / icon_file,
            ]
            
            for icon_path in icon_paths:
                if icon_path.exists():
                    return QIcon(str(icon_path))
            
            # Fallback: generiši simple icon
            print(f"⚠️ Tray icon not found: {icon_file}, using fallback")
            return self._create_fallback_icon()
            
        except Exception as e:
            print(f"⚠️ Error loading tray icon: {e}")
            return QIcon()
    
    def _create_fallback_icon(self) -> QIcon:
        """Kreiraj fallback tray icon ako nije pronađen fajl"""
        try:
            from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush
            from PyQt6.QtCore import Qt
            
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw blue circle
            painter.setBrush(QBrush(QColor(74, 110, 224)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(8, 8, 48, 48)
            
            # Draw white music note
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(22, 18, 8, 8)  # Note head
            painter.drawRect(28, 18, 4, 20)    # Note stem
            
            painter.end()
            
            return QIcon(pixmap)
            
        except Exception as e:
            print(f"⚠️ Could not create fallback icon: {e}")
            return QIcon()
    
    def _on_activated(self, reason):
        """
        Handle tray icon activation (click).
        Sigurna implementacija koja proverava stanje objekata.
        """
        if self._is_cleaning_up or not self._tray:
            return
        
        try:
            # Middle click za play/pause
            if reason == QSystemTrayIcon.ActivationReason.MiddleClick:
                print("🔌 Tray middle click: play/pause")
                self.play_pause_requested.emit()
                return
            
            # Left click za toggle prozora
            if reason == QSystemTrayIcon.ActivationReason.Trigger:
                print("🔌 Tray left click: toggle window")
                self._toggle_window_visibility()
                
        except Exception as e:
            print(f"⚠️ Error in tray activation: {e}")
    
    def _toggle_window_visibility(self):
        """Toggle glavni prozor između vidljiv/skriven"""
        try:
            app = QApplication.instance()
            if not app:
                return
            
            # Pronađi glavni AudioWave prozor
            main_window = None
            for widget in app.topLevelWidgets():
                if isinstance(widget, QMainWindow) and hasattr(widget, 'windowTitle'):
                    title = widget.windowTitle()
                    if "AudioWave" in title or "TrayWave" in title:
                        main_window = widget
                        break
            
            # Ako ne nađemo po naslovu, pronađi prvi QMainWindow
            if not main_window:
                for widget in app.topLevelWidgets():
                    if isinstance(widget, QMainWindow):
                        main_window = widget
                        break
            
            if main_window:
                if main_window.isVisible() and not main_window.isMinimized():
                    # Sakrij prozor
                    print("🔌 Hiding main window")
                    self.hide_requested.emit()
                else:
                    # Prikaži prozor
                    print("🔌 Showing main window")
                    self.show_requested.emit()
            else:
                # Ako ne postoji prozor, emituj show
                print("🔌 Main window not found, requesting show")
                self.show_requested.emit()
                
        except Exception as e:
            print(f"⚠️ Error toggling window visibility: {e}")
    
    def reload_from_settings(self):
        """Reload tray settings iz config-a"""
        if self._is_cleaning_up:
            return
        
        try:
            self._tray_settings = self._config.get_tray_settings()
            
            # Ako je tray disabled, sakrij ga
            if not self._tray_settings.get("enabled", True):
                if self._tray:
                    self._tray.hide()
                return
            
            # Ako je enabled ali nema tray, kreiraj ga
            if not self._tray:
                self._initialize_tray()
                return
            
            # Ažuriraj icon - KORIGOVANO: koristi theme-based icon
            self._tray.setIcon(self._get_tray_theme_icon())
            
            # Prikaži/sakrij prema settings
            if self._tray_settings.get("enabled", True):
                self._tray.show()
            else:
                self._tray.hide()
            
            print("🔄 Tray settings reloaded")
            
        except Exception as e:
            print(f"⚠️ Error reloading tray settings: {e}")
    
    def show_message(self, title: str, message: str, timeout: int = 3000):
        """
        Prikaži notifikaciju iz tray-a.
        
        Args:
            title: Naslov notifikacije
            message: Poruka
            timeout: Vreme prikaza u ms (default: 3000)
        """
        if (self._is_cleaning_up or 
            not self._tray or 
            not self._tray_settings.get("notifications", True)):
            return
        
        try:
            self._tray.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                timeout
            )
        except Exception as e:
            print(f"⚠️ Error showing tray notification: {e}")
    
    def show(self):
        """Prikaži tray icon"""
        if self._tray and not self._is_cleaning_up:
            try:
                self._tray.show()
            except Exception as e:
                print(f"⚠️ Error showing tray: {e}")
    
    def hide(self):
        """Sakrij tray icon"""
        if self._tray and not self._is_cleaning_up:
            try:
                self._tray.hide()
            except Exception as e:
                print(f"⚠️ Error hiding tray: {e}")
    
    def cleanup(self):
        """
        SIGURAN cleanup tray icon-a.
        Prevencija segfault-a kroz pravilno uništavanje Qt objekata.
        """
        if self._is_cleaning_up:
            return
        
        print("🔄 Starting tray cleanup...")
        self._is_cleaning_up = True
        
        try:
            # 1. Diskonektuj sve signale
            try:
                if self._tray:
                    # Diskonektuj activation signal
                    self._tray.activated.disconnect()
                    
                    # Diskonektuj sve akcije iz menija
                    if self._menu_manager:
                        actions = [
                            self._menu_manager.play_action,
                            self._menu_manager.next_action,
                            self._menu_manager.prev_action,
                            self._menu_manager.show_action,
                            self._menu_manager.quit_action
                        ]
                        for action in actions:
                            try:
                                if action:
                                    action.triggered.disconnect()
                            except:
                                pass
            except Exception as e:
                print(f"⚠️ Error disconnecting tray signals: {e}")
            
            # 2. Obriši context menu
            try:
                if self._menu_manager and self._menu_manager.menu:
                    # Clear actions
                    self._menu_manager.menu.clear()
                    # DeleteLater će biti pozvan od strane Qt-a
                    self._menu_manager.menu.setParent(None)
                    self._menu_manager = None
            except Exception as e:
                print(f"⚠️ Error cleaning up tray menu: {e}")
            
            # 3. Sakrij i obriši tray icon
            try:
                if self._tray:
                    # Sakrij prvo
                    self._tray.hide()
                    # Postavi na None - Qt će obrisati kasnije
                    self._tray.setParent(None)
                    self._tray = None
            except Exception as e:
                print(f"⚠️ Error removing tray icon: {e}")
            
            # 4. Diskonektuj naše signale
            try:
                signals = [
                    self.show_requested, self.hide_requested, 
                    self.quit_requested, self.play_pause_requested,
                    self.next_requested, self.prev_requested,
                    self.stop_requested
                ]
                for signal in signals:
                    try:
                        signal.disconnect()
                    except:
                        pass
            except:
                pass
            
            # 5. Očisti reference
            self._app = None
            self._parent_window = None
            self._config = None
            
            print("✅ Tray cleanup completed")
            
        except Exception as e:
            print(f"💥 Critical error during tray cleanup: {e}")
            import traceback
            traceback.print_exc()
    
    def update_tooltip(self, text: str):
        """Ažuriraj tray tooltip"""
        if self._tray and not self._is_cleaning_up:
            try:
                self._tray.setToolTip(text)
            except Exception as e:
                print(f"⚠️ Error updating tray tooltip: {e}")
    
    def is_visible(self) -> bool:
        """Da li je tray icon vidljiv"""
        return (self._tray is not None and 
                not self._is_cleaning_up and 
                self._tray.isVisible())
    
    def set_icon_theme(self, theme: str):
        """
        Podesi theme za tray icon.
        
        Args:
            theme: "auto", "light", ili "dark"
        """
        if self._tray_settings and theme in ["auto", "light", "dark"]:
            self._tray_settings["icon_theme"] = theme
            self._config.set_tray_settings(self._tray_settings)
            
            if self._tray and not self._is_cleaning_up:
                try:
                    # KORIGOVANO: koristi theme-based icon umesto custom
                    self._tray.setIcon(self._get_tray_theme_icon())
                except Exception as e:
                    print(f"⚠️ Error updating tray icon theme: {e}")