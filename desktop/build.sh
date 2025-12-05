#!/bin/bash
# Build script for JarvisCore Desktop with version injection

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get version from git tag or use default
if git describe --tags --exact-match 2>/dev/null; then
    VERSION=$(git describe --tags --exact-match)
    echo -e "${GREEN}✓${NC} Building with git tag: ${YELLOW}${VERSION}${NC}"
else
    VERSION="v1.0.0-dev"
    echo -e "${YELLOW}⚠${NC} No git tag found, using default: ${YELLOW}${VERSION}${NC}"
fi

# Build with version injection
echo -e "${GREEN}→${NC} Building binary..."

wails build -ldflags "-X 'github.com/Lautloserspieler/JarvisCore/desktop/backend/internal/app.Version=${VERSION}'"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Build successful!"
    echo -e "${GREEN}→${NC} Binary: build/bin/"
    echo -e "${GREEN}→${NC} Version: ${YELLOW}${VERSION}${NC}"
else
    echo -e "${RED}✗${NC} Build failed!"
    exit 1
fi
