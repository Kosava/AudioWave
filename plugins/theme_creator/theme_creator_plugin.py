# -*- coding: utf-8 -*-
# plugins/theme_creator/theme_creator_plugin.py
"""
Theme Creator Plugin - Kreiraj sopstvene teme za AudioWave
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QPushButton, QColorDialog, QFontDialog, QComboBox,
    QGroupBox, QGridLayout, QLineEdit, QTextEdit, QMessageBox,
    QFileDialog, QTabWidget, QScrollArea, QFrame, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen, QBrush, QLinearGradient
import json
import os
from datetime import datetime
from pathlib import Path


class ColorPickerButton(QPushButton):
    """Dugme za biranje boje sa preview-om"""
    
    color_changed = pyqtSignal(str)
    
    def __init__(self, color="#667eea", label="Boja"):
        super().__init__()
        self.color = color
        self.label = label
        self.setText(label)
        self.setMinimumWidth(100)
        self.clicked.connect(self.pick_color)
        self.update_style()
    
    def pick_color(self):
        """Otvori color dialog"""
        dialog = QColorDialog(QColor(self.color))
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        
        if dialog.exec():
            new_color = dialog.selectedColor()
            self.color = new_color.name()
            self.update_style()
            self.color_changed.emit(self.color)
    
    def update_style(self):
        """Ažuriraj stil dugmeta da pokazuje boju"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color};
                color: {'white' if self.is_dark_color(self.color) else 'black'};
                border: 2px solid #333;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid #666;
                opacity: 0.9;
            }}
        """)
    
    def is_dark_color(self, hex_color):
        """Proveri da li je boja tamna"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    
    def get_color(self):
        return self.color
    
    def set_color(self, color):
        self.color = color
        self.update_style()


