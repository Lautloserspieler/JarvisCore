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
        """System-Metriken mit Live-Plots"""        with dpg.group(horizontal=True):
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
    
    # ... (Rest der Tab-Methoden bleiben identisch)
    
    # ===================================================================
    # PUBLIC INTERFACE (KOMPATIBILITÄT)
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
    
    def update_context_panels(self, **kwargs):
        """Aktualisiert Context-Panels (Dummy für Kompatibilität)"""
        # ImGui hat keine separaten Context-Panels wie PyQt6
        # Diese Methode ist nur für Kompatibilität vorhanden
        pass
    
    def handle_knowledge_progress(self, payload):
        """Handle Knowledge Progress (Dummy für Kompatibilität)"""
        # Könnte später in einem eigenen Panel angezeigt werden
        if isinstance(payload, dict):
            msg = payload.get("message", str(payload))
            self._log(f"🧠 Knowledge: {msg}")
        else:
            self._log(f"🧠 Knowledge: {payload}")
    
    def show_message(self, title: str, message: str):
        """Zeigt eine Nachricht an (Dummy für Kompatibilität)"""
        self._log(f"{title}: {message}")
    
    # ... (Rest der Methoden bleibt identisch)
    
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
