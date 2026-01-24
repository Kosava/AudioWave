"""
Configuration manager
"""

import json
import os
from pathlib import Path


class Config:
    def __init__(self):
        self.config = {
            "theme": "teal",
            "volume": 70,
            "library_path": str(Path.home() / "Music"),
            "show_on_startup": True,
            "muted": False,
            "last_file": None,
            "window_geometry": None,
            "window_maximized": False,

            # 🆕 Tray settings
            "tray": {
                "enabled": True,
                "close_to_tray": True,
                "notifications": True,
                "icon_theme": "auto"  # auto | light | dark
            }
        }

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    # 🆕 helpers
    def get_tray_settings(self):
        tray = self.config.get("tray")
        if not isinstance(tray, dict):
            tray = {
                "enabled": True,
                "close_to_tray": True,
                "notifications": True,
                "icon_theme": "auto"
            }
            self.config["tray"] = tray
        return tray

    def set_tray_settings(self, tray_settings: dict):
        self.config["tray"] = tray_settings
