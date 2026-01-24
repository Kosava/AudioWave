from PyQt6.QtWidgets import QSystemTrayIcon, QMainWindow, QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from core.config import Config


class TrayIcon(QObject):
    """QSystemTrayIcon wrapper za AudioWave"""

    show_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    play_pause_requested = pyqtSignal()
    next_requested = pyqtSignal()
    prev_requested = pyqtSignal()

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.parent_window = parent

        self.config = Config()
        self.tray_settings = self.config.get_tray_settings()

        self.tray = QSystemTrayIcon(self._load_icon(), parent)
        self.tray.setToolTip("AudioWave")

        from ui.tray.tray_menu import TrayMenu
        self.menu = TrayMenu(self)
        self.tray.setContextMenu(self.menu.menu)

        self.tray.activated.connect(self.on_activated)

        if self.tray_settings.get("enabled", True):
            self.tray.show()
            print("🟢 Tray icon initialized")
        else:
            print("⚪ Tray disabled by settings")

    def _load_icon(self):
        theme = self.tray_settings.get("icon_theme", "auto")

        if theme == "light":
            icon_file = "audiowave_tray_light.png"
        elif theme == "dark":
            icon_file = "audiowave_tray_dark.png"
        else:
            # auto fallback (kasnije theme-aware)
            icon_file = "audiowave_tray_dark.png"

        icon_path = Path("resources/icons") / icon_file

        if not icon_path.exists():
            print(f"⚠️ Tray icon not found: {icon_path}")
            return QIcon()

        return QIcon(str(icon_path))

    def reload_from_settings(self):
        self.tray_settings = self.config.get_tray_settings()
        self.tray.setIcon(self._load_icon())

        if self.tray_settings.get("enabled", True):
            self.tray.show()
        else:
            self.tray.hide()

        print("🔄 Tray settings reloaded")

    def on_activated(self, reason):
        """Handle tray icon activation (click)"""
        # Middle click za play/pause
        if reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            print("📌 Middle click: play/pause")
            self.play_pause_requested.emit()
            return
        
        # Left click za toggle prozora (kao i pre)
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # ✅ TOGGLE LOGIKA: proveri stanje glavnog prozora
            app = QApplication.instance()
            main_window = None
            
            # Pronađi glavni prozor
            for widget in app.topLevelWidgets():
                if isinstance(widget, QMainWindow) and widget.windowTitle() == "TrayWave Player":
                    main_window = widget
                    break
            
            # Ako ne nađemo po naslovu, tražimo po tipu
            if not main_window:
                for widget in app.topLevelWidgets():
                    if isinstance(widget, QMainWindow):
                        main_window = widget
                        break
            
            if main_window:
                if main_window.isVisible() and not main_window.isMinimized():
                    # Ako je prozor vidljiv, sakrij ga
                    print("📌 Tray click: hiding window")
                    self.hide_requested.emit()
                else:
                    # Ako je sakriven ili minimizovan, prikaži ga
                    print("📌 Tray click: showing window")
                    self.show_requested.emit()
            else:
                # Ako ne nađemo prozor, emitujemo show
                print("📌 Tray click: window not found, showing")
                self.show_requested.emit()

    def show_message(self, title, message, timeout=3000):
        if not self.tray_settings.get("notifications", True):
            return

        self.tray.showMessage(
            title,
            message,
            QSystemTrayIcon.MessageIcon.Information,
            timeout
        )

    def cleanup(self):
        if self.tray:
            self.tray.hide()
            print("🔴 Tray icon removed")