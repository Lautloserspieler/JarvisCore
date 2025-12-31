#!/usr/bin/env python3
"""Compatibility entry point for the web launcher."""

from pathlib import Path
import runpy


def main():
    script_path = Path(__file__).resolve().parent / "scripts" / "start_web.py"
    runpy.run_path(str(script_path), run_name="__main__")


if __name__ == "__main__":
    main()
