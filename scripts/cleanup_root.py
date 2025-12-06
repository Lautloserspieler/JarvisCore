#!/usr/bin/env python3
"""Cleanup Root Directory - Organize and remove redundant files."""

import os
import shutil
from pathlib import Path

class RootCleanup:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.root = Path.cwd()
        self.changes = []
    
    def log(self, action, path, target=None):
        """Log changes."""
        msg = f"{'[DRY-RUN] ' if self.dry_run else ''}[{action}] {path}"
        if target:
            msg += f" -> {target}"
        print(msg)
        self.changes.append(msg)
    
    def move_to_docs(self, files):
        """Move documentation files to docs/ directory."""
        docs_dir = self.root / "docs"
        
        for file in files:
            src = self.root / file
            if not src.exists():
                print(f"⚠️  {file} not found, skipping...")
                continue
            
            dst = docs_dir / file
            self.log("MOVE", file, f"docs/{file}")
            
            if not self.dry_run:
                shutil.move(str(src), str(dst))
    
    def delete_files(self, files):
        """Delete specified files."""
        for file in files:
            path = self.root / file
            if not path.exists():
                print(f"⚠️  {file} not found, skipping...")
                continue
            
            self.log("DELETE", file)
            
            if not self.dry_run:
                path.unlink()
    
    def delete_directory(self, dir_name):
        """Delete directory recursively."""
        path = self.root / dir_name
        if not path.exists():
            print(f"⚠️  {dir_name}/ not found, skipping...")
            return
        
        self.log("DELETE DIR", f"{dir_name}/")
        
        if not self.dry_run:
            shutil.rmtree(path)
    
    def run(self):
        """Execute cleanup."""
        print("=" * 60)
        print("🧹 ROOT DIRECTORY CLEANUP")
        print("=" * 60)
        print(f"Mode: {'DRY-RUN (Preview)' if self.dry_run else 'EXECUTE'}\n")
        
        # 1. Move documentation to docs/
        print("\n📚 Moving documentation files to docs/...")
        docs_to_move = [
            "AUTO_REFACTOR.md",
            "CLEANUP_SUMMARY.md",
            "QUICKSTART_CLEANUP.md",
            "REFACTORING_GUIDE.md",
            "UI_CONSOLIDATION.md",
            "ARCHITECTURE.md"
        ]
        self.move_to_docs(docs_to_move)
        
        # 2. Delete redundant start scripts
        print("\n🗑️  Deleting redundant start scripts...")
        scripts_to_delete = [
            "run_jarvis.bat",
            "run_jarvis.sh"
        ]
        self.delete_files(scripts_to_delete)
        
        # 3. Move/Delete redundant entry points
        print("\n🗑️  Cleaning up entry points...")
        # Move to scripts instead of delete (they might be useful)
        for file in ["bootstrap.py", "start_jarvis.py"]:
            src = self.root / file
            if not src.exists():
                continue
            dst = self.root / "scripts" / file
            self.log("MOVE", file, f"scripts/{file}")
            if not self.dry_run:
                shutil.move(str(src), str(dst))
        
        # 4. Delete webapp/ directory
        print("\n🗑️  Deleting webapp/ directory (UI consolidated to desktop/)...")
        self.delete_directory("webapp")
        
        # 5. Delete unnecessary files
        print("\n🗑️  Deleting unnecessary files...")
        unnecessary = [
            "package-lock.json"
        ]
        self.delete_files(unnecessary)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"Total changes: {len(self.changes)}")
        
        if self.dry_run:
            print("\n✅ Dry-run complete! No files were modified.")
            print("\nTo execute these changes, run:")
            print("  python scripts/cleanup_root.py --execute")
        else:
            print("\n✅ Cleanup complete!")
            print("\nNext steps:")
            print("  git add .")
            print('  git commit -m "chore: cleanup root directory"')
            print("  git push origin cleanup/root-directory")

if __name__ == "__main__":
    import sys
    
    execute = "--execute" in sys.argv
    cleanup = RootCleanup(dry_run=not execute)
    cleanup.run()
