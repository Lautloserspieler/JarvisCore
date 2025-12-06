#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Control Center - IRON MAN EDITION
Holographisches UI-Design inspiriert von Tony Stark's JARVIS
GPU-beschleunigt, Neon-Glow, Transparente Panels
"""

import sys
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any
from collections import deque

try:
    import dearpygui.dearpygui as dpg
    IMGUI_AVAILABLE = True
except ImportError:
    IMGUI_AVAILABLE = False
    print("⚠️ DearPyGui nicht installiert!")
    print("Installiere mit: pip install dearpygui")
    sys.exit(1)


class JarvisImGuiAppFull:
    """JARVIS ImGui - IRON MAN HOLOGRAPHIC EDITION"""
    
    def __init__(self, jarvis_instance=None):
        self.jarvis = jarvis_instance
        self.is_running = True
        self.chat_messages = deque(maxlen=100)
        self.cpu_history = deque([0.0] * 100, maxlen=100)
        self.ram_history = deque([0.0] * 100, maxlen=100)
        self.gpu_history = deque([0.0] * 100, maxlen=100)
        self.log_buffer = deque(maxlen=1000)
        
        self._init_imgui()
        self._apply_jarvis_iron_man_theme()
        self._create_ui()
        self._start_updates()
    
    def _init_imgui(self):
        dpg.create_context()
        dpg.create_viewport(
            title="🤖 J.A.R.V.I.S. Control Center - Iron Man Edition",
            width=1920,
            height=1080,
            min_width=1400,
            min_height=800
        )
        dpg.setup_dearpygui()
    
    def _apply_jarvis_iron_man_theme(self):
        """IRON MAN JARVIS HOLOGRAPHIC THEME - Cyan Neon Glow"""
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                # DARK BACKGROUND (Fast schwarz wie im Film)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (5, 10, 18, 240))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (8, 15, 25, 200))
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (10, 18, 30, 240))
                
                # NEON CYAN FRAMES (Holographic Look)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (0, 80, 120, 180))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (0, 150, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (0, 200, 255, 220))
                
                # GLOWING BUTTONS
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 100, 150, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 180, 230, 230))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 220, 255, 255))
                
                # ACTIVE TABS (Bright Cyan)
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (0, 60, 100, 200))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (0, 140, 200, 220))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (0, 200, 255, 255))
                
                # TEXT (Hellblau/Weiß wie Hologramm)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (180, 230, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (100, 130, 150, 255))
                
                # BORDERS & SEPARATORS (Glowing Cyan)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 200, 255, 180))
                dpg.add_theme_color(dpg.mvThemeCol_Separator, (0, 180, 230, 120))
                
                # SCROLLBAR
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (10, 20, 30, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (0, 150, 200, 200))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (0, 200, 255, 230))
                
                # ROUNDED EDGES (Futuristisch)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 8)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 12, 10)
        
        dpg.bind_theme(theme)
    
    def _create_ui(self):
        with dpg.window(label="JARVIS", tag="main", no_close=True, no_collapse=True):
            # === HEADER (Wie Tony Stark's HUD) ===
            with dpg.group(horizontal=True):
                dpg.add_text("🤖 J.A.R.V.I.S.", color=(0, 220, 255, 255))
                dpg.add_text("CONTROL CENTER", pos=(250, 8), color=(100, 200, 255, 200))
                dpg.add_spacer(width=900)
                dpg.add_text("🟢 ONLINE", tag="status_text", color=(0, 255, 150, 255))
            
            dpg.add_separator()
            dpg.add_spacer(height=5)
            
            # === TAB BAR ===
            with dpg.tab_bar():
                with dpg.tab(label="💻 DASHBOARD"): self._tab_dashboard()
                with dpg.tab(label="💬 CHAT"): self._tab_chat()
                with dpg.tab(label="🧠 MODELS"): self._tab_models()
                with dpg.tab(label="🧩 PLUGINS"): self._tab_plugins()
                with dpg.tab(label="🧠 MEMORY"): self._tab_memory()
                with dpg.tab(label="📋 LOGS"): self._tab_logs()
                with dpg.tab(label="⚙️ SETTINGS"): self._tab_settings()
            
            # === FOOTER (Status Bar) ===
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text("• System Ready", tag="footer_status", color=(0, 255, 150, 255))
                dpg.add_spacer(width=50)
                dpg.add_text("FPS: 60", tag="fps_counter", color=(100, 200, 255, 255))
                dpg.add_spacer(width=50)
                dpg.add_text("Powered by Stark Industries", color=(100, 150, 200, 180))
    
    def _tab_dashboard(self):
        """Dashboard mit Live-Metriken (Balken statt Plots)"""
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("📊 SYSTEM METRICS", color=(0, 220, 255, 255))
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            # CPU
            dpg.add_text("💻 CPU:", color=(100, 200, 255, 255))
            dpg.add_progress_bar(tag="cpu_bar", default_value=0.0, width=-1, height=30)
            dpg.add_text("", tag="cpu_text")
            dpg.add_spacer(height=15)
            
            # RAM
            dpg.add_text("💾 RAM:", color=(100, 200, 255, 255))
            dpg.add_progress_bar(tag="ram_bar", default_value=0.0, width=-1, height=30)
            dpg.add_text("", tag="ram_text")
            dpg.add_spacer(height=15)
            
            # GPU
            dpg.add_text("🎮 GPU:", color=(100, 200, 255, 255))
            dpg.add_progress_bar(tag="gpu_bar", default_value=0.0, width=-1, height=30)
            dpg.add_text("", tag="gpu_text")
    
    def _tab_chat(self):
        """Chat-Interface (Wie Kommunikation mit JARVIS)"""
        # Chat History
        with dpg.child_window(height=820, border=True):
            dpg.add_text("", tag="chat_out", wrap=-1)
        
        dpg.add_spacer(height=10)
        
        # Input Area (Großer, wie Sprachbefehl)
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="chat_in",
                width=-150,
                hint="Geben Sie einen Befehl ein...",
                on_enter=True,
                callback=self._send_msg
            )
            dpg.add_button(label="🚀 SENDEN", width=140, height=40, callback=self._send_msg)
    
    def _send_msg(self):
        """Sendet Chat-Nachricht"""
        text = dpg.get_value("chat_in")
        if text.strip():
            self.add_user_message(text)
            dpg.set_value("chat_in", "")
            
            # Process mit JARVIS
            if self.jarvis and hasattr(self.jarvis, 'command_processor'):
                try:
                    response = self.jarvis.command_processor.process_command(text)
                    self.add_assistant_message(response or "Befehl ausgeführt.")
                except Exception as e:
                    self.add_assistant_message(f"❌ Fehler: {e}")
    
    def _tab_models(self):
        """Modell-Manager"""
        dpg.add_text("🧠 LLM MODELS", color=(0, 220, 255, 255))
        dpg.add_separator()
        dpg.add_spacer(height=10)
        
        dpg.add_button(label="🔄 REFRESH", width=200, callback=self._refresh_models)
        dpg.add_spacer(height=10)
        
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="model_list", wrap=-1)
    
    def _refresh_models(self):
        if self.jarvis and hasattr(self.jarvis, 'get_llm_status'):
            try:
                status = self.jarvis.get_llm_status()
                available = status.get("available", {})
                current = status.get("current")
                
                lines = []
                for key, info in available.items():
                    active = "[✅ ACTIVE]" if key == current else ""
                    avail = "✅" if info.get("available") else "❌"
                    lines.append(f"{avail} {key.upper()} {active}")
                    lines.append(f"   File: {info.get('filename', 'N/A')}")
                    lines.append("")
                
                dpg.set_value("model_list", "\n".join(lines) if lines else "No models found.")
            except Exception as e:
                dpg.set_value("model_list", f"Error: {e}")
    
    def _tab_plugins(self):
        """Plugin-Manager"""
        dpg.add_text("🧩 PLUGINS", color=(0, 220, 255, 255))
        dpg.add_separator()
        dpg.add_spacer(height=10)
        
        dpg.add_button(label="🔄 REFRESH", width=200, callback=self._refresh_plugins)
        dpg.add_spacer(height=10)
        
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="plugin_list", wrap=-1)
    
    def _refresh_plugins(self):
        if self.jarvis and hasattr(self.jarvis, 'get_plugin_overview'):
            try:
                plugins = self.jarvis.get_plugin_overview()
                lines = []
                for p in plugins:
                    status = "✅ ONLINE" if p.get("enabled") else "❌ OFFLINE"
                    lines.append(f"{status} {p.get('name', 'Unknown').upper()}")
                    lines.append(f"   Type: {p.get('type', 'N/A')}")
                    lines.append("")
                
                dpg.set_value("plugin_list", "\n".join(lines) if lines else "No plugins found.")
            except Exception as e:
                dpg.set_value("plugin_list", f"Error: {e}")
    
    def _tab_memory(self):
        dpg.add_text("🧠 MEMORY CORE", color=(0, 220, 255, 255))
        dpg.add_separator()
        dpg.add_text("Memory viewer is under construction.")
    
    def _tab_logs(self):
        """Log-Viewer"""
        with dpg.group(horizontal=True):
            dpg.add_button(label="🔄 REFRESH", width=150, callback=self._refresh_logs)
            dpg.add_button(label="🗑️ CLEAR", width=150, callback=self._clear_logs)
        
        dpg.add_spacer(height=10)
        
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="log_out", wrap=0)
    
    def _refresh_logs(self):
        try:
            log = Path("logs/jarvis.log")
            if log.exists():
                logs = log.read_text(encoding="utf-8", errors="ignore")
                dpg.set_value("log_out", logs[-50000:])
        except Exception as e:
            dpg.set_value("log_out", f"Error loading logs: {e}")
    
    def _clear_logs(self):
        dpg.set_value("log_out", "")
    
    def _tab_settings(self):
        dpg.add_text("⚙️ SETTINGS", color=(0, 220, 255, 255))
        dpg.add_separator()
        dpg.add_text("Settings panel is under construction.")
    
    def _start_updates(self):
        def loop():
            while self.is_running:
                self._update_metrics()
                time.sleep(2)
        threading.Thread(target=loop, daemon=True).start()
    
    def _update_metrics(self):
        if self.jarvis and hasattr(self.jarvis, 'get_system_metrics'):
            try:
                m = self.jarvis.get_system_metrics().get("summary", {})
                cpu = m.get('cpu_percent', 0) / 100.0
                ram = m.get('memory_percent', 0) / 100.0
                gpu = m.get('gpu_utilization', 0) / 100.0
                
                dpg.set_value("cpu_bar", cpu)
                dpg.set_value("cpu_text", f"{cpu*100:.1f}% Usage")
                
                dpg.set_value("ram_bar", ram)
                dpg.set_value("ram_text", f"{ram*100:.1f}% Usage")
                
                dpg.set_value("gpu_bar", gpu)
                dpg.set_value("gpu_text", f"{gpu*100:.1f}% Usage" if gpu > 0 else "N/A")
            except: pass
    
    def add_user_message(self, t):
        self.chat_messages.append(f"👤 USER: {t}")
        self._update_chat()
    
    def add_assistant_message(self, t):
        self.chat_messages.append(f"🤖 JARVIS: {t}")
        self._update_chat()
    
    def _update_chat(self):
        dpg.set_value("chat_out", "\n\n".join(self.chat_messages))
    
    def update_status(self, m): pass
    def update_context_panels(self, **kw): pass
    def handle_knowledge_progress(self, p): pass
    def show_message(self, t, m): print(f"{t}: {m}")
    
    def run(self):
        dpg.show_viewport()
        dpg.set_primary_window("main", True)
        
        # Initial load
        if self.jarvis:
            self._refresh_models()
            self._refresh_plugins()
            self._refresh_logs()
        
        # Main loop
        while dpg.is_dearpygui_running() and self.is_running:
            fps = dpg.get_frame_rate()
            dpg.set_value("fps_counter", f"FPS: {fps:.0f}")
            dpg.render_dearpygui_frame()
        
        dpg.destroy_context()


def create_jarvis_imgui_gui_full(jarvis_instance):
    return JarvisImGuiAppFull(jarvis_instance)
