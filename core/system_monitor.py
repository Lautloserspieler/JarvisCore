import psutil
import platform
try:
    # The PyPI package 'speedtest-cli' exposes import name 'speedtest'
    import speedtest  # type: ignore
except Exception:
    speedtest = None  # Fallback when module is not available
try:
    # GPU support is optional and may not be installed everywhere
    import GPUtil  # type: ignore
except Exception:
    GPUtil = None
import time
from typing import Dict, Any, Tuple, List, Optional
import socket
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    Eine Klasse zur Überwachung verschiedener Systemmetriken inklusive CPU, GPU, RAM, Speicher und Netzwerk.
    """
    
    def __init__(self, update_interval: float = 2.0):
        """
        Initialisiert den SystemMonitor.
        
        Args:
            update_interval: Aktualisierungsintervall in Sekunden für die Leistungsüberwachung
        """
        self.update_interval = update_interval
        self._last_update = 0
        self._cached_metrics = {}
        self._gpu_available = self._check_gpu_availability()
    
    def _check_gpu_availability(self) -> bool:
        """Überprüft, ob eine GPU verfügbar ist."""
        if GPUtil is None:
            return False
        try:
            GPUtil.getGPUs()
            return True
        except Exception:
            return False
    
    def get_cpu_info(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Ruft CPU-Informationen und Auslastungsstatistiken ab.
        
        Args:
            use_cache: Wenn True, werden zwischengespeicherte Werte verwendet, falls verfügbar
            
        Returns:
            Dictionary mit CPU-Informationen
        """
        current_time = time.time()
        
        if use_cache and 'cpu' in self._cached_metrics and \
           (current_time - self._last_update) < self.update_interval:
            return self._cached_metrics['cpu']
            
        try:
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
            
            # Detaillierte CPU-Statistiken
            cpu_times = psutil.cpu_times_percent(interval=0.1)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            result = {
                'cpu_usage_percent': cpu_percent,
                'cpu_cores': psutil.cpu_count(logical=False),
                'cpu_threads': psutil.cpu_count(logical=True),
                'cpu_brand': cpu_info.get('brand_raw', 'Unbekannt'),
                'cpu_arch': platform.machine(),
                'cpu_freq': {
                    'current': psutil.cpu_freq().current if psutil.cpu_freq() else None,
                    'max': psutil.cpu_freq().max if psutil.cpu_freq() else None,
                    'min': psutil.cpu_freq().min if psutil.cpu_freq() else None
                },
                'cpu_times': {
                    'user': cpu_times.user,
                    'system': cpu_times.system,
                    'idle': cpu_times.idle,
                    'iowait': getattr(cpu_times, 'iowait', 0.0)  # Nicht auf allen Systemen verfügbar
                },
                'cpu_load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                'timestamp': current_time
            }
            
            # Zwischenspeichern
            self._cached_metrics['cpu'] = result
            self._last_update = current_time
            
            return result
            
        except Exception as e:
            logger.error(f'Fehler beim Abrufen der CPU-Informationen: {str(e)}')
            return {'error': f'Fehler beim Abrufen der CPU-Informationen: {str(e)}'}
    
    def get_memory_info(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Ruft RAM- und Swap-Informationen ab.
        
        Args:
            use_cache: Wenn True, werden zwischengespeicherte Werte verwendet, falls verfügbar
            
        Returns:
            Dictionary mit Speicherinformationen
        """
        current_time = time.time()
        
        if use_cache and 'memory' in self._cached_metrics and \
           (current_time - self._last_update) < self.update_interval:
            return self._cached_metrics['memory']
            
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            result = {
                'ram': {
                    'total': virtual_mem.total,
                    'available': virtual_mem.available,
                    'used': virtual_mem.used,
                    'free': virtual_mem.free,
                    'percent': virtual_mem.percent,
                    'active': getattr(virtual_mem, 'active', None),
                    'inactive': getattr(virtual_mem, 'inactive', None),
                    'buffers': getattr(virtual_mem, 'buffers', None),
                    'cached': getattr(virtual_mem, 'cached', None),
                    'shared': getattr(virtual_mem, 'shared', None)
                },
                'swap': {
                    'total': swap_mem.total,
                    'used': swap_mem.used,
                    'free': swap_mem.free,
                    'percent': swap_mem.percent,
                    'sin': getattr(swap_mem, 'sin', None),  # Swap in
                    'sout': getattr(swap_mem, 'sout', None)  # Swap out
                },
                'timestamp': current_time
            }
            
            # Zwischenspeichern
            self._cached_metrics['memory'] = result
            self._last_update = current_time
            
            return result
            
        except Exception as e:
            logger.error(f'Fehler beim Abrufen der Speicherinformationen: {str(e)}')
            return {'error': f'Fehler beim Abrufen der Speicherinformationen: {str(e)}'}
    
    def get_gpu_info(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Ruft GPU-Informationen und Auslastungsstatistiken ab.
        
        Args:
            use_cache: Wenn True, werden zwischengespeicherte Werte verwendet, falls verfügbar
            
        Returns:
            Dictionary mit GPU-Informationen
        """
        if GPUtil is None or not self._gpu_available:
            return {
                'gpus': [],
                'gpu_available': False,
                'error': 'GPU monitoring not available. Install GPUtil for GPU stats.'
            }
            
        current_time = time.time()
        
        if use_cache and 'gpu' in self._cached_metrics and \
           (current_time - self._last_update) < self.update_interval:
            return self._cached_metrics['gpu']
            
        try:
            if GPUtil is None:
                raise RuntimeError("GPUtil not available")
            gpus = GPUtil.getGPUs()
            if not gpus:
                return {'gpus': [], 'gpu_available': False}
                
            gpu_info = []
            total_load = 0
            total_memory_used = 0
            total_memory_total = 0
            
            for gpu in gpus:
                gpu_data = {
                    'id': gpu.id,
                    'name': gpu.name,
                    'load': gpu.load * 100,  # In Prozent umwandeln
                    'memory_used': gpu.memoryUsed,
                    'memory_total': gpu.memoryTotal,
                    'memory_free': gpu.memoryFree,
                    'memory_util': gpu.memoryUtil * 100,  # In Prozent umwandeln
                    'temperature': gpu.temperature,
                    'driver': gpu.driver,
                    'uuid': gpu.uuid if hasattr(gpu, 'uuid') else None,
                    'serial': gpu.serial if hasattr(gpu, 'serial') else None,
                    'display_mode': gpu.display_mode if hasattr(gpu, 'display_mode') else None,
                    'display_active': gpu.display_active if hasattr(gpu, 'display_active') else None
                }
                
                # Berechne Gesamtwerte für Zusammenfassung
                total_load += gpu.load * 100
                total_memory_used += gpu.memoryUsed
                total_memory_total += gpu.memoryTotal
                
                gpu_info.append(gpu_data)
            
            result = {
                'gpus': gpu_info,
                'gpu_count': len(gpus),
                'gpu_available': True,
                'avg_gpu_load': total_load / len(gpus) if gpus else 0,
                'total_memory_used': total_memory_used,
                'total_memory_total': total_memory_total,
                'total_memory_percent': (total_memory_used / total_memory_total * 100) if total_memory_total > 0 else 0,
                'timestamp': current_time
            }
            
            # Zwischenspeichern
            self._cached_metrics['gpu'] = result
            self._last_update = current_time
            
            return result
            
        except Exception as e:
            logger.error(f'Fehler beim Abrufen der GPU-Informationen: {str(e)}')
            return {'error': f'Fehler beim Abrufen der GPU-Informationen: {str(e)}', 'gpu_available': False}
    
    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Get disk/partition information and usage statistics."""
        try:
            partitions = psutil.disk_partitions()
            disk_info = {}
            
            for partition in partitions:
                try:
                    if partition.fstype and 'cdrom' not in partition.opts:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info[partition.device] = {
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percent': usage.percent
                        }
                except Exception as e:
                    continue
                    
            return {'disks': disk_info}
        except Exception as e:
            return {'error': f'Failed to get disk info: {str(e)}'}
    
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """Get network interface information and statistics."""
        try:
            net_io = psutil.net_io_counters()
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            interfaces = {}
            for name, addrs_list in addrs.items():
                # Skip loopback and non-active interfaces
                if name == 'lo' or name not in stats or not stats[name].isup:
                    continue
                    
                ipv4 = next((addr.address for addr in addrs_list if addr.family == socket.AF_INET), None)
                ipv6 = next((addr.address for addr in addrs_list if addr.family == socket.AF_INET6), None)
                mac = next((addr.address for addr in addrs_list if addr.family == psutil.AF_LINK), None)
                
                interfaces[name] = {
                    'ipv4': ipv4,
                    'ipv6': ipv6,
                    'mac': mac,
                    'is_up': stats[name].isup,
                    'speed': stats[name].speed  # in MB/s
                }
            
            return {
                'interfaces': interfaces,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors_in': net_io.errin,
                'errors_out': net_io.errout,
                'drop_in': net_io.dropin,
                'drop_out': net_io.dropout
            }
        except Exception as e:
            return {'error': f'Failed to get network info: {str(e)}'}
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get general system information."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return {
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': uptime.total_seconds(),
                'uptime': str(uptime)
            }
        except Exception as e:
            return {'error': f'Failed to get system info: {str(e)}'}
    
    @staticmethod
    def get_speedtest() -> Dict[str, Any]:
        """Run a speed test to measure download/upload speeds and ping."""
        if speedtest is None:
            return {'error': 'Speedtest module not available. Install speedtest-cli to enable this feature.'}
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            ping = st.results.ping
            return {
                'download_mbps': round(download_speed, 2),
                'upload_mbps': round(upload_speed, 2),
                'ping_ms': round(ping, 2),
                'server': st.results.server,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': f'Failed to run speed test: {str(e)}'}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all available system metrics."""
        return {
            'system': self.get_system_info(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'gpu': self.get_gpu_info(),
            'disks': self.get_disk_info(),
            'network': self.get_network_info(),
            'speedtest': self.get_speedtest(),
            'timestamp': datetime.now().isoformat()
        }

    def get_system_summary(self, include_details: bool = False) -> Dict[str, Any]:
        """
        Gibt eine Zusammenfassung der Systemressourcen zurück.
        
        Args:
            include_details: Wenn True, werden detaillierte Informationen eingeschlossen
            
        Returns:
            Dictionary mit einer Zusammenfassung der Systemressourcen
        """
        current_time = time.time()
        
        # Alle relevanten Informationen abrufen
        cpu_info = self.get_cpu_info()
        memory_info = self.get_memory_info()
        gpu_info = self.get_gpu_info()
        
        # Zusammenfassung erstellen
        summary = {
            'timestamp': current_time,
            'cpu': {
                'usage_percent': cpu_info.get('cpu_usage_percent'),
                'cores': cpu_info.get('cpu_cores'),
                'model': cpu_info.get('cpu_brand'),
                'load_avg': cpu_info.get('cpu_load_avg')
            },
            'memory': {
                'total': memory_info.get('ram', {}).get('total'),
                'used': memory_info.get('ram', {}).get('used'),
                'percent': memory_info.get('ram', {}).get('percent')
            },
            'gpu': {
                'available': gpu_info.get('gpu_available', False),
                'count': gpu_info.get('gpu_count', 0),
                'avg_load': gpu_info.get('avg_gpu_load', 0),
                'memory_used': gpu_info.get('total_memory_used', 0),
                'memory_total': gpu_info.get('total_memory_total', 0),
                'memory_percent': gpu_info.get('total_memory_percent', 0)
            },
            'status': 'OK'
        }
        
        # Detaillierte Informationen hinzufügen, falls gewünscht
        if include_details:
            summary['cpu_details'] = cpu_info
            summary['memory_details'] = memory_info
            if gpu_info.get('gpu_available'):
                summary['gpu_details'] = gpu_info
        
        return summary


# Beispielhafte Verwendung
if __name__ == "__main__":
    import json
    
    # Logger konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Monitor initialisieren
    monitor = SystemMonitor(update_interval=2.0)
    
    print("=== Systemressourcen-Überwachung ===\n")
    
    # Systemübersicht anzeigen
    print("Systemübersicht:")
    summary = monitor.get_system_summary(include_details=False)
    print(json.dumps(summary, indent=2, default=str))
    
    # Detaillierte Informationen anzeigen
    print("\nDetaillierte CPU-Informationen:")
    print(json.dumps(monitor.get_cpu_info(), indent=2, default=str))
    
    print("\nDetaillierte Speicherinformationen:")
    print(json.dumps(monitor.get_memory_info(), indent=2, default=str))
    
    gpu_info = monitor.get_gpu_info()
    if gpu_info.get('gpu_available'):
        print("\nDetaillierte GPU-Informationen:")
        print(json.dumps(gpu_info, indent=2, default=str))
    
    # Echtzeit-Überwachung für 10 Sekunden
    print("\n=== Echtzeit-Überwachung (10 Sekunden) ===\n")
    
    start_time = time.time()
    duration = 10  # Sekunden
    
    try:
        while time.time() - start_time < duration:
            # Systemübersicht abrufen
            summary = monitor.get_system_summary()
            
            # Ausgabe formatieren
            cpu_usage = summary['cpu']['usage_percent']
            mem_usage = summary['memory']['percent']
            gpu_available = summary['gpu']['available']
            gpu_usage = summary['gpu']['avg_load'] if gpu_available else 'N/A'
            
            print(f"CPU: {cpu_usage:.1f}% | "
                  f"RAM: {mem_usage:.1f}% | "
                  f"GPU: {gpu_usage if isinstance(gpu_usage, str) else f'{gpu_usage:.1f}%'}")
            
            # Kurz warten vor der nächsten Aktualisierung
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nÜberwachung wurde beendet.")
    all_metrics = monitor.get_all_metrics()

    for device, info in all_metrics.get('disks', {}).get('disks', {}).items():
        print(f"  {device} ({info['mountpoint']}): {info['percent']}% used")
    
    # Print network interfaces
    print("\nNetwork Interfaces:")
    for name, info in all_metrics.get('network', {}).get('interfaces', {}).items():
        if info.get('ipv4'):
            print(f"  {name}: {info['ipv4']} (Up: {info['is_up']}, Speed: {info.get('speed', '?')}Mbps)")
    
    # Print speed test results if available
    speedtest_metrics = all_metrics.get('speedtest', {})
    if {'download_mbps', 'upload_mbps', 'ping_ms'} <= speedtest_metrics.keys():
        print("\nSpeed Test Results:")
        print(f"  Download: {speedtest_metrics['download_mbps']} Mbps")
        print(f"  Upload: {speedtest_metrics['upload_mbps']} Mbps")
        print(f"  Ping: {speedtest_metrics['ping_ms']} ms")
