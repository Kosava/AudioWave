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
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
import json
import os


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
        except ImportError:
            eq_dialog = None
            eq_widget = None
        
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
        except ImportError:
            lyrics_dialog = None
            lyrics_widget = None
        
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
    
    def register_plugin(self, plugin: PluginInfo):
        """
        Registruj novi plugin.
        
        Args:
            plugin: PluginInfo objekat
        """
        self.plugins[plugin.id] = plugin
        print(f"🔌 Registered plugin: {plugin.name} ({plugin.id})")
    
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
            print(f"✅ Plugin enabled: {plugin_id}")
            return True
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
            print(f"❌ Plugin disabled: {plugin_id}")
            return True
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
            print(f"⚠️ Plugin not found: {plugin_id}")
            return
        
        if not plugin.enabled:
            print(f"⚠️ Plugin not enabled: {plugin_id}")
            return
        
        if not plugin.dialog_class:
            print(f"⚠️ Plugin has no dialog: {plugin_id}")
            return
        
        dialog = plugin.dialog_class(parent, **kwargs)
        dialog.exec()
    
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
                dialog = plugin.dialog_class(parent, artist=artist, title=title)
                dialog.exec()
    
    def _save_state(self):
        """Sačuvaj stanje pluginova"""
        try:
            # Kreiraj direktorijum ako ne postoji
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            state = {
                plugin_id: plugin.enabled
                for plugin_id, plugin in self.plugins.items()
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"💾 Plugin state saved to {self.config_path}")
        except Exception as e:
            print(f"⚠️ Error saving plugin state: {e}")
    
    def _load_state(self):
        """Učitaj stanje pluginova"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    state = json.load(f)
                
                for plugin_id, enabled in state.items():
                    if plugin_id in self.plugins:
                        self.plugins[plugin_id].enabled = enabled
                
                print(f"📂 Plugin state loaded from {self.config_path}")
        except Exception as e:
            print(f"⚠️ Error loading plugin state: {e}")


# ===== SINGLETON INSTANCA =====
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """
    Dobij globalnu PluginManager instancu.
    
    Returns:
        PluginManager singleton
    """
    global _plugin_manager
    
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    
    return _plugin_manager


# ===== TEST =====
if __name__ == "__main__":
    pm = get_plugin_manager()
    
    print("\n=== All Plugins ===")
    for plugin in pm.get_all_plugins():
        status = "✅" if plugin.enabled else "❌"
        print(f"{status} {plugin.icon} {plugin.name} v{plugin.version}")
    
    print("\n=== Enable Equalizer ===")
    pm.enable_plugin("equalizer")
    
    print("\n=== Enabled Plugins ===")
    for plugin in pm.get_enabled_plugins():
        print(f"  {plugin.icon} {plugin.name}")