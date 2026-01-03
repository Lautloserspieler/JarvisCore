#!/usr/bin/env python3
"""JarvisCore CLI - Command-line interface for starting JarvisCore in different modes."""

import sys
import subprocess
from pathlib import Path


def print_banner():
    """Print JarvisCore banner."""
    print("""
╔══════════════════════════════════════════════════════╗
║              JARVIS CORE SYSTEM v1.2.0               ║
║         Just A Rather Very Intelligent System        ║
╚══════════════════════════════════════════════════════╝
    """)


def print_usage():
    """Print usage information."""
    print("""Usage: jarviscore <mode>

Modes:
  web       Start web development mode (FastAPI + Vite)
  desktop   Start desktop mode (Wails application)
  prod      Start production mode (optimized)
  
Examples:
  jarviscore web      # Default: Browser-based UI for development
  jarviscore desktop  # Native desktop application
  jarviscore prod     # Production deployment

For more information, see: https://github.com/Lautloserspieler/JarvisCore
    """)


def main():
    """Main CLI entry point."""
    project_root = Path(__file__).resolve().parents[2]
    
    # Parse arguments
    if len(sys.argv) < 2:
        print_banner()
        print("\n❌ Error: No mode specified\n")
        print_usage()
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    # Route to appropriate launcher
    if mode == "web":
        print_banner()
        print("🌐 Starting Web Development Mode...\n")
        main_py = project_root / "main.py"
        subprocess.run([sys.executable, str(main_py)], cwd=project_root)
    
    elif mode == "desktop":
        print_banner()
        print("🖥️  Starting Desktop Mode...\n")
        desktop_script = project_root / "scripts" / "start_desktop.py"
        if not desktop_script.exists():
            print("❌ Desktop mode not yet implemented")
            print("   Use 'jarviscore web' for now")
            sys.exit(1)
        subprocess.run([sys.executable, str(desktop_script)], cwd=project_root)
    
    elif mode == "prod" or mode == "production":
        print_banner()
        print("🚀 Starting Production Mode...\n")
        prod_script = project_root / "scripts" / "start_production.py"
        if not prod_script.exists():
            print("❌ Production mode not yet implemented")
            print("   Use 'jarviscore web' for now")
            sys.exit(1)
        subprocess.run([sys.executable, str(prod_script)], cwd=project_root)
    
    elif mode in ["-h", "--help", "help"]:
        print_banner()
        print_usage()
    
    else:
        print_banner()
        print(f"\n❌ Error: Unknown mode '{mode}'\n")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
