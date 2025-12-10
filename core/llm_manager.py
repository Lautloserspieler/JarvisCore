"""
LLM-Manager fuer J.A.R.V.I.S.
Verwaltet lokale Sprachmodelle (Mistral, DeepSeek, Qwen, Llama, etc.)
"""

import os
import json
import shutil
import threading
import time
import random
import hashlib
import contextlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Callable

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    from llama_cpp import Llama
except ImportError:  # pragma: no cover
    Llama = None

from utils.logger import Logger
from core.llm_router import LLMRouter