#!/bin/bash

# Build script for Linux Task Manager Debian package
# Target: Linux Mint 22.1 (based on Ubuntu 24.04)

set -e

echo "======================================"
echo " Linux Task Manager - Debian Builder"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get package version from changelog
VERSION=$(head -n 1 debian/changelog | sed 's/.*(\(.*\)).*/\1/')
PACKAGE_NAME="linux-taskman"

echo "Building ${PACKAGE_NAME} version ${VERSION}"
echo ""

# Check for required tools
echo "Checking build dependencies..."
for cmd in dpkg-buildpackage debuild lintian; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${YELLOW}Warning: $cmd not found${NC}"
        if [ "$cmd" == "dpkg-buildpackage" ]; then
            echo -e "${RED}Error: dpkg-dev is required${NC}"
            echo "Install with: sudo apt install dpkg-dev devscripts lintian"
            exit 1
        fi
    fi
done

# Check for Python dependencies
echo "Checking Python dependencies..."
if ! python3 -c "import gi" 2>/dev/null; then
    echo -e "${YELLOW}Warning: python3-gi not installed${NC}"
fi

if ! python3 -c "import psutil" 2>/dev/null; then
    echo -e "${YELLOW}Warning: python3-psutil not installed${NC}"
    echo "The package will still build, but the application requires this to run."
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -f ../${PACKAGE_NAME}_*.deb
rm -f ../${PACKAGE_NAME}_*.changes
rm -f ../${PACKAGE_NAME}_*.dsc
rm -f ../${PACKAGE_NAME}_*.tar.xz
rm -f ../${PACKAGE_NAME}_*.buildinfo
rm -rf debian/${PACKAGE_NAME}/
rm -rf debian/.debhelper/
rm -f debian/debhelper-build-stamp
rm -f debian/files
rm -f debian/*.substvars
rm -f debian/*.log

# Make sure scripts are executable
chmod +x taskmanager.py
chmod +x debian/rules
chmod +x debian/postinst

# Update desktop file with correct path
echo "Updating desktop file..."
sed -i "s|Exec=.*|Exec=/usr/bin/linux-taskman|" taskmanager.desktop

# Build the package
echo ""
echo "Building Debian package..."
echo "=========================="

# Use dpkg-buildpackage for a clean build
if command -v dpkg-buildpackage &> /dev/null; then
    dpkg-buildpackage -b -us -uc
    BUILD_RESULT=$?
else
    echo -e "${RED}Error: dpkg-buildpackage not found${NC}"
    echo "Install with: sudo apt install dpkg-dev"
    exit 1
fi

if [ $BUILD_RESULT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo ""
    
    # Find the generated .deb file
    DEB_FILE=$(ls -1 ../${PACKAGE_NAME}_*.deb 2>/dev/null | head -n 1)
    
    if [ -f "$DEB_FILE" ]; then
        echo "Package created: $DEB_FILE"
        echo ""
        
        # Show package info
        echo "Package information:"
        echo "==================="
        dpkg-deb -I "$DEB_FILE"
        
        # Run lintian if available
        if command -v lintian &> /dev/null; then
            echo ""
            echo "Running lintian checks..."
            echo "========================"
            lintian "$DEB_FILE" || true
        fi
        
        echo ""
        echo "Installation instructions:"
        echo "========================="
        echo "To install the package, run:"
        echo -e "${GREEN}sudo dpkg -i $DEB_FILE${NC}"
        echo ""
        echo "Or using apt (to resolve dependencies):"
        echo -e "${GREEN}sudo apt install $DEB_FILE${NC}"
        echo ""
        echo "To remove the package later:"
        echo "sudo apt remove ${PACKAGE_NAME}"
    else
        echo -e "${RED}Error: Package file not found${NC}"
        exit 1
    fi
else
    echo ""
    echo -e "${RED}✗ Build failed!${NC}"
    echo "Check the output above for errors."
    exit 1
fi