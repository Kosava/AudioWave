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
EQ_PRESETS: Dict[str, Dict[str, any]] = {
    "Flat": {"gains": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "preamp": 0},
    "Rock": {"gains": [5, 4, 3, 1, -1, -1, 0, 2, 3, 4], "preamp": 2},
    "Pop": {"gains": [1, 2, 3, 4, 3, 1, 0, -1, -1, -1], "preamp": 1},
    "Jazz": {"gains": [4, 3, 1, 2, -2, -2, 0, 1, 2, 3], "preamp": 1},
    "Classical": {"gains": [5, 4, 3, 2, -1, -2, 0, 2, 3, 4], "preamp": 2},
    "Bass Boost": {"gains": [6, 5, 4, 2, 0, 0, 0, 0, 0, 0], "preamp": 3},
    "Treble Boost": {"gains": [0, 0, 0, 0, 0, 0, 2, 4, 5, 6], "preamp": 2},
    "Vocal": {"gains": [-2, -1, 0, 2, 4, 4, 3, 2, 0, -1], "preamp": 0},
    "Electronic": {"gains": [5, 4, 2, 0, -2, 0, 2, 4, 5, 5], "preamp": 1},
    "Hip-Hop": {"gains": [5, 4, 3, 1, -1, -1, 1, 2, 3, 4], "preamp": 2},
    "R&B": {"gains": [3, 4, 5, 3, -1, -1, 2, 3, 3, 2], "preamp": 1},
    "Acoustic": {"gains": [4, 3, 2, 1, 1, 1, 2, 3, 3, 3], "preamp": 0},
    "Dance": {"gains": [5, 4, 2, 0, 0, -1, 1, 3, 4, 5], "preamp": 2},
    "Loudness": {"gains": [4, 3, 0, -2, -4, -4, -2, 0, 3, 4], "preamp": 3},
    "Custom": {"gains": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "preamp": 0}
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
    
    def __init__(self, parent=None, engine=None, app=None):
        super().__init__(parent)
        self.engine = engine
        self.app = app
        self.parent_window = parent
        
        # Ako nema engine-a, pokušaj da ga dobiješ iz app ili parent
        if not self.engine:
            if app and hasattr(app, 'engine'):
                self.engine = app.engine
                print(f"🔊 [EQ] Got engine from app: {type(self.engine).__name__}")
            elif parent and hasattr(parent, 'app') and hasattr(parent.app, 'engine'):
                self.engine = parent.app.engine
                print(f"🔊 [EQ] Got engine from parent: {type(self.engine).__name__}")
            else:
                print(f"⚠️ [EQ] No engine provided and cannot find one!")
        
        self.bands: List[EQBandSlider] = []
        self.current_preset = "Flat"
        self.is_enabled = True
        self._updating_preset = False
        
        # Proveri da li engine podržava EQ
        self.has_real_eq = self._check_eq_support()
        
        print(f"🎛️ [EQ] Dialog initialized with engine: {type(self.engine).__name__ if self.engine else 'None'}")
        print(f"🎛️ [EQ] Has real EQ: {self.has_real_eq}")
        
        self.setup_ui()
        self.apply_theme_style()
        
        # Učitaj trenutne vrednosti iz engine-a
        self._load_from_engine()
    
    def _check_eq_support(self) -> bool:
        """Proveri da li engine ima pravi EQ (GStreamer)"""
        if not self.engine:
            print("⚠️ [EQ] No engine provided for EQ support check")
            return False

        try:
            engine_class = type(self.engine).__name__
            engine_module = type(self.engine).__module__
            
            print(f"🔍 [EQ] Engine type: {engine_class}")
            print(f"🔍 [EQ] Engine module: {engine_module}")
            
            # Proveri da li je GStreamer
            is_gstreamer = (
                "GStreamerEngine" in engine_class or
                "gstreamer_engine" in engine_module.lower() or
                hasattr(self.engine, "equalizer") or
                hasattr(self.engine, "_eq_values")
            )
            
            print(f"🔍 [EQ] Is GStreamer engine: {is_gstreamer}")
            
            # Dodatna provera - ako engine ima has_equalizer metodu
            if hasattr(self.engine, 'has_equalizer'):
                real_eq = self.engine.has_equalizer()
                print(f"🎛️ [EQ] Engine.has_equalizer() = {real_eq}")
                return real_eq
            
            print(f"🎛️ [EQ] Real EQ detection: {is_gstreamer}")
            return bool(is_gstreamer)

        except Exception as e:
            print(f"⚠️ [EQ] Engine detection error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_from_engine(self):
        """Učitaj EQ vrednosti iz engine-a"""
        if not self.engine:
            print("⚠️ [EQ] No engine to load EQ values from")
            return

        try:
            print(f"🔍 [EQ] Trying to load EQ values from engine...")
            
            # Proveri različite metode za dobijanje EQ vrednosti
            if hasattr(self.engine, 'get_equalizer'):
                values = self.engine.get_equalizer()
                print(f"🔍 [EQ] Got EQ values via get_equalizer(): {values}")
                if values and len(values) == 10:
                    self._updating_preset = True
                    for i, band in enumerate(self.bands):
                        band.set_value(values[i])
                    self._updating_preset = False
                    print(f"✅ [EQ] Loaded EQ values from engine")
                    return
            
            if hasattr(self.engine, '_eq_values'):
                values = self.engine._eq_values
                print(f"🔍 [EQ] Got EQ values via _eq_values: {values}")
                if values and len(values) == 10:
                    self._updating_preset = True
                    for i, band in enumerate(self.bands):
                        band.set_value(values[i])
                    self._updating_preset = False
                    print(f"✅ [EQ] Loaded EQ values from _eq_values")
                    return
            
            print(f"⚠️ [EQ] Could not load EQ values from engine")
            
        except Exception as e:
            print(f"⚠️ [EQ] Error loading EQ from engine: {e}")
            import traceback
            traceback.print_exc()
    
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
        
        # Save preset button
        save_btn = QPushButton("💾 Save Preset")
        save_btn.clicked.connect(self._save_preset)
        save_btn.setFixedWidth(120)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_layout.addWidget(save_btn)
        
        layout.addLayout(footer_layout)
    
    def _on_enable_toggled(self, checked: bool):
        self.is_enabled = checked
        if self.engine and hasattr(self.engine, 'enable_equalizer'):
            self.engine.enable_equalizer(checked)
            print(f"🎛️ [EQ] Equalizer {'enabled' if checked else 'disabled'}")
        else:
            print(f"⚠️ [EQ] Engine doesn't have enable_equalizer method")
    
    def _on_preset_changed(self, preset_name: str):
        if self._updating_preset:
            return

        if preset_name in EQ_PRESETS:
            preset_data = EQ_PRESETS[preset_name]
            values = preset_data["gains"]
            preamp = preset_data.get("preamp", 0)

            print(f"🎛️ [EQ] Applying preset: {preset_name}")
            print(f"🎛️ [EQ] Values: {values}, Preamp: {preamp}")

            self._updating_preset = True
            for i, band in enumerate(self.bands):
                band.set_value(float(values[i]))
            self._updating_preset = False

            # 🔥 PRIMENI PRESET NA ENGINE
            self._apply_to_engine(values, preamp)

            self.current_preset = preset_name
    
    def _on_band_changed(self, band_index: int, value: float):
        """Kada se promeni vrednost banda"""
        if self._updating_preset:
            return

        print(f"🎛️ [EQ] Band {band_index} changed to {value}dB")
        
        # 🔥 PRAVA VEZA SA GStreamerEngine
        if self.has_real_eq and self.engine:
            try:
                # Prvo pokušaj sa set_eq_band
                if hasattr(self.engine, "set_eq_band"):
                    self.engine.set_eq_band(band_index, float(value))
                    print(f"✅ [EQ] Applied band {band_index} via set_eq_band")
                # Pokušaj sa equalizer elementom
                elif hasattr(self.engine, "equalizer") and self.engine.equalizer:
                    self.engine.equalizer.set_property(f"band{band_index}", float(value))
                    print(f"✅ [EQ] Applied band {band_index} via equalizer element")
                # Pokušaj sa set_equalizer
                elif hasattr(self.engine, "set_equalizer"):
                    # Treba da ažuriramo celu listu
                    current_values = self.get_eq_values()
                    self.engine.set_equalizer(current_values, 0.0)
                    print(f"✅ [EQ] Applied all bands via set_equalizer")
                else:
                    print(f"⚠️ [EQ] Engine doesn't have EQ application methods!")
                    eq_methods = [m for m in dir(self.engine) if 'eq' in m.lower() or 'band' in m.lower()]
                    print(f"🔍 [EQ] Available EQ methods: {eq_methods}")
            except Exception as e:
                print(f"⚠️ [EQ] Error applying band {band_index}: {e}")
                import traceback
                traceback.print_exc()

        # Proveri da li odgovara nekom presetu
        current_values = self.get_eq_values()

        matched_preset = None
        for name, preset in EQ_PRESETS.items():
            if name != "Custom":
                values = preset["gains"]
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
    
    def _apply_to_engine(self, values: List[float], preamp: float = 0.0):
        """Primeni EQ vrednosti na engine - SA DEBUG ISPISIMA"""
        if not self.engine:
            print("❌ [EQ] No engine to apply EQ to")
            return

        print(f"🎛️ [EQ] Applying EQ to engine: {values}")
        print(f"🎛️ [EQ] Engine type: {type(self.engine).__name__}")
        print(f"🎛️ [EQ] Engine has_equalizer: {hasattr(self.engine, 'has_equalizer') and self.engine.has_equalizer()}")
        
        try:
            # Prvo pokušaj sa set_equalizer (GStreamer ima ovo)
            if hasattr(self.engine, 'set_equalizer'):
                print(f"✅ [EQ] Engine has set_equalizer method")
                try:
                    # GStreamer podržava preamp
                    if hasattr(self.engine, '_eq_preamp'):
                        success = self.engine.set_equalizer(values, preamp)
                        print(f"✅ [EQ] Applied via set_equalizer(values, preamp={preamp}), success={success}")
                    else:
                        success = self.engine.set_equalizer(values)
                        print(f"✅ [EQ] Applied via set_equalizer(values), success={success}")
                    return
                except Exception as e:
                    print(f"⚠️ [EQ] set_equalizer failed: {e}")

            # Alternativni načini
            elif hasattr(self.engine, 'set_eq_band'):
                print(f"✅ [EQ] Engine has set_eq_band method")
                for i, value in enumerate(values):
                    self.engine.set_eq_band(i, value)
                print(f"✅ [EQ] Applied via set_eq_band for all bands")
                return

            elif hasattr(self.engine, 'equalizer') and self.engine.equalizer:
                print(f"✅ [EQ] Engine has equalizer element")
                for i, v in enumerate(values):
                    self.engine.equalizer.set_property(f"band{i}", float(v))
                print(f"✅ [EQ] Applied via equalizer element")
                return

            else:
                print(f"❌ [EQ] Engine has NO EQ methods!")
                print(f"🔍 [EQ] Engine methods: {[m for m in dir(self.engine) if 'eq' in m.lower() or 'band' in m.lower()]}")

        except Exception as e:
            print(f"❌ [EQ] Error applying EQ: {e}")
            import traceback
            traceback.print_exc()

        self.eq_changed.emit(values)
    
    def _reset_eq(self):
        """Reset na Flat"""
        print("🎛️ [EQ] Resetting EQ to Flat")
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
        print("🎛️ [EQ] Custom preset saved (session only)")
    
    def get_eq_values(self) -> List[float]:
        """Vrati listu vrednosti svih bandova"""
        return [band.get_value() for band in self.bands]
    
    def set_eq_values(self, values: List[float]):
        """Postavi vrednosti svih bandova"""
        print(f"🎛️ [EQ] Setting EQ values: {values}")
        self._updating_preset = True
        for i, value in enumerate(values):
            if i < len(self.bands):
                self.bands[i].set_value(value)
        self._updating_preset = False
        self._apply_to_engine(values, 0.0)
    
    def apply_theme_style(self):
        """Primeni stil koji prati temu"""
        primary = "#667eea"
        secondary = "#764ba2"
        bg = "#1a1a2e"
        text = "#ffffff"
        
        # Accent boja za EQ status
        eq_accent = "#4ade80" if self.has_real_eq else "#f59e0b"
        
        try:
            if self.parent_window:
                if hasattr(self.parent_window, 'app') and hasattr(self.parent_window.app, 'theme_manager'):
                    tm = self.parent_window.app.theme_manager
                    if not tm.is_dark_theme():
                        bg = "#f0f0f5"
                        text = "#333333"
                        primary = "#5a6fd6"
                        eq_accent = "#059669" if self.has_real_eq else "#d97706"
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
    
    def __init__(self, parent=None, engine=None, app=None):
        super().__init__(parent)
        self.engine = engine
        self.app = app
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
            preset_data = EQ_PRESETS[preset_name]
            values = preset_data["gains"]
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


class EqualizerPlugin:
    """Main plugin class za Equalizer - za PluginManager registraciju"""
    
    def __init__(self, app=None):
        self.app = app
        self.name = "Equalizer"
        self.id = "equalizer"
        self.version = "1.0.0"
        self.description = "10-band equalizer with presets"
        self.author = "AudioWave"
        
        # Dialog i widget klase (za PluginManager)
        self.Dialog = EqualizerDialog
        self.Widget = EqualizerWidget
    
    def get_dialog(self, parent=None, **kwargs):
        """Vrati instancu dijaloga"""
        if self.app and 'app' not in kwargs:
            kwargs['app'] = self.app
        return self.Dialog(parent, **kwargs)
    
    def get_widget(self, parent=None, **kwargs):
        """Vrati instancu widgeta"""
        if self.app and 'app' not in kwargs:
            kwargs['app'] = self.app
        return self.Widget(parent, **kwargs)