# -*- coding: utf-8 -*-
# plugins/sleeptimer/sleeptimer_plugin.py
"""
Sleep Timer Plugin za AudioWave

Features:
✅ Podesi timer za automatsko zaustavljanje/gašenje
✅ Vidljiv u system tray meniju
✅ Mogućnost poništavanja timera
✅ Opcije: samo zaustavi ili ugasi player
✅ Notifikacije o preostalom vremenu
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QSpinBox, QComboBox, QGroupBox, QRadioButton,
                            QButtonGroup, QProgressBar)
from PyQt6.QtCore import QTimer, pyqtSignal, Qt, QTime
from PyQt6.QtGui import QAction
import sys


class SleepTimerDialog(QDialog):
    """Dialog za podešavanje sleep timer-a"""
    
    # Signal kada se timer aktivira
    timer_started = pyqtSignal(int, str)  # duration_minutes, action
    timer_cancelled = pyqtSignal()
    
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        
        # Čuvaj referencu na app ako je prosleđena
        self.app = kwargs.get('app', None)
        if self.app is None and parent and hasattr(parent, 'app'):
            self.app = parent.app
        
        self.setWindowTitle("⏰ Sleep Timer")
        self.setMinimumWidth(400)
        self.setModal(False)  # Non-modal da bi tray bio pristupačan
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup UI elements"""
        layout = QVBoxLayout()
        
        # ===== INFO LABEL =====
        info_label = QLabel(
            "⏰ Set timer to automatically stop or quit the player."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; padding: 10px;")
        layout.addWidget(info_label)
        
        # ===== TIME SELECTION GROUP =====
        time_group = QGroupBox("⏱️ Time")
        time_layout = QVBoxLayout()
        
        # Hours
        hour_layout = QHBoxLayout()
        hour_layout.addWidget(QLabel("Hours:"))
        self.hours_spin = QSpinBox()
        self.hours_spin.setMinimum(0)
        self.hours_spin.setMaximum(23)
        self.hours_spin.setValue(0)
        self.hours_spin.setSuffix(" h")
        hour_layout.addWidget(self.hours_spin)
        hour_layout.addStretch()
        time_layout.addLayout(hour_layout)
        
        # Minutes
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Minutes:"))
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setMinimum(0)
        self.minutes_spin.setMaximum(59)
        self.minutes_spin.setValue(30)
        self.minutes_spin.setSuffix(" min")
        min_layout.addWidget(self.minutes_spin)
        min_layout.addStretch()
        time_layout.addLayout(min_layout)
        
        # Quick presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Quick select:"))
        
        preset_15 = QPushButton("15 min")
        preset_15.clicked.connect(lambda: self._set_preset(0, 15))
        preset_layout.addWidget(preset_15)
        
        preset_30 = QPushButton("30 min")
        preset_30.clicked.connect(lambda: self._set_preset(0, 30))
        preset_layout.addWidget(preset_30)
        
        preset_60 = QPushButton("60 min")
        preset_60.clicked.connect(lambda: self._set_preset(1, 0))
        preset_layout.addWidget(preset_60)
        
        preset_layout.addStretch()
        time_layout.addLayout(preset_layout)
        
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)
        
        # ===== ACTION SELECTION GROUP =====
        action_group = QGroupBox("🎯 Action when timer expires")
        action_layout = QVBoxLayout()
        
        self.action_button_group = QButtonGroup()
        
        self.stop_radio = QRadioButton("⏹️ Stop playback")
        self.stop_radio.setChecked(True)
        self.action_button_group.addButton(self.stop_radio)
        action_layout.addWidget(self.stop_radio)
        
        self.quit_radio = QRadioButton("❌ Quit player")
        self.action_button_group.addButton(self.quit_radio)
        action_layout.addWidget(self.quit_radio)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # ===== BUTTONS =====
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("✅ Start Timer")
        self.start_button.clicked.connect(self._start_timer)
        self.start_button.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        button_layout.addWidget(self.start_button)
        
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _set_preset(self, hours: int, minutes: int):
        """Postavi brzi preset"""
        self.hours_spin.setValue(hours)
        self.minutes_spin.setValue(minutes)
    
    def _start_timer(self):
        """Start timer"""
        hours = self.hours_spin.value()
        minutes = self.minutes_spin.value()
        
        total_minutes = hours * 60 + minutes
        
        if total_minutes == 0:
            # Show message if time is 0
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "⚠️ Invalid time",
                "Please set time greater than 0 minutes."
            )
            return
        
        # Determine action
        action = "stop" if self.stop_radio.isChecked() else "quit"
        
        # Emit signal
        self.timer_started.emit(total_minutes, action)
        
        # Close dialog
        self.accept()


