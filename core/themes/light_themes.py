# core/themes/light_themes.py - FIXED: Dodao bg_main i bg_secondary za SVE teme

"""All light theme implementations - 17 VIBRANT THEMES with CLEAN player labels!"""

from .base_theme import BaseTheme, StyleComponents


class NordicLightTheme(BaseTheme):
    def __init__(self):
        super().__init__("Nordic Light", "Arial", 13)
        self.primary = "#88c0d0"
        self.secondary = "#5e81ac"
        self.bg_main = "#eceff4"
        self.bg_secondary = "#d8dee9"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#2e3440", accent="#81a1c1",
            title_color="#2e3440", artist_color="#4c566a",
            label_style="minimal"
        )


class PastelDreamTheme(BaseTheme):
    def __init__(self):
        super().__init__("Pastel Dream", "Arial", 13)
        self.primary = "#e5a6c8"
        self.secondary = "#c77daf"
        self.bg_main = "#fef6fb"
        self.bg_secondary = "#f8e8f5"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#5d4e6d", accent="#d68eb8",
            title_color="#8e4585", artist_color="#a97ca0",
            label_style="minimal"
        )


class MintFreshTheme(BaseTheme):
    def __init__(self):
        super().__init__("Mint Fresh", "Arial", 13)
        self.primary = "#6ee7b7"
        self.secondary = "#34d399"
        self.bg_main = "#f0fdf4"
        self.bg_secondary = "#d1fae5"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#064e3b", accent="#10b981",
            title_color="#065f46", artist_color="#047857",
            label_style="minimal"
        )


class CottonCandyTheme(BaseTheme):
    def __init__(self):
        super().__init__("Cotton Candy", "Arial", 13)
        self.primary = "#e879f9"
        self.secondary = "#c084fc"
        self.bg_main = "#fff5fb"
        self.bg_secondary = "#fae8ff"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#7c3aed", accent="#d946ef",
            title_color="#a855f7", artist_color="#c084fc",
            label_style="minimal"
        )


class LavenderFieldsTheme(BaseTheme):
    def __init__(self):
        super().__init__("Lavender Fields", "Arial", 13)
        self.primary = "#a78bfa"
        self.secondary = "#8b5cf6"
        self.bg_main = "#faf8ff"
        self.bg_secondary = "#ede9fe"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#4c1d95", accent="#9333ea",
            title_color="#5b21b6", artist_color="#7c3aed",
            label_style="minimal"
        )


class SunburstOrangeTheme(BaseTheme):
    def __init__(self):
        super().__init__("Sunburst Orange", "Arial", 13)
        self.primary = "#fb923c"
        self.secondary = "#f59e0b"
        self.bg_main = "#fffbeb"
        self.bg_secondary = "#fef3c7"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#7c2d12", accent="#ea580c",
            title_color="#ea580c", artist_color="#f59e0b",
            label_style="minimal"
        )


class ElectricBlueTheme(BaseTheme):
    def __init__(self):
        super().__init__("Electric Blue", "Arial", 13)
        self.primary = "#0ea5e9"
        self.secondary = "#06b6d4"
        self.bg_main = "#f0f9ff"
        self.bg_secondary = "#dbeafe"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#075985", accent="#0284c7",
            title_color="#0369a1", artist_color="#0891b2",
            label_style="minimal"
        )


class HotPinkBlastTheme(BaseTheme):
    def __init__(self):
        super().__init__("Hot Pink Blast", "Arial", 13)
        self.primary = "#ec4899"
        self.secondary = "#f43f5e"
        self.bg_main = "#fdf2f8"
        self.bg_secondary = "#fce7f3"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#831843", accent="#db2777",
            title_color="#be185d", artist_color="#e11d48",
            label_style="minimal"
        )


class LimeExplosionTheme(BaseTheme):
    def __init__(self):
        super().__init__("Lime Explosion", "Arial", 13)
        self.primary = "#84cc16"
        self.secondary = "#65a30d"
        self.bg_main = "#f7fee7"
        self.bg_secondary = "#ecfccb"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#365314", accent="#65a30d",
            title_color="#4d7c0f", artist_color="#65a30d",
            label_style="minimal"
        )


