import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import threading
import json

class LogBuffer:
    """Thread-safe log buffer for real-time log access"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.logs: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.stats = {
            'debug': 0,
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        }
    
    def add_log(self, level: str, category: str, message: str, metadata: dict = None):
        with self.lock:
            import uuid
            log_entry = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'level': level.lower(),
                'category': category,
                'message': message,
                'metadata': metadata or {}
            }
            
            self.logs.append(log_entry)
            if len(self.logs) > self.max_size:
                removed = self.logs.pop(0)
                self.stats[removed['level']] -= 1
            
            self.stats[level.lower()] += 1
    
    def get_logs(self, level: str = None, category: str = None, limit: int = 100):
        with self.lock:
            logs = self.logs.copy()
            
            if level:
                logs = [l for l in logs if l['level'] == level.lower()]
            if category:
                logs = [l for l in logs if l['category'] == category]
            
            return logs[-limit:]
    
    def get_stats(self):
        with self.lock:
            return {
                'total': len(self.logs),
                'byLevel': self.stats.copy(),
                'byCategory': self._count_by_category(),
                'timeRange': {
                    'start': self.logs[0]['timestamp'] if self.logs else datetime.now().isoformat(),
                    'end': self.logs[-1]['timestamp'] if self.logs else datetime.now().isoformat()
                }
            }
    
    def _count_by_category(self):
        categories = {}
        for log in self.logs:
            cat = log['category']
            categories[cat] = categories.get(cat, 0) + 1
        return categories
    
    def clear(self):
        with self.lock:
            self.logs.clear()
            self.stats = {k: 0 for k in self.stats}

# Global log buffer
log_buffer = LogBuffer()

class BufferedHandler(logging.Handler):
    """Custom handler that writes to both file and buffer"""
    
    def emit(self, record):
        try:
            category = getattr(record, 'category', 'system')
            log_buffer.add_log(
                level=record.levelname,
                category=category,
                message=record.getMessage(),
                metadata={
                    'module': record.module,
                    'funcName': record.funcName,
                    'lineno': record.lineno
                }
            )
        except Exception:
            self.handleError(record)

class ColoredFormatter(logging.Formatter):
    """Colored console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logger(name: str = 'jarvis', log_file: str = 'jarvis.log', console_level=logging.INFO):
    """Setup comprehensive logger with file, console and buffer handlers"""
    
    # Create logs directory
    log_path = Path('logs')
    log_path.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # === FILE HANDLER (DETAILED) ===
    file_handler = logging.FileHandler(log_path / log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(module)s.%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # === CONSOLE HANDLER (COLORED, LESS VERBOSE) ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # === BUFFER HANDLER (FOR UI) ===
    buffer_handler = BufferedHandler()
    buffer_handler.setLevel(logging.DEBUG)
    logger.addHandler(buffer_handler)
    
    # Initial log entries
    logger.info("="*60, extra={'category': 'system'})
    logger.info("JARVIS CORE SYSTEM STARTED", extra={'category': 'system'})
    logger.info(f"Log file: {log_path / log_file}", extra={'category': 'system'})
    logger.info("="*60, extra={'category': 'system'})
    
    return logger

# Global logger instance
logger = setup_logger()

# Helper functions for quick logging
def log_info(message: str, category: str = 'system'):
    logger.info(message, extra={'category': category})

def log_error(message: str, category: str = 'system', exc_info=False):
    logger.error(message, extra={'category': category}, exc_info=exc_info)

def log_warning(message: str, category: str = 'system'):
    logger.warning(message, extra={'category': category})

def log_debug(message: str, category: str = 'system'):
    logger.debug(message, extra={'category': category})