class SleepTimerWidget:
    """
    Widget/Manager za sleep timer - upravlja aktivnim tajmerom.
    Ovo NIJE QWidget već helper klasa koja upravlja tajmerom i tray integracijom.
    """
    
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.app = kwargs.get('app', None)
        if self.app is None and parent and hasattr(parent, 'app'):
            self.app = parent.app
        
        # Timer state
        self.is_active = False
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.action = "stop"  # "stop" ili "quit"
        
        # QTimer za countdown
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)
        
        # Tray action reference (biće kreiran kasnije)
        self.tray_action = None
        
        print("✅ SleepTimerWidget initialized")
    
    def start_timer(self, duration_minutes: int, action: str):
        """
        Start sleep timer.
        
        Args:
            duration_minutes: Duration in minutes
            action: "stop" or "quit"
        """
        self.total_seconds = duration_minutes * 60
        self.remaining_seconds = self.total_seconds
        self.action = action
        self.is_active = True
        
        # Start QTimer every 1 second
        self.timer.start(1000)
        
        # Add to tray menu
        self._add_to_tray_menu()
        
        # Show notification
        action_text = "stop playback" if action == "stop" else "quit player"
        self._show_notification(
            "⏰ Sleep Timer Started",
            f"Player will {action_text} in {duration_minutes} min."
        )
        
        print(f"⏰ Sleep timer started: {duration_minutes} min, action: {action}")
    
    def cancel_timer(self):
        """Cancel active timer"""
        if not self.is_active:
            return
        
        self.is_active = False
        self.timer.stop()
        
        # Remove from tray menu
        self._remove_from_tray_menu()
        
        # Notification
        self._show_notification(
            "⏰ Sleep Timer Cancelled",
            "Timer has been cancelled."
        )
        
        print("⏰ Sleep timer cancelled")
    
    def _on_timer_tick(self):
        """Poziva se svake sekunde"""
        if not self.is_active:
            return
        
        self.remaining_seconds -= 1
        
        # Ažuriraj tray text
        self._update_tray_text()
        
        # Proveri da li je vreme isteklo
        if self.remaining_seconds <= 0:
            self._timer_expired()
            return
        
        # Notifications at certain intervals
        remaining_minutes = self.remaining_seconds // 60
        
        # Notification at 5, 1 minute
        if self.remaining_seconds == 5 * 60:  # 5 minutes
            self._show_notification(
                "⏰ Sleep Timer",
                "Remaining: 5 minutes"
            )
        elif self.remaining_seconds == 1 * 60:  # 1 minute
            self._show_notification(
                "⏰ Sleep Timer",
                "Remaining: 1 minute"
            )
    
    def _timer_expired(self):
        """Timer has expired - execute action"""
        self.is_active = False
        self.timer.stop()
        
        action_text = "Stopping playback" if self.action == "stop" else "Quitting player"
        
        # Notification
        self._show_notification(
            "⏰ Sleep Timer Expired",
            action_text
        )
        
        # Remove from tray
        self._remove_from_tray_menu()
        
        # Execute action
        if self.action == "stop":
            self._stop_playback()
        elif self.action == "quit":
            self._quit_application()
        
        print(f"⏰ Sleep timer expired, action: {self.action}")
    
    def _stop_playback(self):
        """Zaustavi reprodukciju"""
        try:
            if self.app and hasattr(self.app, 'engine'):
                self.app.engine.stop()
                print("⏹️ Playback stopped by sleep timer")
        except Exception as e:
            print(f"⚠️ Error stopping playback: {e}")
    
    def _quit_application(self):
        """Ugasi aplikaciju"""
        try:
            if self.app:
                # Sačekaj malo pre gašenja
                QTimer.singleShot(2000, self.app.quit)
                print("❌ Application will quit in 2 seconds")
        except Exception as e:
            print(f"⚠️ Error quitting application: {e}")
    
    def _add_to_tray_menu(self):
        """Dodaj timer status u tray menu"""
        try:
            # Dobij tray menu
            tray = self._get_tray()
            if not tray or not hasattr(tray, '_menu_manager'):
                return
            
            menu = tray._menu_manager.menu
            
            # Kreiraj akciju za timer
            self.tray_action = QAction("⏰ Sleep Timer Active")
            self.tray_action.triggered.connect(self.cancel_timer)
            
            # Dodaj nakon separatora, pre Show Window
            actions = menu.actions()
            # Pronađi "Show Window" akciju
            show_action = None
            for action in actions:
                if "Show" in action.text() or "Window" in action.text():
                    show_action = action
                    break
            
            if show_action:
                menu.insertAction(show_action, self.tray_action)
                menu.insertSeparator(show_action)
            else:
                # Dodaj na kraj ako nema Show action
                menu.addSeparator()
                menu.addAction(self.tray_action)
            
            self._update_tray_text()
            
            print("✅ Timer added to tray menu")
            
        except Exception as e:
            print(f"⚠️ Error adding timer to tray: {e}")
    
    def _remove_from_tray_menu(self):
        """Ukloni timer iz tray menija"""
        try:
            if self.tray_action:
                tray = self._get_tray()
                if tray and hasattr(tray, '_menu_manager'):
                    menu = tray._menu_manager.menu
                    menu.removeAction(self.tray_action)
                    self.tray_action = None
                    print("✅ Timer removed from tray menu")
        except Exception as e:
            print(f"⚠️ Error removing timer from tray: {e}")
    
    def _update_tray_text(self):
        """Update text in tray menu"""
        if not self.tray_action:
            return
        
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        
        action_icon = "⏹️" if self.action == "stop" else "❌"
        
        text = f"⏰ Sleep Timer: {minutes:02d}:{seconds:02d} {action_icon} (click to cancel)"
        self.tray_action.setText(text)
    
    def _get_tray(self):
        """Dobij tray icon instancu"""
        try:
            if self.app and hasattr(self.app, 'tray_icon'):
                return self.app.tray_icon
            elif self.parent and hasattr(self.parent, 'app'):
                if hasattr(self.parent.app, 'tray_icon'):
                    return self.parent.app.tray_icon
        except Exception as e:
            print(f"⚠️ Error getting tray: {e}")
        return None
    
    def _show_notification(self, title: str, message: str):
        """Prikaži sistem notifikaciju"""
        try:
            tray = self._get_tray()
            if tray:
                tray.show_message(title, message, 3000)
        except Exception as e:
            print(f"⚠️ Error showing notification: {e}")


# ===== PLUGIN EXPORTS =====

# Export klasa za plugin manager
EqualizerDialog = None  # Nema equalizer dialog
EqualizerWidget = None  # Nema equalizer widget

SleepTimerDialog = SleepTimerDialog
SleepTimerWidget = SleepTimerWidget


if __name__ == "__main__":
    """Test sleep timer dialog"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = SleepTimerDialog()
    
    def on_timer_started(minutes, action):
        print(f"Timer started: {minutes} min, action: {action}")
    
    dialog.timer_started.connect(on_timer_started)
    dialog.exec()
    
    sys.exit(app.exec())