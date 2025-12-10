#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beautiful Model Manager UI for JARVIS Control Center
Modern, clean design with cards, gradients, and smooth animations
"""

import threading
from typing import Dict, Any, Optional, List

try:
    import dearpygui.dearpygui as dpg
    IMGUI_AVAILABLE = True
except ImportError:
    IMGUI_AVAILABLE = False
    dpg = None

from desktop.model_manager_extended import (
    ModelBenchmark,
    ModelDownloadManager,
    ContextWindowVisualizer,
    format_bytes,
    format_speed,
    format_eta
)


class BeautifulModelManagerUI:
    """Beautiful Model Manager UI with modern design"""
    
    # Modern Color Palette
    COLORS = {
        # Primary colors
        'primary': (88, 101, 242, 255),        # Discord Blurple
        'primary_hover': (108, 121, 255, 255),
        'success': (67, 181, 129, 255),        # Green
        'warning': (250, 166, 26, 255),        # Orange
        'danger': (237, 66, 69, 255),          # Red
        'info': (52, 152, 219, 255),           # Blue
        
        # Backgrounds
        'bg_dark': (23, 25, 35, 255),          # Dark background
        'bg_card': (32, 34, 46, 255),          # Card background
        'bg_hover': (42, 44, 56, 255),         # Hover state
        'bg_input': (28, 30, 40, 255),         # Input background
        
        # Text
        'text_primary': (255, 255, 255, 255),  # White
        'text_secondary': (180, 185, 195, 255),# Gray
        'text_muted': (120, 125, 135, 255),    # Dark gray
        
        # Accents
        'accent_purple': (139, 92, 246, 255),  # Purple
        'accent_pink': (236, 72, 153, 255),    # Pink
        'accent_cyan': (34, 211, 238, 255),    # Cyan
        'accent_gold': (251, 191, 36, 255),    # Gold
    }
    
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.benchmark = ModelBenchmark(jarvis_instance)
        self.download_manager = ModelDownloadManager(jarvis_instance)
        self.download_manager.register_callback(self._on_download_progress)
        
        self.active_download_windows: Dict[str, str] = {}
        self.model_cards: Dict[str, str] = {}
        
        # Create themes
        self._create_themes()
    
    def _create_themes(self):
        """Create modern themes for UI elements"""
        if not dpg:
            return
        
        # Primary Button Theme
        with dpg.theme(tag="theme_primary_button") as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.COLORS['primary'])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, self.COLORS['primary_hover'])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (68, 81, 222, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, self.COLORS['text_primary'])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 15, 10)
        
        # Success Button Theme
        with dpg.theme(tag="theme_success_button") as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.COLORS['success'])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (87, 201, 149, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (47, 161, 109, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, self.COLORS['text_primary'])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 15, 10)
        
        # Danger Button Theme
        with dpg.theme(tag="theme_danger_button") as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.COLORS['danger'])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 86, 89, 255))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (217, 46, 49, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, self.COLORS['text_primary'])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 15, 10)
        
        # Card Theme
        with dpg.theme(tag="theme_card") as theme:
            with dpg.theme_component(dpg.mvChildWindow):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, self.COLORS['bg_card'])
                dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 65, 80, 255))
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)
        
        # Progress Bar Themes
        with dpg.theme(tag="theme_progress_success") as theme:
            with dpg.theme_component(dpg.mvProgressBar):
                dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, self.COLORS['success'])
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, self.COLORS['bg_input'])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
        
        with dpg.theme(tag="theme_progress_warning") as theme:
            with dpg.theme_component(dpg.mvProgressBar):
                dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, self.COLORS['warning'])
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, self.COLORS['bg_input'])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
        
        with dpg.theme(tag="theme_progress_danger") as theme:
            with dpg.theme_component(dpg.mvProgressBar):
                dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, self.COLORS['danger'])
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, self.COLORS['bg_input'])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
    
    def build_ui(self, parent_tag: str):
        """Build beautiful modern UI"""
        if not dpg:
            return
        
        with dpg.child_window(parent=parent_tag, height=-1, tag="beautiful_model_manager"):
            # Header with gradient effect
            self._build_header()
            
            dpg.add_spacer(height=25)
            
            # Action bar with modern buttons
            self._build_action_bar()
            
            dpg.add_spacer(height=25)
            
            # Model cards container
            with dpg.child_window(height=-1, border=False, tag="model_cards_container"):
                dpg.add_text("", tag="model_cards_content")
    
    def _build_header(self):
        """Build modern header with gradient"""
        with dpg.group(horizontal=True):
            # Icon and title
            dpg.add_text("🧠", color=self.COLORS['accent_purple'])
            dpg.bind_item_font(dpg.last_item(), "large_font" if dpg.does_item_exist("large_font") else None)
            
            dpg.add_spacer(width=10)
            
            with dpg.group():
                dpg.add_text("Model Manager", color=self.COLORS['text_primary'])
                dpg.bind_item_font(dpg.last_item(), "large_font" if dpg.does_item_exist("large_font") else None)
                
                dpg.add_text("Manage, benchmark, and compare AI models", color=self.COLORS['text_secondary'])
    
    def _build_action_bar(self):
        """Build action bar with styled buttons"""
        with dpg.group(horizontal=True):
            # Refresh button
            btn = dpg.add_button(
                label="  🔄  Refresh",
                width=130,
                height=45,
                callback=self._refresh_models
            )
            dpg.bind_item_theme(btn, "theme_primary_button")
            
            dpg.add_spacer(width=10)
            
            # Download button
            btn = dpg.add_button(
                label="  📥  Download",
                width=140,
                height=45,
                callback=self._show_download_dialog
            )
            dpg.bind_item_theme(btn, "theme_success_button")
            
            dpg.add_spacer(width=10)
            
            # Benchmark button
            btn = dpg.add_button(
                label="  ⚡  Benchmark",
                width=150,
                height=45,
                callback=self._show_benchmark_dialog
            )
            dpg.bind_item_theme(btn, "theme_primary_button")
            
            dpg.add_spacer(width=10)
            
            # Compare button
            btn = dpg.add_button(
                label="  🔍  Compare",
                width=130,
                height=45,
                callback=self._show_comparison_dialog
            )
            dpg.bind_item_theme(btn, "theme_primary_button")
            
            dpg.add_spacer(width=10)
            
            # Unload button
            btn = dpg.add_button(
                label="  🔴  Unload All",
                width=150,
                height=45,
                callback=self._unload_all_models
            )
            dpg.bind_item_theme(btn, "theme_danger_button")
    
    def _refresh_models(self):
        """Refresh and display models as beautiful cards"""
        if not self.jarvis or not hasattr(self.jarvis, 'llm_manager'):
            return
        
        try:
            # Clear existing cards
            if dpg.does_item_exist("model_cards_content"):
                dpg.delete_item("model_cards_content", children_only=True)
            
            overview = self.jarvis.llm_manager.get_model_overview()
            status = self.jarvis.get_llm_status()
            current = status.get("current")
            loaded = status.get("loaded", [])
            
            parent = "model_cards_content"
            
            # Create card for each model
            for idx, (key, info) in enumerate(overview.items()):
                self._create_model_card(parent, key, info, current, loaded)
                if idx < len(overview) - 1:
                    dpg.add_spacer(height=20, parent=parent)
            
        except Exception as e:
            dpg.add_text(f"❌ Error loading models: {e}", parent="model_cards_content", color=self.COLORS['danger'])
    
    def _create_model_card(self, parent: str, model_key: str, info: dict, current: str, loaded: list):
        """Create a beautiful card for a model"""
        card_tag = f"model_card_{model_key}"
        
        # Determine accent color based on model
        accent_colors = {
            'llama3': self.COLORS['accent_purple'],
            'mistral': self.COLORS['accent_cyan'],
            'deepseek': self.COLORS['accent_pink']
        }
        accent = accent_colors.get(model_key, self.COLORS['accent_gold'])
        
        with dpg.child_window(
            parent=parent,
            height=280,
            border=True,
            tag=card_tag
        ):
            dpg.bind_item_theme(card_tag, "theme_card")
            
            # Card header with status badges
            with dpg.group(horizontal=True):
                # Model icon and name
                dpg.add_text("🤖", color=accent)
                dpg.add_spacer(width=8)
                dpg.add_text(key.upper(), color=self.COLORS['text_primary'])
                
                dpg.add_spacer(width=15)
                
                # Status badges
                if key == current:
                    self._create_badge("🟢 ACTIVE", self.COLORS['success'])
                    dpg.add_spacer(width=5)
                
                if key in loaded:
                    self._create_badge("🔵 LOADED", self.COLORS['info'])
                    dpg.add_spacer(width=5)
                
                if not info.get('downloaded'):
                    self._create_badge("📥 NOT DOWNLOADED", self.COLORS['warning'])
            
            dpg.add_spacer(height=12)
            dpg.add_separator()
            dpg.add_spacer(height=12)
            
            # Model info
            with dpg.group():
                # Display name
                dpg.add_text(info.get('display_name', 'Unknown'), color=self.COLORS['text_secondary'])
                dpg.add_spacer(height=5)
                
                # Description
                dpg.add_text(
                    info.get('description', 'No description')[:80] + "...",
                    color=self.COLORS['text_muted'],
                    wrap=700
                )
                dpg.add_spacer(height=12)
                
                # Specs in grid
                with dpg.group(horizontal=True):
                    # Column 1
                    with dpg.group():
                        dpg.add_text("📊 Context:", color=self.COLORS['text_muted'])
                        dpg.add_text(f"{info.get('context_length', 2048)} tokens", color=self.COLORS['text_secondary'])
                    
                    dpg.add_spacer(width=40)
                    
                    # Column 2
                    with dpg.group():
                        dpg.add_text("💾 Size:", color=self.COLORS['text_muted'])
                        if info.get('downloaded'):
                            dpg.add_text(info.get('size_human', 'Unknown'), color=self.COLORS['text_secondary'])
                        else:
                            dpg.add_text(f"{info.get('size_gb', 0):.1f} GB", color=self.COLORS['text_secondary'])
                    
                    dpg.add_spacer(width=40)
                    
                    # Column 3 - Performance
                    latest = self.benchmark.get_latest_result(model_key)
                    if latest:
                        with dpg.group():
                            dpg.add_text("⚡ Performance:", color=self.COLORS['text_muted'])
                            dpg.add_text(
                                f"{latest.tokens_per_second:.1f} tok/s",
                                color=self.COLORS['success']
                            )
            
            dpg.add_spacer(height=15)
            
            # Action buttons
            with dpg.group(horizontal=True):
                if info.get('downloaded') and info.get('ready'):
                    if key in loaded:
                        btn = dpg.add_button(
                            label="Unload",
                            width=90,
                            height=35,
                            callback=lambda: self._unload_model(model_key)
                        )
                    else:
                        btn = dpg.add_button(
                            label="Load",
                            width=90,
                            height=35,
                            callback=lambda: self._load_model(model_key)
                        )
                        dpg.bind_item_theme(btn, "theme_success_button")
                    
                    dpg.add_spacer(width=8)
                    
                    btn = dpg.add_button(
                        label="⚡ Benchmark",
                        width=120,
                        height=35,
                        callback=lambda s, a, u: self._run_benchmark(u),
                        user_data=model_key
                    )
                    dpg.bind_item_theme(btn, "theme_primary_button")
                    
                else:
                    btn = dpg.add_button(
                        label="📥 Download",
                        width=130,
                        height=35,
                        callback=lambda: self._start_download(model_key)
                    )
                    dpg.bind_item_theme(btn, "theme_success_button")
    
    def _create_badge(self, text: str, color: tuple):
        """Create a status badge"""
        with dpg.child_window(width=110, height=22, border=False):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (*color[:3], 40))
            dpg.add_text(text, color=color)
    
    def _load_model(self, model_key: str):
        """Load model"""
        if self.jarvis and hasattr(self.jarvis, 'llm_manager'):
            def load_thread():
                self.jarvis.llm_manager.load_model(model_key)
                self._refresh_models()
            threading.Thread(target=load_thread, daemon=True).start()
    
    def _unload_model(self, model_key: str):
        """Unload specific model"""
        if self.jarvis and hasattr(self.jarvis, 'llm_manager'):
            self.jarvis.llm_manager._unload_model(model_key)
            self._refresh_models()
    
    def _show_download_dialog(self):
        """Show beautiful download dialog"""
        if not dpg:
            return
        
        try:
            overview = self.jarvis.llm_manager.get_model_overview()
            not_downloaded = {
                key: info for key, info in overview.items()
                if not info.get('downloaded')
            }
            
            if not not_downloaded:
                self._show_notification("All models downloaded! 🎉", "success")
                return
            
        except Exception as e:
            self._show_notification(f"Error: {e}", "error")
            return
        
        # Create modern dialog
        with dpg.window(
            label="Download Models",
            modal=True,
            tag="download_dialog_beautiful",
            width=800,
            height=600,
            pos=[560, 240]
        ):
            dpg.add_text("Select a model to download:", color=self.COLORS['text_primary'])
            dpg.add_spacer(height=15)
            
            for key, info in not_downloaded.items():
                with dpg.child_window(height=140, border=True):
                    dpg.bind_item_theme(dpg.last_item(), "theme_card")
                    
                    with dpg.group(horizontal=True):
                        dpg.add_text("🤖", color=self.COLORS['accent_purple'])
                        dpg.add_spacer(width=10)
                        dpg.add_text(key.upper(), color=self.COLORS['text_primary'])
                    
                    dpg.add_spacer(height=8)
                    dpg.add_text(info.get('display_name', 'Unknown'), color=self.COLORS['text_secondary'])
                    dpg.add_text(info.get('description', '')[:100], color=self.COLORS['text_muted'], wrap=730)
                    
                    dpg.add_spacer(height=10)
                    
                    with dpg.group(horizontal=True):
                        dpg.add_text(f"Size: {info.get('size_gb', 0):.1f} GB", color=self.COLORS['text_secondary'])
                        dpg.add_spacer(width=30)
                        dpg.add_text(f"Context: {info.get('context_length', 2048)} tokens", color=self.COLORS['text_secondary'])
                        
                        # Spacer to push button right
                        dpg.add_spacer(width=200)
                        
                        btn = dpg.add_button(
                            label=f"  📥  Download  ",
                            callback=lambda s, a, u: self._start_download_and_close(u),
                            user_data=key,
                            height=35
                        )
                        dpg.bind_item_theme(btn, "theme_success_button")
                
                dpg.add_spacer(height=10)
            
            dpg.add_spacer(height=10)
            dpg.add_button(
                label="Close",
                width=-1,
                callback=lambda: dpg.delete_item("download_dialog_beautiful")
            )
    
    def _start_download_and_close(self, model_key: str):
        """Start download and close dialog"""
        if dpg.does_item_exist("download_dialog_beautiful"):
            dpg.delete_item("download_dialog_beautiful")
        self._start_download(model_key)
    
    def _start_download(self, model_key: str):
        """Start download with beautiful progress window"""
        self._create_download_progress_window(model_key)
        
        def download_thread():
            self.download_manager.download_model(model_key)
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _create_download_progress_window(self, model_key: str):
        """Create beautiful download progress window"""
        if not dpg:
            return
        
        window_tag = f"download_progress_{model_key}"
        
        if dpg.does_item_exist(window_tag):
            return
        
        with dpg.window(
            label=f"Downloading {model_key.upper()}",
            tag=window_tag,
            width=650,
            height=320,
            pos=[635, 380],
            no_collapse=True
        ):
            # Header
            with dpg.group(horizontal=True):
                dpg.add_text("📥", color=self.COLORS['accent_cyan'])
                dpg.add_spacer(width=10)
                dpg.add_text(f"Downloading {model_key.upper()}", color=self.COLORS['text_primary'], tag=f"{window_tag}_title")
            
            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=15)
            
            # Status
            dpg.add_text("Status: Initializing...", tag=f"{window_tag}_status", color=self.COLORS['text_secondary'])
            dpg.add_spacer(height=15)
            
            # Progress bar with theme
            progress = dpg.add_progress_bar(
                default_value=0,
                tag=f"{window_tag}_progress",
                width=-1,
                height=40,
                overlay="0%"
            )
            dpg.bind_item_theme(progress, "theme_progress_success")
            
            dpg.add_spacer(height=20)
            
            # Stats
            with dpg.child_window(height=80, border=True):
                dpg.bind_item_theme(dpg.last_item(), "theme_card")
                
                with dpg.group(horizontal=True):
                    # Downloaded
                    with dpg.group():
                        dpg.add_text("Downloaded", color=self.COLORS['text_muted'])
                        dpg.add_text("0 B", tag=f"{window_tag}_downloaded", color=self.COLORS['text_primary'])
                    
                    dpg.add_spacer(width=50)
                    
                    # Total
                    with dpg.group():
                        dpg.add_text("Total", color=self.COLORS['text_muted'])
                        dpg.add_text("0 B", tag=f"{window_tag}_total", color=self.COLORS['text_primary'])
                    
                    dpg.add_spacer(width=50)
                    
                    # Speed
                    with dpg.group():
                        dpg.add_text("Speed", color=self.COLORS['text_muted'])
                        dpg.add_text("N/A", tag=f"{window_tag}_speed", color=self.COLORS['info'])
                    
                    dpg.add_spacer(width=50)
                    
                    # ETA
                    with dpg.group():
                        dpg.add_text("ETA", color=self.COLORS['text_muted'])
                        dpg.add_text("N/A", tag=f"{window_tag}_eta", color=self.COLORS['warning'])
            
            dpg.add_spacer(height=15)
            
            # Close button
            btn = dpg.add_button(
                label="Close",
                tag=f"{window_tag}_close_btn",
                width=-1,
                height=40,
                enabled=False,
                callback=lambda: dpg.delete_item(window_tag)
            )
        
        self.active_download_windows[model_key] = window_tag
    
    def _on_download_progress(self, progress):
        """Handle download progress with beautiful updates"""
        if not dpg:
            return
        
        model_key = progress.model
        window_tag = self.active_download_windows.get(model_key)
        
        if not window_tag or not dpg.does_item_exist(window_tag):
            return
        
        # Update progress bar
        if progress.percent is not None:
            dpg.set_value(f"{window_tag}_progress", progress.percent / 100)
            dpg.configure_item(f"{window_tag}_progress", overlay=f"{progress.percent:.1f}%")
            
            # Change color based on progress
            if progress.percent < 33:
                dpg.bind_item_theme(f"{window_tag}_progress", "theme_progress_danger")
            elif progress.percent < 66:
                dpg.bind_item_theme(f"{window_tag}_progress", "theme_progress_warning")
            else:
                dpg.bind_item_theme(f"{window_tag}_progress", "theme_progress_success")
        
        # Update status
        status_map = {
            'in_progress': '⏳ Downloading...',
            'completed': '✅ Complete!',
            'failed': '❌ Failed',
            'error': '❌ Error',
            'already_exists': '✅ Already exists'
        }
        status_text = status_map.get(progress.status, progress.status.title())
        if progress.message:
            status_text += f" - {progress.message}"
        dpg.set_value(f"{window_tag}_status", f"Status: {status_text}")
        
        # Update stats
        dpg.set_value(f"{window_tag}_downloaded", format_bytes(progress.downloaded))
        dpg.set_value(f"{window_tag}_total", format_bytes(progress.total))
        dpg.set_value(f"{window_tag}_speed", format_speed(progress.speed))
        dpg.set_value(f"{window_tag}_eta", format_eta(progress.eta))
        
        # Enable close when done
        if progress.status in ('completed', 'failed', 'error', 'already_exists'):
            dpg.configure_item(f"{window_tag}_close_btn", enabled=True)
            
            if progress.status in ('completed', 'already_exists'):
                self._refresh_models()
    
    def _show_benchmark_dialog(self):
        """Show benchmark dialog"""
        # Implementation similar to model_manager_ui.py but with beautiful styling
        pass
    
    def _run_benchmark(self, model_key: str):
        """Run benchmark"""
        self._show_notification(f"Benchmarking {model_key.upper()}...", "info")
        
        def benchmark_thread():
            result = self.benchmark.run_benchmark(model_key)
            if result:
                self._show_notification(f"Benchmark complete: {result.tokens_per_second:.1f} tok/s", "success")
            else:
                self._show_notification("Benchmark failed!", "error")
            self._refresh_models()
        
        threading.Thread(target=benchmark_thread, daemon=True).start()
    
    def _show_comparison_dialog(self):
        """Show comparison dialog"""
        # Implementation with beautiful table
        pass
    
    def _unload_all_models(self):
        """Unload all models"""
        if self.jarvis and hasattr(self.jarvis, 'llm_manager'):
            self.jarvis.llm_manager.unload_model()
            self._refresh_models()
            self._show_notification("All models unloaded", "success")
    
    def _show_notification(self, message: str, type: str = "info"):
        """Show notification popup"""
        if not dpg:
            return
        
        color_map = {
            'success': self.COLORS['success'],
            'error': self.COLORS['danger'],
            'warning': self.COLORS['warning'],
            'info': self.COLORS['info']
        }
        
        with dpg.window(
            label="Notification",
            modal=True,
            width=400,
            height=150,
            pos=[760, 465],
            no_resize=True
        ):
            dpg.add_text(message, color=color_map.get(type, self.COLORS['text_primary']), wrap=380)
            dpg.add_spacer(height=15)
            btn = dpg.add_button(
                label="OK",
                width=-1,
                height=40,
                callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.last_item()))
            )
            dpg.bind_item_theme(btn, "theme_primary_button")
