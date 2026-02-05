# -*- coding: utf-8 -*-
# plugins/plugin_manager.py
"""
Plugin Manager - Upravljanje pluginovima za AudioWave

OmoguÃ„â€¡ava:
- Registraciju pluginova
- OmoguÃ„â€¡avanje/onemoguÃ„â€¡avanje pluginova
- Ã„Å’uvanje stanja pluginova
- Context menu integraciju
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
import json
import os
import logging


@dataclass
class PluginInfo:
    """Informacije o pluginu"""
    id: str
    name: str
    description: str
    version: str
    author: str
    icon: str = "Ã°Å¸â€Å’"
    enabled: bool = False
    has_dialog: bool = True
    has_widget: bool = False
    has_context_menu: bool = False
    shortcut: str = ""
    dialog_class: Optional[type] = None
    widget_class: Optional[type] = None
    context_menu_items: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertuj PluginInfo u dict (bez klasa)"""
        data = asdict(self)
        # Ukloni reference na klase jer nisu JSON serializable
        data.pop('dialog_class', None)
        data.pop('widget_class', None)
        return data


class PluginManager(QObject):
    """
    Centralni manager za sve pluginove.
    """
    
    # Signali
    plugin_enabled = pyqtSignal(str)   # plugin_id
    plugin_disabled = pyqtSignal(str)  # plugin_id
    plugins_changed = pyqtSignal()
    
    # Signal za dodavanje radio stanice u playlist
    add_radio_to_playlist = pyqtSignal(str, str)  # (naziv, url)
    
    def __init__(self, config_path: str = None):
        super().__init__()
        
        self.plugins: Dict[str, PluginInfo] = {}
        self.config_path = config_path or os.path.expanduser("~/.audiowave/plugins.json")
        self.logger = logging.getLogger(__name__)
        
        # Registruj ugraÃ„â€˜ene pluginove
        self._register_builtin_plugins()
        
        # UÃ„Âitaj stanje
        self._load_state()
    
    def _register_builtin_plugins(self):
        """Registruj ugraÃ„â€˜ene pluginove"""
        
        # Equalizer plugin
        try:
            from plugins.equalizer.equalizer_plugin import EqualizerDialog, EqualizerWidget
            eq_dialog = EqualizerDialog
            eq_widget = EqualizerWidget
            self.logger.info("Equalizer plugin loaded successfully")
        except ImportError as e:
            eq_dialog = None
            eq_widget = None
            self.logger.warning(f"Equalizer plugin not found: {e}")
        
        self.register_plugin(PluginInfo(
            id="equalizer",
            name="Equalizer",
            description="10-band equalizer with presets",
            version="1.0.0",
            author="AudioWave",
            icon="Ã°Å¸Å½â€ºÃ¯Â¸Â",
            enabled=False,
            has_dialog=True,
            has_widget=True,
            has_context_menu=False,
            shortcut="F3",
            dialog_class=eq_dialog,
            widget_class=eq_widget,
        ))
        
        # Lyrics plugin
        try:
            from plugins.lyrics.lyrics_plugin import LyricsDialog, LyricsWidget
            lyrics_dialog = LyricsDialog
            lyrics_widget = LyricsWidget
            self.logger.info("Lyrics plugin loaded successfully")
        except ImportError as e:
            lyrics_dialog = None
            lyrics_widget = None
            self.logger.warning(f"Lyrics plugin not found: {e}")
        
        self.register_plugin(PluginInfo(
            id="lyrics",
            name="Lyrics",
            description="Search and display song lyrics",
            version="1.0.0",
            author="AudioWave",
            icon="Ã°Å¸Å½Â¤",
            enabled=False,
            has_dialog=True,
            has_widget=True,
            has_context_menu=True,
            shortcut="F4",
            dialog_class=lyrics_dialog,
            widget_class=lyrics_widget,
            context_menu_items=[
                {
                    "text": "Ã°Å¸Å½Â¤ Search Lyrics",
                    "action": "search_lyrics",
                    "separator_before": True,
                }
            ]
        ))
        
        # Visualizer plugin - ✅ IMPLEMENTIRAN!
        try:
            from plugins.visualizer.visualizer_plugin import VisualizerDialog, VisualizerWidget
            visualizer_dialog = VisualizerDialog
            visualizer_widget = VisualizerWidget
            self.logger.info("Visualizer plugin loaded successfully")
        except ImportError as e:
            visualizer_dialog = None
            visualizer_widget = None
            self.logger.warning(f"Visualizer plugin not found: {e}")
        
        self.register_plugin(PluginInfo(
            id="visualizer",
            name="Visualizer",
            description="Audio visualization effects (Spectrum, Waveform, Circular, Particles)",
            version="1.0.0",
            author="AudioWave",
            icon="🎵",
            enabled=False,
            has_dialog=True,
            has_widget=True,
            has_context_menu=False,
            shortcut="F6",
            dialog_class=visualizer_dialog,
            widget_class=visualizer_widget,
        ))

        
        # Sleep Timer plugin
        try:
            from plugins.sleeptimer.sleeptimer_plugin import SleepTimerDialog, SleepTimerWidget
            sleep_timer_dialog = SleepTimerDialog
            sleep_timer_widget = SleepTimerWidget
            self.logger.info("Sleep Timer plugin loaded successfully")
        except ImportError as e:
            sleep_timer_dialog = None
            sleep_timer_widget = None
            self.logger.warning(f"Sleep Timer plugin not found: {e}")
        
        self.register_plugin(PluginInfo(
            id="sleep_timer",
            name="Sleep Timer",
            description="Auto-stop or quit after specified time",
            version="1.0.0",
            author="AudioWave",
            icon="Ã¢ÂÂ°",
            enabled=False,
            has_dialog=True,
            has_widget=True,  # Widget je helper za timer management
            has_context_menu=False,
            shortcut="F7",
            dialog_class=sleep_timer_dialog,
            widget_class=sleep_timer_widget,
        ))
        
        # Theme Creator plugin
        try:
            from plugins.theme_creator.theme_creator_plugin import ThemeCreatorDialog, ThemeCreatorWidget
            theme_creator_dialog = ThemeCreatorDialog
            theme_creator_widget = ThemeCreatorWidget
            self.logger.info("Theme Creator plugin loaded successfully")
        except ImportError as e:
            theme_creator_dialog = None
            theme_creator_widget = None
            self.logger.warning(f"Theme Creator plugin not found: {e}")
        
        self.register_plugin(PluginInfo(
            id="theme_creator",
            name="Theme Creator",
            description="Create custom themes for AudioWave",
            version="1.0.0",
            author="AudioWave",
            icon="Ã°Å¸Å½Â¨",
            enabled=True,  # Uvijek omoguÃ„â€¡en jer je koristan za sve!
            has_dialog=True,
            has_widget=True,
            has_context_menu=False,
            shortcut="F9",
            dialog_class=theme_creator_dialog,
            widget_class=theme_creator_widget,
        ))
        
        # ===== RADIO BROWSER PLUGIN =====
        try:
            from plugins.radio_browser.radio_browser_plugin import RadioBrowserPlugin
            radio_browser_widget = RadioBrowserPlugin
            self.logger.info("Radio Browser plugin loaded successfully")
        except ImportError as e:
            radio_browser_widget = None
            self.logger.warning(f"Radio Browser plugin not found: {e}")
        
        self.register_plugin(PluginInfo(
            id="radio_browser",
            name="Radio Browser",
            description="Search and play live radio stations from radio-browser.info",
            version="1.0.0",
            author="TrayWave Team",
            icon="Ã°Å¸â€œÂ¡",
            enabled=True,  # Defaultno omoguÄ‡en
            has_dialog=True,  # Ima configure metodu
            has_widget=True,
            has_context_menu=False,
            shortcut="F5",  # Brzi pristup
            dialog_class=radio_browser_widget,  # Widget ima configure() metodu
            widget_class=radio_browser_widget,
        ))
    
    def register_plugin(self, plugin: PluginInfo):
        """
        Registruj novi plugin.
        
        Args:
            plugin: PluginInfo objekat
        """
        self.plugins[plugin.id] = plugin
        self.logger.info(f"Registered plugin: {plugin.name} ({plugin.id})")
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """
        Dobij plugin po ID-u.
        
        Args:
            plugin_id: ID plugina
            
        Returns:
            PluginInfo ili None
        """
        return self.plugins.get(plugin_id)
    
    def is_enabled(self, plugin_id: str) -> bool:
        """
        Proveri da li je plugin omoguÃ„â€¡en.
        
        Args:
            plugin_id: ID plugina
            
        Returns:
            True ako je plugin omoguÃ„â€¡en, False inaÃ„Âe
        """
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False
        return plugin.enabled
    
    def get_all_plugins(self) -> List[PluginInfo]:
        """
        Dobij listu svih pluginova.
        
        Returns:
            Lista PluginInfo objekata
        """
        return list(self.plugins.values())
    
    def get_enabled_plugins(self) -> List[PluginInfo]:
        """
        Dobij listu omoguÃ„â€¡enih pluginova.
        
        Returns:
            Lista omoguÃ„â€¡enih PluginInfo objekata
        """
        return [p for p in self.plugins.values() if p.enabled]
    
    def enable_plugin(self, plugin_id: str):
        """
        OmoguÃ„â€¡i plugin.
        
        Args:
            plugin_id: ID plugina
        """
        plugin = self.plugins.get(plugin_id)
        
        if not plugin:
            self.logger.warning(f"Plugin not found: {plugin_id}")
            return
        
        if plugin.enabled:
            self.logger.info(f"Plugin already enabled: {plugin_id}")
            return
        
        plugin.enabled = True
        self.plugin_enabled.emit(plugin_id)
        self.plugins_changed.emit()
        self._save_state()
        
        self.logger.info(f"Plugin enabled: {plugin_id}")
    
    def disable_plugin(self, plugin_id: str):
        """
        OnemoguÃ„â€¡i plugin.
        
        Args:
            plugin_id: ID plugina
        """
        plugin = self.plugins.get(plugin_id)
        
        if not plugin:
            self.logger.warning(f"Plugin not found: {plugin_id}")
            return
        
        if not plugin.enabled:
            self.logger.info(f"Plugin already disabled: {plugin_id}")
            return
        
        plugin.enabled = False
        self.plugin_disabled.emit(plugin_id)
        self.plugins_changed.emit()
        self._save_state()
        
        self.logger.info(f"Plugin disabled: {plugin_id}")
    
    def toggle_plugin(self, plugin_id: str):
        """
        Toggle plugin stanje.
        
        Args:
            plugin_id: ID plugina
        """
        plugin = self.plugins.get(plugin_id)
        
        if not plugin:
            return
        
        if plugin.enabled:
            self.disable_plugin(plugin_id)
        else:
            self.enable_plugin(plugin_id)
    
    def show_plugin_dialog(self, plugin_id: str, parent=None, **kwargs):
        """
        PrikaÃ…Â¾i dialog plugina.
        
        Args:
            plugin_id: ID plugina
            parent: Roditeljski widget
            **kwargs: Dodatni argumenti za dialog
        """
        plugin = self.plugins.get(plugin_id)
        
        if not plugin:
            self.logger.warning(f"Plugin not found: {plugin_id}")
            return
        
        if not plugin.enabled:
            self.logger.warning(f"Plugin not enabled: {plugin_id}")
            return
        
        if not plugin.dialog_class:
            self.logger.warning(f"Plugin has no dialog: {plugin_id}")
            return
        
        # Prosledi app ako postoji u kwargs
        if 'app' not in kwargs and parent and hasattr(parent, 'app'):
            kwargs['app'] = parent.app
        
        # Prosledi plugin_manager ako nije veÃ„â€¡ prosleÃ„â€˜en
        if 'plugin_manager' not in kwargs:
            kwargs['plugin_manager'] = self
        
        try:
            dialog = plugin.dialog_class(parent, **kwargs)
            
            # Za Sleep Timer, poveÃ…Â¾i signale
            if plugin_id == "sleep_timer":
                self._connect_sleep_timer_signals(dialog, parent, kwargs)
            
            dialog.exec()
            self.logger.info(f"Dialog shown for plugin: {plugin_id}")
        except Exception as e:
            self.logger.error(f"Error showing dialog for plugin {plugin_id}: {e}")
    
    def _connect_sleep_timer_signals(self, dialog, parent, kwargs):
        """PoveÃ…Â¾i Sleep Timer signale sa widget-om"""
        try:
            # Kreiraj ili dobij Sleep Timer widget
            app = kwargs.get('app', None)
            if app and hasattr(app, 'sleep_timer_widget'):
                # VeÃ„â€¡ postoji
                timer_widget = app.sleep_timer_widget
            else:
                # Kreiraj novi
                from plugins.sleeptimer.sleeptimer_plugin import SleepTimerWidget
                timer_widget = SleepTimerWidget(parent, **kwargs)
                if app:
                    app.sleep_timer_widget = timer_widget
            
            # PoveÃ…Â¾i signal
            dialog.timer_started.connect(timer_widget.start_timer)
            
        except Exception as e:
            self.logger.error(f"Error connecting sleep timer signals: {e}")
    
    def show_plugin_widget(self, plugin_id: str, parent=None, **kwargs):
        """
        Kreiraj i vrati widget plugina.
        
        Args:
            plugin_id: ID plugina
            parent: Roditeljski widget
            **kwargs: Dodatni argumenti za widget
            
        Returns:
            QWidget ili None
        """
        plugin = self.plugins.get(plugin_id)
        
        if not plugin or not plugin.enabled or not plugin.widget_class:
            return None
        
        # Ã¢Å“â€¦ FIX: Za Radio Browser, prosledi sve argumente direktno
        # RadioBrowserPlugin sada moÃ…Â¾e da ekstraktuje Ã…Â¡ta mu treba
        try:
            # Za sve pluginove (ukljuÃ„ÂujuÃ„â€¡i Radio Browser), prosledi sve argumente
            self.logger.info(f"Creating widget for plugin: {plugin_id}")
            
            # Prosledi app ako postoji u kwargs
            if 'app' not in kwargs and parent and hasattr(parent, 'app'):
                kwargs['app'] = parent.app
            
            # Prosledi plugin_manager ako nije veÃ„â€¡ prosleÃ„â€˜en
            if 'plugin_manager' not in kwargs:
                kwargs['plugin_manager'] = self
            
            # Kreiraj widget
            widget = plugin.widget_class(parent, **kwargs)
            self.logger.info(f"Widget created for plugin: {plugin_id}")
            
            # PoveÃ…Â¾i signal za dodavanje radio stanica
            if hasattr(widget, 'add_to_playlist'):
                widget.add_to_playlist.connect(self._handle_radio_station_add)
                self.logger.info(f"Connected add_to_playlist signal for plugin: {plugin_id}")
            
            return widget
            
        except Exception as e:
            self.logger.error(f"Error creating widget for plugin {plugin_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _handle_radio_station_add(self, name: str, url: str):
        """
        Handler za dodavanje radio stanice u playlist.
        Emituje globalni signal koji glavni prozor moÃ…Â¾e da hendluje.
        """
        self.logger.info(f"Radio station add requested: {name} - {url}")
        self.add_radio_to_playlist.emit(name, url)
    
    def get_context_menu_items(self) -> List[Dict]:
        """
        Dobij sve context menu iteme od omoguÃ„â€¡enih pluginova.
        
        Returns:
            Lista menu itema
        """
        items = []
        
        for plugin in self.get_enabled_plugins():
            if plugin.has_context_menu and plugin.context_menu_items:
                for item in plugin.context_menu_items:
                    item_copy = item.copy()
                    item_copy['plugin_id'] = plugin.id
                    items.append(item_copy)
        
        return items
    
    def handle_context_menu_action(self, action: str, plugin_id: str, parent=None, **kwargs):
        """
        Obradi context menu akciju.
        
        Args:
            action: Ime akcije
            plugin_id: ID plugina
            parent: Roditeljski widget
            **kwargs: Dodatni argumenti
        """
        plugin = self.plugins.get(plugin_id)
        
        if not plugin or not plugin.enabled:
            return
        
        # Lyrics plugin
        if plugin_id == "lyrics" and action == "search_lyrics":
            artist = kwargs.get('artist', '')
            title = kwargs.get('title', '')
            
            if plugin.dialog_class:
                try:
                    # Prosledi app ako postoji
                    if parent and hasattr(parent, 'app'):
                        kwargs['app'] = parent.app
                    
                    # Prosledi plugin_manager
                    kwargs['plugin_manager'] = self
                    
                    dialog = plugin.dialog_class(parent, artist=artist, title=title, **kwargs)
                    dialog.exec()
                    self.logger.info(f"Context menu action handled: {action} for plugin {plugin_id}")
                except Exception as e:
                    self.logger.error(f"Error handling context menu action {action}: {e}")
    
    def _save_state(self):
        """SaÃ„Âuvaj stanje pluginova"""
        try:
            # Kreiraj direktorijum ako ne postoji
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            state = {
                plugin_id: plugin.enabled
                for plugin_id, plugin in self.plugins.items()
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            
            self.logger.info(f"Plugin state saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving plugin state: {e}")
    
    def _load_state(self):
        """UÃ„Âitaj stanje pluginova"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                for plugin_id, enabled in state.items():
                    if plugin_id in self.plugins:
                        self.plugins[plugin_id].enabled = enabled
                
                self.logger.info(f"Plugin state loaded from {self.config_path}")
        except FileNotFoundError:
            self.logger.info("No plugin state file found, using defaults")
        except Exception as e:
            self.logger.error(f"Error loading plugin state: {e}")


# ===== SINGLETON INSTANCA =====
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(config_path: str = None) -> PluginManager:
    """
    Dobij globalnu PluginManager instancu.
    
    Args:
        config_path: Opciona putanja do config fajla
        
    Returns:
        PluginManager singleton
    """
    global _plugin_manager
    
    if _plugin_manager is None:
        _plugin_manager = PluginManager(config_path)
    
    return _plugin_manager


# ===== TEST =====
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # PodeÃ…Â¡avanje logginga za test
    logging.basicConfig(level=logging.INFO)
    
    app = QApplication(sys.argv)
    pm = get_plugin_manager()
    
    print("\n" + "="*50)
    print("Ã°Å¸Å½Âµ AUDIOWAVE PLUGIN MANAGER")
    print("="*50)
    
    print("\n=== All Plugins ===")
    for plugin in pm.get_all_plugins():
        status = "Ã¢Å“â€¦" if plugin.enabled else "Ã¢ÂÅ’"
        print(f"{status} {plugin.icon} {plugin.name}")
        print(f"   ID: {plugin.id}")
        print(f"   Desc: {plugin.description}")
        print(f"   Version: {plugin.version}")
        print(f"   Dialog: {'Yes' if plugin.has_dialog else 'No'}")
        print(f"   Widget: {'Yes' if plugin.has_widget else 'No'}")
        print()
    
    print("=== Enabled Plugins ===")
    enabled = pm.get_enabled_plugins()
    if enabled:
        for plugin in enabled:
            print(f"  {plugin.icon} {plugin.name}")
    else:
        print("  No plugins enabled")
    
    print("\n=== Plugin Statistics ===")
    all_plugins = pm.get_all_plugins()
    enabled_count = len([p for p in all_plugins if p.enabled])
    print(f"Total plugins: {len(all_plugins)}")
    print(f"Enabled: {enabled_count}")
    print(f"Disabled: {len(all_plugins) - enabled_count}")
    
    print("\n" + "="*50)
    print("Test zavrÃ…Â¡en!")
    print("="*50)