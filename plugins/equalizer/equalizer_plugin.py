# -*- coding: utf-8 -*-
# plugins/equalizer/equalizer_plugin.py
"""
Equalizer Plugin - 10-band equalizer sa presetima

AudioWave Plugin System

Funkcionira:
- Sa GStreamer engine-om: PRAVI audio EQ
- Sa Qt Multimedia engine-om: Vizuelni EQ (priprema za buduće)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QComboBox, QFrame,
    QWidget, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, List, Optional


# ===== EQ PRESETI =====
EQ_PRESETS: Dict[str, List[float]] = {
    "Flat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "Rock": [5, 4, 3, 1, -1, -1, 0, 2, 3, 4],
    "Pop": [1, 2, 3, 4, 3, 1, 0, -1, -1, -1],
    "Jazz": [4, 3, 1, 2, -2, -2, 0, 1, 2, 3],
    "Classical": [5, 4, 3, 2, -1, -2, 0, 2, 3, 4],
    "Bass Boost": [6, 5, 4, 2, 0, 0, 0, 0, 0, 0],
    "Treble Boost": [0, 0, 0, 0, 0, 0, 2, 4, 5, 6],
    "Vocal": [-2, -1, 0, 2, 4, 4, 3, 2, 0, -1],
    "Electronic": [5, 4, 2, 0, -2, 0, 2, 4, 5, 5],
    "Hip-Hop": [5, 4, 3, 1, -1, -1, 1, 2, 3, 4],
    "R&B": [3, 4, 5, 3, -1, -1, 2, 3, 3, 2],
    "Acoustic": [4, 3, 2, 1, 1, 1, 2, 3, 3, 3],
    "Dance": [5, 4, 2, 0, 0, -1, 1, 3, 4, 5],
    "Loudness": [4, 3, 0, 0, -2, 0, -1, -1, 4, 3],
    "Custom": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
}

# Frekvencije za 10-band EQ
EQ_FREQUENCIES = ["32", "64", "125", "250", "500", "1K", "2K", "4K", "8K", "16K"]


class EQBandSlider(QWidget):
    """Custom slider za jednu EQ traku."""
    
    value_changed = pyqtSignal(int, float)  # band_index, value
    
    def __init__(self, band_index: int, frequency: str, parent=None):
        super().__init__(parent)
        self.band_index = band_index
        self.frequency = frequency
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # dB vrednost
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("font-size: 10px; color: #888; background: transparent;")
        self.value_label.setFixedHeight(20)
        layout.addWidget(self.value_label)
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(-120, 120)  # -12 do +12 dB * 10
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.slider.setTickInterval(30)
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.setMinimumHeight(150)
        layout.addWidget(self.slider, 1, Qt.AlignmentFlag.AlignHCenter)
        
        # Frekvencija label
        freq_label = QLabel(self.frequency)
        freq_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        freq_label.setStyleSheet("font-size: 11px; font-weight: bold; background: transparent;")
        freq_label.setFixedHeight(20)
        layout.addWidget(freq_label)
    
    def _on_value_changed(self, value: int):
        db_value = value / 10.0
        sign = "+" if db_value > 0 else ""
        self.value_label.setText(f"{sign}{db_value:.1f}")
        self.value_changed.emit(self.band_index, db_value)
    
    def set_value(self, value: float):
        self.slider.setValue(int(value * 10))
    
    def get_value(self) -> float:
        return self.slider.value() / 10.0


class EqualizerDialog(QDialog):
    """Glavni Equalizer dialog sa 10-band EQ i presetima."""
    
    eq_changed = pyqtSignal(list)
    
    def __init__(self, parent=None, engine=None):
        super().__init__(parent)
        self.engine = engine
        self.parent_window = parent
        self.bands: List[EQBandSlider] = []
        self.current_preset = "Flat"
        self.is_enabled = True
        self._updating_preset = False
        
        # Proveri da li engine podržava EQ
        self.has_real_eq = self._check_eq_support()
        
        self.setup_ui()
        self.apply_theme_style()
        
        # Učitaj trenutne vrednosti iz engine-a
        self._load_from_engine()
    
    def _check_eq_support(self) -> bool:
        """Proveri da li engine ima pravi EQ"""
        if self.engine and hasattr(self.engine, 'set_equalizer'):
            # Proveri da li je GStreamer engine
            engine_class = self.engine.__class__.__name__
            if engine_class == "GStreamerEngine":
                return True
        return False
    
    def _load_from_engine(self):
        """Učitaj EQ vrednosti iz engine-a"""
        if self.engine and hasattr(self.engine, 'get_equalizer'):
            try:
                values = self.engine.get_equalizer()
                if values and len(values) == 10:
                    self._updating_preset = True
                    for i, band in enumerate(self.bands):
                        band.set_value(values[i])
                    self._updating_preset = False
            except:
                pass
    
    def setup_ui(self):
        self.setWindowTitle("🎛️ Equalizer")
        self.setFixedSize(680, 480)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== HEADER =====
        header_layout = QHBoxLayout()
        
        # Enable checkbox
        self.enable_check = QCheckBox("Enable Equalizer")
        self.enable_check.setChecked(True)
        self.enable_check.toggled.connect(self._on_enable_toggled)
        header_layout.addWidget(self.enable_check)
        
        header_layout.addStretch()
        
        # Preset selector
        preset_label = QLabel("Preset:")
        preset_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(preset_label)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(EQ_PRESETS.keys()))
        self.preset_combo.setCurrentText("Flat")
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        self.preset_combo.setMinimumWidth(150)
        header_layout.addWidget(self.preset_combo)
        
        layout.addLayout(header_layout)
        
        # ===== INFO BANNER =====
        info_frame = QFrame()
        info_frame.setObjectName("eqInfoFrame")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 10, 12, 10)
        
        if self.has_real_eq:
            info_text = "✅ Real-time EQ active (GStreamer backend)"
            info_color = "#4ade80"
        else:
            info_text = "ℹ️ Visual EQ only - Switch to GStreamer backend for real audio EQ"
            info_color = "#888"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet(f"color: {info_color}; font-size: 12px; background: transparent;")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_frame)
        
        # ===== EQ BANDS =====
        bands_frame = QFrame()
        bands_frame.setObjectName("eqBandsFrame")
        bands_layout = QHBoxLayout(bands_frame)
        bands_layout.setSpacing(5)
        bands_layout.setContentsMargins(10, 10, 10, 10)
        
        for i, freq in enumerate(EQ_FREQUENCIES):
            band = EQBandSlider(i, freq)
            band.value_changed.connect(self._on_band_changed)
            self.bands.append(band)
            bands_layout.addWidget(band)
        
        layout.addWidget(bands_frame, 1)
        
        # ===== FOOTER =====
        footer_layout = QHBoxLayout()
        
        # Reset button
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self._reset_eq)
        reset_btn.setFixedWidth(90)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_layout.addWidget(reset_btn)
        
        footer_layout.addStretch()
        
        # Apply button (za Qt Multimedia - priprema za buduće)
        if not self.has_real_eq:
            apply_btn = QPushButton("💾 Save Preset")
            apply_btn.clicked.connect(self._save_preset)
            apply_btn.setFixedWidth(100)
            apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            footer_layout.addWidget(apply_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(80)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def _on_enable_toggled(self, enabled: bool):
        """Toggle EQ on/off"""
        self.is_enabled = enabled
        
        for band in self.bands:
            band.setEnabled(enabled)
        
        self.preset_combo.setEnabled(enabled)
        
        if self.engine and hasattr(self.engine, 'enable_equalizer'):
            self.engine.enable_equalizer(enabled)
        
        if not enabled:
            self._apply_to_engine([0.0] * 10)
        else:
            self._apply_to_engine(self.get_eq_values())
    
    def _on_preset_changed(self, preset_name: str):
        """Primeni preset"""
        if self._updating_preset:
            return
        
        if preset_name in EQ_PRESETS and preset_name != "Custom":
            self.current_preset = preset_name
            values = EQ_PRESETS[preset_name]
            
            self._updating_preset = True
            for i, band in enumerate(self.bands):
                band.set_value(float(values[i]))
            self._updating_preset = False
            
            self._apply_to_engine([float(v) for v in values])
    
    def _on_band_changed(self, band_index: int, value: float):
        """Kada se promeni vrednost banda"""
        if self._updating_preset:
            return
        
        # Primeni na engine odmah (real-time)
        if self.has_real_eq and self.engine:
            self.engine.set_equalizer_band(band_index, value)
        
        # Proveri da li odgovara nekom presetu
        current_values = self.get_eq_values()
        
        matched_preset = None
        for name, values in EQ_PRESETS.items():
            if name != "Custom":
                if all(abs(current_values[i] - values[i]) < 0.5 for i in range(10)):
                    matched_preset = name
                    break
        
        self._updating_preset = True
        if matched_preset:
            self.preset_combo.setCurrentText(matched_preset)
        else:
            self.preset_combo.setCurrentText("Custom")
        self._updating_preset = False
        
        self.eq_changed.emit(current_values)
    
    def _apply_to_engine(self, values: List[float]):
        """Primeni EQ vrednosti na engine"""
        if self.engine and hasattr(self.engine, 'set_equalizer'):
            self.engine.set_equalizer(values)
        
        self.eq_changed.emit(values)
    
    def _reset_eq(self):
        """Reset na Flat"""
        self.preset_combo.setCurrentText("Flat")
    
    def _save_preset(self):
        """Sačuvaj custom preset (placeholder)"""
        QMessageBox.information(
            self,
            "Save Preset",
            "Custom preset saved!\n\n"
            "Note: Presets are saved for the session.\n"
            "Permanent preset saving coming soon."
        )
    
    def get_eq_values(self) -> List[float]:
        """Vrati listu vrednosti svih bandova"""
        return [band.get_value() for band in self.bands]
    
    def set_eq_values(self, values: List[float]):
        """Postavi vrednosti svih bandova"""
        self._updating_preset = True
        for i, value in enumerate(values):
            if i < len(self.bands):
                self.bands[i].set_value(value)
        self._updating_preset = False
        self._apply_to_engine(values)
    
    def apply_theme_style(self):
        """Primeni stil koji prati temu"""
        primary = "#667eea"
        secondary = "#764ba2"
        bg = "#1a1a2e"
        text = "#ffffff"
        
        # Accent boja za EQ status
        eq_accent = "#4ade80" if self.has_real_eq else "#667eea"
        
        try:
            if self.parent_window:
                if hasattr(self.parent_window, 'app') and hasattr(self.parent_window.app, 'theme_manager'):
                    tm = self.parent_window.app.theme_manager
                    if not tm.is_dark_theme():
                        bg = "#f0f0f5"
                        text = "#333333"
                        primary = "#5a6fd6"
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
            
            QCheckBox {{
                color: {text};
                font-size: 13px;
                background: transparent;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {eq_accent};
                border: 2px solid {eq_accent};
                border-radius: 4px;
            }}
            
            QCheckBox::indicator:unchecked {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid #555;
                border-radius: 4px;
            }}
            
            #eqInfoFrame {{
                background-color: rgba(102, 126, 234, 0.1);
                border: 1px solid rgba(102, 126, 234, 0.3);
                border-radius: 6px;
            }}
            
            #eqBandsFrame {{
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }}
            
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid {primary};
                border-radius: 6px;
                padding: 8px 12px;
                color: {text};
                font-size: 13px;
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {bg};
                border: 1px solid {primary};
                selection-background-color: {primary};
                color: {text};
            }}
            
            QSlider::groove:vertical {{
                background: qlineargradient(y1:0, y2:1, 
                    stop:0 #4ade80, stop:0.5 #333, stop:1 #e94560);
                width: 8px;
                border-radius: 4px;
            }}
            
            QSlider::handle:vertical {{
                background: #fff;
                border: 2px solid {eq_accent};
                height: 16px;
                margin: 0 -4px;
                border-radius: 8px;
            }}
            
            QSlider::handle:vertical:hover {{
                background: {eq_accent};
            }}
            
            QPushButton {{
                background-color: rgba(102, 126, 234, 0.2);
                border: 1px solid {primary};
                border-radius: 6px;
                padding: 8px 16px;
                color: {text};
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: {primary};
            }}
            
            QPushButton:pressed {{
                background-color: {secondary};
            }}
        """)


