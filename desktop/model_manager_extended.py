#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extended Model Manager for JARVIS Control Center
Provides model download progress, benchmarking, comparison, and context visualization
"""

import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
import json

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    dpg = None


@dataclass
class DownloadProgress:
    """Download progress tracking"""
    model: str
    status: str
    downloaded: int
    total: int
    percent: Optional[float]
    speed: Optional[float]  # bytes per second
    eta: Optional[float]  # seconds
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkResult:
    """Model benchmark results"""
    model_key: str
    tokens_per_second: float
    inference_time: float  # ms
    context_used: int
    context_available: int
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int
    memory_usage_mb: float
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ModelBenchmark:
    """Handles model benchmarking"""
    
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.logger = jarvis_instance.logger if jarvis_instance else None
        self.results: Dict[str, List[BenchmarkResult]] = {}
        self.results_file = Path("data/model_benchmarks.json")
        self._load_results()
    
    def _load_results(self):
        """Load previous benchmark results"""
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for model_key, results in data.items():
                        self.results[model_key] = [
                            BenchmarkResult(
                                model_key=r['model_key'],
                                tokens_per_second=r['tokens_per_second'],
                                inference_time=r['inference_time'],
                                context_used=r['context_used'],
                                context_available=r['context_available'],
                                timestamp=datetime.fromisoformat(r['timestamp']),
                                prompt_tokens=r['prompt_tokens'],
                                completion_tokens=r['completion_tokens'],
                                memory_usage_mb=r['memory_usage_mb']
                            )
                            for r in results
                        ]
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to load benchmark results: {e}")
    
    def _save_results(self):
        """Save benchmark results"""
        try:
            self.results_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                model_key: [r.to_dict() for r in results]
                for model_key, results in self.results.items()
            }
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to save benchmark results: {e}")
    
    def run_benchmark(self, model_key: str, progress_callback: Optional[Callable] = None) -> Optional[BenchmarkResult]:
        """Run benchmark on specified model"""
        if not self.jarvis or not hasattr(self.jarvis, 'llm_manager'):
            return None
        
        llm_manager = self.jarvis.llm_manager
        
        # Ensure model is loaded
        if not llm_manager._ensure_model(model_key):
            return None
        
        # Benchmark prompt
        test_prompt = (
            "Explain quantum computing in simple terms. "
            "Focus on the key principles and practical applications."
        )
        
        if progress_callback:
            progress_callback({"status": "starting", "model": model_key})
        
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / (1024 * 1024)  # MB
            
            start_time = time.time()
            
            response = llm_manager.generate_response(
                prompt=test_prompt,
                model_key=model_key,
                max_tokens=150,
                temperature=0.7,
                enable_cache=False  # Disable cache for accurate benchmark
            )
            
            end_time = time.time()
            inference_time = (end_time - start_time) * 1000  # Convert to ms
            
            mem_after = process.memory_info().rss / (1024 * 1024)  # MB
            memory_usage = mem_after - mem_before
            
            if not response:
                return None
            
            # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
            prompt_tokens = len(test_prompt) // 4
            completion_tokens = len(response) // 4
            total_tokens = prompt_tokens + completion_tokens
            
            tokens_per_second = total_tokens / (inference_time / 1000)
            
            # Get context info
            metadata = llm_manager.model_metadata.get(model_key, {})
            context_available = metadata.get('context_length', 2048)
            context_used = prompt_tokens + completion_tokens
            
            result = BenchmarkResult(
                model_key=model_key,
                tokens_per_second=tokens_per_second,
                inference_time=inference_time,
                context_used=context_used,
                context_available=context_available,
                timestamp=datetime.now(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                memory_usage_mb=memory_usage
            )
            
            # Store result
            if model_key not in self.results:
                self.results[model_key] = []
            self.results[model_key].append(result)
            
            # Keep only last 10 results per model
            self.results[model_key] = self.results[model_key][-10:]
            
            self._save_results()
            
            if progress_callback:
                progress_callback({"status": "completed", "model": model_key, "result": result.to_dict()})
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Benchmark failed for {model_key}: {e}")
            if progress_callback:
                progress_callback({"status": "error", "model": model_key, "error": str(e)})
            return None
    
    def get_latest_result(self, model_key: str) -> Optional[BenchmarkResult]:
        """Get latest benchmark result for model"""
        results = self.results.get(model_key, [])
        return results[-1] if results else None
    
    def get_average_performance(self, model_key: str) -> Optional[Dict[str, float]]:
        """Get average performance metrics for model"""
        results = self.results.get(model_key, [])
        if not results:
            return None
        
        return {
            'avg_tokens_per_second': sum(r.tokens_per_second for r in results) / len(results),
            'avg_inference_time': sum(r.inference_time for r in results) / len(results),
            'avg_memory_usage_mb': sum(r.memory_usage_mb for r in results) / len(results),
        }


class ModelDownloadManager:
    """Manages model downloads with progress tracking"""
    
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.logger = jarvis_instance.logger if jarvis_instance else None
        self.active_downloads: Dict[str, DownloadProgress] = {}
        self.download_callbacks: List[Callable] = []
        self.download_lock = threading.Lock()
    
    def register_callback(self, callback: Callable):
        """Register callback for download progress updates"""
        self.download_callbacks.append(callback)
    
    def _notify_callbacks(self, progress: DownloadProgress):
        """Notify all registered callbacks"""
        for callback in self.download_callbacks:
            try:
                callback(progress)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Download callback error: {e}")
    
    def download_model(self, model_key: str) -> bool:
        """Download model with progress tracking"""
        if not self.jarvis or not hasattr(self.jarvis, 'llm_manager'):
            return False
        
        def progress_callback(data: Dict[str, Any]):
            progress = DownloadProgress(
                model=data.get('model', model_key),
                status=data.get('status', 'unknown'),
                downloaded=data.get('downloaded', 0),
                total=data.get('total', 0),
                percent=data.get('percent'),
                speed=data.get('speed'),
                eta=data.get('eta'),
                message=data.get('message')
            )
            
            with self.download_lock:
                self.active_downloads[model_key] = progress
            
            self._notify_callbacks(progress)
        
        try:
            result = self.jarvis.llm_manager.download_model(
                model_key,
                progress_cb=progress_callback
            )
            
            # Final progress update
            with self.download_lock:
                if model_key in self.active_downloads:
                    final_progress = self.active_downloads[model_key]
                    final_progress.status = 'completed' if result else 'failed'
                    self._notify_callbacks(final_progress)
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Download failed for {model_key}: {e}")
            
            # Error progress update
            error_progress = DownloadProgress(
                model=model_key,
                status='error',
                downloaded=0,
                total=0,
                percent=0,
                speed=None,
                eta=None,
                message=str(e)
            )
            
            with self.download_lock:
                self.active_downloads[model_key] = error_progress
            
            self._notify_callbacks(error_progress)
            return False
    
    def get_progress(self, model_key: str) -> Optional[DownloadProgress]:
        """Get current download progress for model"""
        with self.download_lock:
            return self.active_downloads.get(model_key)
    
    def is_downloading(self, model_key: str) -> bool:
        """Check if model is currently downloading"""
        with self.download_lock:
            progress = self.active_downloads.get(model_key)
            return progress and progress.status == 'in_progress'


class ContextWindowVisualizer:
    """Visualizes model context window usage"""
    
    @staticmethod
    def create_visualization(context_used: int, context_available: int, parent_tag: str):
        """Create context window visualization in DearPyGui"""
        if not dpg:
            return
        
        if context_available <= 0:
            context_available = 2048
        
        usage_percent = min((context_used / context_available) * 100, 100)
        
        # Color coding based on usage
        if usage_percent < 50:
            color = (100, 255, 100, 255)  # Green
        elif usage_percent < 80:
            color = (255, 200, 0, 255)  # Orange
        else:
            color = (255, 100, 100, 255)  # Red
        
        with dpg.group(parent=parent_tag, horizontal=True):
            dpg.add_text(f"Context: {context_used}/{context_available} tokens")
            dpg.add_progress_bar(
                default_value=usage_percent / 100,
                overlay=f"{usage_percent:.1f}%",
                width=200
            )
            dpg.bind_item_theme(dpg.last_item(), _create_progress_theme(color))


def _create_progress_theme(color):
    """Create themed progress bar"""
    if not dpg:
        return None
    
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvProgressBar):
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, color)
    return theme


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_speed(bytes_per_second: Optional[float]) -> str:
    """Format download speed"""
    if bytes_per_second is None:
        return "N/A"
    return f"{format_bytes(int(bytes_per_second))}/s"


def format_eta(seconds: Optional[float]) -> str:
    """Format ETA"""
    if seconds is None:
        return "N/A"
    
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"
