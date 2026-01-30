# core/themes/__init__.py

"""
Theme system package
"""

from .base_theme import BaseTheme, StyleComponents
from .theme_registry import ThemeRegistry, get_theme_registry, register_custom_theme_from_json
from .dark_themes import (
    DarkModernTheme,
    OceanTheme,
    CyberpunkTheme,
    RetroWaveTheme,
    ForestTheme,
    SolarizedDarkTheme,
    GalacticCoreTheme,
    MoltenLavaTheme,
    CyberNeonTheme,
    DeepOceanTheme,
    AmethystDreamTheme,
    MidnightObsidianTheme,
    BloodMoonTheme,
    QuantumVoidTheme,
    DragonFireTheme,
    NebulaStormTheme
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
    VioletStormTheme,
    NeonPulseTheme,
    SunsetGlowTheme,
    ArcticAuroraTheme,
    ChampagneSparkleTheme
)
# Emergency themes
from .emergency_theme import EmergencyTheme, SafeTheme

__all__ = [
    'BaseTheme',
    'StyleComponents',
    'ThemeRegistry',
    'get_theme_registry',
    'register_custom_theme_from_json',
    # Dark themes
    'DarkModernTheme',
    'OceanTheme',
    'CyberpunkTheme',
    'RetroWaveTheme',
    'ForestTheme',
    'SolarizedDarkTheme',
    'GalacticCoreTheme',
    'MoltenLavaTheme',
    'CyberNeonTheme',
    'DeepOceanTheme',
    'AmethystDreamTheme',
    'MidnightObsidianTheme',
    'BloodMoonTheme',
    'QuantumVoidTheme',
    'DragonFireTheme',
    'NebulaStormTheme',
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
    'VioletStormTheme',
    'NeonPulseTheme',
    'SunsetGlowTheme',
    'ArcticAuroraTheme',
    'ChampagneSparkleTheme',
    # Emergency themes
    'EmergencyTheme',
    'SafeTheme'
]