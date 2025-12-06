#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Control Center - UNREAL ENGINE 5 EDITION
Moderne Flat-UI mit GROßER LESBARER SCHRIFT
Live-Monitoring, Settings, Model Manager, Plugin System
"""

import sys
import threading
import time
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


class JarvisUE5ControlCenter:
    """JARVIS Control Center - Unreal Engine 5 Style mit großer Schrift"""
    
    def __init__(self, jarvis_instance=None):
        self.jarvis = jarvis_instance
        self.is_running = True
        self.chat_messages = deque(maxlen=100)
        self.cpu_history = deque([0.0] * 100, maxlen=100)
        self.ram_history = deque([0.0] * 100, maxlen=100)
        self.gpu_history = deque([0.0] * 100, maxlen=100)
        self.log_buffer = deque(maxlen=500)
        self.log_auto_scroll = True
        
        self._init_context()
        self._setup_fonts()  # NEUE FUNKTION FÜR GROßE SCHRIFT
        self._apply_ue5_theme()
        self._create_ui()
        self._start_background_workers()
    
    def _init_context(self):
        dpg.create_context()
        dpg.create_viewport(
            title="🎮 J.A.R.V.I.S. Control Center - UE5 Edition",
            width=1920,
            height=1080,
            min_width=1600,
            min_height=900
        )
    
    def _setup_fonts(self):
        """Große, lesbare Schrift wie in VS Code / UE5"""
        # Standard-Font vergrößern
        with dpg.font_registry():
            # Haupt-Font (18px - gut lesbar)
            default_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 18)
            
            # Großer Font für Header (28px)
            large_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 28)
            
            # Mittelgroßer Font für Subheader (22px)
            medium_font = dpg.add_font("C:/Windows/Fonts/segoeui.ttf", 22)
        
        dpg.bind_font(default_font)
        
        # Fonts speichern für spätere Nutzung
        self.default_font = default_font
        self.large_font = large_font
        self.medium_font = medium_font
    
    def _apply_ue5_theme(self):
        """UNREAL ENGINE 5 DARK FLAT THEME mit verbessertem Kontrast"""
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                # UE5 Dark Gray Background
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (28, 28, 30, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (35, 35, 37, 255))
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (30, 30, 32, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (70, 70, 72, 255))  # Heller
                
                # Frames (Input fields, etc.)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (45, 45, 48, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (55, 55, 58, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (65, 65, 68, 255))
                
                # Buttons (UE5 Orange/Blue accent)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (50, 50, 52, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (70, 70, 75, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (90, 90, 95, 255))
                
                # Tabs
                dpg.add_theme_color(dpg.mvThemeCol_Tab, (40, 40, 42, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (70, 70, 75, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, (60, 60, 65, 255))
                
                # Text (VIEL HELLER für bessere Lesbarkeit)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (240, 240, 240, 255))  # Fast weiß
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (150, 150, 150, 255))
                
                # Scrollbars
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (35, 35, 37, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (70, 70, 72, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (90, 90, 92, 255))
                
                # Headers
                dpg.add_theme_color(dpg.mvThemeCol_Header, (50, 50, 52, 255))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (70, 70, 75, 255))
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (90, 90, 95, 255))
                
                # Modern Flat Look (minimal rounding)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
                
                # VIEL MEHR PADDING für bessere Lesbarkeit
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 10)  # Vergrößert
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)  # Vergrößert
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 12, 10)    # Vergrößert
                dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 8, 6) # Neu
        
        dpg.bind_theme(theme)
        dpg.setup_dearpygui()
    
    def _create_ui(self):
        with dpg.window(label="JARVIS", tag="main", no_close=True, no_collapse=True):
            # === HEADER BAR (GROß) ===
            with dpg.group(horizontal=True):
                dpg.add_text("🎮 J.A.R.V.I.S.", color=(255, 140, 0, 255))  # Orange
                dpg.bind_item_font(dpg.last_item(), self.large_font)
                
                dpg.add_text(" Control Center", color=(200, 200, 200, 255))
                dpg.bind_item_font(dpg.last_item(), self.medium_font)
                
                dpg.add_spacer(width=800)
                
                dpg.add_text("🟢 ONLINE", tag="status_indicator", color=(100, 255, 100, 255))
                dpg.bind_item_font(dpg.last_item(), self.medium_font)
            
            dpg.add_separator()
            dpg.add_spacer(height=5)
            
            # === TAB BAR (Große Tabs) ===
            with dpg.tab_bar():
                # Tab-Labels mit Emojis sind automatisch gut lesbar durch Font
                with dpg.tab(label="  📊 Dashboard  "): self._build_dashboard()
                with dpg.tab(label="  💬 Chat  "): self._build_chat()
                with dpg.tab(label="  🧠 Models  "): self._build_models()
                with dpg.tab(label="  🧩 Plugins  "): self._build_plugins()
                with dpg.tab(label="  🗄️ Memory  "): self._build_memory()
                with dpg.tab(label="  📜 Logs  "): self._build_logs()
                with dpg.tab(label="  ⚙️ Settings  "): self._build_settings()
            
            # === FOOTER BAR ===
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text("● System Ready", tag="footer_status", color=(100, 255, 100, 255))
                dpg.add_spacer(width=100)
                dpg.add_text("FPS: 60", tag="fps_display", color=(180, 180, 180, 255))
                dpg.add_spacer(width=100)
                dpg.add_text("⚡ Powered by Unreal Engine 5 Design", color=(120, 120, 120, 255))
    
    # ========== DASHBOARD TAB ==========
    def _build_dashboard(self):
        with dpg.child_window(height=-1):
            dpg.add_text("📊 SYSTEM METRICS", color=(255, 140, 0, 255))
            dpg.bind_item_font(dpg.last_item(), self.medium_font)
            
            dpg.add_separator()
            dpg.add_spacer(height=15)
            
            # Live Plots (groß und gut sichtbar)
            with dpg.group(horizontal=True):
                with dpg.child_window(width=620, height=300, border=True):
                    dpg.add_text("🖥️ CPU Usage")
                    dpg.add_spacer(height=5)
                    dpg.add_simple_plot(
                        tag="cpu_plot",
                        default_value=list(self.cpu_history),
                        height=240,
                        histogram=False,
                        overlay="0%"
                    )
                
                with dpg.child_window(width=620, height=300, border=True):
                    dpg.add_text("💾 RAM Usage")
                    dpg.add_spacer(height=5)
                    dpg.add_simple_plot(
                        tag="ram_plot",
                        default_value=list(self.ram_history),
                        height=240,
                        overlay="0%"
                    )
                
                with dpg.child_window(width=-1, height=300, border=True):
                    dpg.add_text("🎮 GPU Usage")
                    dpg.add_spacer(height=5)
                    dpg.add_simple_plot(
                        tag="gpu_plot",
                        default_value=list(self.gpu_history),
                        height=240,
                        overlay="0%"
                    )
            
            dpg.add_spacer(height=15)
            
            # Detailed Stats (große Schrift)
            with dpg.child_window(height=-1, border=True):
                dpg.add_text("📈 DETAILED STATISTICS", color=(100, 180, 255, 255))
                dpg.bind_item_font(dpg.last_item(), self.medium_font)
                dpg.add_separator()
                dpg.add_spacer(height=10)
                dpg.add_text("", tag="detailed_stats")
    
    # ========== CHAT TAB ==========
    def _build_chat(self):
        # Chat History (große Schrift)
        with dpg.child_window(height=820, border=True):
            dpg.add_text("", tag="chat_history", wrap=-1)
        
        dpg.add_spacer(height=10)
        
        # Input (groß)
        with dpg.group(horizontal=True):
            dpg.add_input_text(
                tag="chat_input",
                width=-200,
                height=45,  # Höher
                hint="Enter command...",
                on_enter=True,
                callback=self._on_chat_send
            )
            dpg.add_button(
                label="🚀 SEND",
                width=190,
                height=45,  # Höher
                callback=self._on_chat_send
            )
    
    def _on_chat_send(self):
        text = dpg.get_value("chat_input").strip()
        if not text:
            return
        
        self.add_user_message(text)
        dpg.set_value("chat_input", "")
        
        # Process command
        if self.jarvis and hasattr(self.jarvis, 'command_processor'):
            try:
                resp = self.jarvis.command_processor.process_command(text)
                self.add_assistant_message(resp or "✅ Command executed.")
            except Exception as e:
                self.add_assistant_message(f"❌ Error: {e}")
    
    # ========== MODELS TAB ==========
    def _build_models(self):
        dpg.add_text("🧠 LLM MODEL MANAGER", color=(255, 140, 0, 255))
        dpg.bind_item_font(dpg.last_item(), self.medium_font)
        
        dpg.add_separator()
        dpg.add_spacer(height=15)
        
        with dpg.group(horizontal=True):
            dpg.add_button(label="🔄 Refresh", width=160, height=40, callback=self._refresh_models)
            dpg.add_button(label="📥 Download Model", width=180, height=40, callback=self._show_download_dialog)
            dpg.add_button(label="🔴 Unload All", width=160, height=40, callback=self._unload_models)
        
        dpg.add_spacer(height=15)
        
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="model_status", wrap=-1)
    
    def _refresh_models(self):
        if not self.jarvis or not hasattr(self.jarvis, 'get_llm_status'):
            dpg.set_value("model_status", "❌ LLM Manager not available.")
            return
        
        try:
            status = self.jarvis.get_llm_status()
            available = status.get("available", {})
            current = status.get("current")
            loaded = status.get("loaded", [])
            
            lines = ["═" * 80, ""]
            
            for key, info in available.items():
                is_current = "  🟢 ACTIVE" if key == current else ""
                is_avail = "✅" if info.get("available") else "❌"
                is_loaded = "  🔵 LOADED" if key in loaded else ""
                
                lines.append(f"{is_avail}  {key.upper()}{is_current}{is_loaded}")
                lines.append(f"     📁 File: {info.get('filename', 'N/A')}")
                lines.append(f"     📏 Size: {info.get('size_mb', 0):.1f} MB")
                lines.append("")
                lines.append("─" * 80)
                lines.append("")
            
            if not available:
                lines.append("⚠️  No models configured. Check config/models.json")
            
            dpg.set_value("model_status", "\n".join(lines))
        except Exception as e:
            dpg.set_value("model_status", f"❌ Error: {e}")
    
    def _show_download_dialog(self):
        pass
    
    def _unload_models(self):
        if self.jarvis and hasattr(self.jarvis, 'llm_manager'):
            try:
                self.jarvis.llm_manager.unload_model()
                self._refresh_models()
            except Exception as e:
                print(f"Unload error: {e}")
    
    # ========== PLUGINS TAB ==========
    def _build_plugins(self):
        dpg.add_text("🧩 PLUGIN SYSTEM", color=(255, 140, 0, 255))
        dpg.bind_item_font(dpg.last_item(), self.medium_font)
        
        dpg.add_separator()
        dpg.add_spacer(height=15)
        
        dpg.add_button(label="🔄 Refresh", width=160, height=40, callback=self._refresh_plugins)
        dpg.add_spacer(height=15)
        
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="plugin_status", wrap=-1)
    
    def _refresh_plugins(self):
        if not self.jarvis or not hasattr(self.jarvis, 'get_plugin_overview'):
            dpg.set_value("plugin_status", "❌ Plugin Manager not available.")
            return
        
        try:
            plugins = self.jarvis.get_plugin_overview()
            lines = ["═" * 80, ""]
            
            for p in plugins:
                status = "🟢 ENABLED" if p.get("enabled") else "🔴 DISABLED"
                lines.append(f"{status}  {p.get('name', 'Unknown').upper()}")
                lines.append(f"     🏷️  Type: {p.get('type', 'N/A')}")
                lines.append(f"     📝  {p.get('description', 'No description')}")
                lines.append("")
                lines.append("─" * 80)
                lines.append("")
            
            if not plugins:
                lines.append("⚠️  No plugins loaded.")
            
            dpg.set_value("plugin_status", "\n".join(lines))
        except Exception as e:
            dpg.set_value("plugin_status", f"❌ Error: {e}")
    
    # ========== MEMORY TAB ==========
    def _build_memory(self):
        dpg.add_text("🗄️ MEMORY CORE", color=(255, 140, 0, 255))
        dpg.bind_item_font(dpg.last_item(), self.medium_font)
        
        dpg.add_separator()
        dpg.add_spacer(height=15)
        
        with dpg.group(horizontal=True):
            dpg.add_button(label="🔄 Refresh", width=160, height=40, callback=self._refresh_memory)
            dpg.add_button(label="🗑️ Clear Cache", width=160, height=40, callback=self._clear_memory)
        
        dpg.add_spacer(height=15)
        
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="memory_status", wrap=-1)
    
    def _refresh_memory(self):
        dpg.set_value("memory_status", "🚧 Memory viewer under construction...")
    
    def _clear_memory(self):
        pass
    
    # ========== LOGS TAB ==========
    def _build_logs(self):
        with dpg.group(horizontal=True):
            dpg.add_button(label="🔄 Refresh", width=140, height=40, callback=self._refresh_logs)
            dpg.add_button(label="🗑️ Clear", width=140, height=40, callback=self._clear_logs)
            dpg.add_spacer(width=30)
            dpg.add_checkbox(label="Auto-scroll", tag="log_autoscroll", default_value=True)
        
        dpg.add_spacer(height=10)
        
        with dpg.child_window(height=-1, border=True):
            dpg.add_text("", tag="log_viewer", wrap=0)
    
    def _refresh_logs(self):
        try:
            log_file = Path("logs/jarvis.log")
            if log_file.exists():
                content = log_file.read_text(encoding="utf-8", errors="ignore")
                dpg.set_value("log_viewer", content[-100000:])
        except Exception as e:
            dpg.set_value("log_viewer", f"❌ Error loading logs: {e}")
    
    def _clear_logs(self):
        dpg.set_value("log_viewer", "")
    
    # ========== SETTINGS TAB ==========
    def _build_settings(self):
        dpg.add_text("⚙️ SETTINGS", color=(255, 140, 0, 255))
        dpg.bind_item_font(dpg.last_item(), self.medium_font)
        
        dpg.add_separator()
        dpg.add_spacer(height=15)
        
        with dpg.child_window(height=-1, border=True):
            # LLM Settings
            dpg.add_text("🧠 LLM Settings", color=(100, 180, 255, 255))
            dpg.add_separator()
            dpg.add_spacer(height=8)
            
            dpg.add_checkbox(label="Enable LLM", tag="setting_llm_enabled", default_value=True)
            dpg.add_slider_int(label="Context Length", tag="setting_context_length", 
                             default_value=2048, min_value=512, max_value=8192, width=400)
            dpg.add_slider_float(label="Temperature", tag="setting_temperature",
                               default_value=0.7, min_value=0.0, max_value=2.0, width=400)
            
            dpg.add_spacer(height=25)
            
            # TTS Settings
            dpg.add_text("🔊 TTS Settings", color=(100, 180, 255, 255))
            dpg.add_separator()
            dpg.add_spacer(height=8)
            
            dpg.add_checkbox(label="Enable TTS", tag="setting_tts_enabled", default_value=True)
            dpg.add_slider_int(label="Speech Rate", tag="setting_speech_rate",
                             default_value=150, min_value=50, max_value=300, width=400)
            dpg.add_slider_int(label="Volume", tag="setting_volume",
                             default_value=100, min_value=0, max_value=100, width=400)
            
            dpg.add_spacer(height=25)
            
            # Speech Recognition
            dpg.add_text("🎤 Speech Recognition", color=(100, 180, 255, 255))
            dpg.add_separator()
            dpg.add_spacer(height=8)
            
            dpg.add_checkbox(label="Enable Wake Word", tag="setting_wake_word", default_value=True)
            dpg.add_checkbox(label="Continuous Listening", tag="setting_continuous", default_value=False)
            
            dpg.add_spacer(height=25)
            
            dpg.add_button(label="💾 SAVE SETTINGS", width=250, height=50, callback=self._save_settings)
    
    def _save_settings(self):
        print("Settings saved!")
    
    # ========== BACKGROUND WORKERS ==========
    def _start_background_workers(self):
        def metrics_loop():
            while self.is_running:
                self._update_metrics()
                time.sleep(1.0)
        
        def log_loop():
            while self.is_running:
                if self.log_auto_scroll and dpg.get_value("log_autoscroll"):
                    self._refresh_logs()
                time.sleep(3.0)
        
        threading.Thread(target=metrics_loop, daemon=True).start()
        threading.Thread(target=log_loop, daemon=True).start()
    
    def _update_metrics(self):
        if not self.jarvis or not hasattr(self.jarvis, 'get_system_metrics'):
            return
        
        try:
            metrics = self.jarvis.get_system_metrics()
            summary = metrics.get("summary", {})
            
            cpu = summary.get('cpu_percent', 0)
            ram = summary.get('memory_percent', 0)
            gpu = summary.get('gpu_utilization', 0)
            
            self.cpu_history.append(cpu)
            self.ram_history.append(ram)
            self.gpu_history.append(gpu if gpu > 0 else 0)
            
            dpg.set_value("cpu_plot", list(self.cpu_history))
            dpg.configure_item("cpu_plot", overlay=f"{cpu:.1f}%")
            
            dpg.set_value("ram_plot", list(self.ram_history))
            dpg.configure_item("ram_plot", overlay=f"{ram:.1f}%")
            
            dpg.set_value("gpu_plot", list(self.gpu_history))
            dpg.configure_item("gpu_plot", overlay=f"{gpu:.1f}%" if gpu > 0 else "N/A")
            
            stats_text = f"""
