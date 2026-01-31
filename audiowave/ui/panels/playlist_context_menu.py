# -*- coding: utf-8 -*-
# ui/panels/playlist_context_menu.py
"""
Context menu actions za playlist

Includes:
- Play, Edit Tags, File Info
- Show in Folder
- Plugin integrations (Lyrics when enabled)
"""

import time
import os
import platform
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import QMenu, QMessageBox
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

# Dodajemo import za SVG ikone
from ui.utils.svg_icon_manager import get_icon

try:
    from ui.dialogs.tag_editor_dialog import TagEditorDialog
    TAG_EDITOR_AVAILABLE = True
except ImportError as e:
    TAG_EDITOR_AVAILABLE = False
    print(f'⚠️ Tag Editor not available: {e}')

try:
    from core.metadata_reader import read_metadata
    from core.audio_utils import format_duration, is_audio_file
    METADATA_READER_AVAILABLE = True
except ImportError as e:
    METADATA_READER_AVAILABLE = False
    print(f'⚠️ Metadata utilities not available: {e}')

# Import Plugin Manager
try:
    from plugins.plugin_manager import get_plugin_manager
    PLUGIN_MANAGER_AVAILABLE = True
except ImportError:
    PLUGIN_MANAGER_AVAILABLE = False


class PlaylistContextMenuManager:
    """Manager za context menu actions i file operations"""
    
    def __init__(self, playlist_panel):
        self.playlist_panel = playlist_panel
        
        # Plugin manager
        if PLUGIN_MANAGER_AVAILABLE:
            self.plugin_manager = get_plugin_manager()
        else:
            self.plugin_manager = None
    
    def show_context_menu(self, pos):
        """Show context menu at position"""
        menu = QMenu()
        selected = self.playlist_panel.file_list.selectedItems()
        
        if selected:
            # ===== PLAY ACTION =====
            play_action = QAction("Play", self.playlist_panel)
            play_action.setIcon(get_icon("play", size=16))
            play_action.triggered.connect(
                lambda: self.playlist_panel.play_requested.emit(
                    selected[0].data(Qt.ItemDataRole.UserRole)
                )
            )
            menu.addAction(play_action)
            menu.addSeparator()
            
            # ===== EDIT TAGS =====
            if TAG_EDITOR_AVAILABLE:
                edit_action = QAction("✏️ Edit Tags", self.playlist_panel)
                edit_action.setEnabled(len(selected) == 1)
                edit_action.triggered.connect(self.edit_tags)
                menu.addAction(edit_action)
            
            # ===== FILE INFO =====
            info_action = QAction("ℹ️ File Info", self.playlist_panel)
            info_action.setEnabled(len(selected) == 1)
            info_action.triggered.connect(self.show_file_info)
            menu.addAction(info_action)
            
            # ===== PLUGIN ACTIONS =====
            plugin_actions_added = False
            
            if self.plugin_manager:
                # Lyrics plugin
                if self.plugin_manager.is_enabled("lyrics"):
                    if not plugin_actions_added:
                        menu.addSeparator()
                        plugin_actions_added = True
                    
                    lyrics_action = QAction("🎤 Search Lyrics", self.playlist_panel)
                    lyrics_action.setEnabled(len(selected) == 1)
                    lyrics_action.triggered.connect(self.search_lyrics)
                    menu.addAction(lyrics_action)
                
                # Dodaj ostale plugin akcije ako postoje
                for item in self.plugin_manager.get_context_menu_items():
                    if item.get('plugin_id') != 'lyrics':  # Lyrics smo već dodali
                        if not plugin_actions_added:
                            if item.get('separator_before', False):
                                menu.addSeparator()
                            plugin_actions_added = True
                        
                        action = QAction(item['text'], self.playlist_panel)
                        action.triggered.connect(
                            lambda checked, i=item: self._handle_plugin_action(i)
                        )
                        menu.addAction(action)
            
            menu.addSeparator()
            
            # ===== REMOVE ACTION =====
            remove_action = QAction("🗑️ Remove Selected", self.playlist_panel)
            remove_action.triggered.connect(self.playlist_panel.remove_selected)
            menu.addAction(remove_action)
            
            # ===== SHOW IN FOLDER =====
            if len(selected) == 1:
                show_in_folder = QAction("📂 Show in Folder", self.playlist_panel)
                show_in_folder.triggered.connect(self.show_in_folder)
                menu.addAction(show_in_folder)
        else:
            # No selection - add actions
            add_files_action = QAction("📄 Add Files", self.playlist_panel)
            add_files_action.triggered.connect(self.playlist_panel.add_files)
            menu.addAction(add_files_action)
            
            add_folder_action = QAction("📁 Add Folder", self.playlist_panel)
            add_folder_action.triggered.connect(self.playlist_panel.add_folder)
            menu.addAction(add_folder_action)
            
            menu.addSeparator()
            
            new_playlist_action = QAction("➕ New Playlist", self.playlist_panel)
            new_playlist_action.triggered.connect(self.playlist_panel.create_new_playlist)
            menu.addAction(new_playlist_action)
        
        menu.exec(self.playlist_panel.file_list.viewport().mapToGlobal(pos))
    
    def _handle_plugin_action(self, item):
        """Handle plugin context menu action"""
        if self.plugin_manager:
            plugin_id = item.get('plugin_id')
            action = item.get('action')
            
            # Dobij metadata za trenutnu pesmu
            selected = self.playlist_panel.file_list.selectedItems()
            kwargs = {}
            
            if selected:
                filepath = selected[0].data(Qt.ItemDataRole.UserRole)
                if filepath and METADATA_READER_AVAILABLE:
                    try:
                        metadata = read_metadata(filepath)
                        kwargs['artist'] = metadata.get('artist', '')
                        kwargs['title'] = metadata.get('title', Path(filepath).stem)
                    except:
                        kwargs['title'] = Path(filepath).stem
            
            self.plugin_manager.handle_context_menu_action(
                action, plugin_id, self.playlist_panel, **kwargs
            )
    
    def search_lyrics(self):
        """Search lyrics for selected track"""
        items = self.playlist_panel.file_list.selectedItems()
        if not items:
            return
        
        filepath = items[0].data(Qt.ItemDataRole.UserRole)
        if not filepath:
            return
        
        # Dobij metadata
        artist = ""
        title = Path(filepath).stem  # Fallback na filename
        
        if METADATA_READER_AVAILABLE:
            try:
                metadata = read_metadata(filepath)
                artist = metadata.get('artist', '')
                title = metadata.get('title', title)
            except Exception as e:
                print(f"⚠️ Could not read metadata: {e}")
        
        # Otvori Lyrics dialog
        try:
            from plugins.lyrics.lyrics_plugin import LyricsDialog
            dialog = LyricsDialog(self.playlist_panel, artist=artist, title=title)
            dialog.exec()
        except ImportError:
            QMessageBox.warning(
                self.playlist_panel, 
                "Plugin Not Available",
                "Lyrics plugin is not installed or not available."
            )
    
    def edit_tags(self):
        """Open tag editor dialog"""
        items = self.playlist_panel.file_list.selectedItems()
        if not items:
            QMessageBox.information(self.playlist_panel, "No Selection", 
                "Please select a track to edit tags.")
            return
        
        filepath = items[0].data(Qt.ItemDataRole.UserRole)
        if not filepath or not Path(filepath).exists():
            QMessageBox.warning(self.playlist_panel, "File Not Found", 
                f"File not found:\n{filepath}")
            return
        
        try:
            print(f"🎵 Opening tag editor for: {Path(filepath).name}")
            
            # Check if audio file
            audio_check = True
            if METADATA_READER_AVAILABLE:
                audio_check = is_audio_file(filepath)
            
            if not audio_check:
                reply = QMessageBox.question(
                    self.playlist_panel, "Not Audio File",
                    f"This doesn't appear to be an audio file:\n{Path(filepath).name}\n\n"
                    "Open anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Check for mutagen
            try:
                import mutagen
                print(f"✅ Mutagen available (v{mutagen.version})")
            except ImportError:
                print("❌ Mutagen not installed")
                QMessageBox.warning(self.playlist_panel, "Library Required",
                    "Tag editor requires mutagen library.\n\n"
                    "Install it with:\npip install mutagen\n\n"
                    "Without mutagen, you can only view tags.")
            
            from ui.dialogs.tag_editor_dialog import TagEditorDialog
            dialog = TagEditorDialog(filepath, self.playlist_panel)
            dialog.tags_saved.connect(self.playlist_panel.on_tags_updated)
            dialog.exec()
            
            print(f"✅ Tag editor closed for: {Path(filepath).name}")
            
        except ImportError as e:
            print(f"❌ Cannot import TagEditorDialog: {e}")
            QMessageBox.warning(self.playlist_panel, "Feature Not Available",
                f"Tag editor is not available.\n\nError: {str(e)}")
        except Exception as e:
            print(f"❌ Error opening tag editor: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self.playlist_panel, "Error",
                f"Could not open tag editor:\n{str(e)}")
    
    def show_in_folder(self):
        """Show file in system file explorer"""
        items = self.playlist_panel.file_list.selectedItems()
        if not items:
            return
        
        filepath = items[0].data(Qt.ItemDataRole.UserRole)
        if not filepath:
            return
        
        try:
            path = Path(filepath)
            
            if platform.system() == "Windows":
                # Windows - select file in explorer
                subprocess.run(['explorer', '/select,', str(path)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", str(path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(path.parent)])
                
            print(f"📂 Opened folder: {path.parent}")
        except Exception as e:
            print(f"❌ Error opening folder: {e}")
            QMessageBox.warning(self.playlist_panel, "Error",
                f"Could not open folder:\n{str(e)}")
    
    def show_file_info(self):
        """Show detailed file information with tags"""
        items = self.playlist_panel.file_list.selectedItems()
        if not items:
            QMessageBox.information(self.playlist_panel, "No Selection", 
                "Please select a track to view info.")
            return
        
        filepath = items[0].data(Qt.ItemDataRole.UserRole)
        p = Path(filepath)
        
        if not p.exists():
            QMessageBox.warning(self.playlist_panel, "Error", f"File not found:\n{filepath}")
            return
        
        try:
            metadata = {}
            if METADATA_READER_AVAILABLE:
                try:
                    metadata = read_metadata(filepath)
                except Exception as e:
                    metadata = {}
            
            size_mb = p.stat().st_size / (1024 * 1024)
            
            duration = metadata.get('duration', 0)
            duration_str = format_duration(duration) if duration else "Unknown"
            
            bitrate = metadata.get('bitrate', 0)
            bitrate_str = f"{bitrate // 1000} kbps" if bitrate > 0 else "Unknown"
            
            sample_rate = metadata.get('sample_rate', 0)
            sample_rate_str = f"{sample_rate:,} Hz" if sample_rate > 0 else "Unknown"
            
            channels = metadata.get('channels', 0)
            channels_str = {1: "Mono", 2: "Stereo"}.get(channels, f"{channels} channels")
            
            info = self._format_file_info_html(p, filepath, metadata, size_mb, 
                                             duration_str, bitrate_str, 
                                             sample_rate_str, channels_str)
            
            QMessageBox.information(self.playlist_panel, "File Information", info)
            
        except Exception as e:
            print(f"❌ Error showing file info: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self.playlist_panel, "Error", 
                f"Could not read file information:\n{str(e)}")
    
    def _format_file_info_html(self, path, filepath, metadata, size_mb, 
                              duration_str, bitrate_str, 
                              sample_rate_str, channels_str):
        """Format file information as HTML"""
        return f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
            
            <h3 style="color: #4a6ee0; margin-bottom: 10px;">📀 File Information</h3>
            
            <table cellspacing="0" cellpadding="4" style="border-collapse: collapse; width: 100%;">
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold; width: 140px;">Filename:</td>
                <td>{path.name}</td>
            </tr>
            
            <tr>
                <td style="font-weight: bold;">File Size:</td>
                <td>{size_mb:.2f} MB</td>
            </tr>
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold;">Format:</td>
                <td>{metadata.get('file_format', 'Unknown').upper()}</td>
            </tr>
            
            <tr>
                <td style="font-weight: bold;">Duration:</td>
                <td>{duration_str}</td>
            </tr>
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold;">Bitrate:</td>
                <td>{bitrate_str}</td>
            </tr>
            
            <tr>
                <td style="font-weight: bold;">Sample Rate:</td>
                <td>{sample_rate_str}</td>
            </tr>
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold;">Channels:</td>
                <td>{channels_str}</td>
            </tr>
            
            </table>
            
            <h3 style="color: #4a6ee0; margin-top: 20px; margin-bottom: 10px;">🎵 Metadata Tags</h3>
            
            <table cellspacing="0" cellpadding="4" style="border-collapse: collapse; width: 100%;">
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold; width: 140px;">Title:</td>
                <td>{metadata.get('title', '<i>Not set</i>')}</td>
            </tr>
            
            <tr>
                <td style="font-weight: bold;">Artist:</td>
                <td>{metadata.get('artist', '<i>Not set</i>')}</td>
            </tr>
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold;">Album:</td>
                <td>{metadata.get('album', '<i>Not set</i>')}</td>
            </tr>
            
            <tr>
                <td style="font-weight: bold;">Album Artist:</td>
                <td>{metadata.get('album_artist', '<i>Not set</i>')}</td>
            </tr>
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold;">Year:</td>
                <td>{metadata.get('date', '<i>Not set</i>')}</td>
            </tr>
            
            <tr>
                <td style="font-weight: bold;">Genre:</td>
                <td>{metadata.get('genre', '<i>Not set</i>')}</td>
            </tr>
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold;">Track:</td>
                <td>{metadata.get('track', '<i>Not set</i>')}</td>
            </tr>
            
            <tr>
                <td style="font-weight: bold;">Disc:</td>
                <td>{metadata.get('disc', '<i>Not set</i>')}</td>
            </tr>
            
            <tr style="background-color: #f0f0f0;">
                <td style="font-weight: bold;">Composer:</td>
                <td>{metadata.get('composer', '<i>Not set</i>')}</td>
            </tr>
            
            <tr>
                <td style="font-weight: bold;">Comment:</td>
                <td>{metadata.get('comment', '<i>Not set</i>')}</td>
            </tr>
            
            </table>
            
            <hr style="margin: 20px 0; border: 1px solid #ddd;">
            
            <p style="color: #666; font-size: 12px;">
            <b>Location:</b> {filepath}<br>
            <b>Last modified:</b> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(path.stat().st_mtime))}
            </p>
            
            </body>
            </html>
            """