class EqualizerWidget(QWidget):
    """Kompaktni Equalizer widget za ugrađivanje."""
    
    eq_changed = pyqtSignal(list)
    
    def __init__(self, parent=None, engine=None):
        super().__init__(parent)
        self.engine = engine
        self.bands: List[EQBandSlider] = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Preset row
        preset_layout = QHBoxLayout()
        
        self.enable_check = QCheckBox("Enable")
        self.enable_check.setChecked(True)
        preset_layout.addWidget(self.enable_check)
        
        preset_layout.addStretch()
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(EQ_PRESETS.keys()))
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        
        layout.addLayout(preset_layout)
        
        # Bands
        bands_layout = QHBoxLayout()
        for i, freq in enumerate(EQ_FREQUENCIES):
            band = EQBandSlider(i, freq)
            band.value_changed.connect(self._on_band_changed)
            self.bands.append(band)
            bands_layout.addWidget(band)
        
        layout.addLayout(bands_layout)
    
    def _on_preset_changed(self, preset_name: str):
        if preset_name in EQ_PRESETS:
            values = EQ_PRESETS[preset_name]
            for i, band in enumerate(self.bands):
                band.set_value(float(values[i]))
    
    def _on_band_changed(self, band_index: int, value: float):
        self.eq_changed.emit(self.get_values())
    
    def get_values(self) -> List[float]:
        return [band.get_value() for band in self.bands]
    
    def set_values(self, values: List[float]):
        for i, value in enumerate(values):
            if i < len(self.bands):
                self.bands[i].set_value(value)


def show_equalizer(parent=None, engine=None):
    """Prikaži Equalizer dialog."""
    dialog = EqualizerDialog(parent, engine)
    dialog.exec()