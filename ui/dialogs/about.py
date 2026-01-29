# -*- coding: utf-8 -*-
# ui/dialogs/about.py
"""
About Dialog - Informacije o AudioWave aplikaciji

Prikazuje informacije o aplikaciji, autoru i licenci.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QWidget, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QFont, QDesktopServices
from ui.utils.svg_icon_manager import get_icon


# ===== APLIKACIONE KONSTANTE =====
APP_VERSION = "0.3.1"
APP_NAME = "AudioWave"
APP_DESCRIPTION = "Modern desktop music player with theme support"
AUTHOR_NAME = "Košava"
AUTHOR_GITHUB = "https://github.com/Kosava"
PROJECT_URL = "https://github.com/Kosava/AudioWave"
BUY_ME_COFFEE_URL = "https://buymeacoffee.com/kosava"
LICENSE = "MIT License"
COPYRIGHT_YEAR = "2025"


def create_coffee_button(parent=None):
    """
    Kreira Buy Me a Coffee dugme sa SVG ikonom i fade-in animacijom.
    
    Args:
        parent: Roditeljski widget
        
    Returns:
        QPushButton sa ikonom i animacijom
    """
    btn = QPushButton("Buy Me a Coffee")
    if parent:
        btn.setParent(parent)
    
    btn.setObjectName("coffeeButton")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    
    # Postavi SVG ikonu
    coffee_icon = get_icon("coffee", "#ffffff", 18)
    btn.setIcon(coffee_icon)
    btn.setIconSize(QSize(18, 18))
    
    # Poveži klik
    btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(BUY_ME_COFFEE_URL)))
    
    # Dodaj fade-in animaciju
    effect = QGraphicsOpacityEffect(btn)
    btn.setGraphicsEffect(effect)
    
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(600)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    # Pokreni animaciju kad se dugme prikaže
    anim.start()
    
    # Sačuvaj referencu da GC ne bi uništio animaciju
    btn._fade_anim = anim
    
    return btn


def build_about_content(parent=None, include_footer=True):
    """
    Kreira centralni About sadržaj koji se koristi
    i u AboutDialog i u AboutWidget.
    
    Args:
        parent: Roditeljski widget
        include_footer: Da li da uključi footer sa dugmetom za zatvaranje
        
    Returns:
        QWidget sa about sadržajem
    """
    container = QWidget(parent)
    layout = QVBoxLayout(container)
    layout.setSpacing(16)
    layout.setContentsMargins(30, 20, 30, 20)
    
    # ===== OPIS =====
    desc = QLabel(APP_DESCRIPTION)
    desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    desc.setWordWrap(True)
    desc.setObjectName("descLabel")
    layout.addWidget(desc)
    
    # ===== INFO SEKCUA =====
    info = QFrame()
    info.setObjectName("infoFrame")
    info_layout = QVBoxLayout(info)
    info_layout.setSpacing(8)
    info_layout.setContentsMargins(15, 15, 15, 15)
    
    def create_info_row(label_text, value_text):
        """Kreira red sa labelom i vrednošću."""
        row = QHBoxLayout()
        
        label = QLabel(label_text)
        label.setFixedWidth(90)
        label.setObjectName("infoLabel")
        
        value = QLabel(value_text)
        value.setObjectName("infoValue")
        
        row.addWidget(label)
        row.addWidget(value, 1)
        return row
    
    # Autor
    info_layout.addLayout(create_info_row("Author:", AUTHOR_NAME))
    
    # Licenca
    info_layout.addLayout(create_info_row("License:", LICENSE))
    
    # Copyright
    info_layout.addLayout(create_info_row("Copyright:", f"{COPYRIGHT_YEAR} {AUTHOR_NAME}"))
    
    layout.addWidget(info)
    
    # ===== LINK DUGMAD =====
    links = QHBoxLayout()
    links.setSpacing(15)
    
    # GitHub dugme
    github_btn = QPushButton("GitHub")
    github_btn.setObjectName("linkButton")
    github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(AUTHOR_GITHUB)))
    github_btn.setToolTip(AUTHOR_GITHUB)
    links.addWidget(github_btn)
    
    # Project dugme
    project_btn = QPushButton("Project Page")
    project_btn.setObjectName("linkButton")
    project_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    project_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL)))
    project_btn.setToolTip(PROJECT_URL)
    links.addWidget(project_btn)
    
    layout.addLayout(links)
    
    # ===== BUY ME A COFFEE DUGME =====
    coffee_btn = create_coffee_button(container)
    layout.addWidget(coffee_btn, 0, Qt.AlignmentFlag.AlignCenter)
    
    # Spacer
    layout.addStretch(1)
    
    # ===== TECH INFO =====
    tech_label = QLabel("Built with Python 3.11+ • PyQt6 • Mutagen")
    tech_label.setObjectName("techLabel")
    tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(tech_label)
    
    return container


class AboutDialog(QDialog):
    """
    About dialog - prikazuje informacije o aplikaciji.
    
    Attributes:
        parent: Roditeljski widget
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()
        self.apply_style()
    
    def setup_ui(self):
        """Postavi UI komponente."""
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(420, 580)  # Dovoljna visina za coffee dugme
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowCloseButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ===== HEADER SA IKONOM =====
        header_widget = QWidget()
        header_widget.setObjectName("aboutHeader")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(20, 30, 20, 20)
        
        # Ikona aplikacije
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            pixmap = QPixmap("resources/icons/audiowave_color.png")
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    80, 80, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_label.setPixmap(scaled_pixmap)
            else:
                icon_label.setText("♪")  # Fallback: music note
                icon_label.setFont(QFont("Segoe UI Emoji", 48))
        except:
            icon_label.setText("♪")  # Fallback: music note
            icon_label.setFont(QFont("Segoe UI Emoji", 48))
        
        header_layout.addWidget(icon_label)
        
        # Ime aplikacije
        name_label = QLabel(APP_NAME)
        name_label.setObjectName("appNameLabel")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(name_label)
        
        # Verzija
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(version_label)
        
        layout.addWidget(header_widget)
        
        # ===== SEPARATOR =====
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("aboutSeparator")
        layout.addWidget(separator)
        
        # ===== CENTRALNI SADRŽAJ (SHARED) =====
        content = build_about_content(self)
        layout.addWidget(content, 1)
        
        # ===== FOOTER (SAMO ZA DIALOG) =====
        footer_widget = QWidget()
        footer_widget.setObjectName("aboutFooter")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(20, 15, 20, 15)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        
        footer_layout.addStretch()
        footer_layout.addWidget(close_btn)
        footer_layout.addStretch()
        
        layout.addWidget(footer_widget)
    
    def apply_style(self):
        """Primeni stil na dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            
            /* Header */
            #aboutHeader {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea,
                    stop:1 #764ba2
                );
            }
            
            #appNameLabel {
                font-size: 24px;
                font-weight: bold;
                color: white;
                letter-spacing: 2px;
            }
            
            #versionLabel {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.8);
            }
            
            /* Separator */
            #aboutSeparator {
                background-color: #667eea;
                max-height: 2px;
            }
            
            /* Content */
            QWidget {
                background-color: #1a1a2e;
            }
            
            #descLabel {
                font-size: 14px;
                color: #b0b0b0;
                padding: 10px;
            }
            
            /* Info Frame */
            #infoFrame {
                background-color: rgba(102, 126, 234, 0.1);
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 8px;
            }
            
            #infoLabel {
                font-size: 13px;
                color: #888888;
            }
            
            #infoValue {
                font-size: 13px;
                color: #e0e0e0;
                font-weight: 500;
            }
            
            /* Link Buttons */
            #linkButton {
                background-color: transparent;
                border: 1px solid #667eea;
                border-radius: 6px;
                color: #667eea;
                padding: 8px 20px;
                font-size: 13px;
            }
            
            #linkButton:hover {
                background-color: rgba(102, 126, 234, 0.2);
                color: white;
            }
            
            #linkButton:pressed {
                background-color: rgba(102, 126, 234, 0.4);
            }
            
            /* Coffee Button */
            #coffeeButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF813F,
                    stop:1 #FFBD39
                );
                border: none;
                border-radius: 6px;
                color: white;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 600;
            }
            
            #coffeeButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF9155,
                    stop:1 #FFCA55
                );
            }
            
            #coffeeButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E67329,
                    stop:1 #E6A823
                );
            }
            
            /* Tech Label */
            #techLabel {
                font-size: 11px;
                color: #666666;
                padding: 5px;
            }
            
            /* Footer */
            #aboutFooter {
                background-color: #16162a;
                border-top: 1px solid #2a2a4a;
            }
            
            #closeButton {
                background-color: #667eea;
                border: none;
                border-radius: 6px;
                color: white;
                padding: 10px 30px;
                font-size: 13px;
                font-weight: 500;
            }
            
            #closeButton:hover {
                background-color: #7b8eef;
            }
            
            #closeButton:pressed {
                background-color: #5a6fd6;
            }
        """)
    
    def show_dialog(self):
        """Prikaži dialog."""
        self.exec()


