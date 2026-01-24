# core/themes/theme_registry.py

"""Theme registry - central place to register all themes"""

from typing import Dict, Type
from .base_theme import BaseTheme
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


class ThemeRegistry:
    """Registry for all available themes"""
    
    _themes: Dict[str, Type[BaseTheme]] = {}
    
    @classmethod
    def register(cls, theme_class: Type[BaseTheme]):
        """Register a theme class"""
        theme = theme_class()
        cls._themes[theme.name] = theme_class
        print(f"  🎨 Registered theme: {theme.name}")
        return theme_class
    
    @classmethod
    def get_theme(cls, name: str) -> BaseTheme:
        """Get theme instance by name"""
        if name not in cls._themes:
            print(f"⚠️  Theme '{name}' not found, using Dark Modern")
            name = "Dark Modern"
        
        return cls._themes[name]()
    
    @classmethod
    def get_all_themes(cls) -> Dict[str, BaseTheme]:
        """Get all theme instances"""
        return {name: theme_class() for name, theme_class in cls._themes.items()}
    
    @classmethod
    def get_theme_names(cls) -> list:
        """Get list of theme names"""
        return sorted(list(cls._themes.keys()))
    
    @classmethod
    def is_dark_theme(cls, name: str) -> bool:
        """Check if theme is dark"""
        dark_themes = [
            "Dark Modern", "Ocean", "Cyberpunk", 
            "Retro Wave", "Forest", "Solarized Dark"
        ]
        return name in dark_themes


# Auto-register all themes
print("🎨 Registering themes...")

# Dark themes
ThemeRegistry.register(DarkModernTheme)
ThemeRegistry.register(OceanTheme)
ThemeRegistry.register(CyberpunkTheme)
ThemeRegistry.register(RetroWaveTheme)
ThemeRegistry.register(ForestTheme)
ThemeRegistry.register(SolarizedDarkTheme)

# Light themes
ThemeRegistry.register(NordicLightTheme)
ThemeRegistry.register(PastelDreamTheme)
ThemeRegistry.register(MintFreshTheme)
ThemeRegistry.register(CottonCandyTheme)
ThemeRegistry.register(LavenderFieldsTheme)
ThemeRegistry.register(SunburstOrangeTheme)
ThemeRegistry.register(ElectricBlueTheme)
ThemeRegistry.register(HotPinkBlastTheme)
ThemeRegistry.register(LimeExplosionTheme)
ThemeRegistry.register(TurquoiseTidalTheme)
ThemeRegistry.register(CoralReefTheme)
ThemeRegistry.register(GoldenHourTheme)
ThemeRegistry.register(VioletStormTheme)

print(f"✅ Total themes registered: {len(ThemeRegistry.get_theme_names())}")