#!/usr/bin/env python3
"""
J.A.R.V.I.S. Core - Unified Launcher (Legacy)

Diese Datei leitet auf die neuen Launcher um:
- scripts/start_web.py
- scripts/start_desktop.py
- scripts/start_production.py
"""

import argparse
import sys
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def run_script(script_name, extra_args=None):
    """Run a launcher script with optional args."""
    script_path = REPO_ROOT / "scripts" / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        sys.exit(1)

    args = [sys.executable, str(script_path)]
    if extra_args:
        args.extend(extra_args)
    subprocess.run(args, cwd=REPO_ROOT)


def main():
    parser = argparse.ArgumentParser(
        description='J.A.R.V.I.S. Core Unified Launcher (Legacy)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start_jarvis.py              # Start production mode
  python scripts/start_jarvis.py --dev        # Start desktop dev mode
  python scripts/start_jarvis.py --build      # Build desktop binary
  python scripts/start_jarvis.py --backend    # Start backend only
        """
    )
    parser.add_argument('--dev', action='store_true', help='Start in development mode')
    parser.add_argument('--build', action='store_true', help='Build desktop binary and exit')
    parser.add_argument('--backend', action='store_true', help='Start backend only (no desktop UI)')
    args = parser.parse_args()

    if args.dev:
        extra_args = []
        if args.backend:
            extra_args.append('--backend')
        run_script("start_desktop.py", extra_args)
        return

    if args.build:
        run_script("start_production.py", ["--build"])
        return

    extra_args = []
    if args.backend:
        extra_args.append('--backend')
    run_script("start_production.py", extra_args)


if __name__ == '__main__':
    main()
