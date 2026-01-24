# -*- coding: utf-8 -*-
"""
SVG Icon Manager - Theme-aware inline SVG ikone
ui/utils/svg_icon_manager.py

Sistem za kreiranje i bojenje SVG ikonica koje se prilagođavaju temama.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QByteArray, QSize
from PyQt6.QtSvg import QSvgRenderer


class SVGIconManager:
    """
    Manager za kreiranje theme-aware SVG ikonica.
    Ikone se mogu bojiti prema trenutnoj temi i menjaju se dinamički.
    """
    
    # SVG Templates - čiste ikone bez boja
    ICONS = {
        'add': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z" 
                      fill="{color}" stroke="{color}" stroke-width="0.5"/>
            </svg>
        ''',
        
        'delete': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" 
                      fill="{color}" stroke="{color}" stroke-width="0.3"/>
            </svg>
        ''',
        
        'settings': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z" 
                      fill="{color}"/>
            </svg>
        ''',
        
        'playlist': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 5h18v2H3V5zm0 6h18v2H3v-2zm0 6h12v2H3v-2z" 
                      fill="{color}" stroke="{color}" stroke-width="0.5"/>
                <circle cx="19" cy="18" r="2.5" fill="{color}"/>
            </svg>
        ''',
        
        'play': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 5v14l11-7z" fill="{color}"/>
            </svg>
        ''',
        
        'pause': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" fill="{color}"/>
            </svg>
        ''',
        
        'stop': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <rect x="6" y="6" width="12" height="12" rx="1" fill="{color}"/>
            </svg>
        ''',
        
        'previous': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 6h2v12H6V6zm3 6l8.5 6V6L9 12z" fill="{color}"/>
            </svg>
        ''',
        
        'next': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 18h2V6h-2v12zM6 18l8.5-6L6 6v12z" fill="{color}"/>
            </svg>
        ''',
        
        'volume': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" 
                      fill="{color}"/>
            </svg>
        ''',
        
        'volume_mute': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" 
                      fill="{color}"/>
            </svg>
        ''',
        
        'search': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" 
                      fill="{color}"/>
            </svg>
        ''',
        
        'clear': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" 
                      fill="{color}"/>
            </svg>
        ''',
        
        'folder': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" 
                      fill="{color}"/>
            </svg>
        ''',
        
        # Elegantne ikone za player kontrole sa više detalja
        'play_elegant': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="playGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
                    </linearGradient>
                </defs>
                <path d="M8 5v14l11-7z" fill="url(#playGrad)" stroke="{color}" stroke-width="0.5"/>
            </svg>
        ''',
        
        'pause_elegant': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="pauseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
                    </linearGradient>
                </defs>
                <rect x="6" y="4" width="4" height="16" rx="1" fill="url(#pauseGrad)" stroke="{color}" stroke-width="0.5"/>
                <rect x="14" y="4" width="4" height="16" rx="1" fill="url(#pauseGrad)" stroke="{color}" stroke-width="0.5"/>
            </svg>
        ''',
        
        'stop_elegant': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="stopGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
                    </linearGradient>
                </defs>
                <rect x="6" y="6" width="12" height="12" rx="2" fill="url(#stopGrad)" stroke="{color}" stroke-width="0.5"/>
            </svg>
        ''',
        
        'previous_elegant': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="prevGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
                    </linearGradient>
                </defs>
                <rect x="6" y="6" width="2" height="12" rx="1" fill="url(#prevGrad)"/>
                <path d="M9 12l8.5-6v12z" fill="url(#prevGrad)" stroke="{color}" stroke-width="0.5"/>
            </svg>
        ''',
        
        'next_elegant': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="nextGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
                    </linearGradient>
                </defs>
                <path d="M6 6l8.5 6-8.5 6z" fill="url(#nextGrad)" stroke="{color}" stroke-width="0.5"/>
                <rect x="16" y="6" width="2" height="12" rx="1" fill="url(#nextGrad)"/>
            </svg>
        ''',
        
        'volume_elegant': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="volGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
                    </linearGradient>
                </defs>
                <path d="M3 9v6h4l5 5V4L7 9H3z" fill="url(#volGrad)" stroke="{color}" stroke-width="0.5"/>
                <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" 
                      fill="url(#volGrad)" opacity="0.8"/>
                <path d="M14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" 
                      fill="url(#volGrad)" opacity="0.6"/>
            </svg>
        ''',
        
        'menu': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="menuGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{color};stop-opacity:0.8" />
                    </linearGradient>
                </defs>
                <rect x="3" y="4" width="18" height="2.5" rx="1.25" fill="url(#menuGrad)" stroke="{color}" stroke-width="0.3"/>
                <rect x="3" y="10.75" width="18" height="2.5" rx="1.25" fill="url(#menuGrad)" stroke="{color}" stroke-width="0.3"/>
                <rect x="3" y="17.5" width="18" height="2.5" rx="1.25" fill="url(#menuGrad)" stroke="{color}" stroke-width="0.3"/>
            </svg>
        ''',
        
        'close': '''
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="closeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:{color};stop-opacity:0.7" />
                    </linearGradient>
                </defs>
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" 
                      fill="url(#closeGrad)" stroke="{color}" stroke-width="0.5"/>
            </svg>
        ''',
    }
    
    @staticmethod
    def create_icon(icon_name: str, color: str = "#ffffff", size: int = 24) -> QIcon:
        """
        Kreira QIcon od SVG template-a sa zadatom bojom.
        
        Args:
            icon_name: Ime ikone iz ICONS dict-a
            color: Hex boja (npr. "#667eea")
            size: Veličina ikone u pikselima
            
        Returns:
            QIcon sa renderovanom SVG ikonom
        """
        if icon_name not in SVGIconManager.ICONS:
            # Fallback na play ikonu ako ne postoji
            icon_name = 'play'
        
        # Uzmi SVG template i zameni boju
        svg_template = SVGIconManager.ICONS[icon_name]
        svg_data = svg_template.format(color=color)
        
        # Kreiraj QIcon od SVG-a
        return SVGIconManager._svg_to_icon(svg_data, size)
    
    @staticmethod
    def create_themed_icon(icon_name: str, theme_color: str = None, is_dark: bool = True, size: int = 24) -> QIcon:
        """
        Kreira ikonicu koja automatski bira boju prema temi.
        
        Args:
            icon_name: Ime ikone
            theme_color: Primary boja teme (ako je None, koristi default)
            is_dark: Da li je dark tema (auto-odabir bele/crne)
            size: Veličina
        """
        if theme_color:
            color = theme_color
        else:
            color = "#ffffff" if is_dark else "#333333"
        
        return SVGIconManager.create_icon(icon_name, color, size)
    
    @staticmethod
    def create_colored_icons(icon_name: str, colors: dict, size: int = 24) -> dict:
        """
        Kreira dictionary ikonica sa različitim bojama za hover/pressed state.
        
        Args:
            icon_name: Ime ikone
            colors: Dict sa keys: 'normal', 'hover', 'pressed'
            size: Veličina
            
        Returns:
            Dict sa QIcon za svaki state
        """
        return {
            'normal': SVGIconManager.create_icon(icon_name, colors.get('normal', '#ffffff'), size),
            'hover': SVGIconManager.create_icon(icon_name, colors.get('hover', '#667eea'), size),
            'pressed': SVGIconManager.create_icon(icon_name, colors.get('pressed', '#764ba2'), size),
        }
    
    @staticmethod
    def _svg_to_icon(svg_data: str, size: int = 24) -> QIcon:
        """
        Konvertuje SVG string u QIcon.
        
        Args:
            svg_data: SVG kao string
            size: Veličina ikone
            
        Returns:
            QIcon
        """
        # Konvertuj u bytes
        svg_bytes = QByteArray(svg_data.encode('utf-8'))
        
        # Kreiraj renderer
        renderer = QSvgRenderer(svg_bytes)
        
        # Kreiraj pixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        # Renderuj SVG na pixmap
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
    
    @staticmethod
    def get_icon_names() -> list:
        """Vraća listu svih dostupnih ikonica."""
        return list(SVGIconManager.ICONS.keys())
    
    @staticmethod
    def render_svg_icon(painter: QPainter, icon_name: str, rect, color: str = "#ffffff"):
        """
        Renderuje SVG ikonicu direktno u QPainter.
        Korisno za custom-drawn widgets.
        
        Args:
            painter: QPainter objekat
            icon_name: Ime ikone
            rect: QRectF ili tuple (x, y, width, height) gde treba renderovati
            color: Hex boja
        """
        from PyQt6.QtCore import QRectF
        
        if icon_name not in SVGIconManager.ICONS:
            icon_name = 'play'
        
        # Konvertuj rect ako je tuple
        if isinstance(rect, (tuple, list)):
            rect = QRectF(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
        
        # Uzmi SVG template i zameni boju
        svg_template = SVGIconManager.ICONS[icon_name]
        svg_data = svg_template.format(color=color)
        
        # Kreiraj renderer
        svg_bytes = QByteArray(svg_data.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        
        # Renderuj direktno u painter
        renderer.render(painter, rect)


# Convenience funkcije za brzu upotrebu
def get_icon(name: str, color: str = "#ffffff", size: int = 24) -> QIcon:
    """Brza funkcija za dobijanje ikone."""
    return SVGIconManager.create_icon(name, color, size)


def get_themed_icon(name: str, theme_color: str = None, is_dark: bool = True, size: int = 24) -> QIcon:
    """Brza funkcija za themed ikonu."""
    return SVGIconManager.create_themed_icon(name, theme_color, is_dark, size)


def render_icon(painter, name: str, rect, color: str = "#ffffff"):
    """Brza funkcija za renderovanje ikone u painter."""
    SVGIconManager.render_svg_icon(painter, name, rect, color)


# Primer upotrebe:
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
    import sys
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    central = QWidget()
    layout = QVBoxLayout(central)
    
    # Test različitih ikonica
    for icon_name in ['add', 'delete', 'settings', 'play', 'pause', 'volume']:
        btn = QPushButton(f"{icon_name.title()}")
        btn.setIcon(get_icon(icon_name, "#667eea", 32))
        btn.setIconSize(QSize(32, 32))
        layout.addWidget(btn)
    
    window.setCentralWidget(central)
    window.show()
    sys.exit(app.exec())