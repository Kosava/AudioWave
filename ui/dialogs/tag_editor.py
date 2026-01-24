# ui/dialogs/tag_editor_dialog.py
"""
Modern Tag Editor Dialog - View and edit audio file metadata
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QTabWidget, QWidget, QGridLayout,
    QFrame, QFileDialog, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon
from pathlib import Path
import base64
from io import BytesIO

try:
    from core.metadata_reader import MetadataReader
    from core.audio_utils import format_duration, get_file_size_human
    METADATA_AVAILABLE = True
except ImportError:
    print("⚠️ Metadata reader not available")
    METADATA_AVAILABLE = False


class TagEditorDialog(QDialog):
    """Modern Tag Editor Dialog sa Album Art previewom"""
    
    # Signal kada se tagovi sačuvaju
    tags_saved = pyqtSignal(str, dict)  # filepath, metadata
    
    def __init__(self, filepath: str, parent=None):
        super().__init__(parent)
        
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.metadata = {}
        self.original_metadata = {}
        self.album_art_data = None
        
        self.setup_ui()
        self.load_metadata()
        self.apply_modern_style()
        
        # Center dialog
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2
            )
    
    def setup_ui(self):
        """Setup UI komponente"""
        self.setWindowTitle("Edit Metadata")
        self.setMinimumSize(900, 650)
        self.resize(1000, 700)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === HEADER ===
        header = self.create_header()
        main_layout.addWidget(header)
        
        # === CONTENT AREA ===
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Left side - Album Art & File Info
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel)
        
        # Right side - Tag Fields
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 1)
        
        main_layout.addWidget(content_widget, 1)
        
        # === FOOTER - Action Buttons ===
        footer = self.create_footer()
        main_layout.addWidget(footer)
    
    def create_header(self):
        """Kreiraj header sa naslovom i close button"""
        header = QFrame()
        header.setObjectName("dialogHeader")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(25, 15, 25, 15)
        
        # Icon + Title
        icon_label = QLabel("🎵")
        icon_label.setFont(QFont("Arial", 28))
        
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        self.title_label = QLabel("Edit Metadata")
        self.title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.title_label.setObjectName("dialogTitle")
        
        self.filename_label = QLabel(self.filename)
        self.filename_label.setFont(QFont("Arial", 10))
        self.filename_label.setObjectName("dialogSubtitle")
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.filename_label)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_widget)
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(40, 40)
        close_btn.clicked.connect(self.reject)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(close_btn)
        
        return header
    
    def create_left_panel(self):
        """Levi panel - Album Art i File Info"""
        panel = QFrame()
        panel.setObjectName("leftPanel")
        panel.setFixedWidth(300)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Album Art Section
        art_label = QLabel("Album Art")
        art_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        art_label.setObjectName("sectionLabel")
        layout.addWidget(art_label)
        
        # Album art display
        self.album_art_widget = QLabel()
        self.album_art_widget.setObjectName("albumArtWidget")
        self.album_art_widget.setFixedSize(270, 270)
        self.album_art_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_widget.setScaledContents(False)
        
        # Default placeholder
        self.album_art_widget.setText("🖼️\n\nNo Album Art\n\nDrop image here\nor click to browse")
        self.album_art_widget.setWordWrap(True)
        
        # Make clickable
        self.album_art_widget.mousePressEvent = lambda e: self.select_album_art()
        self.album_art_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(self.album_art_widget)
        
        # Album art buttons
        art_buttons = QHBoxLayout()
        art_buttons.setSpacing(8)
        
        self.extract_btn = QPushButton("Extract")
        self.extract_btn.setObjectName("smallButton")
        self.extract_btn.clicked.connect(self.extract_album_art)
        self.extract_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.remove_art_btn = QPushButton("Remove")
        self.remove_art_btn.setObjectName("smallButton")
        self.remove_art_btn.clicked.connect(self.remove_album_art)
        self.remove_art_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        art_buttons.addWidget(self.extract_btn)
        art_buttons.addWidget(self.remove_art_btn)
        
        layout.addLayout(art_buttons)
        
        # File Info Section
        info_label = QLabel("📄 File Information")
        info_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        info_label.setObjectName("sectionLabel")
        layout.addWidget(info_label)
        
        # Info widget
        self.info_widget = QFrame()
        self.info_widget.setObjectName("infoWidget")
        info_layout = QVBoxLayout(self.info_widget)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(8)
        
        # Will be populated in load_metadata()
        self.info_labels = {}
        
        layout.addWidget(self.info_widget)
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self):
        """Desni panel - Tag fields sa tabovima"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tagTabs")
        
        # Tab 1: Basic Tags
        basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(basic_tab, "📋 Basic Tags")
        
        # Tab 2: Extended Tags
        extended_tab = self.create_extended_tab()
        self.tab_widget.addTab(extended_tab, "🎼 Extended")
        
        # Tab 3: Lyrics
        lyrics_tab = self.create_lyrics_tab()
        self.tab_widget.addTab(lyrics_tab, "📝 Lyrics")
        
        layout.addWidget(self.tab_widget)
        
        return panel
    
    def create_basic_tab(self):
        """Basic tags tab"""
        tab = QWidget()
        
        # Scroll area za tab
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Field storage
        self.fields = {}
        
        row = 0
        
        # Title
        layout.addWidget(self.create_label("Title"), row, 0)
        self.fields['title'] = self.create_input()
        layout.addWidget(self.fields['title'], row, 1)
        row += 1
        
        # Artist
        layout.addWidget(self.create_label("Artist"), row, 0)
        self.fields['artist'] = self.create_input()
        layout.addWidget(self.fields['artist'], row, 1)
        row += 1
        
        # Album
        layout.addWidget(self.create_label("Album"), row, 0)
        self.fields['album'] = self.create_input()
        layout.addWidget(self.fields['album'], row, 1)
        row += 1
        
        # Album Artist
        layout.addWidget(self.create_label("Album Artist"), row, 0)
        self.fields['album_artist'] = self.create_input()
        layout.addWidget(self.fields['album_artist'], row, 1)
        row += 1
        
        # Year & Genre (2 columns)
        year_genre_layout = QHBoxLayout()
        year_genre_layout.setSpacing(12)
        
        year_widget = QWidget()
        year_layout = QVBoxLayout(year_widget)
        year_layout.setContentsMargins(0, 0, 0, 0)
        year_layout.setSpacing(4)
        year_layout.addWidget(self.create_label("Year"))
        self.fields['date'] = self.create_input()
        self.fields['date'].setMaximumWidth(100)
        year_layout.addWidget(self.fields['date'])
        
        genre_widget = QWidget()
        genre_layout = QVBoxLayout(genre_widget)
        genre_layout.setContentsMargins(0, 0, 0, 0)
        genre_layout.setSpacing(4)
        genre_layout.addWidget(self.create_label("Genre"))
        self.fields['genre'] = self.create_input()
        genre_layout.addWidget(self.fields['genre'])
        
        year_genre_layout.addWidget(year_widget)
        year_genre_layout.addWidget(genre_widget, 1)
        
        layout.addLayout(year_genre_layout, row, 0, 1, 2)
        row += 1
        
        # Track & Disc numbers
        track_disc_layout = QHBoxLayout()
        track_disc_layout.setSpacing(8)
        
        # Track #
        track_disc_layout.addWidget(self.create_label("Track #"))
        self.fields['track'] = self.create_input()
        self.fields['track'].setMaximumWidth(60)
        self.fields['track'].setAlignment(Qt.AlignmentFlag.AlignCenter)
        track_disc_layout.addWidget(self.fields['track'])
        
        track_disc_layout.addWidget(QLabel("of"))
        self.fields['total_tracks'] = self.create_input()
        self.fields['total_tracks'].setMaximumWidth(60)
        self.fields['total_tracks'].setAlignment(Qt.AlignmentFlag.AlignCenter)
        track_disc_layout.addWidget(self.fields['total_tracks'])
        
        track_disc_layout.addWidget(QLabel("  "))
        
        # Disc #
        track_disc_layout.addWidget(self.create_label("Disc #"))
        self.fields['disc'] = self.create_input()
        self.fields['disc'].setMaximumWidth(60)
        self.fields['disc'].setAlignment(Qt.AlignmentFlag.AlignCenter)
        track_disc_layout.addWidget(self.fields['disc'])
        
        track_disc_layout.addWidget(QLabel("of"))
        self.fields['total_discs'] = self.create_input()
        self.fields['total_discs'].setMaximumWidth(60)
        self.fields['total_discs'].setAlignment(Qt.AlignmentFlag.AlignCenter)
        track_disc_layout.addWidget(self.fields['total_discs'])
        
        track_disc_layout.addStretch()
        
        layout.addLayout(track_disc_layout, row, 0, 1, 2)
        row += 1
        
        layout.setRowStretch(row, 1)
        
        scroll.setWidget(content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        
        return tab
    
    def create_extended_tab(self):
        """Extended tags tab"""
        tab = QWidget()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QGridLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        row = 0
        
        # Composer
        layout.addWidget(self.create_label("Composer"), row, 0)
        self.fields['composer'] = self.create_input()
        layout.addWidget(self.fields['composer'], row, 1)
        row += 1
        
        # Publisher
        layout.addWidget(self.create_label("Publisher"), row, 0)
        self.fields['publisher'] = self.create_input()
        layout.addWidget(self.fields['publisher'], row, 1)
        row += 1
        
        # Copyright
        layout.addWidget(self.create_label("Copyright"), row, 0)
        self.fields['copyright'] = self.create_input()
        layout.addWidget(self.fields['copyright'], row, 1)
        row += 1
        
        # BPM
        layout.addWidget(self.create_label("BPM"), row, 0)
        self.fields['bpm'] = self.create_input()
        self.fields['bpm'].setMaximumWidth(100)
        layout.addWidget(self.fields['bpm'], row, 1)
        row += 1
        
        # Comment
        layout.addWidget(self.create_label("Comment"), row, 0, Qt.AlignmentFlag.AlignTop)
        self.fields['comment'] = QTextEdit()
        self.fields['comment'].setObjectName("textInput")
        self.fields['comment'].setMaximumHeight(120)
        layout.addWidget(self.fields['comment'], row, 1)
        row += 1
        
        layout.setRowStretch(row, 1)
        
        scroll.setWidget(content)
        
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        
        return tab
    
    def create_lyrics_tab(self):
        """Lyrics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        label = QLabel("Lyrics")
        label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(label)
        
        self.fields['lyrics'] = QTextEdit()
        self.fields['lyrics'].setObjectName("lyricsInput")
        self.fields['lyrics'].setPlaceholderText("Paste lyrics here...")
        layout.addWidget(self.fields['lyrics'])
        
        return tab
    
    def create_footer(self):
        """Footer sa action buttons"""
        footer = QFrame()
        footer.setObjectName("dialogFooter")
        footer.setFixedHeight(80)
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(10)
        
        layout.addStretch()
        
        # Save button
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.setMinimumWidth(150)
        self.save_btn.setMinimumHeight(45)
        self.save_btn.clicked.connect(self.save_tags)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Reload button
        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.setObjectName("reloadButton")
        self.reload_btn.setMinimumHeight(45)
        self.reload_btn.clicked.connect(self.load_metadata)
        self.reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(self.save_btn)
        layout.addWidget(self.reload_btn)
        layout.addWidget(cancel_btn)
        
        return footer
    
    def create_label(self, text):
        """Kreiraj label za formu"""
        label = QLabel(text)
        label.setFont(QFont("Arial", 10, QFont.Weight.Medium))
        label.setObjectName("fieldLabel")
        return label
    
    def create_input(self):
        """Kreiraj input field"""
        input_field = QLineEdit()
        input_field.setObjectName("fieldInput")
        input_field.setMinimumHeight(35)
        return input_field
    
    def load_metadata(self):
        """Učitaj metadata iz fajla"""
        if not METADATA_AVAILABLE:
            QMessageBox.warning(self, "Error", "Metadata reader not available")
            return
        
        try:
            reader = MetadataReader()
            self.metadata = reader.read_metadata(self.filepath)
            self.original_metadata = self.metadata.copy()
            
            # Populate fields
            self.fields['title'].setText(self.metadata.get('title', ''))
            self.fields['artist'].setText(self.metadata.get('artist', ''))
            self.fields['album'].setText(self.metadata.get('album', ''))
            self.fields['album_artist'].setText(self.metadata.get('album_artist', ''))
            self.fields['date'].setText(self.metadata.get('date', ''))
            self.fields['genre'].setText(self.metadata.get('genre', ''))
            
            # Track numbers
            track = self.metadata.get('track', '0')
            self.fields['track'].setText(track.split('/')[0] if '/' in track else track)
            self.fields['total_tracks'].setText(track.split('/')[1] if '/' in track else '')
            
            disc = self.metadata.get('disc', '0')
            self.fields['disc'].setText(disc.split('/')[0] if '/' in disc else disc)
            self.fields['total_discs'].setText(disc.split('/')[1] if '/' in disc else '')
            
            # Extended fields
            self.fields['composer'].setText(self.metadata.get('composer', ''))
            self.fields['publisher'].setText(self.metadata.get('publisher', ''))
            self.fields['copyright'].setText(self.metadata.get('copyright', ''))
            self.fields['bpm'].setText(str(self.metadata.get('bpm', '')))
            self.fields['comment'].setPlainText(self.metadata.get('comment', ''))
            self.fields['lyrics'].setPlainText(self.metadata.get('lyrics', ''))
            
            # Load album art
            if self.metadata.get('has_artwork') and self.metadata.get('artwork_data'):
                self.load_album_art(self.metadata['artwork_data'])
            
            # Update file info
            self.update_file_info()
            
            print(f"✅ Loaded metadata for: {self.filename}")
            
        except Exception as e:
            print(f"❌ Error loading metadata: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load metadata:\n{e}")
    
    def update_file_info(self):
        """Ažuriraj file info panel"""
        # Clear previous
        for i in reversed(range(self.info_widget.layout().count())):
            self.info_widget.layout().itemAt(i).widget().deleteLater()
        
        info_layout = self.info_widget.layout()
        
        info_items = [
            ("Format:", self.metadata.get('file_format', 'Unknown').upper()),
            ("Duration:", format_duration(self.metadata.get('duration', 0))),
            ("Bitrate:", f"{self.metadata.get('bitrate', 0) // 1000} kbps"),
            ("Sample Rate:", f"{self.metadata.get('sample_rate', 0)} Hz"),
            ("Size:", get_file_size_human(self.filepath))
        ]
        
        for key, value in info_items:
            row = QHBoxLayout()
            row.setSpacing(8)
            
            key_label = QLabel(key)
            key_label.setObjectName("infoKey")
            key_label.setFont(QFont("Arial", 9))
            
            value_label = QLabel(value)
            value_label.setObjectName("infoValue")
            value_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            
            row.addWidget(key_label)
            row.addStretch()
            row.addWidget(value_label)
            
            container = QWidget()
            container.setLayout(row)
            info_layout.addWidget(container)
    
    def load_album_art(self, art_data: str):
        """Load album art from base64"""
        try:
            # Decode base64
            image_data = base64.b64decode(art_data)
            
            # Create pixmap
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            if not pixmap.isNull():
                # Scale to fit
                scaled = pixmap.scaled(
                    270, 270,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.album_art_widget.setPixmap(scaled)
                self.album_art_data = art_data
                print("✅ Album art loaded")
        except Exception as e:
            print(f"❌ Error loading album art: {e}")
    
    def select_album_art(self):
        """Select album art image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Album Art",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            try:
                # Load and encode image
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                    art_data = base64.b64encode(image_data).decode('utf-8')
                    self.load_album_art(art_data)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load image:\n{e}")
    
    def extract_album_art(self):
        """Extract album art to file"""
        if not self.album_art_data:
            QMessageBox.information(self, "No Album Art", "This file has no album art to extract.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Album Art",
            str(Path.home() / "cover.jpg"),
            "JPEG Image (*.jpg);;PNG Image (*.png)"
        )
        
        if file_path:
            try:
                image_data = base64.b64decode(self.album_art_data)
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                QMessageBox.information(self, "Success", f"Album art saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save album art:\n{e}")
    
    def remove_album_art(self):
        """Remove album art"""
        self.album_art_widget.clear()
        self.album_art_widget.setText("🖼️\n\nNo Album Art\n\nDrop image here\nor click to browse")
        self.album_art_data = None
        print("🗑️ Album art removed")
    
    def save_tags(self):
        """Save tags (currently read-only, will implement writer later)"""
        QMessageBox.information(
            self,
            "Coming Soon",
            "Tag writing will be implemented in the next phase!\n\n"
            "For now, you can view and edit metadata (not saved yet)."
        )
        
        # TODO: Implement tag writing in next phase
        # self.tags_saved.emit(self.filepath, self.get_current_values())
        # self.accept()
    
    def get_current_values(self):
        """Get current field values"""
        return {
            'title': self.fields['title'].text(),
            'artist': self.fields['artist'].text(),
            'album': self.fields['album'].text(),
            'album_artist': self.fields['album_artist'].text(),
            'date': self.fields['date'].text(),
            'genre': self.fields['genre'].text(),
            'track': self.fields['track'].text(),
            'disc': self.fields['disc'].text(),
            'composer': self.fields['composer'].text(),
            'publisher': self.fields['publisher'].text(),
            'copyright': self.fields['copyright'].text(),
            'bpm': self.fields['bpm'].text(),
            'comment': self.fields['comment'].toPlainText(),
            'lyrics': self.fields['lyrics'].toPlainText(),
        }
    
    def apply_modern_style(self):
        """Apply modern dark theme styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
            }
            
            QFrame#dialogHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #8b5cf6);
                border: none;
            }
            
            QLabel#dialogTitle {
                color: white;
            }
            
            QLabel#dialogSubtitle {
                color: #bfdbfe;
            }
            
            QPushButton#closeButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 18px;
            }
            
            QPushButton#closeButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            
            QFrame#leftPanel {
                background-color: rgba(15, 23, 42, 0.5);
                border-right: 1px solid #334155;
                border-radius: 0;
            }
            
            QLabel#sectionLabel {
                color: #cbd5e1;
            }
            
            QLabel#albumArtWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(59, 130, 246, 0.2),
                    stop:1 rgba(139, 92, 246, 0.2));
                border: 2px dashed #475569;
                border-radius: 12px;
                color: #64748b;
                font-size: 12px;
            }
            
            QLabel#albumArtWidget:hover {
                border-color: #3b82f6;
            }
            
            QPushButton#smallButton {
                background-color: rgba(51, 65, 85, 0.5);
                border: none;
                border-radius: 6px;
                color: #cbd5e1;
                padding: 8px;
                font-size: 11px;
            }
            
            QPushButton#smallButton:hover {
                background-color: #334155;
            }
            
            QFrame#infoWidget {
                background-color: rgba(30, 41, 59, 0.5);
                border: 1px solid rgba(51, 65, 85, 0.3);
                border-radius: 12px;
            }
            
            QLabel#infoKey {
                color: #64748b;
            }
            
            QLabel#infoValue {
                color: #cbd5e1;
            }
            
            QTabWidget#tagTabs::pane {
                border: 1px solid #334155;
                border