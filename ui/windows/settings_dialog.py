# -*- coding: utf-8 -*-
# ui/windows/settings_dialog.py
"""
Settings dialog - SA Audio Backend opcijama, Player Style, About i Plugins tabovima

Kompletan settings dialog za AudioWave Player.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QComboBox, QCheckBox, QSlider,
    QGroupBox, QFormLayout, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QDesktopServices, QCursor
from PyQt6.QtCore import QUrl
import subprocess
import shutil

# Import About konstanti
try:
    from ui.dialogs.about import (
        APP_NAME, APP_VERSION, APP_DESCRIPTION,
        AUTHOR_NAME, AUTHOR_GITHUB, PROJECT_URL,
        LICENSE, COPYRIGHT_YEAR
    )
except ImportError:
    APP_NAME = "AudioWave"
    APP_VERSION = "0.3.0"
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

# Import Engine Factory za ÄÂuvanje preferencije
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


# ===== AUDIO BACKEND DETEKCIJA =====

def detect_available_backends():
    """
    Detektuje dostupne audio backend-ove na sistemu.
    VraÄâ€¡a dict sa statusom svakog backend-a.
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
            self.config_btn.setFixedWidth(80)
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
        
        self.setup_ui()
        # ✓ REPLACED: Theme-aware styling instead of hardcoded dark
        self.apply_theme_stylesheet()
        
        # ✓ NOVO: UÄÂitaj saÄÂuvanu preferenciju audio backend-a
        self._load_saved_backend_preference()
        
    def setup_ui(self):
        self.setWindowTitle(f"{APP_NAME} Settings")
        self.setMinimumSize(600, 580)
        
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
        ✓ NOVO: UÄÂitaj saÄÂuvanu preferenciju audio backend-a i postavi combo box
        """
        try:
            saved_backend = load_engine_preference()
            print(f"[Settings] Loading saved backend preference: {saved_backend}")
            
            # PronaÄâ€˜i index u combo box-u po data vrednosti
            for i in range(self.backend_combo.count()):
                if self.backend_combo.itemData(i) == saved_backend:
                    self.backend_combo.setCurrentIndex(i)
                    print(f"✓ [Settings] Backend combo set to index {i}: {saved_backend}")
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
        group_player = QGroupBox("Player Style")
        form_player = QFormLayout(group_player)
        
        self.player_style_combo = QComboBox()
        self.player_style_combo.addItems(["Modern", "Vinyl Player", "Wave Form", "Minimal Zen"])
        
        if hasattr(self.parent_window, 'player_window') and self.parent_window.player_window:
            current_style = getattr(self.parent_window.player_window, 'player_style', 'Modern')
            index = self.player_style_combo.findText(current_style)
            if index >= 0:
                self.player_style_combo.setCurrentIndex(index)
        
        form_player.addRow("Visual Style:", self.player_style_combo)
        layout.addWidget(group_player)
        
        # UI Options
        group_ui = QGroupBox("UI Options")
        form_ui = QFormLayout(group_ui)
        
        self.animations_check = QCheckBox("Enable animations")
        self.animations_check.setChecked(True)
        
        self.compact_check = QCheckBox("Compact layout")
        
        form_ui.addRow(self.animations_check)
        form_ui.addRow(self.compact_check)
        
        layout.addWidget(group_ui)
        layout.addStretch()
        
        return tab
    
    def preview_theme(self, theme_name):
        if self.theme_manager and self.parent_window:
            self.theme_manager.apply_theme(self.parent_window, theme_name)
    
    def create_audio_tab(self):
        """Audio settings sa backend selekcijom"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # ===== AUDIO BACKEND =====
        group_backend = QGroupBox("Audio Output Backend")
        backend_layout = QVBoxLayout(group_backend)
        
        # Info label
        info_label = QLabel(
            "Select audio backend. GStreamer and PipeWire support real-time EQ.\n"
            "Restart required after changing backend."
        )
        info_label.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
        info_label.setWordWrap(True)
        backend_layout.addWidget(info_label)
        
        # Backend combo
        backend_form = QFormLayout()
        
        self.backend_combo = QComboBox()
        self.backend_combo.setMinimumWidth(250)
        
        # Dodaj dostupne backend-ove
        for backend_id, info in self.available_backends.items():
            status = "✓" if info["available"] else "✗"
            eq_status = "" if info["has_eq"] else ""
            display_text = f"{info['icon']} {info['name']} {eq_status} {status}"
            self.backend_combo.addItem(display_text, backend_id)
            
            # Disable ako nije dostupan
            if not info["available"]:
                index = self.backend_combo.count() - 1
                self.backend_combo.model().item(index).setEnabled(False)
        
        self.backend_combo.currentIndexChanged.connect(self._on_backend_changed)
        backend_form.addRow("Output:", self.backend_combo)
        
        backend_layout.addLayout(backend_form)
        
        # Backend opis
        self.backend_desc_label = QLabel()
        self.backend_desc_label.setStyleSheet(
            "background: rgba(102, 126, 234, 0.1); "
            "border-radius: 6px; padding: 10px; margin-top: 5px;"
        )
        self.backend_desc_label.setWordWrap(True)
        backend_layout.addWidget(self.backend_desc_label)
        
        # AÅ¾uriraj opis
        self._on_backend_changed(0)
        
        layout.addWidget(group_backend)
        
        # ===== VOLUME =====
        group_volume = QGroupBox("Volume")
        form_volume = QFormLayout(group_volume)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        
        self.volume_label = QLabel("70%")
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        
        self.remember_volume_check = QCheckBox("Remember last volume")
        self.remember_volume_check.setChecked(True)
        
        form_volume.addRow("Default volume:", self.volume_slider)
        form_volume.addRow("", self.volume_label)
        form_volume.addRow(self.remember_volume_check)
        
        layout.addWidget(group_volume)
        
        # ===== AUDIO DEVICES =====
        group_devices = QGroupBox("Output Device")
        devices_form = QFormLayout(group_devices)
        
        self.device_combo = QComboBox()
        self.device_combo.addItem("System Default")
        
        # TODO: Popuni sa stvarnim ureÄ‘ajima iz backend-a
        
        self.refresh_devices_btn = QPushButton("Refresh")
        self.refresh_devices_btn.setFixedWidth(80)
        self.refresh_devices_btn.clicked.connect(self._refresh_audio_devices)
        
        device_row = QHBoxLayout()
        device_row.addWidget(self.device_combo, 1)
        device_row.addWidget(self.refresh_devices_btn)
        
        devices_form.addRow("Device:", device_row)
        
        layout.addWidget(group_devices)
        
        layout.addStretch()
        
        return tab
    
    def _on_backend_changed(self, index):
        """Kada se promeni audio backend"""
        backend_id = self.backend_combo.currentData()
        if backend_id and backend_id in self.available_backends:
            info = self.available_backends[backend_id]
            
            eq_text = "✓ Equalizer supported" if info["has_eq"] else "✗ No EQ support"
            status_text = "Available" if info["available"] else "Not installed"
            
            self.backend_desc_label.setText(
                f"<b>{info['name']}</b><br>"
                f"{info['description']}<br><br>"
                f"{eq_text}<br>"
                f"Status: {status_text}"
            )
    
    def _refresh_audio_devices(self):
        """OsveÅ¾i listu audio ureÄ‘aja"""
        # TODO: Implementirati za svaki backend
        QMessageBox.information(
            self, "Refresh Devices",
            "Device list refreshed.\n\n"
            "Note: Full device enumeration requires\n"
            "the selected audio backend to be active."
        )
    
    def create_playback_tab(self):
        """Playback settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        group = QGroupBox("Playback Options")
        form = QFormLayout(group)
        
        self.autoplay_check = QCheckBox("Auto-play on startup")
        self.autoplay_check.setChecked(True)
        
        self.shuffle_check = QCheckBox("Shuffle playback")
        
        self.loop_combo = QComboBox()
        self.loop_combo.addItems(["Off", "Track", "Playlist"])
        self.loop_combo.setCurrentText("Playlist")
        
        self.crossfade_check = QCheckBox("Crossfade between tracks")
        
        self.crossfade_slider = QSlider(Qt.Orientation.Horizontal)
        self.crossfade_slider.setRange(0, 10)
        self.crossfade_slider.setValue(3)
        self.crossfade_slider.setEnabled(False)
        self.crossfade_check.toggled.connect(self.crossfade_slider.setEnabled)
        
        form.addRow(self.autoplay_check)
        form.addRow(self.shuffle_check)
        form.addRow("Loop mode:", self.loop_combo)
        form.addRow(self.crossfade_check)
        form.addRow("Crossfade (sec):", self.crossfade_slider)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return tab
    
    def create_plugins_tab(self):
        """Plugins settings"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        header_label = QLabel("Manage Plugins")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Scroll area za pluginove
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)
        
        if self.plugin_manager:
            for plugin_info in self.plugin_manager.get_all_plugins():
                card = PluginCard(plugin_info)
                card.toggled.connect(self._on_plugin_toggled)
                card.configure_clicked.connect(self._on_plugin_configure)
                self.plugin_cards[plugin_info.id] = card
                scroll_layout.addWidget(card)
        else:
            no_plugins_label = QLabel("Plugin manager not available")
            no_plugins_label.setStyleSheet("color: #888; font-style: italic;")
            scroll_layout.addWidget(no_plugins_label)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        
        layout.addWidget(scroll, 1)
        
        return tab
    
    def _on_plugin_toggled(self, plugin_id: str, enabled: bool):
        """Kada se plugin ukljuÄÂi/iskljuÄÂi"""
        if self.plugin_manager:
            if enabled:
                self.plugin_manager.enable_plugin(plugin_id)
            else:
                self.plugin_manager.disable_plugin(plugin_id)
    
    def _on_plugin_configure(self, plugin_id: str):
        """Kada se klikne Configure na plugin"""
        if self.plugin_manager:
            plugin_info = self.plugin_manager.get_plugin(plugin_id)
            if plugin_info and plugin_info.dialog_class:
                dialog = plugin_info.dialog_class(self.parent_window)
                dialog.exec()
    
    def create_about_tab(self):
        """About tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Logo/Title
        title_label = QLabel(f"{APP_NAME}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title_label)
        
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #667eea; font-size: 14px;")
        layout.addWidget(version_label)
        
        desc_label = QLabel(APP_DESCRIPTION)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #888; margin: 10px 0;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Info
        info_group = QGroupBox("Information")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)
        
        info_layout.addRow("Author:", QLabel(AUTHOR_NAME))
        info_layout.addRow("License:", QLabel(LICENSE))
        info_layout.addRow("© Copyright:", QLabel(f"{COPYRIGHT_YEAR} {AUTHOR_NAME}"))
        
        layout.addWidget(info_group)
        
        # Links
        links_layout = QHBoxLayout()
        links_layout.setSpacing(10)
        
        github_btn = QPushButton("GitHub")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(AUTHOR_GITHUB)))
        links_layout.addWidget(github_btn)
        
        project_btn = QPushButton("Project Page")
        project_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        project_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL)))
        links_layout.addWidget(project_btn)
        
        layout.addLayout(links_layout)
        layout.addStretch()
        
        tech_label = QLabel("Built with Python 3.11+ | PyQt6 | Mutagen")
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(tech_label)
        
        return tab
    
    def restore_defaults(self):
        """Restore defaults"""
        if self.theme_manager:
            index = self.theme_combo.findText("Dark Modern")
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
        
        self.player_style_combo.setCurrentText("Modern")
        self.animations_check.setChecked(True)
        self.compact_check.setChecked(False)
        self.autoplay_check.setChecked(True)
        self.shuffle_check.setChecked(False)
        self.loop_combo.setCurrentText("Playlist")
        self.volume_slider.setValue(70)
        self.remember_volume_check.setChecked(True)
        self.backend_combo.setCurrentIndex(0)
    
    def collect_settings(self):
        """Collect all settings"""
        return {
            "appearance": {
                "theme": self.theme_combo.currentText(),
                "player_style": self.player_style_combo.currentText(),
                "animations": self.animations_check.isChecked(),
                "compact_layout": self.compact_check.isChecked()
            },
            "audio": {
                "backend": self.backend_combo.currentData(),
                "default_volume": self.volume_slider.value(),
                "remember_volume": self.remember_volume_check.isChecked()
            },
            "playback": {
                "autoplay": self.autoplay_check.isChecked(),
                "shuffle": self.shuffle_check.isChecked(),
                "loop_mode": self.loop_combo.currentText().lower()
            },
            "plugins": {}
        }
    
    def apply_settings(self):
        """Apply settings"""
        settings = self.collect_settings()
        
        # Primeni temu
        if self.theme_manager and self.parent_window:
            self.theme_manager.apply_theme(self.parent_window, settings["appearance"]["theme"])
        
        # Primeni player style
        if hasattr(self.parent_window, 'player_window') and self.parent_window.player_window:
            self.parent_window.player_window.set_player_style(settings["appearance"]["player_style"])
        
        # Primeni volume
        if hasattr(self.parent_window, 'engine') and self.parent_window.engine:
            self.parent_window.engine.set_volume(settings["audio"]["default_volume"])
        
        # âœ… Proveri da li se backend ZAISTA promenio
        current_backend = settings["audio"]["backend"]
        previous_backend = load_engine_preference()
        
        print(f"[CHECK] [Settings] Checking backend change:")
        print(f"   Current:  {current_backend}")
        print(f"   Previous: {previous_backend}")
        print(f"   Changed:  {current_backend != previous_backend}")
        
        if current_backend and current_backend != previous_backend:
            # Backend se promenio - saÄuvaj i prikaÅ¾i poruku
            save_engine_preference(current_backend)
            print(f"[SAVE] [Settings] Audio backend changed: {previous_backend} â†’ {current_backend}")
            
            QMessageBox.information(
                self, "Backend Changed",
                f"Audio backend set to: {current_backend}\n\n"
                "Please restart the application for the change to take effect."
            )
        elif current_backend:
            # Backend isti kao pre - samo logujem
            print(f"â„¹ï¸ [Settings] Audio backend unchanged: {current_backend}")
        
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
            print(f"✓ [SettingsDialog] Theme applied: {theme_name} (is_dark={is_dark})")
        
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

def show_settings(parent=None):
    dialog = SettingsDialog(parent)
    dialog.exec()