# core/themes/theme_registry.py

"""Theme registry - central place to register all themes"""

from typing import Dict, Type, Optional
from .base_theme import BaseTheme

# Import svih tamnih tema
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

# Import svih svetlih tema
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


class ThemeRegistry:
    """Registry for all available themes - supports dynamic registration"""
    
    _themes: Dict[str, Type[BaseTheme]] = {}
    _dynamic_themes: Dict[str, Type[BaseTheme]] = {}  # Za custom teme
    
    @classmethod
    def register(cls, theme_class: Type[BaseTheme]):
        """
        Register a theme class (for built-in themes).
        
        Args:
            theme_class: Theme class to register
        """
        theme = theme_class()
        cls._themes[theme.name] = theme_class
        print(f"  🎨 Registered theme: {theme.name}")
        return theme_class
    
    @classmethod
    def register_dynamic_theme(cls, theme_class: Type[BaseTheme]):
        """
        Register a dynamic theme class (for custom themes).
        Dynamic themes can be removed/replaced.
        
        Args:
            theme_class: Theme class to register
        """
        theme = theme_class()
        theme_name = theme.name
        
        # Proveri da li već postoji built-in tema sa istim imenom
        if theme_name in cls._themes:
            print(f"⚠️  Cannot register dynamic theme '{theme_name}' - built-in theme with same name exists")
            return
        
        # Proveri da li već postoji dynamic tema - zameni je
        if theme_name in cls._dynamic_themes:
            print(f"🔄 Replacing existing dynamic theme: {theme_name}")
        
        cls._dynamic_themes[theme_name] = theme_class
        print(f"  ✨ Registered DYNAMIC theme: {theme_name}")
    
    @classmethod
    def unregister_theme(cls, name: str) -> bool:
        """
        Unregister a theme by name (only works for dynamic themes).
        
        Args:
            name: Name of theme to remove
            
        Returns:
            bool: True if theme was removed
        """
        if name in cls._dynamic_themes:
            del cls._dynamic_themes[name]
            print(f"  🗑️  Unregistered dynamic theme: {name}")
            return True
        elif name in cls._themes:
            print(f"⚠️  Cannot unregister built-in theme: {name}")
            return False
        else:
            print(f"⚠️  Theme not found: {name}")
            return False
    
    @classmethod
    def get_theme(cls, name: str) -> BaseTheme:
        """
        Get theme instance by name.
        Checks dynamic themes first, then built-in themes.
        
        Args:
            name: Name of theme to get
            
        Returns:
            BaseTheme: Theme instance
        """
        # Prvo proveri dynamic teme
        if name in cls._dynamic_themes:
            return cls._dynamic_themes[name]()
        
        # Zatim proveri built-in teme
        if name in cls._themes:
            return cls._themes[name]()
        
        # Ako tema ne postoji, koristi Dark Modern
        print(f"⚠️  Theme '{name}' not found, using Dark Modern")
        return cls._themes["Dark Modern"]()
    
    @classmethod
    def get_all_themes(cls) -> Dict[str, BaseTheme]:
        """
        Get all theme instances (built-in + dynamic).
        
        Returns:
            Dict[str, BaseTheme]: All theme instances
        """
        all_themes = {}
        
        # Dodaj built-in teme
        for name, theme_class in cls._themes.items():
            all_themes[name] = theme_class()
        
        # Dodaj dynamic teme (može da overriduje built-in sa istim imenom)
        for name, theme_class in cls._dynamic_themes.items():
            all_themes[name] = theme_class()
        
        return all_themes
    
    @classmethod
    def get_theme_names(cls) -> list:
        """
        Get list of all theme names (built-in + dynamic).
        
        Returns:
            list: Sorted list of theme names
        """
        # Kombinuj ključeve iz oba rečnika
        all_names = set(cls._themes.keys()) | set(cls._dynamic_themes.keys())
        return sorted(list(all_names))
    
    @classmethod
    def get_builtin_theme_names(cls) -> list:
        """
        Get list of built-in theme names only.
        
        Returns:
            list: Built-in theme names
        """
        return sorted(list(cls._themes.keys()))
    
    @classmethod
    def get_dynamic_theme_names(cls) -> list:
        """
        Get list of dynamic (custom) theme names only.
        
        Returns:
            list: Dynamic theme names
        """
        return sorted(list(cls._dynamic_themes.keys()))
    
    @classmethod
    def is_dark_theme(cls, name: str) -> bool:
        """
        Check if theme is dark.
        
        Args:
            name: Theme name to check
            
        Returns:
            bool: True if theme is dark
        """
        # Built-in dark teme
        builtin_dark_themes = [
            "Dark Modern", "Ocean", "Cyberpunk", 
            "Retro Wave", "Forest", "Solarized Dark",
            "Galactic Core", "Molten Lava", "Cyber Neon",
            "Deep Ocean", "Amethyst Dream",
            "Midnight Obsidian", "Blood Moon", "Quantum Void",
            "Dragon Fire", "Nebula Storm"
        ]
        
        # Ako je built-in tema
        if name in builtin_dark_themes:
            return True
        
        # Ako je dynamic tema, proveri ime
        if name in cls._dynamic_themes:
            # Pokušaj da dobiješ instancu i proveriš boje
            try:
                theme = cls._dynamic_themes[name]()
                # Proveri bg_main boju - ako je tamna, tema je dark
                bg_color = getattr(theme, 'bg_main', '#ffffff')
                if isinstance(bg_color, str) and bg_color.startswith('#'):
                    # Prosta heuristika - ako je boja tamna
                    hex_color = bg_color.lstrip('#')
                    if len(hex_color) == 6:
                        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                        return luminance < 0.5
            except:
                pass
        
        # Fallback: proveri ime
        dark_keywords = ['dark', 'noir', 'midnight', 'night', 'black', 'obsidian', 
                        'void', 'nebula', 'storm', 'blood', 'lava', 'dragon', 'quantum']
        return any(keyword in name.lower() for keyword in dark_keywords)
    
    @classmethod
    def theme_exists(cls, name: str) -> bool:
        """
        Check if a theme exists (built-in or dynamic).
        
        Args:
            name: Theme name to check
            
        Returns:
            bool: True if theme exists
        """
        return name in cls._themes or name in cls._dynamic_themes
    
    @classmethod
    def is_dynamic_theme(cls, name: str) -> bool:
        """
        Check if a theme is dynamic (custom).
        
        Args:
            name: Theme name to check
            
        Returns:
            bool: True if theme is dynamic
        """
        return name in cls._dynamic_themes
    
    @classmethod
    def clear_dynamic_themes(cls):
        """
        Clear all dynamic (custom) themes.
        Useful for development or resetting.
        """
        count = len(cls._dynamic_themes)
        cls._dynamic_themes.clear()
        print(f"🧹 Cleared {count} dynamic themes")
    
    @classmethod
    def get_theme_info(cls, name: str) -> Optional[Dict]:
        """
        Get detailed information about a theme.
        
        Args:
            name: Theme name
            
        Returns:
            Optional[Dict]: Theme information or None
        """
        try:
            theme = cls.get_theme(name)
            theme_data = theme.get_theme_data()
            
            info = {
                "name": name,
                "is_dynamic": cls.is_dynamic_theme(name),
                "is_dark": cls.is_dark_theme(name),
                "font_family": theme_data.get("font_family", "Arial"),
                "font_size": theme_data.get("font_size", 13),
                "has_custom_colors": hasattr(theme, 'primary') and hasattr(theme, 'secondary'),
            }
            
            # Dodaj boje ako postoje
            if hasattr(theme, 'primary'):
                info["primary_color"] = theme.primary
                info["secondary_color"] = theme.secondary
                info["bg_main"] = getattr(theme, 'bg_main', '')
                info["bg_secondary"] = getattr(theme, 'bg_secondary', '')
            
            return info
            
        except Exception as e:
            print(f"⚠️  Could not get theme info for '{name}': {e}")
            return None