class ThemePreviewWidget(QWidget):
    """Widget za preview teme u realnom vremenu"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 200)
        
        self.primary_color = "#667eea"
        self.secondary_color = "#764ba2"
        self.bg_color = "#0f172a"
        self.text_color = "#e2e8f0"
        
        self.setAutoFillBackground(True)
        self.update_preview()
    
    def update_colors(self, primary, secondary, bg, text):
        """Ažuriraj boje i ponovo iscrtaj"""
        self.primary_color = primary
        self.secondary_color = secondary
        self.bg_color = bg
        self.text_color = text
        self.update_preview()
        self.repaint()
    
    def update_preview(self):
        """Ažuriraj pozadinu widget-a"""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(self.bg_color))
        self.setPalette(palette)
    
    def paintEvent(self, event):
        """Custom paint za prikaz teme"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Pozadina
        painter.fillRect(self.rect(), QColor(self.bg_color))
        
        # Header sa gradientom
        header_gradient = QLinearGradient(0, 0, self.width(), 50)
        header_gradient.setColorAt(0, QColor(self.primary_color))
        header_gradient.setColorAt(1, QColor(self.secondary_color))
        painter.fillRect(0, 0, self.width(), 50, QBrush(header_gradient))
        
        # Naslov
        painter.setPen(QColor(self.text_color))
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(20, 30, "Preview Title")
        
        # Podnaslov
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(20, 50, "Preview Artist")
        
        # Progress bar
        progress_rect = (20, 140, 260, 8)
        painter.setBrush(QBrush(QColor("#333")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(*progress_rect, 4, 4)
        
        # Progress fill
        progress_fill_rect = (20, 140, 130, 8)  # 50%
        progress_gradient = QLinearGradient(20, 140, 150, 140)
        progress_gradient.setColorAt(0, QColor(self.primary_color))
        progress_gradient.setColorAt(1, QColor(self.secondary_color))
        painter.setBrush(QBrush(progress_gradient))
        painter.drawRoundedRect(*progress_fill_rect, 4, 4)
        
        painter.end()


class ThemeCreatorDialog(QDialog):
    """Glavni dialog za kreiranje tema - FIXED za Settings dialog"""
    
    theme_created = pyqtSignal(dict)  # Emituje JSON teme kada se kreira
    
    def __init__(self, parent=None, **kwargs):
        """
        Inicijalizacija dialog-a.
        
        Args:
            parent: Roditeljski widget
            **kwargs: Može da sadrži 'engine' (ignorišemo za Theme Creator)
        """
        super().__init__(parent)
        
        # Ignoriši kwargs koji nisu potrebni
        # Theme Creator ne koristi audio engine
        
        self.theme_data = {
            "name": "My Custom Theme",
            "type": "dark",  # "dark" ili "light"
            "primary": "#667eea",
            "secondary": "#764ba2",
            "bg_main": "#0f172a",
            "bg_secondary": "#1e293b",
            "text_color": "#e2e8f0",
            "font_family": "Arial",
            "font_size": 13,
            "label_style": "minimal",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "author": ""
        }
        
        self.setup_ui()
        self.setWindowTitle("🎨 Theme Creator")
        self.resize(900, 700)
        
        # Timer za real-time preview (svakih 500ms)
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(500)
    
    def setup_ui(self):
        """Setup korisničkog interfejsa"""
        layout = QVBoxLayout(self)
        
        # Tabovi
        tabs = QTabWidget()
        tabs.addTab(self.create_design_tab(), "🎨 Design")
        tabs.addTab(self.create_export_tab(), "💾 Export")
        tabs.addTab(self.create_import_tab(), "📥 Import")
        layout.addWidget(tabs)
        
        # Dugmadi
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("👁️ Live Preview")
        self.preview_btn.setCheckable(True)
        self.preview_btn.setChecked(True)
        self.preview_btn.clicked.connect(self.toggle_preview)
        button_layout.addWidget(self.preview_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("💾 Save Theme")
        self.save_btn.clicked.connect(self.save_theme)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def create_design_tab(self):
        """Kreiraj design tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scroll area za sav sadržaj
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # === OSNOVNE INFORMACIJE ===
        basic_group = QGroupBox("📝 Basic Information")
        basic_layout = QGridLayout()
        
        basic_layout.addWidget(QLabel("Theme Name:"), 0, 0)
        self.name_edit = QLineEdit(self.theme_data["name"])
        self.name_edit.textChanged.connect(self.update_theme_name)
        basic_layout.addWidget(self.name_edit, 0, 1)
        
        basic_layout.addWidget(QLabel("Author:"), 1, 0)
        self.author_edit = QLineEdit("")
        self.author_edit.textChanged.connect(self.update_author)
        basic_layout.addWidget(self.author_edit, 1, 1)
        
        basic_layout.addWidget(QLabel("Theme Type:"), 2, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["dark", "light"])
        self.type_combo.setCurrentText(self.theme_data["type"])
        self.type_combo.currentTextChanged.connect(self.update_theme_type)
        basic_layout.addWidget(self.type_combo, 2, 1)
        
        basic_layout.addWidget(QLabel("Label Style:"), 3, 0)
        self.style_combo = QComboBox()
        self.style_combo.addItems(["minimal", "glass", "clean", "subtle"])
        self.style_combo.setCurrentText(self.theme_data["label_style"])
        self.style_combo.currentTextChanged.connect(self.update_label_style)
        basic_layout.addWidget(self.style_combo, 3, 1)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # === BOJE ===
        colors_group = QGroupBox("🎨 Colors")
        colors_layout = QGridLayout()
        
        # Red 1: Primarne boje
        colors_layout.addWidget(QLabel("Primary Color:"), 0, 0)
        self.primary_btn = ColorPickerButton(self.theme_data["primary"], "Primary")
        self.primary_btn.color_changed.connect(self.update_primary_color)
        colors_layout.addWidget(self.primary_btn, 0, 1)
        
        colors_layout.addWidget(QLabel("Secondary Color:"), 0, 2)
        self.secondary_btn = ColorPickerButton(self.theme_data["secondary"], "Secondary")
        self.secondary_btn.color_changed.connect(self.update_secondary_color)
        colors_layout.addWidget(self.secondary_btn, 0, 3)
        
        # Red 2: Background boje
        colors_layout.addWidget(QLabel("Main Background:"), 1, 0)
        self.bg_main_btn = ColorPickerButton(self.theme_data["bg_main"], "Main BG")
        self.bg_main_btn.color_changed.connect(self.update_bg_main_color)
        colors_layout.addWidget(self.bg_main_btn, 1, 1)
        
        colors_layout.addWidget(QLabel("Secondary Background:"), 1, 2)
        self.bg_secondary_btn = ColorPickerButton(self.theme_data["bg_secondary"], "Sec BG")
        self.bg_secondary_btn.color_changed.connect(self.update_bg_secondary_color)
        colors_layout.addWidget(self.bg_secondary_btn, 1, 3)
        
        # Red 3: Text boje
        colors_layout.addWidget(QLabel("Text Color:"), 2, 0)
        self.text_btn = ColorPickerButton(self.theme_data["text_color"], "Text")
        self.text_btn.color_changed.connect(self.update_text_color)
        colors_layout.addWidget(self.text_btn, 2, 1)
        
        colors_layout.addWidget(QLabel("Accent Color:"), 2, 2)
        self.accent_btn = ColorPickerButton("#667eea", "Accent")
        self.accent_btn.color_changed.connect(self.update_accent_color)
        colors_layout.addWidget(self.accent_btn, 2, 3)
        
        colors_group.setLayout(colors_layout)
        scroll_layout.addWidget(colors_group)
        
        # === FONT ===
        font_group = QGroupBox("🔤 Font")
        font_layout = QGridLayout()
        
        font_layout.addWidget(QLabel("Font Family:"), 0, 0)
        self.font_btn = QPushButton("Select Font")
        self.font_btn.clicked.connect(self.select_font)
        font_layout.addWidget(self.font_btn, 0, 1)
        
        font_layout.addWidget(QLabel("Font Size:"), 1, 0)
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 20)
        self.font_size_slider.setValue(self.theme_data["font_size"])
        self.font_size_slider.valueChanged.connect(self.update_font_size)
        font_layout.addWidget(self.font_size_slider, 1, 1)
        
        self.font_size_label = QLabel(f"Size: {self.theme_data['font_size']}px")
        font_layout.addWidget(self.font_size_label, 1, 2)
        
        font_group.setLayout(font_layout)
        scroll_layout.addWidget(font_group)
        
        # === PREVIEW ===
        preview_group = QGroupBox("👁️ Live Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_widget = ThemePreviewWidget()
        preview_layout.addWidget(self.preview_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Mini preview sa tekstom
        self.mini_preview = QFrame()
        self.mini_preview.setFixedSize(400, 60)
        self.mini_preview.setObjectName("miniPreview")
        preview_layout.addWidget(self.mini_preview, alignment=Qt.AlignmentFlag.AlignCenter)
        
        preview_group.setLayout(preview_layout)
        scroll_layout.addWidget(preview_group)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_export_tab(self):
        """Kreiraj export tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("💾 Export Theme to JSON"))
        layout.addWidget(QLabel("Your theme will be saved as a JSON file that can be shared or imported later."))
        
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setFont(QFont("Courier New", 10))
        self.update_json_display()
        layout.addWidget(self.json_display)
        
        # Export dugmadi
        export_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("📋 Copy JSON")
        self.copy_btn.clicked.connect(self.copy_json)
        export_layout.addWidget(self.copy_btn)
        
        self.export_btn = QPushButton("💾 Save to File")
        self.export_btn.clicked.connect(self.export_to_file)
        export_layout.addWidget(self.export_btn)
        
        layout.addLayout(export_layout)
        
        # Info
        info_label = QLabel(
            "💡 Save your theme to:\n"
            "  • ~/.audiowave/themes/  (for personal use)\n"
            "  • Anywhere else (to share with others)"
        )
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
    
    def create_import_tab(self):
        """Kreiraj import tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("📥 Import Theme from JSON"))
        layout.addWidget(QLabel("Load an existing theme JSON file to edit or use it."))
        
        # Import dugmadi
        import_layout = QHBoxLayout()
        
        self.browse_btn = QPushButton("📁 Browse JSON File")
        self.browse_btn.clicked.connect(self.browse_json_file)
        import_layout.addWidget(self.browse_btn)
        
        self.load_btn = QPushButton("🔄 Load Theme")
        self.load_btn.clicked.connect(self.load_theme)
        self.load_btn.setEnabled(False)
        import_layout.addWidget(self.load_btn)
        
        layout.addLayout(import_layout)
        
        # Prikaz izabranog fajla
        self.file_label = QLabel("No file selected")
        layout.addWidget(self.file_label)
        
        # Quick import preset dugmadi
        layout.addWidget(QLabel("\n🚀 Quick Import Presets:"))
        
        presets_layout = QHBoxLayout()
        
        preset1 = QPushButton("Import 'Nordic Light'")
        preset1.clicked.connect(lambda: self.import_preset("nordic_light"))
        presets_layout.addWidget(preset1)
        
        preset2 = QPushButton("Import 'Dark Modern'")
        preset2.clicked.connect(lambda: self.import_preset("dark_modern"))
        presets_layout.addWidget(preset2)
        
        preset3 = QPushButton("Import 'Cyberpunk'")
        preset3.clicked.connect(lambda: self.import_preset("cyberpunk"))
        presets_layout.addWidget(preset3)
        
        layout.addLayout(presets_layout)
        
        layout.addStretch()
        return widget
    
    # === UPDATE METODE ===
    
    def update_theme_name(self, name):
        self.theme_data["name"] = name
        self.update_json_display()
    
    def update_author(self, author):
        self.theme_data["author"] = author
        self.update_json_display()
    
    def update_theme_type(self, theme_type):
        self.theme_data["type"] = theme_type
        # Ažuriraj default boje za tip teme
        if theme_type == "dark":
            self.bg_main_btn.set_color("#0f172a")
            self.bg_secondary_btn.set_color("#1e293b")
            self.text_btn.set_color("#e2e8f0")
        else:
            self.bg_main_btn.set_color("#ffffff")
            self.bg_secondary_btn.set_color("#f0f0f0")
            self.text_btn.set_color("#333333")
        self.update_json_display()
    
    def update_label_style(self, style):
        self.theme_data["label_style"] = style
        self.update_json_display()
    
    def update_primary_color(self, color):
        self.theme_data["primary"] = color
        self.update_json_display()
    
    def update_secondary_color(self, color):
        self.theme_data["secondary"] = color
        self.update_json_display()
    
    def update_bg_main_color(self, color):
        self.theme_data["bg_main"] = color
        self.update_json_display()
    
    def update_bg_secondary_color(self, color):
        self.theme_data["bg_secondary"] = color
        self.update_json_display()
    
    def update_text_color(self, color):
        self.theme_data["text_color"] = color
        self.update_json_display()
    
    def update_accent_color(self, color):
        self.theme_data["accent"] = color
        self.update_json_display()
    
    def update_font_size(self, size):
        self.theme_data["font_size"] = size
        self.font_size_label.setText(f"Size: {size}px")
        self.update_json_display()
    
    def select_font(self):
        """Otvori font dialog"""
        font, ok = QFontDialog.getFont()
        if ok:
            self.theme_data["font_family"] = font.family()
            self.font_btn.setText(font.family())
            self.update_json_display()
    
    # === PREVIEW ===
    
    def update_preview(self):
        """Ažuriraj preview widget"""
        self.preview_widget.update_colors(
            self.theme_data["primary"],
            self.theme_data["secondary"],
            self.theme_data["bg_main"],
            self.theme_data["text_color"]
        )
        
        # Ažuriraj mini preview
        self.mini_preview.setStyleSheet(f"""
            QFrame#miniPreview {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme_data['primary']}, 
                    stop:1 {self.theme_data['secondary']});
                border-radius: 10px;
                border: 2px solid {self.theme_data['text_color']}33;
            }}
        """)
    
    def toggle_preview(self, checked):
        """Uključi/isključi live preview"""
        if checked:
            self.preview_timer.start(500)
            self.preview_btn.setText("👁️ Live Preview (ON)")
        else:
            self.preview_timer.stop()
            self.preview_btn.setText("👁️ Live Preview (OFF)")
    
    # === JSON HANDLING ===
    
    def update_json_display(self):
        """Ažuriraj prikaz JSON-a"""
        display_data = self.theme_data.copy()
        # Dodaj timestamp
        display_data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        json_str = json.dumps(display_data, indent=2, ensure_ascii=False)
        self.json_display.setPlainText(json_str)
    
    def copy_json(self):
        """Kopiraj JSON u clipboard"""
        from PyQt6.QtGui import QGuiApplication
        
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.json_display.toPlainText())
        QMessageBox.information(self, "Copied", "JSON copied to clipboard!")
    
    def export_to_file(self):
        """Exportuj temu u JSON fajl"""
        # Kreiraj direktorijum ako ne postoji
        themes_dir = Path.home() / ".audiowave" / "themes"
        themes_dir.mkdir(parents=True, exist_ok=True)
        
        # Predloži ime fajla
        default_name = self.theme_data["name"].replace(" ", "_").lower() + ".json"
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Theme JSON",
            str(themes_dir / default_name),
            "JSON Files (*.json)"
        )
        
        if file_path:
            # Sačuvaj
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.theme_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self, 
                "Theme Saved", 
                f"Theme saved successfully!\n\n{file_path}"
            )
    
    def browse_json_file(self):
        """Browse za JSON fajl"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Theme JSON",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if file_path:
            self.current_json_file = file_path
            self.file_label.setText(f"Selected: {Path(file_path).name}")
            self.load_btn.setEnabled(True)
    
    def load_theme(self):
        """Učitaj temu iz JSON fajla"""
        try:
            with open(self.current_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ažuriraj sve polja
            for key, value in data.items():
                if key in self.theme_data:
                    self.theme_data[key] = value
            
            # Ažuriraj UI
            self.name_edit.setText(data.get("name", ""))
            self.author_edit.setText(data.get("author", ""))
            self.type_combo.setCurrentText(data.get("type", "dark"))
            self.style_combo.setCurrentText(data.get("label_style", "minimal"))
            
            # Ažuriraj color pickere
            self.primary_btn.set_color(data.get("primary", "#667eea"))
            self.secondary_btn.set_color(data.get("secondary", "#764ba2"))
            self.bg_main_btn.set_color(data.get("bg_main", "#0f172a"))
            self.bg_secondary_btn.set_color(data.get("bg_secondary", "#1e293b"))
            self.text_btn.set_color(data.get("text_color", "#e2e8f0"))
            
            # Ažuriraj font
            self.font_btn.setText(data.get("font_family", "Arial"))
            
            # Ažuriraj font size
            font_size = data.get("font_size", 13)
            self.font_size_slider.setValue(font_size)
            
            self.update_json_display()
            QMessageBox.information(self, "Theme Loaded", "Theme loaded successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load theme:\n{str(e)}")
    
    def import_preset(self, preset_name):
        """Učitaj preset temu"""
        presets = {
            "nordic_light": {
                "name": "Nordic Light",
                "type": "light",
                "primary": "#88c0d0",
                "secondary": "#5e81ac",
                "bg_main": "#eceff4",
                "bg_secondary": "#d8dee9",
                "text_color": "#2e3440",
                "font_family": "Arial",
                "font_size": 13,
                "label_style": "minimal",
                "author": "AudioWave"
            },
            "dark_modern": {
                "name": "Dark Modern",
                "type": "dark",
                "primary": "#667eea",
                "secondary": "#764ba2",
                "bg_main": "#0f172a",
                "bg_secondary": "#1e293b",
                "text_color": "#e2e8f0",
                "font_family": "Arial",
                "font_size": 13,
                "label_style": "minimal",
                "author": "AudioWave"
            },
            "cyberpunk": {
                "name": "Cyberpunk",
                "type": "dark",
                "primary": "#c026d3",
                "secondary": "#9333ea",
                "bg_main": "#0a0e1a",
                "bg_secondary": "#1a1030",
                "text_color": "#00ffff",
                "font_family": "Courier New",
                "font_size": 12,
                "label_style": "clean",
                "author": "AudioWave"
            }
        }
        
        if preset_name in presets:
            self.theme_data.update(presets[preset_name])
            
            # Ažuriraj UI
            self.name_edit.setText(self.theme_data["name"])
            self.type_combo.setCurrentText(self.theme_data["type"])
            self.style_combo.setCurrentText(self.theme_data["label_style"])
            self.primary_btn.set_color(self.theme_data["primary"])
            self.secondary_btn.set_color(self.theme_data["secondary"])
            self.bg_main_btn.set_color(self.theme_data["bg_main"])
            self.bg_secondary_btn.set_color(self.theme_data["bg_secondary"])
            self.text_btn.set_color(self.theme_data["text_color"])
            self.font_btn.setText(self.theme_data["font_family"])
            self.font_size_slider.setValue(self.theme_data["font_size"])
            
            self.update_json_display()
            QMessageBox.information(self, "Preset Loaded", f"Loaded {preset_name} preset!")
    
    def save_theme(self):
        """Sačuvaj temu i zatvori dialog"""
        if not self.theme_data["name"]:
            QMessageBox.warning(self, "Warning", "Please enter a theme name!")
            return
        
        # Emituj signal sa temom
        self.theme_created.emit(self.theme_data)
        
        # Automatski export ako želiš
        reply = QMessageBox.question(
            self, "Save Theme",
            "Theme created successfully!\n\nDo you want to export it to a JSON file?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.export_to_file()
        
        self.accept()


class ThemeCreatorWidget(QWidget):
    """Widget za prikaz Theme Creator-a (za plugin sistem)"""
    
    def __init__(self, parent=None, **kwargs):
        """Widget za Theme Creator"""
        super().__init__(parent)
        
        # Ignoriši kwargs
        layout = QVBoxLayout(self)
        
        title = QLabel("🎨 Theme Creator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        description = QLabel(
            "Create custom themes for AudioWave!\n"
            "Design your own color schemes, fonts, and styles."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        self.open_btn = QPushButton("Open Theme Creator")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        self.open_btn.clicked.connect(self.open_creator)
        layout.addWidget(self.open_btn)
        
        layout.addStretch()
    
    def open_creator(self):
        """Otvori Theme Creator dialog"""
        dialog = ThemeCreatorDialog(self)
        dialog.theme_created.connect(self.on_theme_created)
        dialog.exec()
    
    def on_theme_created(self, theme_data):
        """Kada se kreira nova tema"""
        print(f"🎨 New theme created: {theme_data['name']}")
        # Ovdje možete dodati logiku za automatsko učitavanje teme u aplikaciju


# ===== TEST =====
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dialog = ThemeCreatorDialog()
    dialog.show()
    
    sys.exit(app.exec())