# ===== WIDGET ZA UGRAĐIVANJE U SETTINGS =====
class AboutWidget(QWidget):
    """
    About widget - može se ugraditi u Settings kao tab.
    Isti sadržaj kao AboutDialog ali bez dugmadi za zatvaranje.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_widget_style()
    
    def setup_ui(self):
        """Postavi UI komponente."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== HEADER =====
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(10)
        
        # Ikona
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            pixmap = QPixmap("resources/icons/audiowave_color.png")
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    64, 64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_label.setPixmap(scaled_pixmap)
            else:
                icon_label.setText("♪")  # Fallback: music note
                icon_label.setFont(QFont("Segoe UI Emoji", 36))
        except:
            icon_label.setText("♪")  # Fallback: music note
            icon_label.setFont(QFont("Segoe UI Emoji", 36))
        
        header_layout.addWidget(icon_label)
        
        # Ime i verzija
        name_label = QLabel(f"<b style='font-size: 20px;'>{APP_NAME}</b>")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(name_label)
        
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #888;")
        header_layout.addWidget(version_label)
        
        layout.addLayout(header_layout)
        
        # ===== CENTRALNI SADRŽAJ (SHARED) =====
        content = build_about_content(self, include_footer=False)
        layout.addWidget(content, 1)
    
    def apply_widget_style(self):
        """Primeni stil na widget."""
        self.setStyleSheet("""
            AboutWidget {
                background-color: transparent;
            }
            
            #descLabel {
                color: #aaa;
                padding: 10px;
            }
            
            #infoFrame {
                background-color: rgba(102, 126, 234, 0.1);
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 8px;
            }
            
            #infoLabel {
                color: #888;
            }
            
            #infoValue {
                color: #e0e0e0;
            }
            
            /* Link Buttons */
            #linkButton {
                background-color: transparent;
                border: 1px solid #667eea;
                border-radius: 6px;
                color: #667eea;
                padding: 8px 20px;
                font-size: 13px;
            }
            
            #linkButton:hover {
                background-color: rgba(102, 126, 234, 0.2);
                color: white;
            }
            
            /* Coffee Button */
            #coffeeButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF813F,
                    stop:1 #FFBD39
                );
                border: none;
                border-radius: 6px;
                color: white;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 600;
            }
            
            #coffeeButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF9155,
                    stop:1 #FFCA55
                );
            }
            
            /* Tech Label */
            #techLabel {
                color: #666;
                font-size: 11px;
            }
        """)


# ===== HELPER FUNKCIJE =====
def show_about_dialog(parent=None):
    """
    Helper funkcija za prikaz About dialoga.
    
    Args:
        parent: Roditeljski widget (opciono)
    """
    dialog = AboutDialog(parent)
    dialog.show_dialog()


def get_app_info() -> dict:
    """
    Vraća informacije o aplikaciji kao dictionary.
    
    Returns:
        Dict sa APP_NAME, APP_VERSION, itd.
    """
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "author": AUTHOR_NAME,
        "github": AUTHOR_GITHUB,
        "project_url": PROJECT_URL,
        "buy_me_coffee": BUY_ME_COFFEE_URL,
        "license": LICENSE,
        "copyright_year": COPYRIGHT_YEAR,
    }


# ===== TEST =====
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QTabWidget
    
    app = QApplication(sys.argv)
    
    # Testiraj dialog
    dialog = AboutDialog()
    dialog.show()
    
    # Testiraj widget u tab-u
    # tabs = QTabWidget()
    # tabs.addTab(AboutWidget(), "About")
    # tabs.show()
    
    sys.exit(app.exec())