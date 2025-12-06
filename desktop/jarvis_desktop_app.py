#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Native Desktop Application
Echte Desktop-GUI mit PyQt6
"""

import sys
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLineEdit, QPushButton, QLabel, QSplitter,
        QListWidget, QTabWidget, QProgressBar, QStatusBar,
        QGroupBox, QGridLayout, QFrame
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
    from PyQt6.QtGui import QFont, QPalette, QColor, QTextCursor
except ImportError:
    print("❌ PyQt6 nicht installiert!")
    print("Installiere mit: pip install PyQt6")
    sys.exit(1)


class JarvisWorkerSignals(QObject):
    """Signals für Thread-sichere GUI-Updates"""
    status_update = pyqtSignal(str)
    message_received = pyqtSignal(str, str)  # role, text
    context_update = pyqtSignal(dict)
    system_stats = pyqtSignal(dict)


class JarvisDesktopApp(QMainWindow):
    """Native Desktop-GUI für J.A.R.V.I.S."""

    def __init__(self, jarvis_instance=None):
        super().__init__()
        self.jarvis = jarvis_instance
        self.signals = JarvisWorkerSignals()
        
        # Signals verbinden
        self.signals.status_update.connect(self._update_status_label)
        self.signals.message_received.connect(self._add_chat_message)
        self.signals.context_update.connect(self._update_context_panel)
        self.signals.system_stats.connect(self._update_system_stats)
        
        self._init_ui()
        self._apply_dark_theme()
        self._start_background_updates()

    def _init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("J.A.R.V.I.S. Desktop")
        self.setGeometry(100, 100, 1400, 900)

        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Splitter für flexible Größenanpassung
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- LINKE SEITE: Chat & Eingabe ---
        left_panel = self._create_chat_panel()
        splitter.addWidget(left_panel)

        # --- RECHTE SEITE: Tabs für Kontext, System, Logs ---
        right_panel = self._create_info_tabs()
        splitter.addWidget(right_panel)

        # Größenverhältnis: 60% Chat, 40% Info
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)

        # Statusleiste
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Bereit")
        self.status_bar.addPermanentWidget(self.status_label)

    def _create_chat_panel(self) -> QWidget:
        """Erstellt das Chat-Panel (links)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Titel
        title = QLabel("💬 Konversation")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Chat-Verlauf (Textanzeige)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.chat_display)

        # Eingabebereich
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Gib deinen Befehl ein...")
        self.input_field.setFont(QFont("Arial", 11))
        self.input_field.returnPressed.connect(self._send_command)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Senden")
        self.send_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.send_button.clicked.connect(self._send_command)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Steuerbuttons
        control_layout = QHBoxLayout()
        
        self.listen_button = QPushButton("🎤 Spracherkennung")
        self.listen_button.setCheckable(True)
        self.listen_button.clicked.connect(self._toggle_listening)
        control_layout.addWidget(self.listen_button)

        self.clear_button = QPushButton("🗑️ Chat löschen")
        self.clear_button.clicked.connect(self._clear_chat)
        control_layout.addWidget(self.clear_button)

        layout.addLayout(control_layout)
        return panel

    def _create_info_tabs(self) -> QWidget:
        """Erstellt die Info-Tabs (rechts)"""
        tabs = QTabWidget()

        # --- TAB 1: Kontext ---
        context_tab = QWidget()
        context_layout = QVBoxLayout(context_tab)
        
        context_title = QLabel("🧠 Aktueller Kontext")
        context_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        context_layout.addWidget(context_title)
        
        self.context_display = QTextEdit()
        self.context_display.setReadOnly(True)
        self.context_display.setFont(QFont("Consolas", 9))
        context_layout.addWidget(self.context_display)
        
        tabs.addTab(context_tab, "Kontext")

        # --- TAB 2: System ---
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        
        system_title = QLabel("⚙️ System-Status")
        system_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        system_layout.addWidget(system_title)
        
        # System-Metriken Grid
        stats_group = QGroupBox("Ressourcen")
        stats_grid = QGridLayout()
        
        stats_grid.addWidget(QLabel("CPU:"), 0, 0)
        self.cpu_label = QLabel("0%")
        stats_grid.addWidget(self.cpu_label, 0, 1)
        
        stats_grid.addWidget(QLabel("RAM:"), 1, 0)
        self.ram_label = QLabel("0%")
        stats_grid.addWidget(self.ram_label, 1, 1)
        
        stats_grid.addWidget(QLabel("GPU:"), 2, 0)
        self.gpu_label = QLabel("0%")
        stats_grid.addWidget(self.gpu_label, 2, 1)
        
        stats_group.setLayout(stats_grid)
        system_layout.addWidget(stats_group)
        
        # LLM Status
        llm_group = QGroupBox("LLM-Modell")
        llm_layout = QVBoxLayout()
        self.llm_status_label = QLabel("Kein Modell geladen")
        llm_layout.addWidget(self.llm_status_label)
        llm_group.setLayout(llm_layout)
        system_layout.addWidget(llm_group)
        
        system_layout.addStretch()
        tabs.addTab(system_tab, "System")

        # --- TAB 3: Logs ---
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        log_title = QLabel("📋 Aktivitäts-Log")
        log_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        log_layout.addWidget(log_title)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 8))
        log_layout.addWidget(self.log_display)
        
        tabs.addTab(log_tab, "Logs")

        return tabs

    def _apply_dark_theme(self):
        """Wendet das JARVIS Dark Theme an"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(11, 18, 32))  # #0b1220
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(20, 28, 45))  # Dunkleres Input
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(11, 18, 32))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(30, 40, 60))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        self.setPalette(dark_palette)
        
        # Zusätzliches Styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #1e3a5f;
                border: 1px solid #2a5885;
                border-radius: 4px;
                padding: 8px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2a5885;
            }
            QPushButton:pressed {
                background-color: #15293f;
            }
            QPushButton:checked {
                background-color: #2ecc71;
                border-color: #27ae60;
            }
            QLineEdit {
                background-color: #1c2838;
                border: 1px solid #2a5885;
                border-radius: 4px;
                padding: 6px;
                color: white;
            }
            QTextEdit {
                background-color: #0f1621;
                border: 1px solid #1e3a5f;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #2a5885;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

    def _start_background_updates(self):
        """Startet Timer für regelmäßige Updates"""
        # System-Stats alle 2 Sekunden
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._fetch_system_stats)
        self.stats_timer.start(2000)

    # --- EVENT HANDLER ---

    def _send_command(self):
        """Sendet Befehl an JARVIS-Backend"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        self.input_field.clear()
        self._add_chat_message("user", text)
        
        # An JARVIS-Backend senden (in Thread)
        if self.jarvis:
            threading.Thread(
                target=self._process_command_async,
                args=(text,),
                daemon=True
            ).start()
        else:
            self._add_chat_message("assistant", "⚠️ JARVIS-Backend nicht verbunden.")

    def _process_command_async(self, text: str):
        """Verarbeitet Befehl asynchron"""
        try:
            response = self.jarvis.send_text_command(text, source="desktop_app")
            # Response wird über signals.message_received empfangen
        except Exception as e:
            self.signals.message_received.emit("assistant", f"❌ Fehler: {e}")

    def _toggle_listening(self):
        """Schaltet Spracherkennung ein/aus"""
        if self.listen_button.isChecked():
            if self.jarvis:
                success = self.jarvis.start_listening()
                if success:
                    self.signals.status_update.emit("🎤 Hört zu...")
                else:
                    self.listen_button.setChecked(False)
                    self.signals.status_update.emit("⚠️ Spracherkennung nicht verfügbar")
        else:
            if self.jarvis:
                self.jarvis.stop_listening()
            self.signals.status_update.emit("Bereit")

    def _clear_chat(self):
        """Löscht Chat-Verlauf"""
        self.chat_display.clear()
        self._log("Chat-Verlauf gelöscht")

    # --- GUI UPDATE METHODS (Thread-safe via Signals) ---

    def update_status(self, message: str):
        """Wird von JARVIS aufgerufen (thread-safe)"""
        self.signals.status_update.emit(message)

    def _update_status_label(self, message: str):
        """Aktualisiert Statusleiste"""
        self.status_label.setText(message)
        self._log(f"Status: {message}")

    def add_user_message(self, text: str):
        """Wird von JARVIS aufgerufen"""
        self.signals.message_received.emit("user", text)

    def add_assistant_message(self, text: str):
        """Wird von JARVIS aufgerufen"""
        self.signals.message_received.emit("assistant", text)

    def _add_chat_message(self, role: str, text: str):
        """Fügt Nachricht zum Chat hinzu"""
        timestamp = time.strftime("%H:%M:%S")
        
        if role == "user":
            color = "#42a5f5"  # Blau
            prefix = "👤 Du"
        else:
            color = "#66bb6a"  # Grün
            prefix = "🤖 JARVIS"
        
        html = f"""
        <div style="margin: 8px 0; padding: 8px; border-left: 3px solid {color};">
            <b style="color: {color};">{prefix}</b> 
            <span style="color: #888; font-size: 9pt;">{timestamp}</span><br>
            <span style="color: #e0e0e0;">{text}</span>
        </div>
        """
        
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_display.insertHtml(html)
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)

    def update_context_panels(self, **kwargs):
        """Wird von JARVIS aufgerufen"""
        self.signals.context_update.emit(kwargs)

    def _update_context_panel(self, data: dict):
        """Aktualisiert Kontext-Anzeige"""
        import json
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        self.context_display.setPlainText(formatted)

    def _fetch_system_stats(self):
        """Holt System-Statistiken (async)"""
        if not self.jarvis:
            return
        
        threading.Thread(
            target=self._get_stats_async,
            daemon=True
        ).start()

    def _get_stats_async(self):
        """Holt Stats asynchron"""
        try:
            metrics = self.jarvis.get_system_metrics(include_details=False)
            self.signals.system_stats.emit(metrics)
        except Exception:
            pass

    def _update_system_stats(self, metrics: dict):
        """Aktualisiert System-Anzeige"""
        summary = metrics.get("summary", {})
        
        cpu = summary.get("cpu_percent", 0)
        self.cpu_label.setText(f"{cpu:.1f}%")
        
        ram = summary.get("memory_percent", 0)
        self.ram_label.setText(f"{ram:.1f}%")
        
        gpu = summary.get("gpu_utilization", 0)
        self.gpu_label.setText(f"{gpu:.1f}%" if gpu else "N/A")
        
        # LLM Status
        llm_status = self.jarvis.get_llm_status() if self.jarvis else {}
        current_model = llm_status.get("current")
        if current_model:
            self.llm_status_label.setText(f"✅ {current_model}")
        else:
            self.llm_status_label.setText("❌ Kein Modell geladen")

    def _log(self, message: str):
        """Fügt Log-Eintrag hinzu"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")

    def show_message(self, title: str, message: str):
        """Zeigt Nachricht (für JARVIS-Kompatibilität)"""
        self._log(f"{title}: {message}")

    def handle_knowledge_progress(self, payload):
        """Behandelt Wissens-Fortschritt"""
        msg = payload if isinstance(payload, str) else str(payload.get("message", ""))
        self._log(f"📚 {msg}")

    def run(self):
        """Startet GUI-Event-Loop (blocking)"""
        # Ready-Callback aufrufen
        if self.jarvis and hasattr(self.jarvis, "on_gui_ready"):
            self.jarvis.on_gui_ready()
        
        self.show()


def create_jarvis_desktop_gui(jarvis_instance):
    """Factory-Funktion für main.py"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = JarvisDesktopApp(jarvis_instance)
    return window
