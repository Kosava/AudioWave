# ui/dialogs/tag_editor_dialog.py
"""
Modern Tag Editor Dialog - View and edit audio file metadata
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QTabWidget, QWidget, QGridLayout,
    QFrame, QFileDialog, QMessageBox, QScrollArea, QPlainTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon
from pathlib import Path
import base64
from io import BytesIO

try:
    from core.metadata_reader import MetadataReader, read_metadata
    METADATA_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Metadata reader not available: {e}")
    METADATA_AVAILABLE = False

try:
    import mutagen
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, TRCK, COMM, TCOM, TPE2, USLT
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Mutagen not available for writing: {e}")
    MUTAGEN_AVAILABLE = False


class TagEditorDialog(QDialog):
    """Modern Tag Editor Dialog - COMPLETE with read/write"""
    
    tags_saved = pyqtSignal(str, dict)
    
    def __init__(self, filepath: str, parent=None):
        super().__init__(parent)
        
        self.filepath = filepath
        self.filename = Path(filepath).name
        self.metadata = {}
        self.album_art_data = None
        self.new_artwork_path = None
        
        self.setWindowTitle(f"Edit Metadata - {self.filename}")
        self.setMinimumSize(900, 700)
        
        self.setup_ui()
        self.load_metadata()
        self.apply_style()
        
        print(f"🔄 TagEditorDialog initialized for: {self.filename}")
        
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel(f"✏️ Edit Metadata - {self.filename}")
        header.setObjectName("dialogHeader")
        header.setStyleSheet("""
            QLabel#dialogHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border-bottom: 2px solid #1d4ed8;
            }
        """)
        layout.addWidget(header)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tagEditorTabs")
        
        # Basic Info Tab
        basic_tab = QWidget()
        self.setup_basic_tab(basic_tab)
        self.tab_widget.addTab(basic_tab, "🎵 Basic")
        
        # Advanced Tab
        advanced_tab = QWidget()
        self.setup_advanced_tab(advanced_tab)
        self.tab_widget.addTab(advanced_tab, "⚙️ Advanced")
        
        # Lyrics Tab
        lyrics_tab = QWidget()
        self.setup_lyrics_tab(lyrics_tab)
        self.tab_widget.addTab(lyrics_tab, "📝 Lyrics")
        
        layout.addWidget(self.tab_widget, 1)
        
        # Button Panel
        button_panel = QFrame()
        button_panel.setObjectName("buttonPanel")
        button_panel.setStyleSheet("""
            QFrame#buttonPanel {
                background: #1e293b;
                border-top: 1px solid #334155;
                padding: 10px;
            }
        """)
        
        button_layout = QHBoxLayout(button_panel)
        button_layout.setContentsMargins(20, 10, 20, 10)
        
        # Left buttons
        left_buttons = QHBoxLayout()
        
        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.setToolTip("Reload metadata from file")
        self.reload_btn.clicked.connect(self.load_metadata)
        left_buttons.addWidget(self.reload_btn)
        
        left_buttons.addStretch()
        button_layout.addLayout(left_buttons)
        
        # Right buttons
        right_buttons = QHBoxLayout()
        right_buttons.setSpacing(10)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        right_buttons.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("💾 Save Tags")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_tags)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                padding: 8px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0da271;
            }
            QPushButton:pressed {
                background-color: #0c8f63;
            }
        """)
        right_buttons.addWidget(self.save_btn)
        
        button_layout.addLayout(right_buttons)
        
        layout.addWidget(button_panel)
    
    def setup_basic_tab(self, tab):
        """Setup basic info tab"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Main content
        main_content = QHBoxLayout()
        main_content.setSpacing(20)
        
        # Left - Album art
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # Album art label
        art_header = QLabel("Album Art")
        art_header.setStyleSheet("font-weight: bold; color: #cbd5e1;")
        left_panel.addWidget(art_header)
        
        # Artwork display
        self.art_label = QLabel()
        self.art_label.setFixedSize(250, 250)
        self.art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.art_label.setStyleSheet("""
            QLabel {
                background: #0f172a;
                border: 3px solid #334155;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        left_panel.addWidget(self.art_label)
        
        # Artwork buttons
        art_buttons = QHBoxLayout()
        art_buttons.setSpacing(10)
        
        self.load_art_btn = QPushButton("📁 Load Image")
        self.load_art_btn.setToolTip("Load album art from image file")
        self.load_art_btn.clicked.connect(self.load_image_file)
        art_buttons.addWidget(self.load_art_btn)
        
        self.remove_art_btn = QPushButton("🗑️ Remove")
        self.remove_art_btn.setToolTip("Remove album art")
        self.remove_art_btn.clicked.connect(self.remove_album_art)
        art_buttons.addWidget(self.remove_art_btn)
        
        left_panel.addLayout(art_buttons)
        
        # Art info
        self.art_info = QLabel("No album art")
        self.art_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.art_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(self.art_info)
        
        left_panel.addStretch()
        main_content.addLayout(left_panel)
        
        # Right - Basic fields
        right_panel = QWidget()
        right_layout = QGridLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setHorizontalSpacing(15)
        right_layout.setVerticalSpacing(10)
        
        # Field definitions: (key, label, row, col, required)
        field_defs = [
            ('title', 'Title:', 0, 0, True),
            ('artist', 'Artist:', 1, 0, True),
            ('album', 'Album:', 2, 0, False),
            ('album_artist', 'Album Artist:', 3, 0, False),
            ('year', 'Year:', 0, 1, False),
            ('genre', 'Genre:', 1, 1, False),
            ('track', 'Track #:', 2, 1, False),
            ('disc', 'Disc #:', 3, 1, False),
        ]
        
        self.fields = {}
        
        for key, label_text, row, col, required in field_defs:
            # Label
            label = QLabel(label_text)
            if required:
                label.setText(f"<b>{label_text}</b>")
            label.setMinimumWidth(100)
            
            # Field
            field = QLineEdit()
            field.setObjectName(f"field_{key}")
            if required:
                field.setPlaceholderText("Required")
            
            right_layout.addWidget(label, row, col * 2)
            right_layout.addWidget(field, row, col * 2 + 1)
            
            self.fields[key] = field
        
        # Comment field (larger)
        comment_label = QLabel("Comment:")
        right_layout.addWidget(comment_label, 4, 0)
        
        self.comment_field = QPlainTextEdit()
        self.comment_field.setObjectName("field_comment")
        self.comment_field.setMaximumHeight(80)
        self.comment_field.setPlaceholderText("Add comments...")
        right_layout.addWidget(self.comment_field, 4, 1, 1, 3)
        
        # File info section
        right_layout.addWidget(self.create_separator(), 5, 0, 1, 4)
        
        info_label = QLabel("📁 File Information:")
        info_label.setStyleSheet("font-weight: bold; color: #cbd5e1; margin-top: 10px;")
        right_layout.addWidget(info_label, 6, 0, 1, 4)
        
        self.file_info = QLabel()
        self.file_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.file_info.setWordWrap(True)
        right_layout.addWidget(self.file_info, 7, 0, 1, 4)
        
        right_layout.setRowStretch(8, 1)
        
        main_content.addWidget(right_panel, 1)
        layout.addLayout(main_content)
    
    def setup_advanced_tab(self, tab):
        """Setup advanced tab"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Technical info
        tech_label = QLabel("🎛️ Technical Information:")
        tech_label.setStyleSheet("font-weight: bold; color: #cbd5e1; font-size: 13px;")
        layout.addWidget(tech_label)
        
        # Grid for technical fields
        tech_grid = QGridLayout()
        tech_grid.setHorizontalSpacing(20)
        tech_grid.setVerticalSpacing(8)
        
        self.tech_fields = {}
        tech_defs = [
            ('composer', 'Composer:', 0, 0),
            ('publisher', 'Publisher:', 0, 1),
            ('copyright', 'Copyright:', 1, 0),
            ('bpm', 'BPM:', 1, 1),
            ('encoder', 'Encoder:', 2, 0),
            ('bitrate', 'Bitrate:', 3, 0),
            ('sample_rate', 'Sample Rate:', 3, 1),
            ('channels', 'Channels:', 4, 0),
            ('file_format', 'Format:', 4, 1),
        ]
        
        for key, label_text, row, col in tech_defs:
            label = QLabel(label_text)
            field = QLineEdit()
            field.setObjectName(f"tech_{key}")
            field.setReadOnly(key in ['bitrate', 'sample_rate', 'channels', 'file_format'])
            
            tech_grid.addWidget(label, row, col * 2)
            tech_grid.addWidget(field, row, col * 2 + 1)
            
            self.tech_fields[key] = field
        
        layout.addLayout(tech_grid)
        layout.addWidget(self.create_separator())
        
        # ID3 specific
        id3_label = QLabel("🏷️ ID3 Tags (MP3 only):")
        id3_label.setStyleSheet("font-weight: bold; color: #cbd5e1; font-size: 13px;")
        layout.addWidget(id3_label)
        
        id3_grid = QGridLayout()
        id3_grid.setHorizontalSpacing(20)
        id3_grid.setVerticalSpacing(8)
        
        self.id3_fields = {}
        id3_defs = [
            ('lyricist', 'Lyricist:', 0, 0),
            ('conductor', 'Conductor:', 0, 1),
            ('orchestra', 'Orchestra:', 1, 0),
            ('mood', 'Mood:', 1, 1),
            ('isrc', 'ISRC:', 2, 0),
            ('url', 'URL:', 2, 1),
        ]
        
        for key, label_text, row, col in id3_defs:
            label = QLabel(label_text)
            field = QLineEdit()
            field.setObjectName(f"id3_{key}")
            
            id3_grid.addWidget(label, row, col * 2)
            id3_grid.addWidget(field, row, col * 2 + 1)
            
            self.id3_fields[key] = field
        
        layout.addLayout(id3_grid)
        layout.addStretch()
    
    def setup_lyrics_tab(self, tab):
        """Setup lyrics tab"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Info
        info_label = QLabel("📝 Add or edit lyrics for this track")
        info_label.setStyleSheet("color: #94a3b8; font-style: italic;")
        layout.addWidget(info_label)
        
        # Lyrics editor
        self.lyrics_edit = QPlainTextEdit()
        self.lyrics_edit.setObjectName("lyricsEditor")
        self.lyrics_edit.setPlaceholderText(
            "Enter lyrics here...\n\n"
            "You can include timestamps:\n"
            "[00:30] First verse begins...\n"
            "[01:15] Chorus starts..."
        )
        layout.addWidget(self.lyrics_edit, 1)
        
        # Lyrics buttons
        lyric_buttons = QHBoxLayout()
        lyric_buttons.addStretch()
        
        self.clear_lyrics_btn = QPushButton("Clear Lyrics")
        self.clear_lyrics_btn.clicked.connect(lambda: self.lyrics_edit.clear())
        lyric_buttons.addWidget(self.clear_lyrics_btn)
        
        self.paste_lyrics_btn = QPushButton("Paste from Clipboard")
        self.paste_lyrics_btn.clicked.connect(self.paste_lyrics)
        lyric_buttons.addWidget(self.paste_lyrics_btn)
        
        layout.addLayout(lyric_buttons)
    
    def create_separator(self):
        """Create a horizontal separator"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background: #334155; margin: 10px 0;")
        return separator
    
    def load_metadata(self):
        """Load metadata from file"""
        if not METADATA_AVAILABLE:
            self.show_error("MetadataReader not available. Install mutagen.")
            return
        
        try:
            print(f"📖 Loading metadata from: {self.filename}")
            
            # Read metadata
            metadata = read_metadata(self.filepath)
            self.metadata = metadata
            
            # Debug output
            print("=" * 60)
            print(f"📀 METADATA FOR: {self.filename}")
            print("=" * 60)
            
            # Populate basic fields
            for key, field in self.fields.items():
                value = metadata.get(key, '')
                if value and value != 'Unknown' and value != 'Unknown Artist' and value != 'Unknown Album':
                    field.setText(str(value))
                    print(f"✓ {key}: {value}")
                else:
                    print(f"✗ {key}: Not found or empty")
            
            # Comment
            comment = metadata.get('comment', '')
            if comment:
                self.comment_field.setPlainText(comment)
                print(f"✓ comment: {comment[:50]}...")
            
            # Technical fields
            for key, field in self.tech_fields.items():
                value = metadata.get(key, '')
                if value:
                    field.setText(str(value))
            
            # Lyrics
            lyrics = metadata.get('lyrics', '')
            if lyrics:
                self.lyrics_edit.setPlainText(lyrics)
                print(f"✓ lyrics: {len(lyrics)} chars")
            
            # Album art
            if metadata.get('has_artwork') and metadata.get('artwork_data'):
                print("🖼️ Loading album art...")
                self.load_album_art(metadata['artwork_data'])
            else:
                self.set_default_artwork()
                print("🖼️ No album art found")
            
            # Update file info
            self.update_file_info()
            
            print("=" * 60)
            print(f"✅ Metadata loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading metadata: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"Could not read metadata:\n{str(e)}")
    
    def update_file_info(self):
        """Update file information display"""
        try:
            path = Path(self.filepath)
            size_mb = path.stat().st_size / (1024 * 1024)
            
            duration = self.metadata.get('duration', 0)
            duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"
            
            bitrate = self.metadata.get('bitrate', 0)
            bitrate_str = f"{bitrate // 1000} kbps" if bitrate > 0 else "Unknown"
            
            sample_rate = self.metadata.get('sample_rate', 0)
            sample_rate_str = f"{sample_rate:,} Hz" if sample_rate > 0 else "Unknown"
            
            channels = self.metadata.get('channels', 2)
            channels_str = {1: "Mono", 2: "Stereo"}.get(channels, f"{channels} channels")
            
            info = f"""
            <div style="font-family: 'Courier New', monospace; font-size: 11px;">
            <b>Location:</b> {path.parent}<br>
            <b>Size:</b> {size_mb:.2f} MB • <b>Duration:</b> {duration_str}<br>
            <b>Audio:</b> {bitrate_str} • {sample_rate_str} • {channels_str}<br>
            <b>Format:</b> {self.metadata.get('file_format', 'Unknown').upper()}
            </div>
            """
            
            self.file_info.setText(info)
            
        except Exception as e:
            self.file_info.setText(f"Error reading file info: {str(e)}")
    
    def load_album_art(self, art_data):
        """Load album art from base64 data"""
        try:
            if not art_data:
                self.set_default_artwork()
                return
                
            image_data = base64.b64decode(art_data)
            pixmap = QPixmap()
            
            if pixmap.loadFromData(image_data):
                scaled = pixmap.scaled(
                    240, 240, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.art_label.setPixmap(scaled)
                self.art_info.setText(f"Album art loaded ({pixmap.width()}×{pixmap.height()})")
                print(f"✅ Album art loaded: {pixmap.width()}×{pixmap.height()}")
            else:
                self.set_default_artwork()
                print("❌ Failed to load album art image")
                
        except Exception as e:
            print(f"❌ Error loading album art: {e}")
            self.set_default_artwork()
    
    def set_default_artwork(self):
        """Set default artwork placeholder"""
        default_text = "No Album Art"
        self.art_label.setText(default_text)
        self.art_label.setStyleSheet("""
            QLabel {
                background: #0f172a;
                border: 3px dashed #475569;
                border-radius: 8px;
                color: #64748b;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        self.art_info.setText("No album art embedded in file")
    
    def load_image_file(self):
        """Load image file for album art"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Album Art Image", 
            str(Path.home() / "Pictures"),
            "Images (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        
        if files:
            image_path = files[0]
            pixmap = QPixmap(image_path)
            
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    240, 240, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.art_label.setPixmap(scaled)
                self.new_artwork_path = image_path
                self.art_info.setText(f"New image: {Path(image_path).name}")
                print(f"📸 Loaded new artwork from: {image_path}")
            else:
                QMessageBox.warning(self, "Error", "Could not load image file")
    
    def remove_album_art(self):
        """Remove album art"""
        reply = QMessageBox.question(
            self, "Remove Album Art",
            "Remove album art from this track?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.set_default_artwork()
            self.new_artwork_path = None
            print("🗑️ Album art removed")
    
    def paste_lyrics(self):
        """Paste lyrics from clipboard"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.lyrics_edit.setPlainText(text)
            print("📋 Lyrics pasted from clipboard")
    
    def save_tags(self):
        """Save metadata back to file"""
        try:
            print(f"💾 Saving tags to: {self.filename}")
            
            # Collect data from all fields
            tags = {}
            
            # Basic fields
            for key, field in self.fields.items():
                text = field.text().strip()
                if text:
                    tags[key] = text
            
            # Comment
            comment = self.comment_field.toPlainText().strip()
            if comment:
                tags['comment'] = comment
            
            # Lyrics
            lyrics = self.lyrics_edit.toPlainText().strip()
            if lyrics:
                tags['lyrics'] = lyrics
            
            # Technical fields (read-only, just for display)
            for key, field in self.tech_fields.items():
                if not field.isReadOnly():
                    text = field.text().strip()
                    if text:
                        tags[key] = text
            
            # Save using mutagen if available
            if MUTAGEN_AVAILABLE:
                success = self.save_with_mutagen(tags)
            else:
                success = False
            
            if success:
                # Emit signal
                self.tags_saved.emit(self.filepath, tags)
                
                # Show success message
                QMessageBox.information(
                    self, "Success ✅",
                    f"Tags saved successfully for:\n{self.filename}"
                )
                
                print(f"✅ Tags saved: {tags}")
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Warning",
                    f"Tags were collected but could not be written to file.\n\n"
                    f"Collected tags:\n{dict(list(tags.items())[:5])}..."
                )
                
        except Exception as e:
            print(f"❌ Error saving tags: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, "Error ❌",
                f"Could not save tags:\n{str(e)}"
            )
    
    def save_with_mutagen(self, tags):
        """Save tags using mutagen library"""
        try:
            audio = mutagen.File(self.filepath, easy=True)
            
            if audio is None:
                print(f"❌ Could not load file with mutagen: {self.filepath}")
                return False
            
            # Map our field names to mutagen field names
            field_map = {
                'title': 'title',
                'artist': 'artist',
                'album': 'album',
                'album_artist': 'albumartist',
                'year': 'date',
                'genre': 'genre',
                'track': 'tracknumber',
                'disc': 'discnumber',
                'composer': 'composer',
                'comment': 'comment',
                'lyrics': 'lyrics',
            }
            
            # Set tags
            for our_key, mutagen_key in field_map.items():
                if our_key in tags:
                    value = str(tags[our_key])
                    if value:
                        audio[mutagen_key] = value
                        print(f"✓ Set {mutagen_key}: {value}")
            
            # Save artwork if new one was loaded
            if self.new_artwork_path and Path(self.new_artwork_path).exists():
                self.save_artwork_to_file(audio)
            
            # Save changes
            audio.save()
            print(f"💾 File saved: {self.filepath}")
            
            return True
            
        except Exception as e:
            print(f"❌ Mutagen save error: {e}")
            return False
    
    def save_artwork_to_file(self, audio):
        """Save artwork to audio file"""
        try:
            from mutagen.id3 import APIC, ID3
            from mutagen.flac import Picture, FLAC
            from mutagen.mp4 import MP4Cover
            
            ext = Path(self.filepath).suffix.lower()
            image_path = self.new_artwork_path
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            if ext == '.mp3':
                if 'APIC:' not in audio:
                    # Add APIC frame for MP3
                    audio.tags.add(APIC(
                        encoding=3,  # UTF-8
                        mime='image/jpeg',  # or detect from file
                        type=3,  # 3 = front cover
                        desc='Cover',
                        data=image_data
                    ))
            
            elif ext == '.flac':
                picture = Picture()
                picture.data = image_data
                picture.type = 3  # Front cover
                picture.mime = 'image/jpeg'
                picture.desc = 'Cover'
                audio.clear_pictures()
                audio.add_picture(picture)
            
            elif ext in ['.m4a', '.mp4']:
                cover = MP4Cover(image_data, MP4Cover.FORMAT_JPEG)
                audio['covr'] = [cover]
            
            print(f"🖼️ Artwork saved to file")
            
        except Exception as e:
            print(f"❌ Error saving artwork: {e}")
    
    def show_error(self, message):
        """Show error message"""
        QMessageBox.warning(self, "Error", message)
    
    def apply_style(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
            }
            QTabWidget::pane {
                border: 1px solid #334155;
                background: #0f172a;
            }
            QTabBar::tab {
                background: #1e293b;
                color: #94a3b8;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #334155;
            }
            QLabel {
                color: #cbd5e1;
            }
            QLineEdit, QPlainTextEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px;
                color: #e2e8f0;
                selection-background-color: #3b82f6;
            }
            QLineEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #3b82f6;
                background-color: #0f172a;
            }
            QLineEdit[readOnly="true"] {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #475569;
            }
            QPushButton {
                background-color: #334155;
                color: #e2e8f0;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #475569;
                border-color: #64748b;
            }
            QPushButton:pressed {
                background-color: #1e293b;
            }
            QPlainTextEdit#lyricsEditor {
                font-family: "Courier New", monospace;
                font-size: 12px;
            }
        """)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test file
    test_file = Path.home() / "Music" / "test.mp3"
    
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
    
    if test_file.exists():
        print(f"🧪 Testing TagEditorDialog with: {test_file}")
        dialog = TagEditorDialog(str(test_file))
        dialog.show()
        sys.exit(app.exec())
    else:
        print(f"❌ Test file not found: {test_file}")
        print("Usage: python3 tag_editor_dialog.py <audio_file>")