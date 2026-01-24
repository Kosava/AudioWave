# core/themes/__init__.py

"""
Theme system package
"""

from .base_theme import BaseTheme, StyleComponents
from .theme_registry import ThemeRegistry
from .dark_themes import (
    DarkModernTheme,
    OceanTheme,
    CyberpunkTheme,
    RetroWaveTheme,
    ForestTheme,
    SolarizedDarkTheme
)
from .light_themes import (
    NordicLightTheme,
    PastelDreamTheme,
    MintFreshTheme,
    CottonCandyTheme,
    LavenderFieldsTheme,
    SunburstOrangeTheme,
    ElectricBlueTheme,
    HotPinkBlastTheme,
    LimeExplosionTheme,
    TurquoiseTidalTheme,
    CoralReefTheme,
    GoldenHourTheme,
    VioletStormTheme
)

__all__ = [
    'BaseTheme',
    'StyleComponents',
    'ThemeRegistry',
    # Dark themes
    'DarkModernTheme',
    'OceanTheme',
    'CyberpunkTheme',
    'RetroWaveTheme',
    'ForestTheme',
    'SolarizedDarkTheme',
    # Light themes
    'NordicLightTheme',
    'PastelDreamTheme',
    'MintFreshTheme',
    'CottonCandyTheme',
    'LavenderFieldsTheme',
    'SunburstOrangeTheme',
    'ElectricBlueTheme',
    'HotPinkBlastTheme',
    'LimeExplosionTheme',
    'TurquoiseTidalTheme',
    'CoralReefTheme',
    'GoldenHourTheme',
    'VioletStormTheme'
]