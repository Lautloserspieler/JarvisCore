#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Dear ImGui Desktop Application
GPU-beschleunigt, Ultra-Performance, JARVIS Neon-Theme
"""

import sys
import threading
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import deque

try:
    import dearpygui.dearpygui as dpg
    IMGUI_AVAILABLE = True
except ImportError:
    IMGUI_AVAILABLE = False
    print("⚠️ DearPyGui nicht installiert!")
    print("Installiere mit: pip install dearpygui")
    sys.exit(1)


class JarvisImGuiApp:
    """JARVIS Dear ImGui Desktop-GUI - Ultra-Performance Edition"""
    
    def __init__(self, jarvis_instance=None):
        self.jarvis = jarvis_instance
        self.is_running = True
        
        # UI State
        self.selected_model = None
        self.chat_messages = deque(maxlen=100)
        self.current_tab = "dashboard"
        
        # System Metrics History (für Plots)
        self.cpu_history = deque([0.0] * 100, maxlen=100)
        self.ram_history = deque([0.0] * 100, maxlen=100)
        self.gpu_history = deque([0.0] * 100, maxlen=100)
        
        # Model Download Progress
        self.download_progress = 0.0
        self.download_status = ""
        
        # Logs
        self.log_buffer = deque(maxlen=1000)
        self.log_filter = ""
        
        # Init ImGui
        self._init_imgui()
        self._apply_jarvis_theme()
        self._create_main_window()
        
        # Start background updates
        self._start_background_thread()
    
    def _init_imgui(self):
        """Initialisiert Dear ImGui Context"""
        dpg.create_context()
        dpg.create_viewport(
            title="🤖 J.A.R.V.I.S. Control Center",
            width=1600,
            height=1000,
            min_width=1200,
            min_height=700
        )
        dpg.setup_dearpygui()
    
    def _apply_jarvis_theme(self):
        """JARVIS Neon-Blue Theme - Iron Man Style"""
        with dpg.theme() as jarvis_theme:
            with dpg.theme_component(dpg.mvAll):
                # Background Colors (Dark Blue)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (11, 18, 32, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (15, 22, 33, 255))
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (20, 28, 45, 255))
                
                # Frame Colors (Neon Blue)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30, 58, 95, 200))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (42, 88, 130, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (42, 130, 218, 255))
                
                # Button Colors
                dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 58, 95, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (42, 88, 130, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (42, 130, 218, 255))
                
                # Header Colors (Tabs)
                dpg.add_theme_color(dpg.mvThemeCol_Header, (30, 58, 95, 255))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (42, 88, 130, 255))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (42, 130, 218, 255))
                
                # Tab Colors
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (30, 58, 95, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (42, 88, 130, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (42, 130, 218, 255))
                
                # Text Colors
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (136, 136, 136, 255))
                
                # Border & Separator (Neon Glow)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (42, 130, 218, 150))
                dpg.add_theme_color(dpg.mvThemeCol_Separator, (42, 130, 218, 100))
                
                # Scrollbar
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (15, 22, 33, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (42, 88, 130, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (42, 130, 218, 255))
                
                # Plot Colors (Cyan Neon)
                dpg.add_theme_color(dpg.mvPlotCol_Line, (0, 255, 255, 255))
                dpg.add_theme_color(dpg.mvPlotCol_Fill, (0, 200, 255, 100))
                
                # Styles
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
        
        dpg.bind_theme(jarvis_theme)
    
    def _create_main_window(self):
        """Erstellt das Haupt-Window mit Tab-Bar"""
        with dpg.window(label="J.A.R.V.I.S.", tag="main_window", no_close=True):
            # Header
            with dpg.group(horizontal=True):
                dpg.add_text("🤖 J.A.R.V.I.S.", color=(100, 181, 246, 255))
                dpg.add_text("Desktop Control Center", pos=(180, 8), color=(100, 181, 246, 180))
                dpg.add_spacer(width=800)
                dpg.add_text("", tag="status_text", color=(46, 204, 113, 255))
            
            dpg.add_separator()
            
            # Tab Bar
            with dpg.tab_bar():
                # Tab 1: Dashboard
                with dpg.tab(label="💻 Dashboard"):
                    self._create_dashboard_tab()
                
                # Tab 2: Chat
                with dpg.tab(label="💬 Chat"):
                    self._create_chat_tab()
                
                # Tab 3: Models
                with dpg.tab(label="🧠 Modelle"):
                    self._create_models_tab()
                
                # Tab 4: Plugins
                with dpg.tab(label="🧩 Plugins"):
                    self._create_plugins_tab()
                
                # Tab 5: Memory
                with dpg.tab(label="🧠 Gedächtnis"):
                    self._create_memory_tab()
                
                # Tab 6: Logs
                with dpg.tab(label="📋 Logs"):
                    self._create_logs_tab()
                
                # Tab 7: Settings
                with dpg.tab(label="⚙️ Einstellungen"):
                    self._create_settings_tab()
            
            # Footer Status
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text("🟢 Online", tag="connection_status", color=(46, 204, 113, 255))
                dpg.add_spacer(width=50)
                dpg.add_text("FPS: 60", tag="fps_counter", color=(100, 181, 246, 255))
    
    # ===================================================================
    # TAB 1: DASHBOARD
    # ===================================================================
    def _create_dashboard_tab(self):
        """System-Metriken mit Live-Plots"""
        with dpg.group(horizontal=True):
            # Left Column: Metric Cards
            with dpg.child_window(width=400, height=600):
                dpg.add_text("📊 System-Metriken", color=(100, 181, 246, 255))
                dpg.add_separator()
                
                # CPU Card
                with dpg.group():
                    dpg.add_text("💻 CPU", color=(100, 181, 246, 255))
                    dpg.add_text("0.0%", tag="cpu_value", color=(255, 255, 255, 255))
                    dpg.add_text("0 MHz", tag="cpu_detail", color=(136, 136, 136, 255))
                    dpg.add_separator()
                
                # RAM Card
                with dpg.group():
                    dpg.add_text("💾 RAM", color=(100, 181, 246, 255))
                    dpg.add_text("0.0%", tag="ram_value", color=(255, 255, 255, 255))
                    dpg.add_text("0.0 GB frei", tag="ram_detail", color=(136, 136, 136, 255))
                    dpg.add_separator()
                
                # GPU Card
                with dpg.group():
                    dpg.add_text("🎮 GPU", color=(100, 181, 246, 255))
                    dpg.add_text("N/A", tag="gpu_value", color=(255, 255, 255, 255))
                    dpg.add_text("0 MB VRAM", tag="gpu_detail", color=(136, 136, 136, 255))
                    dpg.add_separator()
                
                # Disk Card
                with dpg.group():
                    dpg.add_text("💾 Disk", color=(100, 181, 246, 255))
                    dpg.add_text("0.0%", tag="disk_value", color=(255, 255, 255, 255))
                    dpg.add_text("0.0 GB frei", tag="disk_detail", color=(136, 136, 136, 255))
                    dpg.add_separator()
                
                # Uptime Card
                with dpg.group():
                    dpg.add_text("⏱️ Uptime", color=(100, 181, 246, 255))
                    dpg.add_text("0.0h", tag="uptime_value", color=(255, 255, 255, 255))
            
            # Right Column: Live Plots
            with dpg.child_window(width=-1, height=600):
                dpg.add_text("📈 Live-Metriken", color=(100, 181, 246, 255))
                dpg.add_separator()
                
                # CPU Plot
                with dpg.plot(label="CPU Usage", height=150, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Zeit")
                    with dpg.plot_axis(dpg.mvYAxis, label="%"):
                        dpg.add_line_series(list(range(100)), list(self.cpu_history), 
                                          label="CPU", tag="cpu_plot")
                
                # RAM Plot
                with dpg.plot(label="RAM Usage", height=150, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Zeit")
                    with dpg.plot_axis(dpg.mvYAxis, label="%"):
                        dpg.add_line_series(list(range(100)), list(self.ram_history), 
                                          label="RAM", tag="ram_plot")
                
                # GPU Plot
                with dpg.plot(label="GPU Usage", height=150, width=-1):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Zeit")
                    with dpg.plot_axis(dpg.mvYAxis, label="%"):
                        dpg.add_line_series(list(range(100)), list(self.gpu_history), 
                                          label="GPU", tag="gpu_plot")
    
    # ===================================================================
    # TAB 2: CHAT
    # ===================================================================
    def _create_chat_tab(self):
        """Chat-Interface"""
        # Chat History
        with dpg.child_window(height=-60, border=True):
            dpg.add_text("💬 Chat-Verlauf", color=(100, 181, 246, 255), tag="chat_history")
        
        dpg.add_separator()
        
        # Input
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                hint="Schreibe einen Befehl oder eine Frage...",
                tag="chat_input",
                width=-150,
                on_enter=True,
                callback=self._send_chat_message
            )
            dpg.add_button(label="🚀 Senden", callback=self._send_chat_message)
        
        # Controls
        with dpg.group(horizontal=True):
            dpg.add_button(label="🎵 Spracherkennung", tag="listen_btn", callback=self._toggle_listening)
            dpg.add_button(label="🗑️ Chat löschen", callback=self._clear_chat)
    
    # ===================================================================
    # TAB 3: MODELS
    # ===================================================================
    def _create_models_tab(self):
        """Model Control Panel"""
        # Header
        with dpg.group(horizontal=True):
            dpg.add_text("🧠 LLM Modelle", color=(100, 181, 246, 255))
            dpg.add_spacer(width=50)
            dpg.add_text("❌ Kein Modell", tag="current_model_status", color=(198, 40, 40, 255))
        
        dpg.add_separator()
        
        # Model Selector
        with dpg.group(horizontal=True):
            dpg.add_text("Modell auswählen:")
            dpg.add_combo(
                items=["-- Wähle ein Modell --"],
                tag="model_selector",
                width=400,
                callback=self._on_model_selected
            )
        
        dpg.add_separator()
        
        # Actions
        with dpg.group(horizontal=True):
            dpg.add_button(label="⬇️ Laden", callback=lambda: self._model_action("load"))
            dpg.add_button(label="⬆️ Entladen", callback=lambda: self._model_action("unload"))
            dpg.add_button(label="📥 Download", callback=lambda: self._model_action("download"))
            dpg.add_button(label="🔄 Aktualisieren", callback=self._refresh_models)
        
        # Progress Bar
        dpg.add_progress_bar(tag="model_download_progress", default_value=0.0, width=-1)
        dpg.add_text("", tag="model_download_status", color=(100, 181, 246, 255))
        
        dpg.add_separator()
        
        # Model List
        with dpg.child_window(height=200, border=True):
            dpg.add_text("Verfügbare Modelle:\n\n", tag="model_list", wrap=0)
        
        # Metadata
        dpg.add_text("Metadata:", color=(100, 181, 246, 255))
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("{}", tag="model_metadata", wrap=0)
    
    # ===================================================================
    # TAB 4: PLUGINS
    # ===================================================================
    def _create_plugins_tab(self):
        """Plugin Manager"""
        with dpg.group(horizontal=True):
            dpg.add_text("🧩 Plugin-Übersicht", color=(100, 181, 246, 255))
            dpg.add_spacer(width=50)
            dpg.add_button(label="🔄 Aktualisieren", callback=self._refresh_plugins)
        
        dpg.add_separator()
        
        # Plugin Table
        with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True, 
                      borders_innerV=True, borders_outerV=True, tag="plugin_table"):
            dpg.add_table_column(label="Name")
            dpg.add_table_column(label="Modul")
            dpg.add_table_column(label="Status")
            dpg.add_table_column(label="Sandbox")
    
    # ===================================================================
    # TAB 5: MEMORY
    # ===================================================================
    def _create_memory_tab(self):
        """Gedächtnis-Übersicht"""
        dpg.add_text("🧠 Kontext-Zusammenfassung", color=(100, 181, 246, 255))
        with dpg.child_window(height=200, border=True):
            dpg.add_text("Keine Daten", tag="memory_summary", wrap=0)
        
        dpg.add_separator()
        
        dpg.add_text("📜 Konversationsverlauf", color=(100, 181, 246, 255))
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="memory_messages", wrap=0)
    
    # ===================================================================
    # TAB 6: LOGS
    # ===================================================================
    def _create_logs_tab(self):
        """Log-Viewer"""
        with dpg.group(horizontal=True):
            dpg.add_button(label="🔄 Aktualisieren", callback=self._refresh_logs)
            dpg.add_button(label="🗑️ Logs löschen", callback=self._clear_logs)
            dpg.add_spacer(width=50)
            dpg.add_input_text(hint="🔍 Filter...", tag="log_filter_input", 
                             width=200, callback=self._filter_logs)
        
        dpg.add_separator()
        
        # Log Output
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="log_output", wrap=0)
    
    # ===================================================================
    # TAB 7: SETTINGS
    # ===================================================================
    def _create_settings_tab(self):
        """Einstellungen"""
        # Speech Settings
        with dpg.collapsing_header(label="🎤 Sprach-Einstellungen", default_open=True):
            dpg.add_checkbox(label="Wake Word aktiviert", tag="wake_word_enabled")
            dpg.add_slider_int(label="Min. Wörter", tag="min_words", default_value=1, 
                             min_value=1, max_value=10, width=200)
            dpg.add_slider_int(label="TTS-Rate", tag="tts_rate", default_value=120, 
                             min_value=120, max_value=260, width=200)
            dpg.add_button(label="💾 Speichern")
        
        # Audio Settings
        with dpg.collapsing_header(label="🔊 Audio", default_open=True):
            dpg.add_combo(label="Eingabegerät", items=["Default"], tag="audio_device")
            dpg.add_button(label="📊 Pegel messen", callback=self._measure_audio_level)
            dpg.add_text("Pegel: --", tag="audio_level")
        
        # System Settings
        with dpg.collapsing_header(label="⚙️ System", default_open=True):
            dpg.add_checkbox(label="Debug-Modus", tag="debug_mode")
            dpg.add_checkbox(label="Autostart", tag="autostart")
            dpg.add_button(label="💾 Speichern")
    
    # ===================================================================
    # CALLBACKS
    # ===================================================================
    def _send_chat_message(self):
        """Sendet Chat-Nachricht"""
        text = dpg.get_value("chat_input")
        if not text:
            return
        
        dpg.set_value("chat_input", "")
        self.chat_messages.append(f"[Du] {text}")
        self._update_chat_display()
        
        # Send to JARVIS
        if self.jarvis:
            threading.Thread(
                target=lambda: self.jarvis.send_text_command(text, source="imgui_app"),
                daemon=True
            ).start()
    
    def _clear_chat(self):
        """Löscht Chat-Verlauf"""
        self.chat_messages.clear()
        self._update_chat_display()
    
    def _update_chat_display(self):
        """Aktualisiert Chat-Anzeige"""
        chat_text = "\n".join(self.chat_messages)
        dpg.set_value("chat_history", chat_text)
    
    def _toggle_listening(self):
        """Toggle Spracherkennung"""
        # TODO: Implement
        pass
    
    def _on_model_selected(self, sender, app_data):
        """Model ausgewählt"""
        self.selected_model = app_data
        self._log(f"Modell ausgewählt: {app_data}")
    
    def _model_action(self, action: str):
        """Führt Model-Aktion aus"""
        if not self.jarvis or not self.selected_model:
            self._log("❌ Kein Modell ausgewählt!")
            return
        
        self._log(f"🚀 Modell-Aktion: {action} - {self.selected_model}")
        
        try:
            if action == "download":
                dpg.set_value("model_download_progress", 0.0)
                dpg.set_value("model_download_status", "Download startet...")
                threading.Thread(
                    target=lambda: self.jarvis.control_llm_model("download", self.selected_model),
                    daemon=True
                ).start()
            elif action == "load":
                result = self.jarvis.control_llm_model("load", self.selected_model)
                if result.get("success"):
                    self._log(f"✅ Modell geladen: {self.selected_model}")
                else:
                    self._log("❌ Modell-Laden fehlgeschlagen")
            elif action == "unload":
                result = self.jarvis.control_llm_model("unload", self.selected_model)
                if result.get("success"):
                    self._log("✅ Modell entladen")
                else:
                    self._log("❌ Modell-Entladen fehlgeschlagen")
            
            time.sleep(0.5)
            self._refresh_models()
        except Exception as e:
            self._log(f"❌ Model-Action Fehler: {e}")
    
    def _refresh_models(self):
        """Aktualisiert Model-Liste"""
        if not self.jarvis or not hasattr(self.jarvis, 'get_llm_status'):
            return
        
        try:
            llm_status = self.jarvis.get_llm_status()
            available = llm_status.get("available", {})
            
            # Update Selector
            model_names = ["-- Wähle ein Modell --"] + list(available.keys())
            dpg.configure_item("model_selector", items=model_names)
            
            # Update List
            model_text = "Verfügbare Modelle:\n\n"
            for key, info in available.items():
                status = "✅ Installiert" if info.get("available") else "📥 Download verfügbar"
                size = info.get("size_mb", "?")
                model_text += f"• {key}: {status} ({size} MB)\n"
            dpg.set_value("model_list", model_text)
            
            # Update Metadata
            metadata = llm_status.get("metadata", {})
            meta_text = json.dumps(metadata, indent=2, ensure_ascii=False)
            dpg.set_value("model_metadata", meta_text)
            
            # Update Status
            current = llm_status.get("current")
            if current:
                dpg.set_value("current_model_status", f"✅ {current}")
                dpg.configure_item("current_model_status", color=(46, 204, 113, 255))
            else:
                dpg.set_value("current_model_status", "❌ Kein Modell")
                dpg.configure_item("current_model_status", color=(198, 40, 40, 255))
        except Exception as e:
            self._log(f"Model-Refresh Fehler: {e}")
    
    def _refresh_plugins(self):
        """Aktualisiert Plugin-Liste"""
        if not self.jarvis or not hasattr(self.jarvis, 'get_plugin_overview'):
            return
        
        try:
            plugins = self.jarvis.get_plugin_overview()
            
            # Clear table
            dpg.delete_item("plugin_table", children_only=True, slot=1)
            
            # Re-add columns
            with dpg.table(parent="plugin_table", header_row=True):
                dpg.add_table_column(label="Name")
                dpg.add_table_column(label="Modul")
                dpg.add_table_column(label="Status")
                dpg.add_table_column(label="Sandbox")
                
                # Add rows
                for plugin in plugins:
                    with dpg.table_row():
                        dpg.add_text(plugin.get("name", ""))
                        dpg.add_text(plugin.get("module", ""))
                        status = "✅" if plugin.get("enabled") else "❌"
                        dpg.add_text(status)
                        sandbox = "🔒" if plugin.get("sandbox") else "🔓"
                        dpg.add_text(sandbox)
        except Exception as e:
            self._log(f"Plugin-Refresh Fehler: {e}")
    
    def _refresh_logs(self):
        """Aktualisiert Logs"""
        try:
            log_file = Path("logs/jarvis.log")
            if log_file.exists():
                logs = log_file.read_text(encoding="utf-8", errors="ignore")
                dpg.set_value("log_output", logs[-50000:])  # Last 50KB
        except Exception as e:
            self._log(f"Log-Refresh Fehler: {e}")
    
    def _clear_logs(self):
        """Löscht Logs"""
        if self.jarvis and hasattr(self.jarvis, 'clear_logs'):
            self.jarvis.clear_logs()
        dpg.set_value("log_output", "")
        self._log("🗑️ Logs gelöscht")
    
    def _filter_logs(self):
        """Filtert Logs"""
        # TODO: Implement log filtering
        pass
    
    def _measure_audio_level(self):
        """Misst Audio-Pegel"""
        if not self.jarvis or not hasattr(self.jarvis, 'sample_audio_level'):
            return
        
        dpg.set_value("audio_level", "Messe...")
        
        def measure():
            try:
                level = self.jarvis.sample_audio_level(duration=2.0)
                if level:
                    dpg.set_value("audio_level", f"Pegel: {level:.2f}")
                else:
                    dpg.set_value("audio_level", "Pegel: N/A")
            except Exception as e:
                dpg.set_value("audio_level", f"Fehler: {e}")
        
        threading.Thread(target=measure, daemon=True).start()
    
    def _log(self, message: str):
        """Fügt Log-Eintrag hinzu"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_buffer.append(log_entry)
        print(log_entry)
    
    # ===================================================================
    # BACKGROUND UPDATES
    # ===================================================================
    def _start_background_thread(self):
        """Startet Background-Update Thread"""
        def update_loop():
            while self.is_running:
                try:
                    self._update_system_metrics()
                    time.sleep(2.0)  # Update alle 2 Sekunden
                except Exception as e:
                    print(f"Background update error: {e}")
        
        threading.Thread(target=update_loop, daemon=True).start()
    
    def _update_system_metrics(self):
        """Aktualisiert System-Metriken"""
        if not self.jarvis or not hasattr(self.jarvis, 'get_system_metrics'):
            return
        
        try:
            metrics = self.jarvis.get_system_metrics(include_details=False)
            summary = metrics.get("summary", {})
            
            cpu = summary.get("cpu_percent", 0)
            ram = summary.get("memory_percent", 0)
            gpu = summary.get("gpu_utilization", 0)
            disk = summary.get("disk_percent", 0)
            uptime = summary.get("uptime_hours", 0)
            
            # Update Values
            dpg.set_value("cpu_value", f"{cpu:.1f}%")
            dpg.set_value("cpu_detail", f"{summary.get('cpu_freq', 0):.0f} MHz")
            dpg.set_value("ram_value", f"{ram:.1f}%")
            dpg.set_value("ram_detail", f"Frei: {summary.get('memory_free', 0):.1f} GB")
            dpg.set_value("gpu_value", f"{gpu:.1f}%" if gpu else "N/A")
            dpg.set_value("gpu_detail", f"VRAM: {summary.get('gpu_memory', 0):.0f} MB")
            dpg.set_value("disk_value", f"{disk:.1f}%")
            dpg.set_value("disk_detail", f"Frei: {summary.get('disk_free', 0):.1f} GB")
            dpg.set_value("uptime_value", f"{uptime:.1f}h")
            
            # Update Plots
            self.cpu_history.append(cpu)
            self.ram_history.append(ram)
            self.gpu_history.append(gpu if gpu else 0.0)
            
            dpg.set_value("cpu_plot", [list(range(100)), list(self.cpu_history)])
            dpg.set_value("ram_plot", [list(range(100)), list(self.ram_history)])
            dpg.set_value("gpu_plot", [list(range(100)), list(self.gpu_history)])
            
        except Exception as e:
            print(f"Metrics update error: {e}")
    
    # ===================================================================
    # PUBLIC INTERFACE
    # ===================================================================
    def add_user_message(self, text: str):
        """Fügt User-Nachricht hinzu"""
        self.chat_messages.append(f"👤 [Du] {text}")
        self._update_chat_display()
    
    def add_assistant_message(self, text: str):
        """Fügt JARVIS-Nachricht hinzu"""
        self.chat_messages.append(f"🤖 [JARVIS] {text}")
        self._update_chat_display()
    
    def update_status(self, message: str):
        """Aktualisiert Status"""
        dpg.set_value("status_text", f"🟢 {message}")
    
    def run(self):
        """Startet die GUI"""
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        self._log("🚀 ImGui-GUI gestartet")
        
        # Initial data load
        if self.jarvis:
            self._refresh_models()
            self._refresh_plugins()
            self._refresh_logs()
        
        # Main loop
        while dpg.is_dearpygui_running() and self.is_running:
            # Update FPS counter
            fps = dpg.get_frame_rate()
            dpg.set_value("fps_counter", f"FPS: {fps:.0f}")
            
            dpg.render_dearpygui_frame()
        
        self._log("🛑 ImGui-GUI beendet")
        self.is_running = False
        dpg.destroy_context()


def create_jarvis_imgui_gui(jarvis_instance):
    """Erstellt die JARVIS ImGui GUI"""
    if not IMGUI_AVAILABLE:
        raise ImportError("DearPyGui ist nicht installiert. Installiere es mit: pip install dearpygui")
    
    window = JarvisImGuiApp(jarvis_instance)
    return window
