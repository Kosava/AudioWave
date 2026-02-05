# -*- coding: utf-8 -*-
# ui/windows/settings_dialog.py
"""
Settings dialog - SA Audio Backend opcijama, Player Style, About i Plugins tabovima

Kompletan settings dialog za AudioWave Player.

NOVE OPCIJE:
✅ Minimize to tray on close (checkbox u Playback tabu)
✅ Resume playback position (checkbox u Playback tabu)
✅ Keyboard Shortcuts kartica - pregled svih prečica
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QComboBox, QCheckBox, QSlider,
    QGroupBox, QFormLayout, QFrame, QScrollArea, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtCore import QUrl
import subprocess
import shutil

# Import About konstanti - samo za fallback ako AboutWidget ne postoji
try:
    from ui.dialogs.about import (
        APP_NAME, APP_VERSION, APP_DESCRIPTION,
        AUTHOR_NAME, AUTHOR_GITHUB, PROJECT_URL,
        LICENSE, COPYRIGHT_YEAR
    )
except ImportError:
    APP_NAME = "AudioWave"
    APP_VERSION = "0.3.5"
    APP_DESCRIPTION = "Modern desktop music player with theme support"
    AUTHOR_NAME = "Košava"
    AUTHOR_GITHUB = "https://github.com/Kosava"
    PROJECT_URL = "https://github.com/Kosava/AudioWave"
    LICENSE = "MIT License"
    COPYRIGHT_YEAR = "2025"

# Import Plugin Manager
try:
    from plugins.plugin_manager import get_plugin_manager
    PLUGIN_MANAGER_AVAILABLE = True
except ImportError:
    PLUGIN_MANAGER_AVAILABLE = False

# Import Engine Factory za čuvanje preferencije
try:
    from core.engine_factory import (
        save_engine_preference, 
        load_engine_preference,
        check_engine_availability
    )
    ENGINE_FACTORY_AVAILABLE = True
except ImportError:
    ENGINE_FACTORY_AVAILABLE = False
    def save_engine_preference(engine_id):
        pass
    def load_engine_preference():
        return "qt_multimedia"
    def check_engine_availability(engine_id):
        return engine_id == "qt_multimedia"

# Import Config za tray i resume settings
try:
    from core.config import Config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    class Config:
        def __init__(self): pass
        def get_tray_settings(self): return {"minimize_to_tray": True}
        def set_tray_settings(self, s): pass
        def is_resume_playback_enabled(self): return False
        def set_resume_playback_enabled(self, e): pass


# ===== AUDIO BACKEND DETEKCIJA =====

def detect_available_backends():
    """
    Detektuje dostupne audio backend-ove na sistemu.
    Vraća dict sa statusom svakog backend-a.
    """
    backends = {
        "qt_multimedia": {
            "name": "Qt Multimedia",
            "available": True,  # Uvek dostupan jer koristimo PyQt6
            "has_eq": False,
            "description": "Default Qt6 audio (no EQ support)",
            "icon": ""
        },
        "gstreamer": {
            "name": "GStreamer",
            "available": False,
            "has_eq": True,
            "description": "Full EQ support via equalizer-10bands",
            "icon": ""
        },
        "pipewire": {
            "name": "PipeWire",
            "available": False,
            "has_eq": True,
            "description": "Modern Linux audio with filter-chain EQ",
            "icon": ""
        },
        "pulseaudio": {
            "name": "PulseAudio",
            "available": False,
            "has_eq": True,
            "description": "Linux audio with pulseeffects EQ",
            "icon": ""
        },
        "jack": {
            "name": "JACK",
            "available": False,
            "has_eq": True,
            "description": "Professional low-latency audio",
            "icon": ""
        },
        "null": {
            "name": "Null Output",
            "available": True,
            "has_eq": False,
            "description": "Silent output for testing",
            "icon": ""
        }
    }
    
    # Proveri GStreamer
    try:
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import Gst
        Gst.init(None)
        backends["gstreamer"]["available"] = True
    except:
        pass
    
    # Proveri PipeWire
    if shutil.which("pw-cli") or shutil.which("pipewire"):
        backends["pipewire"]["available"] = True
        # Dodatno proveri Python biblioteku
        try:
            import pipewire_python
            backends["pipewire"]["description"] += " (Python API ready)"
        except:
            backends["pipewire"]["description"] += " (CLI only)"
    
    # Proveri PulseAudio
    if shutil.which("pactl") or shutil.which("pulseaudio"):
        backends["pulseaudio"]["available"] = True
        try:
            import pulsectl
            backends["pulseaudio"]["description"] += " (Python API ready)"
        except:
            pass
    
    # Proveri JACK
    if shutil.which("jackd") or shutil.which("jack_control"):
        backends["jack"]["available"] = True
        try:
            import jack
            backends["jack"]["description"] += " (Python API ready)"
        except:
            pass
    
    return backends


class PluginCard(QFrame):
    """Kartica za jedan plugin u Settings-u."""
    
    toggled = pyqtSignal(str, bool)
    configure_clicked = pyqtSignal(str)
    
    def __init__(self, plugin_info, parent=None):
        super().__init__(parent)
        self.plugin_info = plugin_info
        self.setup_ui()
    
    def setup_ui(self):
        self.setObjectName("pluginCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            #pluginCard {
                background-color: rgba(102, 126, 234, 0.1);
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 8px;
            }
            #pluginCard:hover {
                background-color: rgba(102, 126, 234, 0.15);
                border-color: rgba(102, 126, 234, 0.5);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Ikona - SVG umesto emoji
        from ui.utils.svg_icon_manager import get_icon
        
        # Mapiranje plugin ID-eva na SVG ikone
        icon_map = {
            'equalizer': 'equalizer_icon',
            'lyrics': 'lyrics_icon',
            'notifications': 'notification_icon',
            'discord': 'discord_icon',
            'scrobbler': 'scrobbler_icon',
            'visualizer': 'visualizer_icon',
            'statistics': 'stats_icon',
            'shortcuts': 'shortcuts_icon',
            'themes': 'theme_icon',
        }
        
        icon_name = icon_map.get(self.plugin_info.id, 'plugin')
        svg_icon = get_icon(icon_name, "#667eea", 32)
        
        icon_label = QLabel()
        icon_label.setPixmap(svg_icon.pixmap(32, 32))
        icon_label.setFixedWidth(40)
        layout.addWidget(icon_label)
        
        # Info sekcija
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(self.plugin_info.name)
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent;")
        info_layout.addWidget(name_label)
        
        desc_label = QLabel(self.plugin_info.description)
        desc_label.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        meta_text = f"v{self.plugin_info.version}"
        if self.plugin_info.shortcut:
            meta_text += f" | {self.plugin_info.shortcut}"
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        info_layout.addWidget(meta_label)
        
        layout.addLayout(info_layout, 1)
        
        # Kontrole
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(5)
        
        self.enable_check = QCheckBox("Enable")
        self.enable_check.setChecked(self.plugin_info.enabled)
        self.enable_check.toggled.connect(self._on_toggled)
        controls_layout.addWidget(self.enable_check)
        
        if self.plugin_info.has_dialog and self.plugin_info.dialog_class:
            self.config_btn = QPushButton("Configure")
            self.config_btn.setFixedWidth(100)
            self.config_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.config_btn.clicked.connect(self._on_configure)
            self.config_btn.setEnabled(self.plugin_info.enabled)
            controls_layout.addWidget(self.config_btn)
        
        layout.addLayout(controls_layout)
    
    def _on_toggled(self, checked: bool):
        self.toggled.emit(self.plugin_info.id, checked)
        if hasattr(self, 'config_btn'):
            self.config_btn.setEnabled(checked)
    
    def _on_configure(self):
        self.configure_clicked.emit(self.plugin_info.id)


class SettingsDialog(QDialog):
    """Settings dialog sa svim opcijama"""
    
    settings_saved = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.plugin_cards = {}
        self.available_backends = detect_available_backends()
        
        # Cache za plugin dialoge/prozore da se ne kreiraju uvek iznova
        self.plugin_dialogs = {}
        
        # Get app reference
        if hasattr(parent, 'app'):
            self.app = parent.app
        else:
            self.app = None
        
        # Theme manager
        if hasattr(parent, 'app') and hasattr(parent.app, 'theme_manager'):
            self.theme_manager = parent.app.theme_manager
        else:
            self.theme_manager = None
        
        # Plugin manager
        if PLUGIN_MANAGER_AVAILABLE:
            self.plugin_manager = get_plugin_manager()
        else:
            self.plugin_manager = None
        
        # ✅ FIX: koristi ISTU config instancu iz aplikacije
        if hasattr(parent, 'app') and hasattr(parent.app, 'config'):
            self.config = parent.app.config
        else:
            self.config = None
        
        self.setup_ui()
        # ✅ REPLACED: Theme-aware styling instead of hardcoded dark
        self.apply_theme_stylesheet()
        
        # ✅ NOVO: Učitaj sačuvanu preferenciju audio backend-a
        self._load_saved_backend_preference()
        
    def setup_ui(self):
        self.setWindowTitle(f"{APP_NAME} Settings")
        self.setMinimumSize(650, 600)
        
        layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        
        # ===== TABOVI SA SVG IKONAMA =====
        from ui.utils.svg_icon_manager import get_icon
        
        # Appearance tab
        appearance_tab = self.create_appearance_tab()
        appearance_icon = get_icon('palette', "#667eea", 16)
        self.tab_widget.addTab(appearance_tab, appearance_icon, "Appearance")
        
        # Audio tab
        audio_tab = self.create_audio_tab()
        audio_icon = get_icon('speaker', "#667eea", 16)
        self.tab_widget.addTab(audio_tab, audio_icon, "Audio")
        
        # Playback tab
        playback_tab = self.create_playback_tab()
        playback_icon = get_icon('play_circle', "#667eea", 16)
        self.tab_widget.addTab(playback_tab, playback_icon, "Playback")
        
        # ✅ NOVO: Keyboard Shortcuts tab
        shortcuts_tab = self.create_shortcuts_tab()
        shortcuts_icon = get_icon('keyboard', "#667eea", 16)
        self.tab_widget.addTab(shortcuts_tab, shortcuts_icon, "Shortcuts")
        
        # Plugins tab
        plugins_tab = self.create_plugins_tab()
        plugins_icon = get_icon('plugin', "#667eea", 16)
        self.tab_widget.addTab(plugins_tab, plugins_icon, "Plugins")
        
        # About tab
        about_tab = self.create_about_tab()
        about_icon = get_icon('info_circle', "#667eea", 16)
        self.tab_widget.addTab(about_tab, about_icon, "About")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        btn_defaults = QPushButton("Restore Defaults")
        btn_defaults.clicked.connect(self.restore_defaults)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self.apply_settings)
        
        button_layout.addWidget(btn_defaults)
        button_layout.addStretch()
        button_layout.addWidget(btn_cancel)
        button_layout.addWidget(btn_apply)
        
        layout.addLayout(button_layout)
    
    def _load_saved_backend_preference(self):
        """
        ✅ NOVO: Učitaj sačuvanu preferenciju audio backend-a i postavi combo box
        """
        try:
            saved_backend = load_engine_preference()
            print(f"[Settings] Loading saved backend preference: {saved_backend}")
            
            # Pronađi index u combo box-u po data vrednosti
            for i in range(self.backend_combo.count()):
                if self.backend_combo.itemData(i) == saved_backend:
                    self.backend_combo.setCurrentIndex(i)
                    print(f"✅ [Settings] Backend combo set to index {i}: {saved_backend}")
                    break
            else:
                print(f"[Settings] Saved backend '{saved_backend}' not found in combo, using default")
        except Exception as e:
            print(f"[Settings] Error loading backend preference: {e}")
    
    def create_appearance_tab(self):
        """Appearance settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Color Theme
        group_theme = QGroupBox("Color Theme")
        form_theme = QFormLayout(group_theme)
        
        self.theme_combo = QComboBox()
        if self.theme_manager:
            themes = self.theme_manager.get_available_themes()
            self.theme_combo.addItems(themes)
            current_theme = self.theme_manager.current_theme
            index = self.theme_combo.findText(current_theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            self.theme_combo.currentTextChanged.connect(self.preview_theme)
        else:
            self.theme_combo.addItems(["Dark Modern", "Ocean", "Cyberpunk"])
        
        form_theme.addRow("Color Theme:", self.theme_combo)
        layout.addWidget(group_theme)
        
        # Player Style
        group_style = QGroupBox("Player Style")
        form_style = QFormLayout(group_style)
        
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Modern Compact", "Classic Full", "Minimal"])
        
        # ✅ FIX: Koristi player_style atribut, ne current_style
        if hasattr(self.parent_window, 'player_window') and self.parent_window.player_window:
            if hasattr(self.parent_window.player_window, 'player_style'):
                current_style = self.parent_window.player_window.player_style
                index = self.style_combo.findText(current_style)
                if index >= 0:
                    self.style_combo.setCurrentIndex(index)
        
        form_style.addRow("Layout:", self.style_combo)
        layout.addWidget(group_style)
        
        layout.addStretch()
        return tab
    
    def create_audio_tab(self):
        """Audio settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Audio Backend Selection
        group_backend = QGroupBox("Audio Backend")
        form_backend = QFormLayout(group_backend)
        
        self.backend_combo = QComboBox()
        
        # Dodaj backend-ove u combo box
        for backend_id, info in self.available_backends.items():
            if info["available"]:
                display_name = f"{info['name']}"
                if info["has_eq"]:
                    display_name += " ✓ EQ"
                self.backend_combo.addItem(display_name, backend_id)
        
        # Postavi trenutni backend iz config-a
        try:
            current_backend = load_engine_preference()
            for i in range(self.backend_combo.count()):
                if self.backend_combo.itemData(i) == current_backend:
                    self.backend_combo.setCurrentIndex(i)
                    break
        except:
            pass
        
        # Status label
        self.backend_status = QLabel()
        self._update_backend_status()
        self.backend_combo.currentIndexChanged.connect(self._update_backend_status)
        
        form_backend.addRow("Engine:", self.backend_combo)
        form_backend.addRow("Status:", self.backend_status)
        
        layout.addWidget(group_backend)
        
        # Volume
        group_volume = QGroupBox("Volume Settings")
        form_volume = QFormLayout(group_volume)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self._update_volume_label)
        
        self.volume_label = QLabel("70%")
        
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        
        form_volume.addRow("Default Volume:", volume_layout)
        layout.addWidget(group_volume)
        
        layout.addStretch()
        return tab
    
    def create_playback_tab(self):
        """Playback settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Integration
        group_system = QGroupBox("System Integration")
        system_layout = QVBoxLayout(group_system)
        
        self.minimize_check = QCheckBox("Minimize to system tray on close")
        
        # ✅ NOVO: Učitaj trenutnu vrednost iz config-a
        if self.config:
            tray_settings = self.config.get_tray_settings()
            self.minimize_check.setChecked(tray_settings.get("minimize_to_tray", True))
        else:
            self.minimize_check.setChecked(True)
        
        self.minimize_check.setToolTip("When enabled, closing the window will minimize to tray instead of quitting")
        system_layout.addWidget(self.minimize_check)
        
        layout.addWidget(group_system)
        
        # Playback Behavior
        group_playback = QGroupBox("Playback Behavior")
        playback_layout = QVBoxLayout(group_playback)
        
        self.resume_check = QCheckBox("Resume playback position on startup")
        
        # ✅ NOVO: Učitaj trenutnu vrednost iz config-a
        if self.config:
            self.resume_check.setChecked(self.config.is_resume_playback_enabled())
        else:
            self.resume_check.setChecked(False)
        
        self.resume_check.setToolTip("Remember and restore playback position when app restarts")
        playback_layout.addWidget(self.resume_check)
        
        layout.addWidget(group_playback)
        
        layout.addStretch()
        return tab
    
    def create_shortcuts_tab(self):
        """
        ✅ NOVO: Keyboard Shortcuts tab - pregled svih prečica
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("🎹 Keyboard Shortcuts")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Info tekst
        info = QLabel("All available keyboard shortcuts for AudioWave Player:")
        info.setStyleSheet("color: #888; padding: 0 10px 10px 10px;")
        layout.addWidget(info)
        
        # Tabela prečica
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Shortcut", "Action", "Category"])
        
        # Definiši sve prečice
        shortcuts_data = [
            # Playback
            ("Space", "Play / Pause", "Playback"),
            ("Enter", "Play selected track", "Playback"),
            ("Esc", "Stop playback", "Playback"),
            ("M", "Toggle mute", "Playback"),
            
            # Navigation
            ("↑ / ↓", "Navigate playlist", "Navigation"),
            ("Alt + ↑", "Previous track", "Navigation"),
            ("Alt + ↓", "Next track", "Navigation"),
            ("← / →", "Seek ±5 seconds", "Navigation"),
            ("Ctrl + ← / →", "Seek ±10 seconds", "Navigation"),
            
            # Volume
            ("Ctrl + ↑ / ↓", "Volume ±5%", "Volume"),
            ("Alt + ↑ / ↓", "Volume ±10%", "Volume"),
            
            # Playlist
            ("Ctrl + A", "Select all tracks", "Playlist"),
            ("Del", "Remove selected tracks", "Playlist"),
            ("Ctrl + O", "Open files", "Playlist"),
            ("Ctrl + L", "Clear playlist", "Playlist"),
            ("F2", "Toggle playlist visibility", "Playlist"),
            ("F5", "Refresh playlist", "Playlist"),
            
            # Plugins
            ("F3 / Ctrl + E", "Open Equalizer", "Plugins"),
            ("F4", "Open Lyrics", "Plugins"),
            ("F7", "Sleep Timer", "Plugins"),
            ("Ctrl + P", "Plugin settings", "Plugins"),
            
            # Other
            ("Ctrl + S", "Open Settings", "Other"),
            ("F1", "About AudioWave", "Other"),
            ("Ctrl + H", "Show shortcuts (this)", "Other"),
            ("Ctrl + Q", "Quit application", "Other"),
        ]
        
        # Popuni tabelu
        table.setRowCount(len(shortcuts_data))
        
        for row, (shortcut, action, category) in enumerate(shortcuts_data):
            # Shortcut kolona
            shortcut_item = QTableWidgetItem(shortcut)
            shortcut_item.setFont(QFont("Monospace", 10, QFont.Weight.Bold))
            table.setItem(row, 0, shortcut_item)
            
            # Action kolona
            action_item = QTableWidgetItem(action)
            table.setItem(row, 1, action_item)
            
            # Category kolona
            category_item = QTableWidgetItem(category)
            category_item.setForeground(Qt.GlobalColor.gray)
            table.setItem(row, 2, category_item)
        
        # Stilizuj tabelu
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        
        # Resize kolone
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        table.verticalHeader().setVisible(False)
        
        layout.addWidget(table)
        
        # Footer note
        footer = QLabel("💡 Tip: Most shortcuts work globally when the player window is focused.")
        footer.setStyleSheet("color: #888; padding: 10px; font-style: italic;")
        layout.addWidget(footer)
        
        return tab
    
    def create_plugins_tab(self):
        """Plugins tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header_label = QLabel("🔌 Installed Plugins")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header_label)
        
        # Scroll area za plugin kartice
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        plugins_widget = QWidget()
        plugins_layout = QVBoxLayout(plugins_widget)
        plugins_layout.setSpacing(10)
        
        if self.plugin_manager:
            plugins = self.plugin_manager.get_all_plugins()
            
            if plugins:
                for plugin_info in plugins:
                    card = PluginCard(plugin_info, self)
                    card.toggled.connect(self._on_plugin_toggled)
                    card.configure_clicked.connect(self._on_plugin_configure)
                    self.plugin_cards[plugin_info.id] = card
                    plugins_layout.addWidget(card)
            else:
                no_plugins = QLabel("No plugins installed")
                no_plugins.setStyleSheet("color: #888; padding: 20px;")
                plugins_layout.addWidget(no_plugins)
        else:
            error_label = QLabel("❌ Plugin system not available")
            error_label.setStyleSheet("color: #ff6b6b; padding: 20px;")
            plugins_layout.addWidget(error_label)
        
        plugins_layout.addStretch()
        scroll.setWidget(plugins_widget)
        layout.addWidget(scroll)
        
        return tab
    
    def create_about_tab(self):
        """About tab - koristi postojeći AboutWidget iz about.py"""
        from ui.dialogs.about import AboutWidget
        return AboutWidget(self)
    
    def _update_backend_status(self):
        """Update backend status label"""
        backend_id = self.backend_combo.currentData()
        if backend_id and backend_id in self.available_backends:
            info = self.available_backends[backend_id]
            status = f"✓ Available"
            if info["has_eq"]:
                status += " • Equalizer Support"
            self.backend_status.setText(status)
            self.backend_status.setStyleSheet("color: #4ade80;")
        else:
            self.backend_status.setText("⚠ Not available")
            self.backend_status.setStyleSheet("color: #ff6b6b;")
    
    def _update_volume_label(self, value):
        """Update volume label"""
        self.volume_label.setText(f"{value}%")
    
    def _on_plugin_toggled(self, plugin_id: str, enabled: bool):
        """Handle plugin toggle"""
        if self.plugin_manager:
            if enabled:
                self.plugin_manager.enable_plugin(plugin_id)
            else:
                self.plugin_manager.disable_plugin(plugin_id)
            print(f"✅ Plugin '{plugin_id}' {'enabled' if enabled else 'disabled'}")
    
    def _on_plugin_configure(self, plugin_id: str):
        """Open plugin configuration"""
        if self.plugin_manager:
            try:
                # Proveri da li već postoji keširani dialog/prozor
                if plugin_id in self.plugin_dialogs:
                    dialog = self.plugin_dialogs[plugin_id]
                    # Ako je QWidget (prozor), samo pokaži i podesi fokus
                    if isinstance(dialog, QWidget) and not isinstance(dialog, QDialog):
                        dialog.show()
                        dialog.raise_()
                        dialog.activateWindow()
                    # Ako je QDialog, exec() ponovo
                    else:
                        dialog.exec()
                    return
                
                # Kreiraj novi dialog/prozor
                dialog = self.plugin_manager.show_plugin_dialog(plugin_id, self.parent_window)
                
                # Keširaj ga za buduće otvaranje
                if dialog:
                    self.plugin_dialogs[plugin_id] = dialog
                    print(f"✅ Cached dialog for plugin '{plugin_id}'")
            except Exception as e:
                print(f"❌ Error opening plugin config: {e}")
                import traceback
                traceback.print_exc()
    
    def preview_theme(self, theme_name):
        """Preview selected theme"""
        if self.theme_manager:
            self.theme_manager.apply_theme(self.parent_window, theme_name)
    
    def restore_defaults(self):
        """Restore default settings"""
        reply = QMessageBox.question(
            self, "Restore Defaults",
            "Are you sure you want to restore all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.theme_combo.setCurrentIndex(0)
            self.style_combo.setCurrentIndex(0)
            self.volume_slider.setValue(70)
            self.minimize_check.setChecked(True)
            self.resume_check.setChecked(False)
    
    def apply_settings(self):
        """Apply and save settings"""
        settings = {
            "appearance": {
                "theme": self.theme_combo.currentText(),
                "player_style": self.style_combo.currentText()
            },
            "audio": {
                "backend": self.backend_combo.currentData(),
                "default_volume": self.volume_slider.value()
            },
            "playback": {
                "minimize_to_tray": self.minimize_check.isChecked(),
                "resume_playback": self.resume_check.isChecked()
            }
        }
        
        # Primeni temu
        if self.theme_manager:
            self.theme_manager.apply_theme(self.parent_window, settings["appearance"]["theme"])
        
        # Primeni player style
        if hasattr(self.parent_window, 'player_window') and self.parent_window.player_window:
            self.parent_window.player_window.set_player_style(settings["appearance"]["player_style"])
        
        # Primeni volume
        if hasattr(self.parent_window, 'engine') and self.parent_window.engine:
            self.parent_window.engine.set_volume(settings["audio"]["default_volume"])
        
        # ✅ NOVO: Sačuvaj tray settings
        if self.config:
            tray_settings = self.config.get_tray_settings()
            tray_settings["minimize_to_tray"] = settings["playback"]["minimize_to_tray"]
            # Takođe ažuriraj close_to_tray da bude isti
            tray_settings["close_to_tray"] = settings["playback"]["minimize_to_tray"]
            self.config.set_tray_settings(tray_settings, auto_save=False)
            
            # Ažuriraj i u parent window ako postoji
            if hasattr(self.parent_window, 'tray_settings'):
                self.parent_window.tray_settings = tray_settings
            
            print(f"✅ [Settings] Minimize to tray: {settings['playback']['minimize_to_tray']}")
        
        # ✅ NOVO: Sačuvaj resume playback
        if self.config:
            self.config.set_resume_playback_enabled(
                settings["playback"]["resume_playback"]
            )
            print(f"✅ [Settings] Resume playback: {settings['playback']['resume_playback']}")
        
        # ✅ Proveri da li se backend ZAISTA promenio
        current_backend = settings["audio"]["backend"]
        previous_backend = load_engine_preference()
        
        print(f"[CHECK] [Settings] Checking backend change:")
        print(f"   Current:  {current_backend}")
        print(f"   Previous: {previous_backend}")
        print(f"   Changed:  {current_backend != previous_backend}")
        
        if current_backend and current_backend != previous_backend:
            # Backend se promenio - sačuvaj i prikaži poruku
            save_engine_preference(current_backend)
            print(f"[SAVE] [Settings] Audio backend changed: {previous_backend} → {current_backend}")
            
            QMessageBox.information(
                self, "Backend Changed",
                f"Audio backend set to: {current_backend}\n\n"
                "Please restart the application for the change to take effect."
            )
        elif current_backend:
            # Backend isti kao pre - samo logujem
            print(f"✔️ [Settings] Audio backend unchanged: {current_backend}")
        
        # Sačuvaj sve promene
        if self.config:
            self.config.save()
        
        self.settings_saved.emit(settings)
        self.accept()
    
    def apply_theme_stylesheet(self):
        """Apply current theme to settings dialog - theme-aware for light/dark themes"""
        try:
            from core.themes.base_theme import StyleComponents
            from core.themes.theme_registry import ThemeRegistry
            
            # Get current theme
            if self.app and hasattr(self.app, 'config'):
                theme_name = self.app.config.get_theme()
            else:
                theme_name = "Dark Modern"
            
            theme = ThemeRegistry.get_theme(theme_name)
            is_dark = ThemeRegistry.is_dark_theme(theme_name)
            
            # Dynamic text color based on theme type
            text_color = "#ffffff" if is_dark else "#2e3440"
            
            # Generate theme-aware stylesheet
            stylesheet = StyleComponents.get_settings_dialog_stylesheet(
                primary=theme.primary,
                bg_main=theme.bg_main,
                bg_secondary=theme.bg_secondary,
                text_color=text_color,
                is_dark=is_dark
            )
            
            self.setStyleSheet(stylesheet)
            print(f"✅ [SettingsDialog] Theme applied: {theme_name} (is_dark={is_dark})")
        
        except Exception as e:
            print(f"[SettingsDialog] Could not apply theme: {e}")
            # Fallback to hardcoded dark theme
            self.apply_style_fallback()
    
    def apply_style_fallback(self):
        """Fallback styling if theme system fails"""
        """Primeni stil"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                color: #ffffff;
            }
            
            QTabWidget::pane {
                border: 1px solid #333;
                border-radius: 6px;
                background-color: #1a1a2e;
            }
            
            QTabBar::tab {
                background-color: #2a2a4a;
                color: #888;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            
            QTabBar::tab:selected {
                background-color: #667eea;
                color: #ffffff;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QComboBox {
                background-color: #2a2a4a;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 150px;
            }
            
            QComboBox:hover {
                border-color: #667eea;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2a2a4a;
                border: 1px solid #667eea;
                selection-background-color: #667eea;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #555;
            }
            
            QCheckBox::indicator:checked {
                background-color: #667eea;
                border-color: #667eea;
            }
            
            QSlider::groove:horizontal {
                background: #333;
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #667eea;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            
            QSlider::sub-page:horizontal {
                background: #667eea;
                border-radius: 3px;
            }
            
            QPushButton {
                background-color: #2a2a4a;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px 16px;
                color: #ffffff;
            }
            
            QPushButton:hover {
                background-color: #667eea;
                border-color: #667eea;
            }
            
            QTableWidget {
                background-color: #1a1a2e;
                alternate-background-color: #252540;
                gridline-color: #333;
                border: 1px solid #333;
                border-radius: 6px;
            }
            
            QTableWidget::item {
                padding: 8px;
            }
            
            QTableWidget::item:selected {
                background-color: #667eea;
                color: #ffffff;
            }
            
            QHeaderView::section {
                background-color: #2a2a4a;
                color: #ffffff;
                padding: 8px;
                border: none;
                border-right: 1px solid #333;
                border-bottom: 1px solid #333;
                font-weight: bold;
            }
        """)
    
    def show_about_tab(self):
        for i in range(self.tab_widget.count()):
            if "About" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                break
        self.exec()
    
    def show_plugins_tab(self):
        for i in range(self.tab_widget.count()):
            if "Plugins" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                break
        self.exec()
    
    def show_audio_tab(self):
        for i in range(self.tab_widget.count()):
            if "Audio" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                break
        self.exec()
    
    def show_shortcuts_tab(self):
        """✅ NOVO: Prikaži Shortcuts karticu"""
        for i in range(self.tab_widget.count()):
            if "Shortcuts" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                break
        self.exec()


# ===== HELPER FUNKCIJE =====

def show_about(parent=None):
    dialog = SettingsDialog(parent)
    dialog.show_about_tab()

def show_plugins(parent=None):
    dialog = SettingsDialog(parent)
    dialog.show_plugins_tab()

def show_audio_settings(parent=None):
    dialog = SettingsDialog(parent)
    dialog.show_audio_tab()

def show_shortcuts(parent=None):
    """✅ NOVO: Helper funkcija za prikaz Shortcuts taba"""
    dialog = SettingsDialog(parent)
    dialog.show_shortcuts_tab()

def show_settings(parent=None):
    dialog = SettingsDialog(parent)
    dialog.exec()