# ============================================================
# AUTO-REGISTER ALL BUILT-IN THEMES
# ============================================================

print("🎨 Registering built-in themes...")

# ===== DARK THEMES =====
print("🌌 Dark Themes:")
ThemeRegistry.register(DarkModernTheme)
ThemeRegistry.register(OceanTheme)
ThemeRegistry.register(CyberpunkTheme)
ThemeRegistry.register(RetroWaveTheme)
ThemeRegistry.register(ForestTheme)
ThemeRegistry.register(SolarizedDarkTheme)
ThemeRegistry.register(GalacticCoreTheme)
ThemeRegistry.register(MoltenLavaTheme)
ThemeRegistry.register(CyberNeonTheme)
ThemeRegistry.register(DeepOceanTheme)
ThemeRegistry.register(AmethystDreamTheme)
ThemeRegistry.register(MidnightObsidianTheme)
ThemeRegistry.register(BloodMoonTheme)
ThemeRegistry.register(QuantumVoidTheme)
ThemeRegistry.register(DragonFireTheme)
ThemeRegistry.register(NebulaStormTheme)

# ===== LIGHT THEMES =====
print("🌞 Light Themes:")
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
ThemeRegistry.register(NeonPulseTheme)
ThemeRegistry.register(SunsetGlowTheme)
ThemeRegistry.register(ArcticAuroraTheme)
ThemeRegistry.register(ChampagneSparkleTheme)

