# ui/panels/playlist_delegate.py
# Winamp-style item delegate sa integrisanim cache-om

from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtCore import Qt, QSize, QRect, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont

from .playlist_cache import PlaylistCacheManager


class WinampPlaylistItemDelegate(QStyledItemDelegate):
    """Optimized Winamp-style playlist item delegate sa cache-om"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.index_width = 40
        self.time_width = 60
        self.right_margin = 12
        self.left_margin = 5
        
        # Cache manager
        self.cache_manager = PlaylistCacheManager()
        self.playlist_panel = None
    
    def set_playlist_panel(self, panel):
        """Set reference to parent playlist panel for cache coordination"""
        self.playlist_panel = panel
        self.cache_manager.playlist_panel = panel
    
    def paint(self, painter, option, index):
        """Optimized painting with minimal operations"""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = option.rect
        
        # Get active track for highlighting
        panel = getattr(self, "playlist_panel", None)
        active = None
        if panel:
            active = panel.get_current_highlighted_file()
        
        filepath = index.data(Qt.ItemDataRole.UserRole)
        
        # Draw active track highlight
        if active and filepath:
            import os
            if os.path.normpath(os.path.abspath(filepath)) == active:
                painter.fillRect(option.rect, QColor(74, 110, 224, 80))
        
        # Draw selection background if needed
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, option.palette.highlight())
            painter.setPen(option.palette.highlightedText().color())
            time_color = option.palette.highlightedText().color()
        else:
            painter.setPen(option.palette.text().color())
            time_color = QColor(150, 150, 150)

        if not filepath:
            painter.restore()
            return
        
        # Get cached data
        display_name = self.cache_manager.get_display_name(filepath)
        duration_str = self.cache_manager.get_duration(filepath)
        item_index = f"{index.row() + 1}."

        # Setup fonts
        monospace_font = QFont("Monospace", 9)
        regular_font = QFont("Arial", 10)

        # Draw time (right aligned)
        painter.setFont(monospace_font)
        painter.setPen(time_color)
        
        time_rect = QRect(
            rect.right() - self.time_width - self.right_margin,
            rect.top(),
            self.time_width,
            rect.height()
        )
        painter.drawText(time_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, duration_str)

        # Draw index (left aligned)
        painter.setPen(option.palette.text().color())
        index_rect = QRect(
            rect.left() + self.left_margin, 
            rect.top(), 
            self.index_width, 
            rect.height()
        )
        painter.drawText(index_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, item_index)

        # Draw display name (middle)
        name_left = index_rect.right() + 10
        name_right = time_rect.left() - 10
        name_width = max(0, name_right - name_left)

        if name_width > 0:
            name_rect = QRect(name_left, rect.top(), name_width, rect.height())
            painter.setFont(regular_font)
            
            # Use cached metrics to avoid recalculation
            fm = painter.fontMetrics()
            elided_text = fm.elidedText(
                display_name, 
                Qt.TextElideMode.ElideRight, 
                name_width
            )
            
            painter.drawText(
                name_rect, 
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                elided_text
            )

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 26)
    
    def get_display_name_cached(self, filepath):
        """Get display name from cache (public wrapper)"""
        return self.cache_manager.get_display_name(filepath)
    
    def get_duration(self, filepath):
        """Get duration from cache (public wrapper)"""
        return self.cache_manager.get_duration(filepath)
    
    def clear_cache(self):
        """Clear all caches"""
        self.cache_manager.clear_cache()
    
    def clear_cache_for_file(self, filepath):
        """Clear cache for specific file"""
        self.cache_manager.clear_cache_for_file(filepath)
    
    def get_stats(self):
        """Get cache statistics"""
        return self.cache_manager.get_stats()