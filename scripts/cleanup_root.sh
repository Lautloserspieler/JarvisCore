#!/bin/bash
# Linux/macOS Shell Script for Root Cleanup

set -e

echo "============================================================"
echo "ROOT DIRECTORY CLEANUP"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.8+"
    exit 1
fi

# Ask for confirmation
echo "This will clean up the root directory:"
echo "  - Move docs to docs/"
echo "  - Delete redundant scripts"
echo "  - Remove webapp/"
echo ""
read -p "Continue? (y/n): " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Running cleanup script..."
echo ""

python3 scripts/cleanup_root.py --execute

echo ""
echo "============================================================"
echo "CLEANUP COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  git add ."
echo '  git commit -m "chore: cleanup root directory"'
echo "  git push origin cleanup/root-directory"
echo ""