# ===== STATISTIKA =====
all_themes = ThemeRegistry.get_theme_names()
builtin_count = len(ThemeRegistry.get_builtin_theme_names())
dynamic_count = len(ThemeRegistry.get_dynamic_theme_names())
dark_count = len([t for t in all_themes if ThemeRegistry.is_dark_theme(t)])
light_count = len(all_themes) - dark_count

print(f"\n✅ Theme registry initialized:")
print(f"   📦 Built-in themes: {builtin_count}")
print(f"   ✨ Dynamic themes: {dynamic_count}")
print(f"   🌌 Dark themes: {dark_count}")
print(f"   🌞 Light themes: {light_count}")
print(f"   🎯 Total: {len(all_themes)} themes")

if dynamic_count > 0:
    print(f"\n📋 Dynamic themes: {', '.join(ThemeRegistry.get_dynamic_theme_names())}")

print(f"\n📋 All themes: {', '.join(all_themes)}")


# ===== UTILITY FUNCTIONS =====

def get_theme_registry() -> ThemeRegistry:
    """
    Get the theme registry instance (singleton pattern).
    
    Returns:
        ThemeRegistry: Theme registry instance
    """
    return ThemeRegistry


def register_custom_theme_from_json(json_data: dict) -> bool:
    """
    Utility function to register a custom theme from JSON data.
    Can be called from Theme Creator or other parts of the app.
    
    Args:
        json_data: Dictionary with theme configuration
        
    Returns:
        bool: True if successful
    """
    try:
        from .base_theme import BaseTheme, StyleComponents
        
        theme_name = json_data.get("name", "Custom Theme")
        theme_type = json_data.get("type", "dark").lower()
        
        # Kreiraj dinamičku klasu
        class_name = f"Custom{theme_name.replace(' ', '').replace('-', '')}Theme"
        
        # Sačuvaj podatke teme
        theme_primary = json_data.get("primary", "#667eea")
        theme_secondary = json_data.get("secondary", "#764ba2")
        theme_bg_main = json_data.get("bg_main", "#0f172a" if theme_type == "dark" else "#ffffff")
        theme_bg_secondary = json_data.get("bg_secondary", "#1e293b" if theme_type == "dark" else "#f0f0f0")
        theme_text_color = json_data.get("text_color", "#e2e8f0" if theme_type == "dark" else "#333333")
        theme_accent = json_data.get("accent", theme_primary)
        theme_title_color = json_data.get("title_color", theme_text_color)
        theme_artist_color = json_data.get("artist_color", theme_text_color)
        theme_label_style = json_data.get("label_style", "minimal")
        theme_font_family = json_data.get("font_family", "Arial")
        theme_font_size = json_data.get("font_size", 13)
        
        class CustomTheme(BaseTheme):
            def __init__(self):
                super().__init__(theme_name, theme_font_family, theme_font_size)
                self.primary = theme_primary
                self.secondary = theme_secondary
                self.bg_main = theme_bg_main
                self.bg_secondary = theme_bg_secondary
                self.json_data = json_data
            
            def get_stylesheet(self) -> str:
                return StyleComponents.get_complete_theme(
                    primary=self.primary,
                    secondary=self.secondary,
                    bg=self.bg_main,
                    text_color=theme_text_color,
                    accent=theme_accent,
                    title_color=theme_title_color,
                    artist_color=theme_artist_color,
                    label_style=theme_label_style
                )
        
        # Promeni ime klase
        CustomTheme.__name__ = class_name
        CustomTheme.__qualname__ = class_name
        
        # Registruj temu
        ThemeRegistry.register_dynamic_theme(CustomTheme)
        print(f"✅ Custom theme '{theme_name}' registered via utility function")
        return True
        
    except Exception as e:
        print(f"❌ Failed to register custom theme: {e}")
        import traceback
        traceback.print_exc()
        return False