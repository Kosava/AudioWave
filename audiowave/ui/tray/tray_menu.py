# -*- coding: utf-8 -*-
# ui/tray/tray_menu.py
"""
Tray context menu za AudioWave Player

FEATURES:
✅ Play/Pause, Next, Previous kontrole
✅ Show/Hide Window toggle (menja tekst dinamički)
✅ Quit opcija
"""

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
from ui.utils.svg_icon_manager import get_icon  # ✅ DODATO


class TrayMenu:
    """
    Tray context menu sa dinamičkim Show/Hide opcijama.
    
    Attributes:
        tray_icon: Referenca na TrayIcon objekat
        menu: QMenu instanca
        show_action: QAction za Show/Hide Window
    """

    def __init__(self, tray_icon):
        """
        Initialize tray menu.
        
        Args:
            tray_icon: TrayIcon objekat koji sadrži signale
        """
        self.tray_icon = tray_icon
        self.menu = QMenu()
        
        # ✅ Čuvamo state za toggle
        self._window_visible = True

        # Actions
        self.play_action = QAction("Play / Pause")  # ✅ PROMENJENO
        self.next_action = QAction("Next")  # ✅ PROMENJENO
        self.prev_action = QAction("Previous")  # ✅ PROMENJENO
        self.stop_action = QAction("Stop")  # ✅ PROMENJENO
        
        # ✅ PROMENJENO: Show/Hide Window umesto samo Show Window
        self.show_action = QAction("Hide Window")  # ✅ PROMENJENO: Početno je prozor vidljiv
        
        self.quit_action = QAction("Quit")  # ✅ PROMENJENO

        # Set icons for actions
        # ✅ DODATO: Postavljamo ikone za sve akcije
        self.play_action.setIcon(get_icon("play", size=16))
        self.stop_action.setIcon(get_icon("stop", size=16))
        self.next_action.setIcon(get_icon("next", size=16))
        self.prev_action.setIcon(get_icon("previous", size=16))
        self.show_action.setIcon(get_icon("menu", size=16))
        self.quit_action.setIcon(get_icon("quit", size=16))

        # Connect actions
        self.play_action.triggered.connect(tray_icon.play_pause_requested.emit)
        self.next_action.triggered.connect(tray_icon.next_requested.emit)
        self.prev_action.triggered.connect(tray_icon.prev_requested.emit)
        self.stop_action.triggered.connect(tray_icon.stop_requested.emit)
        
        # ✅ PROMENJENO: Toggle umesto samo show
        self.show_action.triggered.connect(self._on_show_hide_clicked)
        
        self.quit_action.triggered.connect(tray_icon.quit_requested.emit)

        # Build menu
        self.menu.addAction(self.play_action)
        self.menu.addAction(self.stop_action)
        self.menu.addSeparator()
        self.menu.addAction(self.prev_action)
        self.menu.addAction(self.next_action)
        self.menu.addSeparator()
        self.menu.addAction(self.show_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)
    
    def _on_show_hide_clicked(self):
        """
        Handle Show/Hide klik - toggle vidljivost prozora.
        Emituje odgovarajući signal i ažurira tekst.
        """
        if self._window_visible:
            # Prozor je vidljiv, sakrij ga
            self.tray_icon.hide_requested.emit()
            self._window_visible = False
            self.show_action.setText("Show Window")  # ✅ PROMENJENO
        else:
            # Prozor je skriven, prikaži ga
            self.tray_icon.show_requested.emit()
            self._window_visible = True
            self.show_action.setText("Hide Window")  # ✅ PROMENJENO
    
    def update_window_state(self, is_visible: bool):
        """
        Ažuriraj stanje menija kada se prozor prikaže/sakrije spolja.
        
        Args:
            is_visible: Da li je prozor trenutno vidljiv
        """
        self._window_visible = is_visible
        if is_visible:
            self.show_action.setText("Hide Window")  # ✅ PROMENJENO
        else:
            self.show_action.setText("Show Window")  # ✅ PROMENJENO
    
    def set_playing_state(self, is_playing: bool):
        """
        Ažuriraj Play/Pause tekst prema stanju.
        
        Args:
            is_playing: Da li se trenutno reprodukuje
        """
        if is_playing:
            self.play_action.setIcon(get_icon("pause", size=16))  # ✅ PROMENJENO
            self.play_action.setText("Pause")  # ✅ PROMENJENO
        else:
            self.play_action.setIcon(get_icon("play", size=16))  # ✅ PROMENJENO
            self.play_action.setText("Play")  # ✅ PROMENJENO