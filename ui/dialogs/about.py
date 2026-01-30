# -*- coding: utf-8 -*-
# ui/dialogs/about.py
"""
About Dialog - Informacije o AudioWave aplikaciji

Prikazuje informacije o aplikaciji, autoru i licenci.
✅ SA BUY ME A COFFEE DUGMETOM!
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QDesktopServices
from PyQt6.QtCore import QUrl


# ===== APLIKACIONE KONSTANTE =====
APP_VERSION = "0.3.1"
APP_NAME = "AudioWave"
APP_DESCRIPTION = "Modern desktop music player with theme support"
AUTHOR_NAME = "Košava"
AUTHOR_GITHUB = "https://github.com/Kosava"
PROJECT_URL = "https://github.com/Kosava/AudioWave"
BUY_ME_COFFEE_URL = "https://buymeacoffee.com/kosava"  # ✅ BUY ME A COFFEE LINK
LICENSE = "MIT License"
COPYRIGHT_YEAR = "2025"


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
        self.setFixedSize(420, 520)
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
                icon_label.setText("♪")
                icon_label.setFont(QFont("Segoe UI Emoji", 48))
        except:
            icon_label.setText("♪")
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
        
        # ===== CONTENT =====
        content_widget = QWidget()
        content_widget.setObjectName("aboutContent")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(30, 20, 30, 20)
        
        # Opis
        desc_label = QLabel(APP_DESCRIPTION)
        desc_label.setObjectName("descLabel")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)
        
        # Info sekcija
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(15, 15, 15, 15)
        
        # Autor
        author_row = self._create_info_row("Author:", AUTHOR_NAME)
        info_layout.addLayout(author_row)
        
        # Licenca
        license_row = self._create_info_row("License:", LICENSE)
        info_layout.addLayout(license_row)
        
        # Copyright
        copyright_row = self._create_info_row("Copyright:", f"{COPYRIGHT_YEAR} {AUTHOR_NAME}")
        info_layout.addLayout(copyright_row)
        
        content_layout.addWidget(info_frame)
        
        # ===== LINKOVI =====
        links_layout = QHBoxLayout()
        links_layout.setSpacing(15)
        
        # GitHub button
        github_btn = QPushButton("GitHub")
        github_btn.setObjectName("linkButton")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.clicked.connect(self._open_github)
        github_btn.setToolTip(AUTHOR_GITHUB)
        links_layout.addWidget(github_btn)
        
        # Project page button
        project_btn = QPushButton("Project Page")
        project_btn.setObjectName("linkButton")
        project_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        project_btn.clicked.connect(self._open_project)
        project_btn.setToolTip(PROJECT_URL)
        links_layout.addWidget(project_btn)
        
        content_layout.addLayout(links_layout)
        
        # ===== ☕ BUY ME A COFFEE DUGME ===== ✅ NOVO!
        coffee_layout = QHBoxLayout()
        coffee_layout.setContentsMargins(0, 8, 0, 0)
        
        coffee_btn = QPushButton("☕ Buy Me a Coffee")
        coffee_btn.setObjectName("coffeeButton")
        coffee_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        coffee_btn.clicked.connect(self._open_coffee)  # ✅ Povezano sa metodom
        coffee_btn.setToolTip("Support the development")
        coffee_layout.addWidget(coffee_btn)
        
        content_layout.addLayout(coffee_layout)
        # ===== KRAJ COFFEE DUGMETA =====
        
        # Spacer
        content_layout.addStretch()
        
        # Technologies
        tech_label = QLabel("Built with Python 3.11+ • PyQt6 • Mutagen")
        tech_label.setObjectName("techLabel")
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(tech_label)
        
        layout.addWidget(content_widget, 1)
        
        # ===== FOOTER =====
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
    
    def _create_info_row(self, label_text: str, value_text: str) -> QHBoxLayout:
        """
        Kreira red sa labelom i vrednošću.
        
        Args:
            label_text: Tekst labele
            value_text: Tekst vrednosti
            
        Returns:
            QHBoxLayout sa labelom i vrednošću
        """
        row = QHBoxLayout()
        
        label = QLabel(label_text)
        label.setObjectName("infoLabel")
        label.setFixedWidth(100)
        
        value = QLabel(value_text)
        value.setObjectName("infoValue")
        
        row.addWidget(label)
        row.addWidget(value, 1)
        
        return row
    
    def _open_github(self):
        """Otvori GitHub stranicu autora."""
        QDesktopServices.openUrl(QUrl(AUTHOR_GITHUB))
    
    def _open_project(self):
        """Otvori stranicu projekta."""
        QDesktopServices.openUrl(QUrl(PROJECT_URL))
    
    def _open_coffee(self):
        """✅ Otvori Buy Me a Coffee stranicu."""
        print(f"☕ Opening Buy Me a Coffee: {BUY_ME_COFFEE_URL}")
        QDesktopServices.openUrl(QUrl(BUY_ME_COFFEE_URL))
    
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
            #aboutContent {
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
            
            /* ☕ Coffee Button - NARANDŽASTO-ŽUTI GRADIENT */
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
                icon_label.setText("♪")
                icon_label.setFont(QFont("Segoe UI Emoji", 36))
        except:
            icon_label.setText("♪")
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
        
        # ===== OPIS =====
        desc_label = QLabel(APP_DESCRIPTION)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #aaa; padding: 10px;")
        layout.addWidget(desc_label)
        
        # ===== INFO =====
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        info_data = [
            ("Author", AUTHOR_NAME),
            ("License", LICENSE),
            ("Copyright", f"{COPYRIGHT_YEAR} {AUTHOR_NAME}"),
        ]
        
        for label, value in info_data:
            row = QHBoxLayout()
            lbl = QLabel(f"<b>{label}:</b>")
            lbl.setFixedWidth(80)
            val = QLabel(value)
            row.addWidget(lbl)
            row.addWidget(val, 1)
            info_layout.addLayout(row)
        
        layout.addLayout(info_layout)
        
        # ===== LINKOVI =====
        links_layout = QHBoxLayout()
        links_layout.setSpacing(10)
        
        github_btn = QPushButton("GitHub")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(AUTHOR_GITHUB)))
        links_layout.addWidget(github_btn)
        
        project_btn = QPushButton("Project")
        project_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        project_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL)))
        links_layout.addWidget(project_btn)
        
        layout.addLayout(links_layout)
        
        # ===== ☕ BUY ME A COFFEE - ISPOD GITHUB/PROJECT =====
        coffee_layout = QHBoxLayout()
        coffee_layout.setContentsMargins(0, 10, 0, 0)
        
        coffee_btn = QPushButton("☕ Buy Me a Coffee")
        coffee_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        coffee_btn.setToolTip("Support development if you enjoy this project")
        coffee_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF813F,
                    stop:1 #FFBD39
                );
                border: none;
                border-radius: 6px;
                color: white;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF9155,
                    stop:1 #FFCA55
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E67329,
                    stop:1 #E6A823
                );
            }
        """)
        coffee_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(BUY_ME_COFFEE_URL)))
        coffee_layout.addWidget(coffee_btn)
        
        layout.addLayout(coffee_layout)
        
        # Spacer
        layout.addStretch()
        
        # Tech info
        tech_label = QLabel("Built with Python 3.11+ • PyQt6 • Mutagen")
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(tech_label)


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
        "buy_me_coffee": BUY_ME_COFFEE_URL,  # ✅ COFFEE LINK
        "license": LICENSE,
        "copyright_year": COPYRIGHT_YEAR,
    }


# ===== TEST =====
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = AboutDialog()
    dialog.show()
    
    sys.exit(app.exec())