🖥️  CPU: {cpu:.1f}% ({summary.get('cpu_count', 0)} cores)

💾  RAM: {ram:.1f}% ({summary.get('memory_used_gb', 0):.1f} GB / {summary.get('memory_total_gb', 0):.1f} GB)

🎮  GPU: {gpu:.1f}% ({summary.get('gpu_name', 'N/A')})

🌡️  Temperature: {summary.get('cpu_temp', 0):.1f}°C

⚡  Power: {summary.get('power_usage', 0):.1f}W
            """.strip()
            dpg.set_value("detailed_stats", stats_text)
        
        except Exception:
            pass
    
    # ========== CHAT HELPERS ==========
    def add_user_message(self, text):
        self.chat_messages.append(f"👤 USER:\n{text}")
        self._update_chat_display()
    
    def add_assistant_message(self, text):
        self.chat_messages.append(f"\n🤖 JARVIS:\n{text}")
        self._update_chat_display()
    
    def _update_chat_display(self):
        dpg.set_value("chat_history", "\n\n".join(self.chat_messages))
    
    # ========== GUI INTERFACE ==========
    def update_status(self, msg): pass
    def update_context_panels(self, **kw): pass
    def handle_knowledge_progress(self, p): pass
    def show_message(self, title, msg): print(f"{title}: {msg}")
    
    def run(self):
        dpg.show_viewport()
        dpg.set_primary_window("main", True)
        
        if self.jarvis:
            self._refresh_models()
            self._refresh_plugins()
            self._refresh_logs()
        
        while dpg.is_dearpygui_running() and self.is_running:
            fps = dpg.get_frame_rate()
            dpg.set_value("fps_display", f"FPS: {fps:.0f}")
            dpg.render_dearpygui_frame()
        
        dpg.destroy_context()


def create_jarvis_imgui_gui_full(jarvis_instance):
    return JarvisUE5ControlCenter(jarvis_instance)
