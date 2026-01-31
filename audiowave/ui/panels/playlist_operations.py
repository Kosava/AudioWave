# -*- coding: utf-8 -*-
# ui/panels/playlist_operations.py
# Playlist operations: add, remove, clear, drag & drop

import time
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QMenu
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction

try:
    from core.audio_utils import is_audio_file
    AUDIO_UTILS_AVAILABLE = True
except ImportError as e:
    AUDIO_UTILS_AVAILABLE = False
    print(f'⚠️ Audio utils not available: {e}')


class PlaylistOperationsManager:
    """Manager za playlist operacije: add, remove, clear, drag & drop"""
    
    def __init__(self, playlist_panel):
        self.playlist_panel = playlist_panel
    
    def add_files(self, files=None):
        """Add files to current playlist"""
        if files is None:
            files, _ = QFileDialog.getOpenFileNames(
                self.playlist_panel, "Select Audio Files", str(Path.home() / "Music"),
                "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;All Files (*.*)"
            )
        
        if files and self.playlist_panel.playlist_manager:
            self.playlist_panel.playlist_manager.add_files(files)
            self.playlist_panel.show_status_message(f"Added {len(files)} files")
    
    def add_folder(self):
        """Add folder contents to playlist"""
        folder = QFileDialog.getExistingDirectory(
            self.playlist_panel, "Select Music Folder", str(Path.home() / "Music")
        )
        
        if folder and self.playlist_panel.playlist_manager:
            folder_path = Path(folder)
            audio_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']
            
            audio_files = []
            for ext in audio_extensions:
                audio_files.extend(folder_path.rglob(f"*{ext}"))
                audio_files.extend(folder_path.rglob(f"*{ext.upper()}"))
            
            if audio_files:
                file_paths = [str(f) for f in audio_files]
                self.playlist_panel.playlist_manager.add_files(file_paths)
                self.playlist_panel.show_status_message(f"Added {len(file_paths)} files from folder")
            else:
                QMessageBox.information(self.playlist_panel, "No Audio Files", 
                    "No audio files found in the selected folder.")
    
    def add_url(self):
        """Add URL (radio stream) to playlist"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        
        # Dialog za unos URL-a
        url, ok = QInputDialog.getText(
            self.playlist_panel,
            "Add Stream URL",
            "Enter stream URL (radio station or audio stream):",
            QLineEdit.EchoMode.Normal,
            "https://"
        )
        
        if ok and url and url.strip():
            url = url.strip()
            
            # Provera da li URL počinje sa http:// ili https://
            if not url.startswith(('http://', 'https://', 'mms://', 'rtsp://')):
                QMessageBox.warning(
                    self.playlist_panel,
                    "Invalid URL",
                    "URL must start with http://, https://, mms://, or rtsp://"
                )
                return
            
            # Dialog za opciono unos imena stanice
            name, ok2 = QInputDialog.getText(
                self.playlist_panel,
                "Stream Name",
                "Enter a name for this stream (optional):",
                QLineEdit.EchoMode.Normal,
                ""
            )
            
            if ok2:
                if self.playlist_panel.playlist_manager:
                    # Ako je dato ime, kreiraj custom display name
                    # PlaylistManager će direktno dodati URL kao fajl
                    self.playlist_panel.playlist_manager.add_files([url])
                    
                    if name and name.strip():
                        # Sačuvaj custom ime za ovaj URL u metadata cache
                        # (ovo će delegate koristiti za prikaz)
                        display_name = f"📻 {name.strip()}"
                    else:
                        # Ekstraktuj ime iz URL-a
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc or "Stream"
                        display_name = f"📻 {domain}"
                    
                    self.playlist_panel.show_status_message(f"Added stream: {display_name}")
                else:
                    QMessageBox.warning(
                        self.playlist_panel,
                        "Error",
                        "Playlist manager not available"
                    )
    
    def clear_playlist(self):
        """Clear current playlist"""
        if not self.playlist_panel.playlist_manager:
            print("⚠️ Clear playlist: No playlist manager available")
            return
        
        # Uzmi ime trenutne plejliste (ukloni emoji prefiks)
        current_playlist = self.playlist_panel.playlist_selector.currentText().replace("♪ ", "")
        track_count = len(self.playlist_panel.playlist_manager.current_playlist)
        
        print(f"🗑️ Clear playlist requested: '{current_playlist}' ({track_count} tracks)")
        
        # Potvrdi brisanje sa korisnikom
        reply = QMessageBox.question(
            self.playlist_panel, "Clear Playlist",
            f"Clear all {track_count} tracks from '{current_playlist}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            print(f"✅ User confirmed - clearing playlist '{current_playlist}'")
            
            # Pozovi clear_playlist metodu na playlist manager-u
            success = self.playlist_panel.playlist_manager.clear_playlist(current_playlist)
            
            if success:
                print(f"✅ Playlist '{current_playlist}' successfully cleared")
                
                # KRITIČNO: Eksplicitno osvež UI da prikaže praznu listu
                self.playlist_panel.load_current_playlist()
                self.playlist_panel.show_status_message(f"Cleared {current_playlist}")
            else:
                print(f"❌ Failed to clear playlist '{current_playlist}'")
                QMessageBox.warning(
                    self.playlist_panel,
                    "Error",
                    f"Failed to clear playlist '{current_playlist}'"
                )
        else:
            print(f"❌ User cancelled clear operation")
    
    def remove_selected(self):
        """Remove selected items from playlist"""
        items = self.playlist_panel.file_list.selectedItems()
        if items and self.playlist_panel.playlist_manager:
            paths = [i.data(Qt.ItemDataRole.UserRole) for i in items]
            self.playlist_panel.playlist_manager.remove_files(paths)
            self.playlist_panel.show_status_message(f"Removed {len(paths)} tracks")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.playlist_panel.setStyleSheet("""
                QWidget#playlist_panel {
                    border: 2px dashed #4CAF50;
                    border-radius: 5px;
                }
            """)
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave events"""
        self.playlist_panel.setStyleSheet("")
        super(type(self.playlist_panel), self.playlist_panel).dragLeaveEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        self.playlist_panel.setStyleSheet("")
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files_to_add = []
            folders_to_scan = []
            
            for url in urls:
                local_path = url.toLocalFile()
                path = Path(local_path)
                
                if path.is_file():
                    if AUDIO_UTILS_AVAILABLE and is_audio_file(str(path)):
                        files_to_add.append(str(path))
                    elif not AUDIO_UTILS_AVAILABLE:
                        # Fallback: check extension
                        ext = path.suffix.lower()
                        if ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']:
                            files_to_add.append(str(path))
                elif path.is_dir():
                    folders_to_scan.append(path)
            
            audio_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.oga', '.mp4']
            
            for folder in folders_to_scan:
                for ext in audio_extensions:
                    files_to_add.extend([str(f) for f in folder.rglob(f"*{ext}")])
                    files_to_add.extend([str(f) for f in folder.rglob(f"*{ext.upper()}")])
            
            if files_to_add:
                if self.playlist_panel.playlist_manager:
                    self.playlist_panel.playlist_manager.add_files(files_to_add)
                    self.playlist_panel.load_current_playlist()
                    
                    folder_count = len(folders_to_scan)
                    if folder_count > 0:
                        msg = f"Added {len(files_to_add)} files ({folder_count} folder{'s' if folder_count > 1 else ''})"
                    else:
                        msg = f"Added {len(files_to_add)} files"
                    
                    self.playlist_panel.show_status_message(f"♪ {msg}")
            else:
                self.playlist_panel.show_status_message("⚠️ No audio files found", 2000)
            
            event.acceptProposedAction()
        else:
            event.ignore()