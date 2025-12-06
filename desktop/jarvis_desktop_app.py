#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Native Desktop Application
Vollständige Feature-Parity mit Web-UI
"""

import sys
import threading
import time
import json
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLineEdit, QPushButton, QLabel, QSplitter, QTabWidget,
        QProgressBar, QStatusBar, QGroupBox, QGridLayout, QScrollArea,
        QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QSpinBox,
        QComboBox, QTextBrowser, QFrame, QPushButton as QBtn
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QSize
    from PyQt6.QtGui import QFont, QPalette, QColor, QTextCursor, QIcon, QPixmap, QPainter, QLinearGradient
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("⚠️ PyQt6 nicht installiert!")
    print("Installiere mit: pip install PyQt6")


class JarvisDesktopApp(QMainWindow):
    """Native Desktop-GUI für J.A.R.V.I.S. - Full Feature Parity mit Web-UI"""
    
    # Signal für Thread-Safe GUI Updates
    gui_update_signal = pyqtSignal(object)
    
    def __init__(self, jarvis_instance=None, app=None):
        super().__init__()
        self.jarvis = jarvis_instance
        self.app = app
        self.is_running = True
        self.selected_model = None  # Für LLM Model Selector
        
        # Signal verbinden
        self.gui_update_signal.connect(self._execute_gui_callback)
        
        self._init_ui()
        self._apply_jarvis_theme()
        self._start_background_updates()
        
        # Initial data load
        self._initial_data_load()

    def _init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("🤖 J.A.R.V.I.S. Desktop Control Center")
        self.setGeometry(50, 50, 1600, 1000)

        # Hauptcontainer
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HEADER ===
        header = self._create_header()
        main_layout.addWidget(header)

        # === TABS ===
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        main_layout.addWidget(self.tabs)

        # Tab-Seiten erstellen
        self.tabs.addTab(self._create_chat_tab(), "💬 Chat")
        self.tabs.addTab(self._create_assistant_tab(), "🧑‍💻 Assistenz")
        self.tabs.addTab(self._create_system_tab(), "⚙️ System")
        self.tabs.addTab(self._create_models_tab(), "🧠 Modelle")
        self.tabs.addTab(self._create_plugins_tab(), "🧩 Plugins")
        self.tabs.addTab(self._create_crawler_tab(), "🕸️ Crawler")
        self.tabs.addTab(self._create_memory_tab(), "🧠 Gedächtnis")
        self.tabs.addTab(self._create_training_tab(), "🎯 Training")
        self.tabs.addTab(self._create_logs_tab(), "📋 Logs")
        self.tabs.addTab(self._create_settings_tab(), "🔧 Einstellungen")

        # Statusleiste
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("✅ Bereit")
        self.ws_indicator = QLabel("🟢 Online")
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.ws_indicator)

    def _create_header(self) -> QWidget:
        """Erstellt den Header mit Titel und Controls"""
        header = QWidget()
        header.setObjectName("appHeader")
        header.setFixedHeight(80)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)

        # Titel
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        title = QLabel("🤖 J.A.R.V.I.S.")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        subtitle = QLabel("Desktop Control Center")
        subtitle.setStyleSheet("color: #64b5f6; font-size: 12px;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addWidget(title_container)

        layout.addStretch()

        # Rechte Controls
        self.listening_indicator = QLabel("🎵 Idle")
        self.listening_indicator.setStyleSheet("""
            background: #1e3a5f;
            padding: 8px 16px;
            border-radius: 16px;
            font-weight: bold;
            color: white;
        """)
        layout.addWidget(self.listening_indicator)

        return header

    # ===================================================================
    # TAB 1: CHAT
    # ===================================================================
    def _create_chat_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Chat-Verlauf
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.chat_display, stretch=1)

        # Eingabe
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("✏️ Schreibe einen Befehl oder eine Frage...")
        self.input_field.setFont(QFont("Arial", 11))
        self.input_field.returnPressed.connect(self._send_command)
        input_layout.addWidget(self.input_field)

        send_btn = QPushButton("🚀 Senden")
        send_btn.setFixedWidth(120)
        send_btn.clicked.connect(self._send_command)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        # Controls
        controls = QHBoxLayout()
        self.listen_button = QPushButton("🎵 Spracherkennung")
        self.listen_button.setCheckable(True)
        self.listen_button.clicked.connect(self._toggle_listening)
        controls.addWidget(self.listen_button)

        clear_btn = QPushButton("🗑️ Chat löschen")
        clear_btn.clicked.connect(lambda: self.chat_display.clear())
        controls.addWidget(clear_btn)
        controls.addStretch()

        layout.addLayout(controls)
        return widget

    # ===================================================================
    # TAB 2: ASSISTENZ
    # ===================================================================
    def _create_assistant_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        # Kontext
        ctx_group = QGroupBox("🧠 Kontext")
        ctx_layout = QVBoxLayout()
        self.context_display = QTextEdit()
        self.context_display.setReadOnly(True)
        self.context_display.setMaximumHeight(200)
        ctx_layout.addWidget(self.context_display)
        ctx_group.setLayout(ctx_layout)
        content_layout.addWidget(ctx_group)

        # Sprachsteuerung
        speech_group = QGroupBox("🎤 Sprachsteuerung")
        speech_layout = QVBoxLayout()
        
        self.wake_word_checkbox = QCheckBox("Wake Word aktiv")
        self.tts_stream_checkbox = QCheckBox("TTS Ausgabe aktiv")
        speech_layout.addWidget(self.wake_word_checkbox)
        speech_layout.addWidget(self.tts_stream_checkbox)
        
        speech_group.setLayout(speech_layout)
        content_layout.addWidget(speech_group)

        # Wissensfortschritt
        knowledge_group = QGroupBox("📚 Wissensfortschritt")
        knowledge_layout = QVBoxLayout()
        self.knowledge_feed = QTextEdit()
        self.knowledge_feed.setReadOnly(True)
        self.knowledge_feed.setMaximumHeight(200)
        knowledge_layout.addWidget(self.knowledge_feed)
        knowledge_group.setLayout(knowledge_layout)
        content_layout.addWidget(knowledge_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    # ===================================================================
    # TAB 3: SYSTEM
    # ===================================================================
    def _create_system_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Metriken-Grid
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(15)

        # CPU Card
        cpu_card = self._create_metric_card("💻 CPU", "---%")
        self.cpu_value_label = cpu_card["value"]
        self.cpu_detail_label = cpu_card["detail"]
        metrics_grid.addWidget(cpu_card["widget"], 0, 0)

        # RAM Card
        ram_card = self._create_metric_card("💾 RAM", "---%")
        self.ram_value_label = ram_card["value"]
        self.ram_detail_label = ram_card["detail"]
        metrics_grid.addWidget(ram_card["widget"], 0, 1)

        # GPU Card
        gpu_card = self._create_metric_card("🎮 GPU", "---%")
        self.gpu_value_label = gpu_card["value"]
        self.gpu_detail_label = gpu_card["detail"]
        metrics_grid.addWidget(gpu_card["widget"], 0, 2)

        # Disk Card
        disk_card = self._create_metric_card("💾 Disk", "---%")
        self.disk_value_label = disk_card["value"]
        self.disk_detail_label = disk_card["detail"]
        metrics_grid.addWidget(disk_card["widget"], 1, 0)

        # Uptime Card
        uptime_card = self._create_metric_card("⏱️ Uptime", "---")
        self.uptime_value_label = uptime_card["value"]
        self.uptime_detail_label = uptime_card["detail"]
        metrics_grid.addWidget(uptime_card["widget"], 1, 1)

        layout.addLayout(metrics_grid)

        # Details
        details_group = QGroupBox("📊 Details")
        details_layout = QVBoxLayout()
        self.system_details = QTextEdit()
        self.system_details.setReadOnly(True)
        details_layout.addWidget(self.system_details)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group, stretch=1)

        return widget

    def _create_metric_card(self, label: str, value: str) -> Dict:
        """Erstellt eine Metrik-Karte"""
        card = QFrame()
        card.setObjectName("metricCard")
        card.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("color: #64b5f6; font-size: 12px; font-weight: bold;")
        layout.addWidget(label_widget)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        layout.addWidget(value_label)
        
        detail_label = QLabel("...")
        detail_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(detail_label)
        
        return {
            "widget": card,
            "value": value_label,
            "detail": detail_label
        }

    # ===================================================================
    # TAB 4-10: MODELS, PLUGINS, CRAWLER, MEMORY, TRAINING, LOGS, SETTINGS
    # ===================================================================
    
    def _create_models_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("🧠 LLM Modelle"))
        self.current_model_label = QLabel("❌ Kein Modell")
        self.current_model_label.setStyleSheet("background: #c62828; padding: 4px 12px; border-radius: 12px; color: white; font-weight: bold;")
        header_layout.addWidget(self.current_model_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Modell auswählen:"))
        self.model_selector = QComboBox()
        self.model_selector.addItem("-- Wähle ein Modell --")
        self.model_selector.currentTextChanged.connect(self._on_model_selected)
        selector_layout.addWidget(self.model_selector, stretch=1)
        layout.addLayout(selector_layout)
        actions = QHBoxLayout()
        load_btn = QPushButton("⬇️ Laden")
        load_btn.clicked.connect(lambda: self._model_action("load"))
        actions.addWidget(load_btn)
        unload_btn = QPushButton("⬆️ Entladen")
        unload_btn.clicked.connect(lambda: self._model_action("unload"))
        actions.addWidget(unload_btn)
        download_btn = QPushButton("📥 Download")
        download_btn.clicked.connect(lambda: self._model_action("download"))
        actions.addWidget(download_btn)
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self._refresh_models)
        actions.addWidget(refresh_btn)
        actions.addStretch()
        layout.addLayout(actions)
        self.model_progress = QProgressBar()
        self.model_progress.setVisible(False)
        self.model_progress_label = QLabel("")
        self.model_progress_label.setVisible(False)
        layout.addWidget(self.model_progress)
        layout.addWidget(self.model_progress_label)
        list_group = QGroupBox("Verfügbare Modelle")
        list_layout = QVBoxLayout()
        self.model_list = QTextEdit()
        self.model_list.setReadOnly(True)
        self.model_list.setMaximumHeight(200)
        list_layout.addWidget(self.model_list)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        meta_group = QGroupBox("Metadata")
        meta_layout = QVBoxLayout()
        self.model_metadata = QTextEdit()
        self.model_metadata.setReadOnly(True)
        meta_layout.addWidget(self.model_metadata)
        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group, stretch=1)
        return widget

    def _create_plugins_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        header = QHBoxLayout()
        header.addWidget(QLabel("🧩 Plugin-Übersicht"))
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self._refresh_plugins)
        header.addWidget(refresh_btn)
        header.addStretch()
        layout.addLayout(header)
        self.plugin_table = QTableWidget()
        self.plugin_table.setColumnCount(5)
        self.plugin_table.setHorizontalHeaderLabels(["Name", "Modul", "Status", "Sandbox", "Aktionen"])
        self.plugin_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.plugin_table)
        return widget

    def _create_crawler_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        status_group = QGroupBox("🕸️ Crawler Status")
        status_layout = QGridLayout()
        status_layout.addWidget(QLabel("Verbindung:"), 0, 0)
        self.crawler_status_label = QLabel("--")
        status_layout.addWidget(self.crawler_status_label, 0, 1)
        status_layout.addWidget(QLabel("Dokumente:"), 1, 0)
        self.crawler_docs_label = QLabel("--")
        status_layout.addWidget(self.crawler_docs_label, 1, 1)
        status_layout.addWidget(QLabel("Jobs:"), 2, 0)
        self.crawler_jobs_label = QLabel("--")
        status_layout.addWidget(self.crawler_jobs_label, 2, 1)
        status_group.setLayout(status_layout)
        content_layout.addWidget(status_group)
        actions_group = QGroupBox("Aktionen")
        actions_layout = QHBoxLayout()
        sync_btn = QPushButton("🔄 Sync starten")
        sync_btn.clicked.connect(self._crawler_sync)
        actions_layout.addWidget(sync_btn)
        pause_btn = QPushButton("⏸️ Pause")
        actions_layout.addWidget(pause_btn)
        resume_btn = QPushButton("▶️ Resume")
        actions_layout.addWidget(resume_btn)
        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        content_layout.addWidget(actions_group)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    def _create_memory_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        summary_group = QGroupBox("🧠 Kontext-Zusammenfassung")
        summary_layout = QVBoxLayout()
        self.memory_summary = QTextEdit()
        self.memory_summary.setReadOnly(True)
        self.memory_summary.setMaximumHeight(150)
        summary_layout.addWidget(self.memory_summary)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        history_group = QGroupBox("📜 Konversationsverlauf")
        history_layout = QVBoxLayout()
        self.memory_messages = QTextEdit()
        self.memory_messages.setReadOnly(True)
        history_layout.addWidget(self.memory_messages)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group, stretch=1)
        return widget

    def _create_training_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form_group = QGroupBox("➕ Benutzerdefinierte Befehle")
        form_layout = QVBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Muster (z.B. 'wie spät ist es')")
        form_layout.addWidget(QLabel("Muster:"))
        form_layout.addWidget(self.pattern_input)
        self.response_input = QTextEdit()
        self.response_input.setPlaceholderText("Antwort...")
        self.response_input.setMaximumHeight(80)
        form_layout.addWidget(QLabel("Antwort:"))
        form_layout.addWidget(self.response_input)
        add_btn = QPushButton("➕ Befehl hinzufügen")
        add_btn.clicked.connect(self._add_custom_command)
        form_layout.addWidget(add_btn)
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        training_group = QGroupBox("🎯 Training")
        training_layout = QVBoxLayout()
        train_btn = QPushButton("🚀 Training starten")
        train_btn.clicked.connect(self._run_training)
        training_layout.addWidget(train_btn)
        self.training_log = QTextEdit()
        self.training_log.setReadOnly(True)
        self.training_log.setMaximumHeight(200)
        training_layout.addWidget(self.training_log)
        training_group.setLayout(training_layout)
        layout.addWidget(training_group)
        layout.addStretch()
        return widget

    def _create_logs_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        controls = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.clicked.connect(self._refresh_logs)
        controls.addWidget(refresh_btn)
        clear_btn = QPushButton("🗑️ Logs löschen")
        clear_btn.clicked.connect(self._clear_logs)
        controls.addWidget(clear_btn)
        controls.addStretch()
        self.log_filter = QLineEdit()
        self.log_filter.setPlaceholderText("🔍 Filter...")
        self.log_filter.setMaximumWidth(200)
        self.log_filter.textChanged.connect(self._filter_logs)
        controls.addWidget(self.log_filter)
        layout.addLayout(controls)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_output)
        self.log_output_full = ""
        return widget

    def _create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        speech_group = QGroupBox("🎤 Sprach-Einstellungen")
        speech_layout = QGridLayout()
        speech_layout.addWidget(QLabel("Wake Word:"), 0, 0)
        self.settings_wake_word_check = QCheckBox("Aktiviert")
        speech_layout.addWidget(self.settings_wake_word_check, 0, 1)
        speech_layout.addWidget(QLabel("Min. Wörter:"), 1, 0)
        self.settings_min_words_spin = QSpinBox()
        self.settings_min_words_spin.setRange(1, 10)
        speech_layout.addWidget(self.settings_min_words_spin, 1, 1)
        speech_layout.addWidget(QLabel("TTS-Rate:"), 2, 0)
        self.settings_tts_rate_spin = QSpinBox()
        self.settings_tts_rate_spin.setRange(120, 260)
        speech_layout.addWidget(self.settings_tts_rate_spin, 2, 1)
        save_speech_btn = QPushButton("💾 Speichern")
        speech_layout.addWidget(save_speech_btn, 3, 0, 1, 2)
        speech_group.setLayout(speech_layout)
        content_layout.addWidget(speech_group)
        audio_group = QGroupBox("🔊 Audio")
        audio_layout = QVBoxLayout()
        self.settings_device_combo = QComboBox()
        audio_layout.addWidget(QLabel("Eingabegerät:"))
        audio_layout.addWidget(self.settings_device_combo)
        measure_btn = QPushButton("📊 Pegel messen")
        measure_btn.clicked.connect(self._measure_audio_level)
        audio_layout.addWidget(measure_btn)
        self.audio_level_label = QLabel("Pegel: --")
        audio_layout.addWidget(self.audio_level_label)
        audio_group.setLayout(audio_layout)
        content_layout.addWidget(audio_group)
        system_group = QGroupBox("⚙️ System")
        system_layout = QVBoxLayout()
        self.settings_debug_check = QCheckBox("Debug-Modus")
        system_layout.addWidget(self.settings_debug_check)
        self.settings_autostart_check = QCheckBox("Autostart")
        system_layout.addWidget(self.settings_autostart_check)
        save_system_btn = QPushButton("💾 Speichern")
        system_layout.addWidget(save_system_btn)
        system_group.setLayout(system_layout)
        content_layout.addWidget(system_group)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return widget

    # ===================================================================
    # THEME
    # ===================================================================
    def _apply_jarvis_theme(self):
        """Wendet das EINHEITLICHE dunkle JARVIS Theme an"""
        dark_palette = QPalette()
        bg_dark = QColor(11, 18, 32)
        bg_darker = QColor(15, 22, 33)
        dark_palette.setColor(QPalette.ColorRole.Window, bg_dark)
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, bg_darker)
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 28, 45))
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(30, 40, 60))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(136, 136, 136))
        self.setPalette(dark_palette)
        self.app.setPalette(dark_palette)
        self.setStyleSheet("""
            * { background: #0b1220; color: white; }
            QMainWindow { background: #0b1220; }
            QWidget { background: #0b1220; color: white; }
            #appHeader { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a2332, stop:1 #243447); border-bottom: 2px solid #2a5885; }
            QTabWidget::pane { border: 1px solid #2a5885; background: #0f1621; border-radius: 4px; }
            QTabBar::tab { background: #1e3a5f; color: white; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #2a5885; font-weight: bold; }
            QTabBar::tab:hover { background: #254a70; }
            QPushButton { background: #1e3a5f; border: 1px solid #2a5885; border-radius: 6px; padding: 10px 20px; color: white; font-weight: bold; min-height: 20px; }
            QPushButton:hover { background: #2a5885; border-color: #3d7ab8; }
            QPushButton:pressed { background: #15293f; }
            QPushButton:checked { background: #2ecc71; border-color: #27ae60; }
            QLineEdit, QSpinBox, QComboBox { background: #1c2838; border: 1px solid #2a5885; border-radius: 4px; padding: 8px; color: white; }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #42a5f6; }
            QComboBox::drop-down { border: none; background: #2a5885; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 6px solid white; width: 0; height: 0; }
            QComboBox QAbstractItemView { background: #1c2838; color: white; selection-background-color: #2a5885; border: 1px solid #2a5885; }
            QTextEdit, QTextBrowser { background: #0f1621; border: 1px solid #2a5885; border-radius: 4px; padding: 8px; color: white; }
            QGroupBox { background: #0f1621; border: 2px solid #2a5885; border-radius: 6px; margin-top: 12px; padding-top: 12px; font-weight: bold; color: #64b5f6; }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; background: #0f1621; }
            #metricCard { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e3a5f, stop:1 #15293f); border: 1px solid #2a5885; border-radius: 8px; min-height: 120px; }
            QTableWidget { background: #0f1621; gridline-color: #2a5885; border: 1px solid #2a5885; color: white; }
            QTableWidget::item { padding: 8px; color: white; background: #0f1621; }
            QTableWidget::item:selected { background: #2a5885; color: white; }
            QHeaderView::section { background: #1e3a5f; color: white; padding: 8px; border: none; font-weight: bold; }
            QScrollBar:vertical { background: #0f1621; width: 14px; border-radius: 7px; margin: 0; }
            QScrollBar::handle:vertical { background: #2a5885; border-radius: 7px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #3d7ab8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; background: none; }
            QScrollBar:horizontal { background: #0f1621; height: 14px; border-radius: 7px; }
            QScrollBar::handle:horizontal { background: #2a5885; border-radius: 7px; min-width: 30px; }
            QScrollArea { background: #0b1220; border: none; }
            QScrollArea > QWidget > QWidget { background: #0b1220; }
            QProgressBar { border: 1px solid #2a5885; border-radius: 4px; background: #0f1621; text-align: center; color: white; height: 25px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60); border-radius: 3px; }
            QCheckBox { color: white; spacing: 8px; background: transparent; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #2a5885; border-radius: 3px; background: #0f1621; }
            QCheckBox::indicator:checked { background: #2ecc71; border-color: #27ae60; }
            QLabel { color: white; background: transparent; }
            QStatusBar { background: #1a2332; color: white; border-top: 1px solid #2a5885; }
            QStatusBar QLabel { background: transparent; }
        """)

    # ===================================================================
    # THREAD-SAFE GUI UPDATES mit SIGNAL!
    # ===================================================================
    def _safe_update_gui(self, callback):
        """Führt GUI-Update THREAD-SAFE aus via Signal"""
        if self.is_running:
            self.gui_update_signal.emit(callback)

    def _execute_gui_callback(self, callback):
        """Wird im Main-Thread ausgeführt (via Signal)"""
        try:
            if callable(callback):
                callback()
        except Exception as e:
            print(f"GUI callback error: {e}")
            traceback.print_exc()

    # ===================================================================
    # BACKGROUND UPDATES
    # ===================================================================
    def _initial_data_load(self):
        threading.Thread(target=self._load_initial_data_async, daemon=True).start()
    
    def _load_initial_data_async(self):
        """KRITISCH: Alle Refreshes müssen thread-safe sein!"""
        time.sleep(0.5)
        try:
            # ALLE diese Aufrufe müssen intern _safe_update_gui verwenden!
            self._refresh_models_async()
            self._refresh_plugins_async()
            self._refresh_logs()
            self._refresh_memory_async()
            self._refresh_crawler_status_async()
        except Exception as e:
            print(f"Initial data load error: {e}")
            traceback.print_exc()

    def _start_background_updates(self):
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._fetch_all_stats)
        self.stats_timer.start(2000)

    def _fetch_all_stats(self):
        if not self.jarvis or not self.is_running:
            return
        threading.Thread(target=self._update_stats_async, daemon=True).start()

    def _update_stats_async(self):
        if not self.is_running or not self.jarvis or not hasattr(self.jarvis, 'get_system_metrics'):
            return
        try:
            metrics = self.jarvis.get_system_metrics(include_details=False)
            summary = metrics.get("summary", {})
            cpu = summary.get("cpu_percent", 0)
            ram = summary.get("memory_percent", 0)
            gpu = summary.get("gpu_utilization", 0)
            disk = summary.get("disk_percent", 0)
            uptime = summary.get("uptime_hours", 0)
            self._safe_update_gui(lambda: self._update_system_metrics_ui(cpu, ram, gpu, disk, uptime, summary))
            if hasattr(self.jarvis, 'get_llm_status'):
                llm_status = self.jarvis.get_llm_status()
                current_model = llm_status.get("current")
                self._safe_update_gui(lambda: self._update_llm_status_ui(current_model))
            if self.tabs.currentIndex() == 5:
                self._refresh_crawler_status_async()
            if self.tabs.currentIndex() == 6:
                self._refresh_memory_async()
        except Exception as e:
            print(f"Stats-Update Fehler: {e}")
            traceback.print_exc()

    def _update_system_metrics_ui(self, cpu, ram, gpu, disk, uptime, summary):
        """Wird im Main-Thread ausgeführt - SAFE!"""
        try:
            self.cpu_value_label.setText(f"{cpu:.1f}%")
            self.cpu_detail_label.setText(f"{summary.get('cpu_freq', 0):.0f} MHz")
            self.ram_value_label.setText(f"{ram:.1f}%")
            self.ram_detail_label.setText(f"Frei: {summary.get('memory_free', 0):.1f} GB")
            self.gpu_value_label.setText(f"{gpu:.1f}%" if gpu else "N/A")
            self.gpu_detail_label.setText(f"VRAM: {summary.get('gpu_memory', 0):.0f} MB")
            self.disk_value_label.setText(f"{disk:.1f}%")
            self.disk_detail_label.setText(f"Frei: {summary.get('disk_free', 0):.1f} GB")
            self.uptime_value_label.setText(f"{uptime:.1f}h")
            details = json.dumps(summary, indent=2, ensure_ascii=False)
            self.system_details.setPlainText(details)
        except Exception as e:
            print(f"Update system metrics UI error: {e}")

    def _update_llm_status_ui(self, current_model):
        """Wird im Main-Thread ausgeführt - SAFE!"""
        try:
            if current_model:
                self.current_model_label.setText(f"✅ {current_model}")
                self.current_model_label.setStyleSheet("background: #2ecc71; padding: 4px 12px; border-radius: 12px; color: white; font-weight: bold;")
            else:
                self.current_model_label.setText("❌ Kein Modell")
                self.current_model_label.setStyleSheet("background: #c62828; padding: 4px 12px; border-radius: 12px; color: white; font-weight: bold;")
        except Exception as e:
            print(f"Update LLM status UI error: {e}")

    # ===================================================================
    # HANDLER - ALLE JETZT THREAD-SAFE!
    # ===================================================================
    def _refresh_models(self):
        """Public Methode - ruft async Version auf"""
        threading.Thread(target=self._refresh_models_async, daemon=True).start()
    
    def _refresh_models_async(self):
        """KRITISCH: Alle GUI-Updates via _safe_update_gui!"""
        if not self.jarvis or not hasattr(self.jarvis, 'get_llm_status'):
            return
        try:
            llm_status = self.jarvis.get_llm_status()
            available = llm_status.get("available", {})
            
            # GUI-Update 1: ComboBox leeren und füllen
            def update_combo():
                self.model_selector.clear()
                self.model_selector.addItem("-- Wähle ein Modell --")
                for model_key in available.keys():
                    self.model_selector.addItem(model_key)
            self._safe_update_gui(update_combo)
            
            # GUI-Update 2: Model List
            model_text = "Verfügbare Modelle:\n\n"
            for key, info in available.items():
                status = "✅ Installiert" if info.get("available") else "📥 Download verfügbar"
                size = info.get("size_mb", "?")
                model_text += f"• {key}: {status} ({size} MB)\n"
            self._safe_update_gui(lambda: self.model_list.setPlainText(model_text))
            
            # GUI-Update 3: Metadata
            metadata = llm_status.get("metadata", {})
            meta_text = json.dumps(metadata, indent=2, ensure_ascii=False)
            self._safe_update_gui(lambda: self.model_metadata.setPlainText(meta_text))
            
        except Exception as e:
            print(f"Model-Refresh Fehler: {e}")
            traceback.print_exc()
    
    def _on_model_selected(self, model_name: str):
        if model_name and model_name != "-- Wähle ein Modell --":
            self.selected_model = model_name
            self._log(f"Modell ausgewählt: {model_name}")

    def _model_action(self, action: str):
        if not self.jarvis or not self.selected_model:
            self._log("❌ Kein Modell ausgewählt!")
            return
        self._log(f"🚀 Modell-Aktion: {action} - {self.selected_model}")
        try:
            if action == "download":
                self._safe_update_gui(lambda: (self.model_progress.setVisible(True), self.model_progress_label.setVisible(True), self.model_progress.setValue(0), self.model_progress_label.setText("Download startet...")))
                threading.Thread(target=lambda: self.jarvis.control_llm_model("download", self.selected_model), daemon=True).start()
            elif action == "load":
                result = self.jarvis.control_llm_model("load", self.selected_model)
                if result.get("success"):
                    self._log(f"✅ Modell geladen: {self.selected_model}")
                else:
                    self._log(f"❌ Modell-Laden fehlgeschlagen")
            elif action == "unload":
                result = self.jarvis.control_llm_model("unload", self.selected_model)
                if result.get("success"):
                    self._log(f"✅ Modell entladen")
                else:
                    self._log(f"❌ Modell-Entladen fehlgeschlagen")
            time.sleep(0.5)
            self._refresh_models()
        except Exception as e:
            self._log(f"❌ Model-Action Fehler: {e}")
            traceback.print_exc()
            self._safe_update_gui(lambda: (self.model_progress.setVisible(False), self.model_progress_label.setVisible(False)))

    def _refresh_plugins(self):
        """Public Methode - ruft async Version auf"""
        threading.Thread(target=self._refresh_plugins_async, daemon=True).start()
    
    def _refresh_plugins_async(self):
        """KRITISCH: Alle GUI-Updates via _safe_update_gui!"""
        if not self.jarvis or not hasattr(self.jarvis, 'get_plugin_overview'):
            return
        try:
            plugins = self.jarvis.get_plugin_overview()
            
            def update_table():
                self.plugin_table.setRowCount(len(plugins))
                for i, plugin in enumerate(plugins):
                    self.plugin_table.setItem(i, 0, QTableWidgetItem(plugin.get("name", "")))
                    self.plugin_table.setItem(i, 1, QTableWidgetItem(plugin.get("module", "")))
                    status = "✅" if plugin.get("enabled") else "❌"
                    self.plugin_table.setItem(i, 2, QTableWidgetItem(status))
                    sandbox = "🔒" if plugin.get("sandbox") else "🔓"
                    self.plugin_table.setItem(i, 3, QTableWidgetItem(sandbox))
                    self.plugin_table.setItem(i, 4, QTableWidgetItem("---"))
            
            self._safe_update_gui(update_table)
        except Exception as e:
            print(f"Plugin-Refresh Fehler: {e}")
            traceback.print_exc()

    def _refresh_crawler_status_async(self):
        """KRITISCH: Alle GUI-Updates via _safe_update_gui!"""
        if not self.jarvis or not hasattr(self.jarvis, 'get_crawler_status'):
            return
        try:
            status = self.jarvis.get_crawler_status()
            connected = "✅ Verbunden" if status.get("connected") else "❌ Offline"
            self._safe_update_gui(lambda: self.crawler_status_label.setText(connected))
            docs = status.get("documents_total", 0)
            self._safe_update_gui(lambda: self.crawler_docs_label.setText(f"{docs} Dokumente"))
            jobs = len(status.get("running_jobs", []))
            self._safe_update_gui(lambda: self.crawler_jobs_label.setText(f"{jobs} aktive Jobs"))
        except Exception as e:
            print(f"Crawler-Status Fehler: {e}")
            traceback.print_exc()
    
    def _crawler_sync(self):
        if not self.jarvis or not hasattr(self.jarvis, 'run_crawler_sync_now'):
            return
        self._log("🔄 Crawler-Sync gestartet...")
        threading.Thread(target=lambda: self.jarvis.run_crawler_sync_now(), daemon=True).start()

    def _refresh_memory_async(self):
        """KRITISCH: Alle GUI-Updates via _safe_update_gui!"""
        if not self.jarvis or not hasattr(self.jarvis, 'get_memory_snapshot'):
            return
        try:
            snapshot = self.jarvis.get_memory_snapshot(limit=20)
            summary = snapshot.get("short_term_summary", "Keine Daten")
            self._safe_update_gui(lambda: self.memory_summary.setPlainText(summary))
            messages = snapshot.get("recent_messages", [])
            msg_text = ""
            for msg in messages:
                role = msg.get("role", "")
                text = msg.get("message", msg.get("text", ""))
                timestamp = msg.get("timestamp", "")
                msg_text += f"[{role}] {text}\n{timestamp}\n\n"
            self._safe_update_gui(lambda: self.memory_messages.setPlainText(msg_text))
        except Exception as e:
            print(f"Memory-Refresh Fehler: {e}")
            traceback.print_exc()

    def _add_custom_command(self):
        pattern = self.pattern_input.text().strip()
        response = self.response_input.toPlainText().strip()
        if not pattern or not response:
            self._log("❌ Muster und Antwort müssen ausgefüllt sein!")
            return
        if self.jarvis and hasattr(self.jarvis, 'add_custom_command_entry'):
            try:
                success = self.jarvis.add_custom_command_entry(pattern, response)
                if success:
                    self._log(f"✅ Befehl hinzugefügt: {pattern}")
                    self._safe_update_gui(lambda: (self.pattern_input.clear(), self.response_input.clear()))
                else:
                    self._log("❌ Befehl konnte nicht hinzugefügt werden")
            except Exception as e:
                self._log(f"❌ Fehler: {e}")
                traceback.print_exc()
    
    def _run_training(self):
        if not self.jarvis or not hasattr(self.jarvis, 'run_training_cycle'):
            return
        self._log("🚀 Training wird gestartet...")
        timestamp = time.strftime("%H:%M:%S")
        self._safe_update_gui(lambda: self.training_log.append(f"[{timestamp}] Training gestartet..."))
        def train():
            try:
                result = self.jarvis.run_training_cycle()
                self._safe_update_gui(lambda: self.training_log.append(f"✅ Training abgeschlossen: {result}"))
            except Exception as e:
                self._safe_update_gui(lambda: self.training_log.append(f"❌ Fehler: {e}"))
                traceback.print_exc()
        threading.Thread(target=train, daemon=True).start()

    def _refresh_logs(self):
        """Logs sind lokal - direkter Zugriff OK"""
        try:
            log_file = Path("logs/jarvis.log")
            if log_file.exists():
                logs = log_file.read_text(encoding="utf-8", errors="ignore")
                self.log_output_full = logs[-100000:]
                self._safe_update_gui(lambda: (self.log_output.setPlainText(self.log_output_full), self.log_output.moveCursor(QTextCursor.MoveOperation.End)))
        except Exception as e:
            print(f"Log-Refresh Fehler: {e}")
            traceback.print_exc()
    
    def _filter_logs(self, filter_text: str):
        if not filter_text:
            self.log_output.setPlainText(self.log_output_full)
            return
        filtered = "\n".join(line for line in self.log_output_full.split("\n") if filter_text.lower() in line.lower())
        self.log_output.setPlainText(filtered)

    def _clear_logs(self):
        if self.jarvis and hasattr(self.jarvis, 'clear_logs'):
            self.jarvis.clear_logs()
        self._safe_update_gui(lambda: (self.log_output.clear(), setattr(self, 'log_output_full', '')))
        self._log("🗑️ Logs gelöscht")

    def _measure_audio_level(self):
        if not self.jarvis or not hasattr(self.jarvis, 'sample_audio_level'):
            return
        self._safe_update_gui(lambda: self.audio_level_label.setText("Messe..."))
        def measure():
            try:
                level = self.jarvis.sample_audio_level(duration=2.0)
                if level:
                    self._safe_update_gui(lambda: self.audio_level_label.setText(f"Pegel: {level:.2f}"))
                else:
                    self._safe_update_gui(lambda: self.audio_level_label.setText("Pegel: N/A"))
            except Exception as e:
                self._safe_update_gui(lambda: self.audio_level_label.setText(f"Fehler: {e}"))
                traceback.print_exc()
        threading.Thread(target=measure, daemon=True).start()

    def _send_command(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self._safe_update_gui(lambda: self.input_field.clear())
        self._add_chat_message("user", text)
        if self.jarvis:
            threading.Thread(target=lambda: self.jarvis.send_text_command(text, source="desktop_app"), daemon=True).start()

    def _toggle_listening(self):
        if self.listen_button.isChecked():
            if self.jarvis and self.jarvis.start_listening():
                self._safe_update_gui(lambda: (self.listening_indicator.setText("🎤 Hört zu"), self.listening_indicator.setStyleSheet("background: #2ecc71; padding: 8px 16px; border-radius: 16px; font-weight: bold; color: white;")))
            else:
                self.listen_button.setChecked(False)
        else:
            if self.jarvis:
                self.jarvis.stop_listening()
            self._safe_update_gui(lambda: (self.listening_indicator.setText("🎵 Idle"), self.listening_indicator.setStyleSheet("background: #1e3a5f; padding: 8px 16px; border-radius: 16px; font-weight: bold; color: white;")))

    def update_status(self, message: str):
        try:
            self._safe_update_gui(lambda: (self.status_label.setText(f"🟢 {message}"), self._log(f"Status: {message}")))
        except Exception as e:
            print(f"Update status error: {e}")

    def add_user_message(self, text: str):
        try:
            self._add_chat_message("user", text)
        except Exception as e:
            print(f"Add user message error: {e}")

    def add_assistant_message(self, text: str):
        try:
            self._add_chat_message("assistant", text)
        except Exception as e:
            print(f"Add assistant message error: {e}")

    def _add_chat_message(self, role: str, text: str):
        timestamp = time.strftime("%H:%M:%S")
        if role == "user":
            color = "#42a5f6"
            icon = "👤"
            name = "Du"
        else:
            color = "#66bb6a"
            icon = "🤖"
            name = "JARVIS"
        html = f"""
        <div style="margin: 12px 0; padding: 12px; border-left: 4px solid {color}; background: rgba(30, 58, 95, 0.3); border-radius: 4px;">
            <div style="margin-bottom: 6px;">
                <b style="color: {color}; font-size: 11pt;">{icon} {name}</b>
                <span style="color: #888; font-size: 9pt; margin-left: 8px;">{timestamp}</span>
            </div>
            <div style="color: #e0e0e0; font-size: 10pt; line-height: 1.5;">{text}</div>
        </div>
        """
        self._safe_update_gui(lambda: (self.chat_display.moveCursor(QTextCursor.MoveOperation.End), self.chat_display.insertHtml(html), self.chat_display.moveCursor(QTextCursor.MoveOperation.End)))

    def update_context_panels(self, **kwargs):
        try:
            formatted = json.dumps(kwargs, indent=2, ensure_ascii=False)
            self._safe_update_gui(lambda: self.context_display.setPlainText(formatted))
        except Exception as e:
            print(f"Update context error: {e}")

    def handle_knowledge_progress(self, payload):
        msg = payload if isinstance(payload, str) else str(payload.get("message", ""))
        timestamp = time.strftime("%H:%M:%S")
        self._safe_update_gui(lambda: self.knowledge_feed.append(f"[{timestamp}] 📚 {msg}"))

    def _log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self._safe_update_gui(lambda: self.log_output.append(log_entry))
        self.log_output_full += log_entry + "\n"

    def show_message(self, title: str, message: str):
        self._log(f"{title}: {message}")

    def post_to_qt(self, callback):
        self._safe_update_gui(callback)

    def closeEvent(self, event):
        self.is_running = False
        if self.stats_timer:
            self.stats_timer.stop()
        if self.jarvis:
            self.jarvis.is_running = False
        event.accept()

    def run(self):
        self.show()
        self._log("🚀 Desktop-GUI gestartet")
        if self.jarvis and hasattr(self.jarvis, "on_gui_ready"):
            try:
                self.jarvis.on_gui_ready()
            except Exception as e:
                self._log(f"on_gui_ready Fehler: {e}")
                traceback.print_exc()
        if self.app:
            self.app.exec()
        self._log("🛑 Desktop-GUI beendet")


def create_jarvis_desktop_gui(jarvis_instance):
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 ist nicht installiert. Installiere es mit: pip install PyQt6")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = JarvisDesktopApp(jarvis_instance, app=app)
    return window
