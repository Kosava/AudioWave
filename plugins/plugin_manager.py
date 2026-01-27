# -*- coding: utf-8 -*-
# plugins/plugin_manager.py
"""
Plugin Manager - Upravljanje pluginovima za AudioWave

Omogućava:
- Registraciju pluginova
- Omogućavanje/onemogućavanje pluginova
- Čuvanje stanja pluginova
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
    icon: str = "🔌"
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
    
    def __init__(self, config_path: str = None):
        super().__init__()
        
        self.plugins: Dict[str, PluginInfo] = {}
        self.config_path = config_path or os.path.expanduser("~/.audiowave/plugins.json")
        self.logger = logging.getLogger(__name__)
        
        # Registruj ugrađene pluginove
        self._register_builtin_plugins()
        
        # Učitaj stanje
        self._load_state()
    
    def _register_builtin_plugins(self):
        """Registruj ugrađene pluginove"""
        
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
            icon="🎛️",
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
            icon="🎤",
            enabled=False,
            has_dialog=True,
            has_widget=True,
            has_context_menu=True,
            shortcut="F4",
            dialog_class=lyrics_dialog,
            widget_class=lyrics_widget,
            context_menu_items=[
                {
                    "text": "🎤 Search Lyrics",
                    "action": "search_lyrics",
                    "separator_before": True,
                }
            ]
        ))
        
        # Visualizer plugin (placeholder)
        self.register_plugin(PluginInfo(
            id="visualizer",
            name="Visualizer",
            description="Audio visualization effects",
            version="0.1.0",
            author="AudioWave",
            icon="📊",
            enabled=False,
            has_dialog=True,
            has_widget=False,
            has_context_menu=False,
            shortcut="F6",
            dialog_class=None,  # TODO: Implementirati
        ))
        
        # Sleep Timer plugin (placeholder)
        self.register_plugin(PluginInfo(
            id="sleep_timer",
            name="Sleep Timer",
            description="Auto-stop playback after specified time",
            version="0.1.0",
            author="AudioWave",
            icon="⏰",
            enabled=False,
            has_dialog=True,
            has_widget=False,
            has_context_menu=False,
            shortcut="",
            dialog_class=None,  # TODO: Implementirati
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
            icon="🎨",
            enabled=True,  # Uvijek omogućen jer je koristan za sve!
            has_dialog=True,
            has_widget=True,
            has_context_menu=False,
            shortcut="F9",
            dialog_class=theme_creator_dialog,
            widget_class=theme_creator_widget,
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
    
    def get_all_plugins(self) -> List[PluginInfo]:
        """
        Dobij listu svih pluginova.
        
        Returns:
            Lista PluginInfo objekata
        """
        return list(self.plugins.values())
    
    def get_enabled_plugins(self) -> List[PluginInfo]:
        """
        Dobij listu omogućenih pluginova.
        
        Returns:
            Lista omogućenih PluginInfo objekata
        """
        return [p for p in self.plugins.values() if p.enabled]
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Omogući plugin.
        
        Args:
            plugin_id: ID plugina
            
        Returns:
            True ako je uspešno
        """
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = True
            self._save_state()
            self.plugin_enabled.emit(plugin_id)
            self.plugins_changed.emit()
            self.logger.info(f"Plugin enabled: {plugin_id}")
            return True
        self.logger.warning(f"Plugin not found for enabling: {plugin_id}")
        return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Onemogući plugin.
        
        Args:
            plugin_id: ID plugina
            
        Returns:
            True ako je uspešno
        """
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = False
            self._save_state()
            self.plugin_disabled.emit(plugin_id)
            self.plugins_changed.emit()
            self.logger.info(f"Plugin disabled: {plugin_id}")
            return True
        self.logger.warning(f"Plugin not found for disabling: {plugin_id}")
        return False
    
    def toggle_plugin(self, plugin_id: str) -> bool:
        """
        Toggle stanje plugina.
        
        Args:
            plugin_id: ID plugina
            
        Returns:
            Novo stanje (True = enabled)
        """
        if plugin_id in self.plugins:
            if self.plugins[plugin_id].enabled:
                self.disable_plugin(plugin_id)
                return False
            else:
                self.enable_plugin(plugin_id)
                return True
        self.logger.warning(f"Plugin not found for toggling: {plugin_id}")
        return False
    
    def is_enabled(self, plugin_id: str) -> bool:
        """
        Proveri da li je plugin omogućen.
        
        Args:
            plugin_id: ID plugina
            
        Returns:
            True ako je omogućen
        """
        plugin = self.plugins.get(plugin_id)
        return plugin.enabled if plugin else False
    
    def show_plugin_dialog(self, plugin_id: str, parent=None, **kwargs):
        """
        Prikaži dialog plugina.
        
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
        
        # Prosledi plugin_manager ako nije već prosleđen
        if 'plugin_manager' not in kwargs:
            kwargs['plugin_manager'] = self
        
        try:
            dialog = plugin.dialog_class(parent, **kwargs)
            dialog.exec()
            self.logger.info(f"Dialog shown for plugin: {plugin_id}")
        except Exception as e:
            self.logger.error(f"Error showing dialog for plugin {plugin_id}: {e}")
    
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
        
        # Prosledi app ako postoji u kwargs
        if 'app' not in kwargs and parent and hasattr(parent, 'app'):
            kwargs['app'] = parent.app
        
        # Prosledi plugin_manager ako nije već prosleđen
        if 'plugin_manager' not in kwargs:
            kwargs['plugin_manager'] = self
        
        try:
            widget = plugin.widget_class(parent, **kwargs)
            self.logger.info(f"Widget created for plugin: {plugin_id}")
            return widget
        except Exception as e:
            self.logger.error(f"Error creating widget for plugin {plugin_id}: {e}")
            return None
    
    def get_context_menu_items(self) -> List[Dict]:
        """
        Dobij sve context menu iteme od omogućenih pluginova.
        
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
        """Sačuvaj stanje pluginova"""
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
        """Učitaj stanje pluginova"""
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
    
    # Podešavanje logginga za test
    logging.basicConfig(level=logging.INFO)
    
    app = QApplication(sys.argv)
    pm = get_plugin_manager()
    
    print("\n" + "="*50)
    print("🎵 AUDIOWAVE PLUGIN MANAGER")
    print("="*50)
    
    print("\n=== All Plugins ===")
    for plugin in pm.get_all_plugins():
        status = "✅" if plugin.enabled else "❌"
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
    
    # Test prosleđivanje app parametra
    print("\n=== Testing app parameter passing ===")
    
    class MockParent:
        def __init__(self):
            self.app = "MockAppInstance"
    
    mock_parent = MockParent()
    
    # Testiranje show_plugin_dialog sa app parametrom
    try:
        # Ovo će samo testirati poziv, neće otvoriti dijalog ako plugin nije dostupan
        pm.show_plugin_dialog("equalizer", mock_parent)
        print("✓ Plugin dialog called with app parameter")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test Theme Creator plugin
    print("\n=== Testing Theme Creator Plugin ===")
    theme_creator = pm.get_plugin("theme_creator")
    if theme_creator:
        print(f"Found: {theme_creator.name}")
        print(f"Enabled: {theme_creator.enabled}")
        print(f"Has dialog: {theme_creator.has_dialog}")
    else:
        print("Theme Creator plugin not found!")
        print("Make sure plugins/theme_creator/theme_creator_plugin.py exists")
    
    print("\n" + "="*50)
    print("Test završen!")
    print("="*50)