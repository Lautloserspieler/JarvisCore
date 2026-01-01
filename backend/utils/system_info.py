import psutil
import platform
import subprocess
import re
from typing import Any

def get_gpu_info() -> dict[str, Any]:
    """Detect GPU information"""
    try:
        # Try nvidia-smi first
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                parts = output.split(',')
                return {
                    'name': parts[0].strip(),
                    'utilization': float(parts[1].strip()),
                    'memory_used': float(parts[2].strip()),
                    'memory_total': float(parts[3].strip()),
                    'available': True
                }
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    
    # Fallback: No GPU detected
    return {
        'name': 'Keine GPU erkannt',
        'utilization': 0,
        'memory_used': 0,
        'memory_total': 0,
        'available': False
    }

def get_cpu_info() -> dict[str, Any]:
    """Get CPU information"""
    return {
        'cores': psutil.cpu_count(logical=False),
        'threads': psutil.cpu_count(logical=True),
        'utilization': psutil.cpu_percent(interval=1),
        'name': platform.processor() or 'Unknown CPU'
    }

def get_memory_info() -> dict[str, Any]:
    """Get RAM information"""
    mem = psutil.virtual_memory()
    return {
        'total': round(mem.total / (1024**3), 2),  # GB
        'used': round(mem.used / (1024**3), 2),    # GB
        'available': round(mem.available / (1024**3), 2),  # GB
        'percent': mem.percent
    }

def get_disk_info() -> dict[str, Any]:
    """Get disk information"""
    disk = psutil.disk_usage('/')
    return {
        'total': round(disk.total / (1024**3), 2),  # GB
        'used': round(disk.used / (1024**3), 2),    # GB
        'free': round(disk.free / (1024**3), 2),    # GB
        'percent': disk.percent
    }

def get_network_info() -> dict[str, Any]:
    """Get network information"""
    return {
        'status': 'Online',
        'interfaces': len(psutil.net_if_addrs())
    }

def get_uptime() -> str:
    """Get system uptime"""
    boot_time = psutil.boot_time()
    uptime_seconds = psutil.time.time() - boot_time

    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    return f"{hours}h {minutes}m"

def get_all_system_info() -> dict[str, Any]:
    """Get complete system information"""
    return {
        'cpu': get_cpu_info(),
        'gpu': get_gpu_info(),
        'memory': get_memory_info(),
        'disk': get_disk_info(),
        'network': get_network_info(),
        'uptime': get_uptime(),
        'platform': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'python_version': platform.python_version()
        }
    }
