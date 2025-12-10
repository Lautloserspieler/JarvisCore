#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extended Model Manager UI for JARVIS Control Center
Integrates download progress, benchmarking, and model comparison
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


class ExtendedModelManagerUI:
    """Extended Model Manager UI with all advanced features"""
    
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.benchmark = ModelBenchmark(jarvis_instance)
        self.download_manager = ModelDownloadManager(jarvis_instance)
        self.download_manager.register_callback(self._on_download_progress)
        
        self.active_download_windows: Dict[str, str] = {}
        self.comparison_window_open = False
    
    def build_ui(self, parent_tag: str):
        """Build complete extended model manager UI"""
        if not dpg:
            return
        
        with dpg.child_window(parent=parent_tag, height=-1, tag="model_manager_container"):
            # Header
            dpg.add_text("🧠 ENHANCED MODEL MANAGER", color=(255, 140, 0, 255))
            dpg.add_separator()
            dpg.add_spacer(height=15)
            
            # Action buttons row
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔄 Refresh",
                    width=120,
                    height=40,
                    callback=self._refresh_models
                )
                dpg.add_button(
                    label="📥 Download",
                    width=120,
                    height=40,
                    callback=self._show_download_dialog
                )
                dpg.add_button(
                    label="⚡ Benchmark",
                    width=130,
                    height=40,
                    callback=self._show_benchmark_dialog
                )
                dpg.add_button(
                    label="🔍 Compare",
                    width=120,
                    height=40,
                    callback=self._show_comparison_dialog
                )
                dpg.add_button(
                    label="🔴 Unload All",
                    width=130,
                    height=40,
                    callback=self._unload_all_models
                )
            
            dpg.add_spacer(height=15)
            
            # Model list area
            with dpg.child_window(height=-1, border=True, tag="enhanced_model_list"):
                dpg.add_text("", tag="enhanced_model_status", wrap=-1)
    
    def _refresh_models(self):
        """Refresh model list with enhanced information"""
        if not self.jarvis or not hasattr(self.jarvis, 'llm_manager'):
            dpg.set_value("enhanced_model_status", "❌ LLM Manager not available")
            return
        
        try:
            overview = self.jarvis.llm_manager.get_model_overview()
            status = self.jarvis.get_llm_status()
            current = status.get("current")
            loaded = status.get("loaded", [])
            
            lines = ["═" * 120, ""]
            
            for key, info in overview.items():
                # Status indicators
                is_ready = "✅" if info.get("ready") else "❌"
                is_current = "  🟢 ACTIVE" if key == current else ""
                is_loaded = "  🔵 LOADED" if key in loaded else ""
                
                lines.append(f"{is_ready}  {key.upper()}{is_current}{is_loaded}")
                lines.append(f"     📝 {info.get('display_name', 'Unknown')}")
                lines.append(f"     💬 {info.get('description', 'No description')}")
                
                # File and size info
                if info.get("downloaded"):
                    size_human = info.get('size_human', 'Unknown')
                    lines.append(f"     📁 {info.get('filename', 'N/A')} ({size_human})")
                else:
                    lines.append(f"     📁 Not downloaded - {info.get('size_gb', 0):.1f} GB required")
                
                # Context window
                context_len = info.get('context_length', 2048)
                lines.append(f"     📊 Context Window: {context_len} tokens")
                
                # Benchmark results
                latest_benchmark = self.benchmark.get_latest_result(key)
                if latest_benchmark:
                    lines.append(f"     ⚡ Latest Benchmark:")
                    lines.append(f"        • {latest_benchmark.tokens_per_second:.1f} tokens/sec")
                    lines.append(f"        • {latest_benchmark.inference_time:.0f} ms inference time")
                    lines.append(f"        • {latest_benchmark.memory_usage_mb:.1f} MB memory")
                else:
                    avg_perf = self.benchmark.get_average_performance(key)
                    if avg_perf:
                        lines.append(f"     ⚡ Average Performance: {avg_perf['avg_tokens_per_second']:.1f} tokens/sec")
                
                # GPU info for loaded models
                if key in loaded:
                    metadata = self.jarvis.llm_manager.model_metadata.get(key, {})
                    gpu_layers = metadata.get('gpu_layers', 0)
                    if gpu_layers > 0:
                        lines.append(f"     🎮 GPU Acceleration: {gpu_layers} layers")
                    else:
                        lines.append(f"     🖥️  CPU Only")
                    
                    load_time = metadata.get('load_duration', 0)
                    if load_time:
                        lines.append(f"     ⏱️  Load Time: {load_time:.1f}s")
                
                # Action buttons placeholder
                lines.append(f"     [Load] [Unload] [Benchmark] [Download]")
                
                lines.append("")
                lines.append("─" * 120)
                lines.append("")
            
            if not overview:
                lines.append("⚠️  No models configured")
            
            dpg.set_value("enhanced_model_status", "\n".join(lines))
            
        except Exception as e:
            dpg.set_value("enhanced_model_status", f"❌ Error: {e}")
    
    def _show_download_dialog(self):
        """Show model download selection dialog"""
        if not dpg:
            return
        
        try:
            overview = self.jarvis.llm_manager.get_model_overview()
            not_downloaded = {
                key: info for key, info in overview.items()
                if not info.get('downloaded')
            }
            
            if not not_downloaded:
                self._show_popup("Info", "All models are already downloaded!")
                return
            
        except Exception as e:
            self._show_popup("Error", f"Failed to get model list: {e}")
            return
        
        with dpg.window(
            label="📥 Download Model",
            modal=True,
            tag="enhanced_download_dialog",
            width=700,
            height=500,
            pos=[610, 290]
        ):
            dpg.add_text("Select a model to download:", color=(255, 140, 0, 255))
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            for key, info in not_downloaded.items():
                with dpg.child_window(height=120, border=True):
                    with dpg.group(horizontal=True):
                        dpg.add_text(f"📦 {key.upper()}", color=(100, 180, 255, 255))
                        dpg.add_spacer(width=20)
                        dpg.add_button(
                            label=f"📥 Download ({info.get('size_gb', 0):.1f} GB)",
                            callback=lambda s, a, u: self._start_download(u),
                            user_data=key
                        )
                    
                    dpg.add_text(f"{info.get('display_name', 'Unknown')}")
                    dpg.add_text(f"💬 {info.get('description', '')}", wrap=650)
                    dpg.add_text(f"📊 Context: {info.get('context_length', 2048)} tokens")
                
                dpg.add_spacer(height=5)
            
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            dpg.add_button(
                label="Close",
                width=-1,
                callback=lambda: dpg.delete_item("enhanced_download_dialog")
            )
    
    def _start_download(self, model_key: str):
        """Start model download"""
        if dpg.does_item_exist("enhanced_download_dialog"):
            dpg.delete_item("enhanced_download_dialog")
        
        self._create_download_progress_window(model_key)
        
        def download_thread():
            self.download_manager.download_model(model_key)
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _create_download_progress_window(self, model_key: str):
        """Create download progress tracking window"""
        if not dpg:
            return
        
        window_tag = f"download_progress_{model_key}"
        
        if dpg.does_item_exist(window_tag):
            return
        
        with dpg.window(
            label=f"Downloading {model_key.upper()}",
            tag=window_tag,
            width=600,
            height=280,
            pos=[660, 400],
            no_collapse=True
        ):
            dpg.add_text(f"Model: {model_key.upper()}", color=(255, 140, 0, 255), tag=f"{window_tag}_model")
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            dpg.add_text("Status: Initializing...", tag=f"{window_tag}_status")
            dpg.add_spacer(height=10)
            
            dpg.add_progress_bar(
                default_value=0,
                tag=f"{window_tag}_progress",
                width=-1,
                height=35,
                overlay="0%"
            )
            dpg.add_spacer(height=15)
            
            with dpg.group(horizontal=True):
                dpg.add_text("Downloaded:", color=(180, 180, 180, 255))
                dpg.add_text("0 B", tag=f"{window_tag}_downloaded")
                dpg.add_text(" / ", color=(180, 180, 180, 255))
                dpg.add_text("0 B", tag=f"{window_tag}_total")
            
            dpg.add_spacer(height=8)
            
            with dpg.group(horizontal=True):
                dpg.add_text("Speed:", color=(180, 180, 180, 255))
                dpg.add_text("N/A", tag=f"{window_tag}_speed")
                dpg.add_spacer(width=80)
                dpg.add_text("ETA:", color=(180, 180, 180, 255))
                dpg.add_text("N/A", tag=f"{window_tag}_eta")
            
            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            dpg.add_button(
                label="Close",
                tag=f"{window_tag}_close_btn",
                width=-1,
                enabled=False,
                callback=lambda: dpg.delete_item(window_tag)
            )
        
        self.active_download_windows[model_key] = window_tag
    
    def _on_download_progress(self, progress):
        """Handle download progress updates"""
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
        
        # Update status
        status_map = {
            'in_progress': 'Downloading',
            'completed': '✅ Complete',
            'failed': '❌ Failed',
            'error': '❌ Error',
            'already_exists': '✅ Already exists'
        }
        status_text = status_map.get(progress.status, progress.status.replace('_', ' ').title())
        if progress.message:
            status_text += f" - {progress.message}"
        dpg.set_value(f"{window_tag}_status", f"Status: {status_text}")
        
        # Update sizes
        dpg.set_value(f"{window_tag}_downloaded", format_bytes(progress.downloaded))
        dpg.set_value(f"{window_tag}_total", format_bytes(progress.total))
        
        # Update speed and ETA
        dpg.set_value(f"{window_tag}_speed", format_speed(progress.speed))
        dpg.set_value(f"{window_tag}_eta", format_eta(progress.eta))
        
        # Enable close button when finished
        if progress.status in ('completed', 'failed', 'error', 'already_exists'):
            dpg.configure_item(f"{window_tag}_close_btn", enabled=True)
            
            # Auto-refresh model list
            if progress.status in ('completed', 'already_exists'):
                self._refresh_models()
    
    def _show_benchmark_dialog(self):
        """Show benchmark selection dialog"""
        if not dpg:
            return
        
        try:
            status = self.jarvis.get_llm_status()
            loaded = status.get("loaded", [])
            ready_models = status.get("ready_models", [])
            
            if not ready_models:
                self._show_popup("Info", "No models available for benchmarking!\nDownload and load a model first.")
                return
            
        except Exception as e:
            self._show_popup("Error", f"Failed to get model list: {e}")
            return
        
        with dpg.window(
            label="⚡ Run Benchmark",
            modal=True,
            tag="benchmark_dialog",
            width=550,
            height=400,
            pos=[685, 340]
        ):
            dpg.add_text("Select models to benchmark:", color=(255, 140, 0, 255))
            dpg.add_text("(Models will be loaded automatically if needed)", color=(180, 180, 180, 255))
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            for model_key in ready_models:
                is_loaded = " (Loaded)" if model_key in loaded else ""
                dpg.add_button(
                    label=f"⚡ Benchmark {model_key.upper()}{is_loaded}",
                    width=-1,
                    height=40,
                    callback=lambda s, a, u: self._run_benchmark(u),
                    user_data=model_key
                )
                dpg.add_spacer(height=5)
            
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Benchmark All",
                    width=260,
                    callback=lambda: self._benchmark_all(ready_models)
                )
                dpg.add_button(
                    label="Cancel",
                    width=260,
                    callback=lambda: dpg.delete_item("benchmark_dialog")
                )
    
    def _run_benchmark(self, model_key: str):
        """Run benchmark for single model"""
        if dpg.does_item_exist("benchmark_dialog"):
            dpg.delete_item("benchmark_dialog")
        
        self._show_popup("Benchmark", f"Running benchmark for {model_key.upper()}...\nThis may take 30-60 seconds.")
        
        def benchmark_thread():
            result = self.benchmark.run_benchmark(model_key)
            
            if result:
                self._show_benchmark_result(result)
            else:
                self._show_popup("Error", f"Benchmark failed for {model_key}!")
            
            self._refresh_models()
        
        threading.Thread(target=benchmark_thread, daemon=True).start()
    
    def _benchmark_all(self, model_keys: List[str]):
        """Run benchmark for all models"""
        if dpg.does_item_exist("benchmark_dialog"):
            dpg.delete_item("benchmark_dialog")
        
        self._show_popup(
            "Benchmark All",
            f"Benchmarking {len(model_keys)} models...\nThis will take several minutes.\nPlease wait."
        )
        
        def benchmark_all_thread():
            results = []
            for model_key in model_keys:
                result = self.benchmark.run_benchmark(model_key)
                if result:
                    results.append(result)
            
            if results:
                self._show_comparison_results(results)
            
            self._refresh_models()
        
        threading.Thread(target=benchmark_all_thread, daemon=True).start()
    
    def _show_benchmark_result(self, result):
        """Display benchmark result in popup window"""
        if not dpg:
            return
        
        with dpg.window(
            label=f"Benchmark: {result.model_key.upper()}",
            width=600,
            height=500,
            pos=[660, 290]
        ):
            dpg.add_text(f"🧠 {result.model_key.upper()}", color=(255, 140, 0, 255))
            dpg.add_separator()
            dpg.add_spacer(height=15)
            
            # Performance metrics
            dpg.add_text("⚡ Performance Metrics:", color=(100, 180, 255, 255))
            dpg.add_spacer(height=5)
            dpg.add_text(f"   Tokens/Second: {result.tokens_per_second:.2f}")
            dpg.add_text(f"   Inference Time: {result.inference_time:.1f} ms")
            dpg.add_text(f"   Memory Usage: {result.memory_usage_mb:.1f} MB")
            
            dpg.add_spacer(height=15)
            
            # Token metrics
            dpg.add_text("📊 Token Metrics:", color=(100, 180, 255, 255))
            dpg.add_spacer(height=5)
            dpg.add_text(f"   Prompt Tokens: {result.prompt_tokens}")
            dpg.add_text(f"   Completion Tokens: {result.completion_tokens}")
            dpg.add_text(f"   Total Tokens: {result.prompt_tokens + result.completion_tokens}")
            
            dpg.add_spacer(height=15)
            
            # Context usage
            dpg.add_text("📏 Context Window Usage:", color=(100, 180, 255, 255))
            dpg.add_spacer(height=5)
            dpg.add_text(f"   Used: {result.context_used} tokens")
            dpg.add_text(f"   Available: {result.context_available} tokens")
            
            ContextWindowVisualizer.create_visualization(
                result.context_used,
                result.context_available,
                dpg.last_container()
            )
            
            dpg.add_spacer(height=15)
            
            # Timestamp
            dpg.add_text(f"🕐 {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", color=(180, 180, 180, 255))
            
            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            dpg.add_button(
                label="Close",
                width=-1,
                callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.last_item()))
            )
    
    def _show_comparison_dialog(self):
        """Show model comparison selection dialog"""
        if not dpg:
            return
        
        # Get models with benchmark results
        models_with_results = [
            key for key in self.benchmark.results.keys()
            if self.benchmark.get_latest_result(key) is not None
        ]
        
        if len(models_with_results) < 2:
            self._show_popup(
                "Info",
                "At least 2 models need benchmark results for comparison!\nRun benchmarks first."
            )
            return
        
        results = [self.benchmark.get_latest_result(key) for key in models_with_results]
        self._show_comparison_results(results)
    
    def _show_comparison_results(self, results: List):
        """Show model comparison table"""
        if not dpg or not results:
            return
        
        if self.comparison_window_open:
            return
        
        self.comparison_window_open = True
        
        with dpg.window(
            label="🔍 Model Comparison",
            width=900,
            height=600,
            pos=[510, 240],
            on_close=lambda: setattr(self, 'comparison_window_open', False)
        ):
            dpg.add_text("📊 Performance Comparison", color=(255, 140, 0, 255))
            dpg.add_separator()
            dpg.add_spacer(height=15)
            
            # Comparison table
            with dpg.table(
                header_row=True,
                borders_innerH=True,
                borders_outerH=True,
                borders_innerV=True,
                borders_outerV=True,
                row_background=True
            ):
                # Headers
                dpg.add_table_column(label="Model")
                dpg.add_table_column(label="Tokens/Sec")
                dpg.add_table_column(label="Inference (ms)")
                dpg.add_table_column(label="Memory (MB)")
                dpg.add_table_column(label="Context Used")
                dpg.add_table_column(label="Timestamp")
                
                # Rows
                for result in sorted(results, key=lambda r: r.tokens_per_second, reverse=True):
                    with dpg.table_row():
                        dpg.add_text(result.model_key.upper())
                        dpg.add_text(f"{result.tokens_per_second:.2f}")
                        dpg.add_text(f"{result.inference_time:.1f}")
                        dpg.add_text(f"{result.memory_usage_mb:.1f}")
                        dpg.add_text(f"{result.context_used}/{result.context_available}")
                        dpg.add_text(result.timestamp.strftime('%H:%M:%S'))
            
            dpg.add_spacer(height=15)
            
            # Winner callout
            fastest = max(results, key=lambda r: r.tokens_per_second)
            dpg.add_text(
                f"🏆 Fastest: {fastest.model_key.upper()} ({fastest.tokens_per_second:.2f} tokens/sec)",
                color=(100, 255, 100, 255)
            )
            
            most_efficient = min(results, key=lambda r: r.memory_usage_mb)
            dpg.add_text(
                f"💾 Most Efficient: {most_efficient.model_key.upper()} ({most_efficient.memory_usage_mb:.1f} MB)",
                color=(100, 180, 255, 255)
            )
    
    def _unload_all_models(self):
        """Unload all loaded models"""
        if self.jarvis and hasattr(self.jarvis, 'llm_manager'):
            try:
                self.jarvis.llm_manager.unload_model()
                self._refresh_models()
                self._show_popup("Success", "All models unloaded successfully!")
            except Exception as e:
                self._show_popup("Error", f"Failed to unload models: {e}")
    
    def _show_popup(self, title: str, message: str):
        """Show simple popup message"""
        if not dpg:
            return
        
        with dpg.window(
            label=title,
            modal=True,
            width=400,
            height=150,
            pos=[760, 465],
            no_resize=True
        ):
            dpg.add_text(message, wrap=380)
            dpg.add_spacer(height=10)
            dpg.add_separator()
            dpg.add_spacer(height=10)
            dpg.add_button(
                label="OK",
                width=-1,
                callback=lambda: dpg.delete_item(dpg.get_item_parent(dpg.last_item()))
            )