class TurquoiseTidalTheme(BaseTheme):
    def __init__(self):
        super().__init__("Turquoise Tidal", "Arial", 13)
        self.primary = "#14b8a6"
        self.secondary = "#06b6d4"
        self.bg_main = "#f0fdfa"
        self.bg_secondary = "#ccfbf1"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#134e4a", accent="#0d9488",
            title_color="#0f766e", artist_color="#0891b2",
            label_style="minimal"
        )


class CoralReefTheme(BaseTheme):
    def __init__(self):
        super().__init__("Coral Reef", "Arial", 13)
        self.primary = "#fb7185"
        self.secondary = "#fbbf24"
        self.bg_main = "#fff1f2"
        self.bg_secondary = "#ffe4e6"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#881337", accent="#f43f5e",
            title_color="#be123c", artist_color="#e11d48",
            label_style="minimal"
        )


class GoldenHourTheme(BaseTheme):
    def __init__(self):
        super().__init__("Golden Hour", "Arial", 13)
        self.primary = "#f59e0b"
        self.secondary = "#eab308"
        self.bg_main = "#fffbeb"
        self.bg_secondary = "#fef3c7"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#78350f", accent="#d97706",
            title_color="#b45309", artist_color="#ca8a04",
            label_style="minimal"
        )


class VioletStormTheme(BaseTheme):
    def __init__(self):
        super().__init__("Violet Storm", "Arial", 13)
        self.primary = "#8b5cf6"
        self.secondary = "#a855f7"
        self.bg_main = "#faf5ff"
        self.bg_secondary = "#f3e8ff"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#581c87", accent="#7c3aed",
            title_color="#6b21a8", artist_color="#7e22ce",
            label_style="minimal"
        )


class NeonPulseTheme(BaseTheme):
    """NEON PULSE - Svetla ali grmi!"""
    
    def __init__(self):
        super().__init__("Neon Pulse", "Arial", 13)
        self.primary = "#00ff9d"      # NEON zelena
        self.secondary = "#00b8ff"    # NEON plava
        self.bg_main = "#ffffff"
        self.bg_secondary = "#f0f0f0"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#111111", accent="#ff00aa",  # NEON roza za accent
            title_color="#ff0066", artist_color="#333333",
            label_style="glass"  # Glass stil za efekt!
        )


class SunsetGlowTheme(BaseTheme):
    """SUNSET GLOW - Tople boje zalaska sunca"""
    
    def __init__(self):
        super().__init__("Sunset Glow", "Arial", 13)
        self.primary = "#ff6b35"      # Narandžasta
        self.secondary = "#ffa62e"    # Žuta
        self.bg_main = "#fffaf0"
        self.bg_secondary = "#ffe8d6"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#5a3e1b", accent="#e63946",  # Crvena za kontrast
            title_color="#d90429", artist_color="#8d5a2d",
            label_style="clean"
        )


class ArcticAuroraTheme(BaseTheme):
    """ARCTIC AURORA - Polarna svetlost u ledenoj pustinji"""
    
    def __init__(self):
        super().__init__("Arctic Aurora", "Verdana", 13)
        self.primary = "#00e0ff"      # Ledeno plava
        self.secondary = "#00ffaa"    # Ledeno zelena
        self.bg_main = "#ffffff"
        self.bg_secondary = "#f0f8ff"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#003366", accent="#ff66cc",  # Magenta accent
            title_color="#0066cc", artist_color="#0099cc",
            label_style="glass"
        )


class ChampagneSparkleTheme(BaseTheme):
    """CHAMPAGNE SPARKLE - Šampanjac sa zlatnim mjehurićima"""
    
    def __init__(self):
        super().__init__("Champagne Sparkle", "Georgia", 14)
        self.primary = "#ffd166"      # Zlatno žuta
        self.secondary = "#ffb347"    # Narandžasta
        self.bg_main = "#fffef0"
        self.bg_secondary = "#fff8e1"
    
    def get_stylesheet(self) -> str:
        return StyleComponents.get_complete_theme(
            primary=self.primary, secondary=self.secondary, bg=self.bg_main,
            text_color="#5d4037", accent="#d4af37",  # Zlatni accent
            title_color="#b8860b", artist_color="#8b7355",
            label_style="subtle"
        )