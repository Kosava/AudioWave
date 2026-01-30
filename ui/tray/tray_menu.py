# ui/tray/tray_menu.py

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction


class TrayMenu:
    """Tray context menu"""

    def __init__(self, tray_icon):
        self.tray_icon = tray_icon
        self.menu = QMenu()

        # Actions
        self.play_action = QAction("▶ Play / Pause")
        self.next_action = QAction("⏭ Next")
        self.prev_action = QAction("⏮ Previous")
        self.show_action = QAction("🪟 Show Window")
        self.quit_action = QAction("❌ Quit")

        # Connect actions
        self.play_action.triggered.connect(tray_icon.play_pause_requested.emit)
        self.next_action.triggered.connect(tray_icon.next_requested.emit)
        self.prev_action.triggered.connect(tray_icon.prev_requested.emit)
        self.show_action.triggered.connect(tray_icon.show_requested.emit)
        self.quit_action.triggered.connect(tray_icon.quit_requested.emit)

        # Build menu
        self.menu.addAction(self.play_action)
        self.menu.addSeparator()
        self.menu.addAction(self.prev_action)
        self.menu.addAction(self.next_action)
        self.menu.addSeparator()
        self.menu.addAction(self.show_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)