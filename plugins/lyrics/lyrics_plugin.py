# -*- coding: utf-8 -*-
# plugins/lyrics/lyrics_plugin.py
"""
Lyrics Plugin - Pretraga i prikaz tekstova pesama

AudioWave Plugin System

Koristi više API-ja sa fallback opcijama:
1. LRCLIB (besplatan, dobar za popularne pesme)
2. lyrics.ovh (besplatan)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QFrame,
    QWidget, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont
from typing import Optional
import urllib.parse
import urllib.request
import json
import re
import ssl


class LyricsSearchThread(QThread):
    """
    Thread za pretragu lyrics-a u pozadini.
    Koristi više izvora sa fallback opcijama.
    """
    
    lyrics_found = pyqtSignal(str, str)  # Tekst pesme, source
    error_occurred = pyqtSignal(str)
    search_started = pyqtSignal()
    search_finished = pyqtSignal()
    status_update = pyqtSignal(str)
    
    def __init__(self, artist: str, title: str):
        super().__init__()
        self.artist = artist.strip()
        self.title = title.strip()
        
        # SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def run(self):
        """Pokreni pretragu kroz više izvora"""
        self.search_started.emit()
        
        # Lista API-ja za pokušaj
        apis = [
            ("LRCLIB", self._try_lrclib),
            ("lyrics.ovh", self._try_lyrics_ovh),
        ]
        
        for api_name, api_func in apis:
            try:
                self.status_update.emit(f"🔍 Trying {api_name}...")
                lyrics = api_func()
                
                if lyrics and len(lyrics) > 30:
                    self.lyrics_found.emit(lyrics, api_name)
                    self.search_finished.emit()
                    return
            except Exception as e:
                print(f"⚠️ {api_name} error: {e}")
                continue
        
        # Ako ništa nije pronađeno
        self.error_occurred.emit(
            f"Lyrics not found for:\n'{self.artist} - {self.title}'"
        )
        self.search_finished.emit()
    
    def _try_lrclib(self) -> Optional[str]:
        """
        LRCLIB API - besplatan API za lyrics
        https://lrclib.net/
        """
        # Search endpoint
        query = f"{self.artist} {self.title}".strip()
        query_encoded = urllib.parse.quote(query)
        
        url = f"https://lrclib.net/api/search?q={query_encoded}"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'AudioWave/0.3.0 (https://github.com/Kosava/AudioWave)')
        
        with urllib.request.urlopen(req, timeout=15, context=self.ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if data and len(data) > 0:
                # Uzmi prvi rezultat
                first_result = data[0]
                
                # Preferiraj plain lyrics
                if first_result.get('plainLyrics'):
                    return first_result['plainLyrics'].strip()
                
                # Fallback na synced lyrics (ukloni timestamps)
                elif first_result.get('syncedLyrics'):
                    synced = first_result['syncedLyrics']
                    # Ukloni [MM:SS.xx] timestamps
                    plain = re.sub(r'\[\d{2}:\d{2}\.\d{2,3}\]\s*', '', synced)
                    return plain.strip()
        
        return None
    
    def _try_lyrics_ovh(self) -> Optional[str]:
        """
        lyrics.ovh API (besplatan, bez ključa)
        """
        if not self.artist:
            return None
        
        artist_encoded = urllib.parse.quote(self.artist)
        title_encoded = urllib.parse.quote(self.title)
        
        url = f"https://api.lyrics.ovh/v1/{artist_encoded}/{title_encoded}"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'AudioWave/0.3.0')
        
        with urllib.request.urlopen(req, timeout=15, context=self.ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if 'lyrics' in data and data['lyrics']:
                return data['lyrics'].strip()
        
        return None


class LyricsDialog(QDialog):
    """
    Glavni Lyrics dialog za prikaz i pretragu tekstova.
    """
    
    def __init__(self, parent=None, engine=None, artist: str = "", title: str = ""):
        super().__init__(parent)
        self.engine = engine  # <- DODATO radi kompatibilnosti sa plugin sistemom
        self.search_thread: Optional[LyricsSearchThread] = None
        self.parent_window = parent
        
        self.setup_ui()
        self.apply_theme_style()
        
        # Ako su prosleđeni artist i title, pokreni pretragu
        if title:
            self.title_input.setText(title)
            if artist:
                self.artist_input.setText(artist)
            QTimer.singleShot(300, self._search_lyrics)
    
    def setup_ui(self):
        self.setWindowTitle("🎤 Lyrics")
        self.setMinimumSize(550, 650)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== SEARCH SECTION =====
        search_frame = QFrame()
        search_frame.setObjectName("lyricsSearchFrame")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setSpacing(10)
        
        # Artist input
        artist_layout = QHBoxLayout()
        artist_label = QLabel("Artist:")
        artist_label.setFixedWidth(50)
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Enter artist name (optional)...")
        self.artist_input.returnPressed.connect(self._search_lyrics)
        artist_layout.addWidget(artist_label)
        artist_layout.addWidget(self.artist_input)
        search_layout.addLayout(artist_layout)
        
        # Title input
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_label.setFixedWidth(50)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter song title...")
        self.title_input.returnPressed.connect(self._search_lyrics)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        search_layout.addLayout(title_layout)
        
        # Search button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.search_btn = QPushButton("🔍 Search Lyrics")
        self.search_btn.clicked.connect(self._search_lyrics)
        self.search_btn.setFixedWidth(150)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(self.search_btn)
        
        search_layout.addLayout(btn_layout)
        layout.addWidget(search_frame)
        
        # ===== STATUS LABEL =====
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("lyricsStatusLabel")
        layout.addWidget(self.status_label)
        
        # ===== LYRICS DISPLAY =====
        lyrics_header = QHBoxLayout()
        lyrics_label = QLabel("📝 Lyrics")
        lyrics_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        lyrics_header.addWidget(lyrics_label)
        
        self.source_label = QLabel("")
        self.source_label.setStyleSheet("color: #888; font-size: 11px;")
        lyrics_header.addStretch()
        lyrics_header.addWidget(self.source_label)
        
        layout.addLayout(lyrics_header)
        
        self.lyrics_text = QTextEdit()
        self.lyrics_text.setReadOnly(True)
        self.lyrics_text.setPlaceholderText(
            "Lyrics will appear here...\n\n"
            "Tips for better results:\n"
            "• Enter both artist and song title\n"
            "• Use original artist name\n"
            "• Remove 'feat.' or featured artists\n"
            "• Use official song title"
        )
        self.lyrics_text.setFont(QFont("Segoe UI", 11))
        self.lyrics_text.setObjectName("lyricsTextEdit")
        layout.addWidget(self.lyrics_text, 1)
        
        # ===== FOOTER =====
        footer_layout = QHBoxLayout()
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(self._copy_lyrics)
        copy_btn.setFixedWidth(80)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_layout.addWidget(copy_btn)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self._clear_lyrics)
        clear_btn.setFixedWidth(80)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_layout.addWidget(clear_btn)
        
        footer_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(80)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def _search_lyrics(self):
        """Pokreni pretragu lyrics-a"""
        artist = self.artist_input.text().strip()
        title = self.title_input.text().strip()
        
        if not title:
            self.status_label.setText("⚠️ Please enter the song title")
            self.status_label.setStyleSheet("color: #e94560;")
            return
        
        # Zaustavi prethodnu pretragu
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.terminate()
            self.search_thread.wait()
        
        # Pokreni novu pretragu
        self.search_thread = LyricsSearchThread(artist, title)
        self.search_thread.search_started.connect(self._on_search_started)
        self.search_thread.status_update.connect(self._on_status_update)
        self.search_thread.lyrics_found.connect(self._on_lyrics_found)
        self.search_thread.error_occurred.connect(self._on_search_error)
        self.search_thread.search_finished.connect(self._on_search_finished)
        self.search_thread.start()
    
    def _on_search_started(self):
        self.search_btn.setEnabled(False)
        self.search_btn.setText("⏳ Searching...")
        self.status_label.setText("🔍 Searching...")
        self.status_label.setStyleSheet("color: #667eea;")
        self.lyrics_text.clear()
        self.source_label.setText("")
    
    def _on_status_update(self, status: str):
        self.status_label.setText(status)
    
    def _on_lyrics_found(self, lyrics: str, source: str):
        self.lyrics_text.setPlainText(lyrics)
        self.status_label.setText("✅ Lyrics found!")
        self.status_label.setStyleSheet("color: #4ade80;")
        self.source_label.setText(f"Source: {source}")
    
    def _on_search_error(self, error: str):
        self.status_label.setText("❌ Not found")
        self.status_label.setStyleSheet("color: #e94560;")
        self.lyrics_text.setPlainText(
            f"{error}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Tips for better results:\n\n"
            "• Make sure artist and title are spelled correctly\n"
            "• Use original language (not translated titles)\n"
            "• Try without featuring artists\n"
            "• Some songs may not have lyrics available\n"
        )
    
    def _on_search_finished(self):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("🔍 Search Lyrics")
    
    def _copy_lyrics(self):
        lyrics = self.lyrics_text.toPlainText()
        if lyrics and "Tips for better results" not in lyrics:
            clipboard = QApplication.clipboard()
            clipboard.setText(lyrics)
            self.status_label.setText("📋 Copied to clipboard!")
            self.status_label.setStyleSheet("color: #4ade80;")
        else:
            self.status_label.setText("⚠️ No lyrics to copy")
            self.status_label.setStyleSheet("color: #e94560;")
    
    def _clear_lyrics(self):
        self.lyrics_text.clear()
        self.artist_input.clear()
        self.title_input.clear()
        self.status_label.setText("")
        self.source_label.setText("")
        self.artist_input.setFocus()
    
    def set_song(self, artist: str, title: str):
        self.artist_input.setText(artist)
        self.title_input.setText(title)
        self._search_lyrics()
    
    def apply_theme_style(self):
        """Primeni stil koji prati temu aplikacije"""
        primary = "#667eea"
        secondary = "#764ba2"
        bg = "#1a1a2e"
        text = "#ffffff"
        
        # Pokušaj izvući da li je dark/light tema
        try:
            if self.parent_window:
                if hasattr(self.parent_window, 'app') and hasattr(self.parent_window.app, 'theme_manager'):
                    tm = self.parent_window.app.theme_manager
                    if not tm.is_dark_theme():
                        bg = "#f0f0f5"
                        text = "#333333"
        except:
            pass
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            
            QLabel {{
                color: {text};
                background: transparent;
            }}
            
            #lyricsSearchFrame {{
                background-color: rgba(102, 126, 234, 0.1);
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 10px;
                padding: 10px;
            }}
            
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid #444;
                border-radius: 6px;
                padding: 10px;
                color: {text};
                font-size: 13px;
            }}
            
            QLineEdit:focus {{
                border-color: {primary};
                background-color: rgba(255, 255, 255, 0.15);
            }}
            
            #lyricsTextEdit {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid #444;
                border-radius: 8px;
                padding: 15px;
                color: {text};
                font-size: 12px;
            }}
            
            QPushButton {{
                background-color: rgba(102, 126, 234, 0.2);
                border: 1px solid {primary};
                border-radius: 6px;
                padding: 10px 16px;
                color: {text};
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: {primary};
            }}
            
            QPushButton:pressed {{
                background-color: {secondary};
            }}
            
            QPushButton:disabled {{
                background-color: #333;
                border-color: #555;
                color: #666;
            }}
        """)


class LyricsWidget(QWidget):
    """Kompaktni Lyrics widget za side panel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("🎤 Lyrics")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        self.lyrics_text = QTextEdit()
        self.lyrics_text.setReadOnly(True)
        self.lyrics_text.setPlaceholderText("No lyrics loaded")
        layout.addWidget(self.lyrics_text)
        
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.clicked.connect(self._open_search)
        layout.addWidget(self.search_btn)
    
    def _open_search(self):
        dialog = LyricsDialog(self)
        dialog.exec()
    
    def set_lyrics(self, lyrics: str):
        self.lyrics_text.setPlainText(lyrics)
    
    def clear_lyrics(self):
        self.lyrics_text.clear()


def show_lyrics_dialog(parent=None, engine=None, artist: str = "", title: str = ""):
    """Prikaži Lyrics dialog."""
    dialog = LyricsDialog(parent, engine, artist, title)
    dialog.exec()
