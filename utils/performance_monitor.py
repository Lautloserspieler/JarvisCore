#!/usr/bin/env python3
"""
Performance Monitoring System für J.A.R.V.I.S.
Trackt Execution Times, Memory Usage, API Latency
"""

import time
import functools
import psutil
import threading
from typing import Dict, List, Optional, Callable, Any
from collections import deque
from datetime import datetime
import json
from pathlib import Path


class PerformanceMonitor:
    """Zentrales Performance Monitoring System"""

    _instance: Optional['PerformanceMonitor'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton Pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.metrics: Dict[str, deque] = {}
        self.counters: Dict[str, int] = {}
        self.max_history = 100
        self.enabled = True
        self._lock = threading.Lock()

        # System Metriken
        self.system_samples: deque = deque(maxlen=60)  # 1 Minute History
        self._system_monitor_active = False

    def measure(self, name: str):
        """Decorator für automatisches Zeit-Tracking

        Usage:
            @perf_monitor.measure("llm_inference")
            def generate_response(prompt):
                return llm.generate(prompt)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    success = False
                    raise e
                finally:
                    duration = time.perf_counter() - start
                    self._record_timing(name, duration, success)
            return sync_wrapper
        return decorator

    def measure_async(self, name: str):
        """Decorator für async Funktionen

        Usage:
            @perf_monitor.measure_async("async_api_call")
            async def fetch_data():
                return await api.get()
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    success = False
                    raise e
                finally:
                    duration = time.perf_counter() - start
                    self._record_timing(name, duration, success)
            return async_wrapper
        return decorator

    def _record_timing(self, name: str, duration: float, success: bool = True):
        """Internes Timing Recording"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=self.max_history)

            self.metrics[name].append({
                'duration': duration,
                'timestamp': time.time(),
                'success': success,
            })

            # Counter für Gesamt-Aufrufe
            counter_key = f"{name}_count"
            self.counters[counter_key] = self.counters.get(counter_key, 0) + 1

            if not success:
                error_key = f"{name}_errors"
                self.counters[error_key] = self.counters.get(error_key, 0) + 1

    def record_event(self, name: str, value: float = 1.0, tags: Optional[Dict] = None):
        """Manuelles Event Recording

        Usage:
            perf_monitor.record_event("cache_hit", 1.0)
            perf_monitor.record_event("model_load", 5.2, {"model": "llama3"})
        """
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=self.max_history)

            self.metrics[name].append({
                'value': value,
                'timestamp': time.time(),
                'tags': tags or {},
            })

    def increment_counter(self, name: str, amount: int = 1):
        """Counter erhöhen

        Usage:
            perf_monitor.increment_counter("api_requests")
            perf_monitor.increment_counter("tokens_generated", 128)
        """
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + amount

    def get_stats(self, name: str) -> Dict[str, Any]:
        """Statistiken für Metrik abrufen"""
        with self._lock:
            if name not in self.metrics:
                return {}

            data = list(self.metrics[name])
            if not data:
                return {}

            # Nur duration-basierte Metriken
            if 'duration' in data[0]:
                durations = [item['duration'] for item in data]
                successes = sum(1 for item in data if item.get('success', True))

                return {
                    'name': name,
                    'count': len(durations),
                    'success_rate': (successes / len(data)) * 100 if data else 0,
                    'avg_ms': (sum(durations) / len(durations)) * 1000,
                    'min_ms': min(durations) * 1000,
                    'max_ms': max(durations) * 1000,
                    'p50_ms': self._percentile(durations, 0.5) * 1000,
                    'p95_ms': self._percentile(durations, 0.95) * 1000,
                    'p99_ms': self._percentile(durations, 0.99) * 1000,
                    'total_time_s': sum(durations),
                }
            else:
                # Event-basierte Metriken
                values = [item.get('value', 0) for item in data]
                return {
                    'name': name,
                    'count': len(values),
                    'sum': sum(values),
                    'avg': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Alle Metriken abrufen"""
        with self._lock:
            stats = {}
            for name in self.metrics.keys():
                stats[name] = self.get_stats(name)

            # Counters hinzufügen
            stats['counters'] = dict(self.counters)

            # System Metriken
            stats['system'] = self.get_system_stats()

            return stats

    def get_system_stats(self) -> Dict[str, Any]:
        """System Resource Metriken"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            stats = {
                'cpu_percent': cpu_percent,
                'memory_used_gb': memory.used / (1024 ** 3),
                'memory_total_gb': memory.total / (1024 ** 3),
                'memory_percent': memory.percent,
                'disk_used_gb': disk.used / (1024 ** 3),
                'disk_total_gb': disk.total / (1024 ** 3),
                'disk_percent': disk.percent,
            }

            # GPU Stats (falls vorhanden)
            try:
                import torch
                if torch.cuda.is_available():
                    stats['gpu_available'] = True
                    stats['gpu_count'] = torch.cuda.device_count()
                    stats['gpu_memory_allocated_gb'] = torch.cuda.memory_allocated(0) / (1024 ** 3)
                    stats['gpu_memory_reserved_gb'] = torch.cuda.memory_reserved(0) / (1024 ** 3)
            except Exception:
                pass

            return stats

        except Exception:
            return {}

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Berechnet Percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """Export Metriken als JSON"""
        stats = self.get_all_stats()

        if filepath:
            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2)
            return filepath
        else:
            return json.dumps(stats, indent=2)

    def reset(self):
        """Alle Metriken zurücksetzen"""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()

    def disable(self):
        """Performance Monitoring deaktivieren"""
        self.enabled = False

    def enable(self):
        """Performance Monitoring aktivieren"""
        self.enabled = True


# Globale Instanz
perf_monitor = PerformanceMonitor()


# Convenience Functions
def measure(name: str):
    """Shortcut für perf_monitor.measure()"""
    return perf_monitor.measure(name)


def measure_async(name: str):
    """Shortcut für perf_monitor.measure_async()"""
    return perf_monitor.measure_async(name)


def record_event(name: str, value: float = 1.0, tags: Optional[Dict] = None):
    """Shortcut für perf_monitor.record_event()"""
    perf_monitor.record_event(name, value, tags)


def increment_counter(name: str, amount: int = 1):
    """Shortcut für perf_monitor.increment_counter()"""
    perf_monitor.increment_counter(name, amount)


def get_stats(name: Optional[str] = None) -> Dict[str, Any]:
    """Shortcut für perf_monitor.get_stats() oder get_all_stats()"""
    if name:
        return perf_monitor.get_stats(name)
    return perf_monitor.get_all_stats()
