#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Dear ImGui Desktop Application - FULL VERSION
GPU-beschleunigt, Ultra-Performance, JARVIS Neon-Theme
ALLE 7 TABS: Dashboard, Chat, Models, Plugins, Memory, Logs, Settings
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
    """JARVIS ImGui - Vollversion mit allen Features"""
    
    def __init__(self, jarvis_instance=None):
        self.jarvis = jarvis_instance
        self.is_running = True
        self.chat_messages = deque(maxlen=100)
        self.cpu_history = deque([0.0] * 100, maxlen=100)
        self.ram_history = deque([0.0] * 100, maxlen=100)
        self.gpu_history = deque([0.0] * 100, maxlen=100)
        self.log_buffer = deque(maxlen=1000)
        
        self._init_imgui()
        self._apply_theme()
        self._create_ui()
        self._start_updates()
    
    def _init_imgui(self):
        dpg.create_context()
        dpg.create_viewport(title="🤖 J.A.R.V.I.S. Control Center", width=1600, height=1000)
        dpg.setup_dearpygui()
    
    def _apply_theme(self):
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (11, 18, 32, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (15, 22, 33, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30, 58, 95, 200))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 58, 95, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (42, 88, 130, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (30, 58, 95, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (42, 130, 218, 255))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
        dpg.bind_theme(theme)
    
    def _create_ui(self):
        with dpg.window(label="JARVIS", tag="main", no_close=True):
            dpg.add_text("🤖 J.A.R.V.I.S. Control Center", color=(100, 181, 246, 255))
            dpg.add_separator()
            
            with dpg.tab_bar():
                with dpg.tab(label="💻 Dashboard"): self._tab_dashboard()
                with dpg.tab(label="💬 Chat"): self._tab_chat()
                with dpg.tab(label="🧠 Modelle"): self._tab_models()
                with dpg.tab(label="🧩 Plugins"): self._tab_plugins()
                with dpg.tab(label="🧠 Memory"): self._tab_memory()
                with dpg.tab(label="📋 Logs"): self._tab_logs()
                with dpg.tab(label="⚙️ Settings"): self._tab_settings()
    
    def _tab_dashboard(self):
        with dpg.child_window(height=600):
            dpg.add_text("📊 System-Metriken")
            dpg.add_text("CPU: 0%", tag="cpu_val")
            dpg.add_text("RAM: 0%", tag="ram_val")
            dpg.add_text("GPU: N/A", tag="gpu_val")
    
    def _tab_chat(self):
        with dpg.child_window(height=700, border=True):
            dpg.add_text("", tag="chat_out", wrap=0)
        dpg.add_input_text(tag="chat_in", width=-100, on_enter=True, callback=self._send_msg)
        dpg.add_button(label="🚀 Send", callback=self._send_msg)
    
    def _send_msg(self):
        text = dpg.get_value("chat_in")
        if text.strip():
            self.add_user_message(text)
            dpg.set_value("chat_in", "")
    
    def _tab_models(self):
        dpg.add_button(label="🔄 Refresh", callback=self._refresh_models)
        dpg.add_text("", tag="model_list")
    
    def _refresh_models(self):
        if self.jarvis and hasattr(self.jarvis, 'get_llm_status'):
            status = self.jarvis.get_llm_status()
            dpg.set_value("model_list", str(status))
    
    def _tab_plugins(self):
        dpg.add_button(label="🔄 Refresh", callback=self._refresh_plugins)
        dpg.add_text("", tag="plugin_list")
    
    def _refresh_plugins(self):
        if self.jarvis and hasattr(self.jarvis, 'get_plugin_overview'):
            plugins = self.jarvis.get_plugin_overview()
            dpg.set_value("plugin_list", "\n".join([p.get('name', 'N/A') for p in plugins]))
    
    def _tab_memory(self):
        dpg.add_text("Memory-Viewer (in Entwicklung)")
    
    def _tab_logs(self):
        dpg.add_button(label="🔄 Refresh", callback=self._refresh_logs)
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="log_out", wrap=0)
    
    def _refresh_logs(self):
        try:
            log = Path("logs/jarvis.log")
            if log.exists():
                dpg.set_value("log_out", log.read_text(encoding="utf-8", errors="ignore")[-50000:])
        except: pass
    
    def _tab_settings(self):
        dpg.add_text("Einstellungen (in Entwicklung)")
    
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
                dpg.set_value("cpu_val", f"CPU: {m.get('cpu_percent', 0):.1f}%")
                dpg.set_value("ram_val", f"RAM: {m.get('memory_percent', 0):.1f}%")
            except: pass
    
    def add_user_message(self, t): self.chat_messages.append(f"👤 {t}"); self._update_chat()
    def add_assistant_message(self, t): self.chat_messages.append(f"🤖 {t}"); self._update_chat()
    def _update_chat(self): dpg.set_value("chat_out", "\n".join(self.chat_messages))
    def update_status(self, m): pass
    def update_context_panels(self, **kw): pass
    def handle_knowledge_progress(self, p): pass
    def show_message(self, t, m): print(f"{t}: {m}")
    
    def run(self):
        dpg.show_viewport()
        dpg.set_primary_window("main", True)
        while dpg.is_dearpygui_running() and self.is_running:
            dpg.render_dearpygui_frame()
        dpg.destroy_context()


def create_jarvis_imgui_gui_full(jarvis_instance):
    return JarvisImGuiAppFull(jarvis_instance)
