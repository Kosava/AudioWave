#!/usr/bin/env python3
"""
Radio Browser Plugin for TrayWave
Allows searching and playing live radio stations from radio-browser.info API
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QComboBox, QSpinBox,
    QGroupBox, QCheckBox, QMessageBox, QProgressBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer
from PyQt6.QtGui import QIcon, QAction, QCloseEvent
import requests
import json
from typing import List, Dict, Optional
from pathlib import Path


class RadioFetcherThread(QThread):
    """Thread za asinhrono preuzimanje radio stanica"""
    
    finished = pyqtSignal(list)  # Lista stanica
    error = pyqtSignal(str)  # Poruka o grešci
    progress = pyqtSignal(int)  # Progres (0-100)
    
    def __init__(self, params: Dict):
        super().__init__()
        self.params = params
        self.api_base = "https://de1.api.radio-browser.info/json/stations"
        
    def run(self):
        """Pokreće preuzimanje stanica"""
        try:
            self.progress.emit(10)
            
            # Pripremi URL i parametre
            endpoint = self.params.get('endpoint', 'search')
            url = f"{self.api_base}/{endpoint}"
            
            headers = {"User-Agent": "TrayWave/2.0 Radio Browser Plugin"}
            
            # Parametri pretrage
            search_params = {
                "hidebroken": "true",
                "order": self.params.get('order', 'votes'),
                "reverse": "true",
                "limit": self.params.get('limit', 100)
            }
            
            # Dodaj specifične filtere
            if self.params.get('tag'):
                search_params['tag'] = self.params['tag']
            if self.params.get('country'):
                search_params['countrycode'] = self.params['country']
            if self.params.get('language'):
                search_params['language'] = self.params['language']
            if self.params.get('name'):
                search_params['name'] = self.params['name']
            if self.params.get('codec'):
                search_params['codec'] = self.params['codec']
            if self.params.get('bitrate_min'):
                search_params['bitrateMin'] = self.params['bitrate_min']
            
            self.progress.emit(30)
            
            # Pošalji zahtev
            response = requests.get(url, params=search_params, headers=headers, timeout=15)
            response.raise_for_status()
            
            self.progress.emit(60)
            
            # Parsiranje rezultata
            raw_stations = response.json()
            stations = []
            
            blocked_countries = set(self.params.get('blocked_countries', []))
            
            for station in raw_stations:
                # Filtriraj blokirane zemlje
                country_code = (station.get("countrycode") or "").upper()
                if country_code in blocked_countries:
                    continue
                
                name = station.get("name", "Unknown Station")
                url = station.get("url_resolved") or station.get("url")
                
                if not url:
                    continue
                
                stations.append({
                    "name": name.strip(),
                    "url": url.strip(),
                    "country": station.get("country", ""),
                    "countrycode": country_code,
                    "tags": station.get("tags", ""),
                    "codec": station.get("codec", ""),
                    "bitrate": station.get("bitrate", 0),
                    "votes": station.get("votes", 0),
                    "language": station.get("language", ""),
                    "homepage": station.get("homepage", ""),
                    "favicon": station.get("favicon", "")
                })
            
            self.progress.emit(100)
            self.finished.emit(stations)
            
        except requests.RequestException as e:
            self.error.emit(f"Greška prilikom preuzimanja: {str(e)}")
        except Exception as e:
            self.error.emit(f"Neočekivana greška: {str(e)}")


class RadioBrowserPlugin(QMainWindow):  # ⭐ PROMENJENO: QMainWindow umesto QWidget
    """
    Radio Browser Plugin - pretraga i reprodukcija radio stanica
    """
    
    # Signal za dodavanje stanice u playlist
    add_to_playlist = pyqtSignal(str, str)  # (naziv, url)
    
    def __init__(self, *args, **kwargs):
        """
        Inicijalizacija Radio Browser plugina.
        
        Podržava sve načine pozivanja:
        - RadioBrowserPlugin(plugin_manager)
        - RadioBrowserPlugin(plugin_manager, parent)
        - RadioBrowserPlugin(parent, plugin_manager=...)
        - RadioBrowserPlugin(plugin_manager=..., parent=...)
        """
        # Ekstraktuj parent iz args ili kwargs
        parent = None
        
        # Prvo proveri args
        for arg in args:
            if isinstance(arg, QWidget):
                parent = arg
                break
        
        # Onda proveri kwargs
        if parent is None and 'parent' in kwargs:
            parent = kwargs.get('parent')
        
        # Sada pozovi super konstruktor
        super().__init__(parent)
        
        # Ekstraktuj plugin_manager
        plugin_manager = None
        
        # Proveri args (sve što nije QWidget)
        for arg in args:
            if not isinstance(arg, QWidget):
                plugin_manager = arg
                break
        
        # Proveri kwargs
        if plugin_manager is None and 'plugin_manager' in kwargs:
            plugin_manager = kwargs.get('plugin_manager')
        
        self.plugin_manager = plugin_manager
        self.settings = QSettings("TrayWave", "RadioBrowserPlugin")
        self.current_stations = []
        self.fetcher_thread = None
        
        # Window setup - da ima title bar sa kontrolama
        self.setWindowTitle("📡 Radio Browser - AudioWave")
        self.setWindowIcon(QIcon("resources/icons/radio.png") if hasattr(self, 'windowIcon') else QIcon())
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(800, 500)
        
        # Debug info
        print(f"📡 [RadioBrowserPlugin] Initializing as QMainWindow...")
        print(f"   Parent: {parent}")
        print(f"   Plugin manager: {self.plugin_manager}")
        print(f"   args count: {len(args)}")
        print(f"   kwargs keys: {list(kwargs.keys())}")
        
        self.init_ui()
        self.load_settings()
        
        # Timer za cleanup pri zatvaranju
        self.closing = False
        
    def init_ui(self):
        """Inicijalizuje korisničko okruženje"""
        # Centralni widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Tab widget za različite sekcije
        tabs = QTabWidget()
        
        # Tab 1: Pretraga
        search_tab = self.create_search_tab()
        tabs.addTab(search_tab, "🔍 Pretraga")
        
        # Tab 2: Podešavanja
        settings_tab = self.create_settings_tab()
        tabs.addTab(settings_tab, "⚙️ Podešavanja")
        
        # Tab 3: Favoriti (za buduću implementaciju)
        favorites_tab = self.create_favorites_tab()
        tabs.addTab(favorites_tab, "⭐ Favoriti")
        
        layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Spremno za pretragu radio stanica")
        
    def create_search_tab(self) -> QWidget:
        """Kreira tab za pretragu stanica"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Brza pretraga po kategorijama
        quick_search_group = QGroupBox("Brza pretraga")
        quick_layout = QVBoxLayout()
        
        quick_buttons_layout = QHBoxLayout()
        
        categories = [
            ("🎸 Rock", "rock"),
            ("🎵 Pop", "pop"),
            ("🎹 Jazz", "jazz"),
            ("🎧 Electronic", "electronic"),
            ("🎤 Hip Hop", "hip hop"),
            ("🎼 Classical", "classical"),
            ("📻 News", "news"),
            ("🇷🇸 EX-YU", "RS")
        ]
        
        for label, tag in categories:
            btn = QPushButton(label)
            if tag == "RS":
                btn.clicked.connect(lambda _, t=tag: self.quick_search_country(t))
            else:
                btn.clicked.connect(lambda _, t=tag: self.quick_search_tag(t))
            quick_buttons_layout.addWidget(btn)
            
        quick_layout.addLayout(quick_buttons_layout)
        quick_search_group.setLayout(quick_layout)
        layout.addWidget(quick_search_group)
        
        # Napredna pretraga
        advanced_group = QGroupBox("Napredna pretraga")
        advanced_layout = QVBoxLayout()
        
        # Red 1: Naziv stanice
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Naziv:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Npr. BBC, Radio 1...")
        name_layout.addWidget(self.name_input)
        advanced_layout.addLayout(name_layout)
        
        # Red 2: Žanr i Država
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Žanr:"))
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("rock, jazz, pop...")
        filters_layout.addWidget(self.tag_input)
        
        filters_layout.addWidget(QLabel("Država:"))
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("RS, US, GB...")
        filters_layout.addWidget(self.country_input)
        
        advanced_layout.addLayout(filters_layout)
        
        # Red 3: Jezik i Codec
        tech_layout = QHBoxLayout()
        
        tech_layout.addWidget(QLabel("Jezik:"))
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("serbian, english...")
        tech_layout.addWidget(self.language_input)
        
        tech_layout.addWidget(QLabel("Codec:"))
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["Svi", "MP3", "AAC", "OGG", "FLAC"])
        tech_layout.addWidget(self.codec_combo)
        
        advanced_layout.addLayout(tech_layout)
        
        # Red 4: Bitrate i sortiranje
        options_layout = QHBoxLayout()
        
        options_layout.addWidget(QLabel("Min. Bitrate:"))
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(0, 320)
        self.bitrate_spin.setValue(0)
        self.bitrate_spin.setSuffix(" kbps")
        options_layout.addWidget(self.bitrate_spin)
        
        options_layout.addWidget(QLabel("Sortiranje:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Glasovi", "Bitrate", "Naziv"])
        options_layout.addWidget(self.sort_combo)
        
        options_layout.addWidget(QLabel("Limit:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(10, 500)
        self.limit_spin.setValue(100)
        options_layout.addWidget(self.limit_spin)
        
        advanced_layout.addLayout(options_layout)
        
        # Dugme za pretragu
        search_btn = QPushButton("🔍 Pretraži radio stanice")
        search_btn.clicked.connect(self.search_stations)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        advanced_layout.addWidget(search_btn)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Rezultati
        results_group = QGroupBox("Rezultati pretrage")
        results_layout = QVBoxLayout()
        
        # Tabela sa rezultatima
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Naziv", "Država", "Žanr", "Codec", "Bitrate", "Glasovi", "Akcije"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        results_layout.addWidget(self.results_table)
        
        # Status label
        self.status_label = QLabel("Ukucajte kriterijume pretrage i kliknite 'Pretraži'")
        results_layout.addWidget(self.status_label)
        
        # Dugmad za akcije
        actions_layout = QHBoxLayout()
        
        add_selected_btn = QPushButton("➕ Dodaj selektovane u playlist")
        add_selected_btn.clicked.connect(self.add_selected_to_playlist)
        add_selected_btn.setToolTip("Dodaje sve selektovane stanice u playlist")
        actions_layout.addWidget(add_selected_btn)
        
        add_all_btn = QPushButton("➕➕ Dodaj sve u playlist")
        add_all_btn.clicked.connect(self.add_all_to_playlist)
        add_all_btn.setToolTip("Dodaje sve pronađene stanice u playlist")
        actions_layout.addWidget(add_all_btn)
        
        clear_btn = QPushButton("❌ Očisti rezultate")
        clear_btn.clicked.connect(self.clear_results)
        clear_btn.setToolTip("Briše sve rezultate pretrage")
        actions_layout.addWidget(clear_btn)
        
        results_layout.addLayout(actions_layout)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        return widget
    
    def create_settings_tab(self) -> QWidget:
        """Kreira tab sa podešavanjima"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Blokirane zemlje
        blocked_group = QGroupBox("Blokirane zemlje")
        blocked_layout = QVBoxLayout()
        
        blocked_info = QLabel("Stanice iz ovih zemalja neće biti prikazane:")
        blocked_info.setWordWrap(True)
        blocked_layout.addWidget(blocked_info)
        
        self.blocked_input = QLineEdit()
        self.blocked_input.setPlaceholderText("Npr: RU, UA, BY (razdvojeno zarezom)")
        blocked_layout.addWidget(self.blocked_input)
        
        # Predefinisane opcije
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Brzi presets:"))
        
        preset_btn1 = QPushButton("Blokiraj RU/UA/BY")
        preset_btn1.clicked.connect(lambda: self.blocked_input.setText("RU, UA, BY"))
        preset_btn1.setToolTip("Blokiraj Rusiju, Ukrajinu i Belorusiju")
        presets_layout.addWidget(preset_btn1)
        
        preset_btn2 = QPushButton("Samo Balkan")
        preset_btn2.clicked.connect(lambda: self.blocked_input.setText(""))
        preset_btn2.setToolTip("Prikaži samo stanice sa Balkana")
        presets_layout.addWidget(preset_btn2)
        
        preset_btn3 = QPushButton("Očisti")
        preset_btn3.clicked.connect(lambda: self.blocked_input.setText(""))
        preset_btn3.setToolTip("Ukloni sve blokade")
        presets_layout.addWidget(preset_btn3)
        
        blocked_layout.addLayout(presets_layout)
        blocked_group.setLayout(blocked_layout)
        layout.addWidget(blocked_group)
        
        # Filteri kvaliteta
        quality_group = QGroupBox("Filteri kvaliteta")
        quality_layout = QVBoxLayout()
        
        self.hide_broken_check = QCheckBox("Sakrij nefunkcionalne stanice")
        self.hide_broken_check.setChecked(True)
        self.hide_broken_check.setToolTip("Sakrij stanice koje trenutno ne rade")
        quality_layout.addWidget(self.hide_broken_check)
        
        self.min_votes_layout = QHBoxLayout()
        self.min_votes_layout.addWidget(QLabel("Minimum glasova:"))
        self.min_votes_spin = QSpinBox()
        self.min_votes_spin.setRange(0, 10000)
        self.min_votes_spin.setValue(0)
        self.min_votes_spin.setToolTip("Prikaži samo stanice sa najmanje ovako glasova")
        self.min_votes_layout.addWidget(self.min_votes_spin)
        quality_layout.addLayout(self.min_votes_layout)
        
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        # Automatsko dodavanje
        auto_group = QGroupBox("Automatizacija")
        auto_layout = QVBoxLayout()
        
        self.auto_play_check = QCheckBox("Automatski pokreni prvu stanicu nakon pretrage")
        self.auto_play_check.setToolTip("Odmah pokreni prvu pronađenu stanicu")
        auto_layout.addWidget(self.auto_play_check)
        
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)
        
        # Sačuvaj podešavanja
        save_btn = QPushButton("💾 Sačuvaj podešavanja")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        return widget
    
    def create_favorites_tab(self) -> QWidget:
        """Kreira tab za favorite (placeholder)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Favoriti će biti implementirani u sledećoj verziji")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(label)
        
        info_label = QLabel(
            "Ovde ćete moći da sačuvate omiljene radio stanice\n"
            "za brzi pristup u budućnosti."
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
    
    def clear_results(self):
        """Očisti rezultate pretrage"""
        self.results_table.setRowCount(0)
        self.current_stations = []
        self.status_label.setText("Rezultati očišćeni")
        self.statusBar().showMessage("Rezultati očišćeni", 3000)
    
    def quick_search_tag(self, tag: str):
        """Brza pretraga po žanru"""
        self.tag_input.setText(tag)
        self.name_input.clear()
        self.country_input.clear()
        self.language_input.clear()
        self.search_stations()
    
    def quick_search_country(self, country_code: str):
        """Brza pretraga po državi"""
        self.country_input.setText(country_code)
        self.name_input.clear()
        self.tag_input.clear()
        self.language_input.clear()
        self.search_stations()
    
    def search_stations(self):
        """Pokreće pretragu stanica"""
        # Proveri da li već traži
        if self.fetcher_thread and self.fetcher_thread.isRunning():
            QMessageBox.information(self, "U toku", "Pretraga je već u toku, sačekajte...")
            return
        
        # Pripremi parametre
        params = {
            'endpoint': 'search',
            'limit': self.limit_spin.value(),
            'blocked_countries': self.get_blocked_countries()
        }
        
        # Dodaj filtere ako postoje
        if self.name_input.text().strip():
            params['name'] = self.name_input.text().strip()
        
        if self.tag_input.text().strip():
            params['tag'] = self.tag_input.text().strip()
        
        if self.country_input.text().strip():
            params['country'] = self.country_input.text().strip().upper()
        
        if self.language_input.text().strip():
            params['language'] = self.language_input.text().strip()
        
        codec = self.codec_combo.currentText()
        if codec != "Svi":
            params['codec'] = codec
        
        if self.bitrate_spin.value() > 0:
            params['bitrate_min'] = self.bitrate_spin.value()
        
        # Mapiranje sortiranja
        sort_map = {
            "Glasovi": "votes",
            "Bitrate": "bitrate",
            "Naziv": "name"
        }
        params['order'] = sort_map.get(self.sort_combo.currentText(), "votes")
        
        # Pokreni thread za preuzimanje
        self.fetcher_thread = RadioFetcherThread(params)
        self.fetcher_thread.finished.connect(self.on_stations_fetched)
        self.fetcher_thread.error.connect(self.on_fetch_error)
        self.fetcher_thread.progress.connect(self.on_progress)
        
        # Prikaži progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Preuzimanje stanica...")
        self.statusBar().showMessage("Pretraga radio stanica u toku...")
        
        # Očisti prethodne rezultate
        self.results_table.setRowCount(0)
        
        self.fetcher_thread.start()
    
    def on_progress(self, value: int):
        """Ažurira progress bar"""
        self.progress_bar.setValue(value)
    
    def on_stations_fetched(self, stations: List[Dict]):
        """Poziva se kada su stanice preuzete"""
        self.current_stations = stations
        self.progress_bar.setVisible(False)
        
        # Primeni filter za minimalne glasove
        min_votes = self.min_votes_spin.value()
        if min_votes > 0:
            stations = [s for s in stations if s.get('votes', 0) >= min_votes]
        
        # Popuni tabelu
        self.results_table.setRowCount(0)
        
        for station in stations:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            self.results_table.setItem(row, 0, QTableWidgetItem(station['name']))
            self.results_table.setItem(row, 1, QTableWidgetItem(f"{station['country']} ({station['countrycode']})"))
            self.results_table.setItem(row, 2, QTableWidgetItem(station['tags'][:50]))
            self.results_table.setItem(row, 3, QTableWidgetItem(station['codec'].upper()))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{station['bitrate']} kbps"))
            self.results_table.setItem(row, 5, QTableWidgetItem(str(station['votes'])))
            
            # Dugme za dodavanje
            add_btn = QPushButton("➕ Dodaj")
            add_btn.setToolTip("Dodaj ovu stanicu u playlist")
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 3px;
                    padding: 3px 8px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            add_btn.clicked.connect(lambda _, s=station: self.add_station_to_playlist(s))
            self.results_table.setCellWidget(row, 6, add_btn)
        
        self.status_label.setText(f"Pronađeno {len(stations)} radio stanica")
        self.statusBar().showMessage(f"Pronađeno {len(stations)} stanica", 5000)
        
        # Auto-play prva stanica ako je omogućeno
        if self.auto_play_check.isChecked() and stations:
            self.add_station_to_playlist(stations[0])
    
    def on_fetch_error(self, error_msg: str):
        """Poziva se u slučaju greške"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Greška: {error_msg}")
        self.statusBar().showMessage(f"Greška: {error_msg}", 5000)
        QMessageBox.warning(self, "Greška", error_msg)
    
    def add_station_to_playlist(self, station: Dict):
        """Dodaje stanicu u playlist"""
        name = station['name']
        url = station['url']
        
        # Emituj signal prema plugin manageru
        self.add_to_playlist.emit(name, url)
        
        self.status_label.setText(f"✅ Dodato: {name}")
        self.statusBar().showMessage(f"✅ Dodato: {name}", 3000)
    
    def add_selected_to_playlist(self):
        """Dodaje selektovane stanice u playlist"""
        selected_rows = set(item.row() for item in self.results_table.selectedItems())
        
        if not selected_rows:
            QMessageBox.information(self, "Info", "Nijedna stanica nije selektovana")
            return
        
        count = 0
        for row in selected_rows:
            if row < len(self.current_stations):
                self.add_station_to_playlist(self.current_stations[row])
                count += 1
        
        self.status_label.setText(f"✅ Dodato {count} stanica")
        self.statusBar().showMessage(f"✅ Dodato {count} stanica u playlist", 3000)
    
    def add_all_to_playlist(self):
        """Dodaje sve pronađene stanice u playlist"""
        if not self.current_stations:
            QMessageBox.information(self, "Info", "Nema stanica za dodavanje")
            return
        
        reply = QMessageBox.question(
            self,
            "Potvrda",
            f"Dodati {len(self.current_stations)} stanica u playlist?\n\n"
            "Napomena: Ovo može potrajati nekoliko sekundi.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for station in self.current_stations:
                self.add_station_to_playlist(station)
            
            self.status_label.setText(f"✅ Dodato {len(self.current_stations)} stanica")
            self.statusBar().showMessage(f"✅ Dodato {len(self.current_stations)} stanica u playlist", 5000)
    
    def show_context_menu(self, pos):
        """Prikazuje kontekstualni meni"""
        row = self.results_table.rowAt(pos.y())
        if row < 0 or row >= len(self.current_stations):
            return
        
        station = self.current_stations[row]
        
        menu = QMenu(self)
        
        add_action = QAction("➕ Dodaj u playlist", self)
        add_action.triggered.connect(lambda: self.add_station_to_playlist(station))
        menu.addAction(add_action)
        
        menu.addSeparator()
        
        play_action = QAction("▶️ Pokreni odmah", self)
        play_action.triggered.connect(lambda: self.play_station_now(station))
        menu.addAction(play_action)
        
        menu.addSeparator()
        
        info_action = QAction("ℹ️ Informacije", self)
        info_action.triggered.connect(lambda: self.show_station_info(station))
        menu.addAction(info_action)
        
        if station.get('homepage'):
            web_action = QAction("🌐 Otvori web stranicu", self)
            web_action.triggered.connect(lambda: self.open_homepage(station['homepage']))
            menu.addAction(web_action)
        
        menu.exec(self.results_table.mapToGlobal(pos))
    
    def play_station_now(self, station: Dict):
        """Pokreće stanicu odmah (bez dodavanja u playlist)"""
        # Ovo će biti implementirano kada bude engine podrška za stream-ove
        QMessageBox.information(
            self,
            "Uskoro",
            f"Direktno pokretanje radio stanica će biti omogućeno u narednoj verziji.\n\n"
            f"Za sada, stanica '{station['name']}' je dodata u playlist."
        )
        self.add_station_to_playlist(station)
    
    def show_station_info(self, station: Dict):
        """Prikazuje detaljne informacije o stanici"""
        favicon_html = ""
        if station.get('favicon'):
            favicon_html = f"<p><b>Logo:</b> <img src=\"{station['favicon']}\" height='64'></p>"
        
        info_text = f"""
<h3>{station['name']}</h3>
{favicon_html}
<p><b>Država:</b> {station['country']} ({station['countrycode']})</p>
<p><b>Jezik:</b> {station['language']}</p>
<p><b>Žanrovi:</b> {station['tags']}</p>
<p><b>Codec:</b> {station['codec'].upper()}</p>
<p><b>Bitrate:</b> {station['bitrate']} kbps</p>
<p><b>Glasovi:</b> {station['votes']}</p>
<p><b>URL:</b> <a href="{station['url']}">{station['url']}</a></p>
"""
        
        if station.get('homepage'):
            info_text += f"<p><b>Web stranica:</b> <a href=\"{station['homepage']}\">{station['homepage']}</a></p>"
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Informacije: {station['name']}")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(info_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def open_homepage(self, url: str):
        """Otvara homepage stanice u browseru"""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))
    
    def get_blocked_countries(self) -> List[str]:
        """Vraća listu blokiranih zemalja"""
        text = self.blocked_input.text().strip()
        if not text:
            return []
        
        return [c.strip().upper() for c in text.split(',') if c.strip()]
    
    def save_settings(self):
        """Čuva podešavanja"""
        self.settings.setValue("blocked_countries", self.blocked_input.text())
        self.settings.setValue("hide_broken", self.hide_broken_check.isChecked())
        self.settings.setValue("min_votes", self.min_votes_spin.value())
        self.settings.setValue("auto_play", self.auto_play_check.isChecked())
        
        QMessageBox.information(self, "Uspešno", "Podešavanja su sačuvana")
        self.statusBar().showMessage("Podešavanja sačuvana", 3000)
    
    def load_settings(self):
        """Učitava sačuvana podešavanja"""
        blocked = self.settings.value("blocked_countries", "")
        self.blocked_input.setText(blocked)
        
        hide_broken = self.settings.value("hide_broken", True, type=bool)
        self.hide_broken_check.setChecked(hide_broken)
        
        min_votes = self.settings.value("min_votes", 0, type=int)
        self.min_votes_spin.setValue(min_votes)
        
        auto_play = self.settings.value("auto_play", False, type=bool)
        self.auto_play_check.setChecked(auto_play)
    
    def closeEvent(self, event: QCloseEvent):
        """Handle close event - čisti threadove"""
        self.closing = True
        
        # Zaustavi thread ako je aktivan
        if self.fetcher_thread and self.fetcher_thread.isRunning():
            self.fetcher_thread.quit()
            self.fetcher_thread.wait(1000)  # Čekaj 1 sekundu
        
        # Prihvati close event
        event.accept()
        print("📡 [RadioBrowserPlugin] Window closed")


# Plugin metadata
PLUGIN_INFO = {
    "name": "Radio Browser",
    "version": "1.0.0",
    "description": "Pretraga i reprodukcija živih radio stanica sa radio-browser.info",
    "author": "TrayWave Team",
    "widget_class": RadioBrowserPlugin
}


def create_plugin(*args, **kwargs):
    """Factory funkcija za kreiranje plugin instance"""
    return RadioBrowserPlugin(*args, **kwargs)