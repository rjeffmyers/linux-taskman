#!/bin/bash

# Simple build script for Linux Task Manager Debian package
# This version uses fakeroot and dpkg-deb directly (simpler approach)
# Target: Linux Mint 22.1

set -e

echo "============================================"
echo " Linux Task Manager - Simple Debian Builder"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Package info
PACKAGE_NAME="linux-taskman"
VERSION="1.0.0"
ARCH="all"
DEB_FILE="${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "Building ${PACKAGE_NAME} version ${VERSION}"
echo ""

# Check for required tools
if ! command -v dpkg-deb &> /dev/null; then
    echo -e "${RED}Error: dpkg-deb not found${NC}"
    echo "Install with: sudo apt install dpkg"
    exit 1
fi

# Create package directory structure
echo "Creating package structure..."
PKG_DIR="build/${PACKAGE_NAME}_${VERSION}_${ARCH}"
rm -rf build
mkdir -p "$PKG_DIR"

# Create DEBIAN directory
mkdir -p "$PKG_DIR/DEBIAN"

# Create control file
cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.6), python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, python3-psutil
Maintainer: Linux Task Manager Contributors <noreply@example.com>
Description: Linux Task Manager - System monitoring tool
 A GTK+ system monitoring application that combines the functionality
 of Linux's top command with the user interface style of Windows Task Manager.
 Features include CPU/memory monitoring, process management, and user sessions.
EOF

# Create postinst script
cat > "$PKG_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    configure)
        # Update desktop database
        if which update-desktop-database > /dev/null 2>&1; then
            update-desktop-database -q /usr/share/applications || true
        fi
        
        echo ""
        echo "=============================================="
        echo " Linux Task Manager has been installed!"
        echo "=============================================="
        echo ""
        echo "You can run it from:"
        echo "  • Application menu under 'System Tools'"
        echo "  • Terminal: linux-taskman"
        echo ""
        ;;
esac

exit 0
EOF

chmod 755 "$PKG_DIR/DEBIAN/postinst"

# Create directory structure
echo "Installing files..."
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/doc/${PACKAGE_NAME}"

# Copy files
cp taskmanager.py "$PKG_DIR/usr/bin/linux-taskman"
chmod 755 "$PKG_DIR/usr/bin/linux-taskman"

# Update desktop file and copy
sed "s|Exec=.*|Exec=/usr/bin/linux-taskman|" taskmanager.desktop > "$PKG_DIR/usr/share/applications/linux-taskman.desktop"
chmod 644 "$PKG_DIR/usr/share/applications/linux-taskman.desktop"

# Copy documentation
cp README.md "$PKG_DIR/usr/share/doc/${PACKAGE_NAME}/"
chmod 644 "$PKG_DIR/usr/share/doc/${PACKAGE_NAME}/README.md"

# Create copyright file
cat > "$PKG_DIR/usr/share/doc/${PACKAGE_NAME}/copyright" << 'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: linux-taskman
Source: https://github.com/yourusername/linux-taskman

Files: *
Copyright: 2024 Linux Task Manager Contributors
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
EOF

# Set proper permissions
echo "Setting permissions..."
find "$PKG_DIR" -type d -exec chmod 755 {} \;
find "$PKG_DIR/usr/share" -type f -exec chmod 644 {} \;
chmod 755 "$PKG_DIR/usr/bin/linux-taskman"

# Build the package
echo ""
echo "Building Debian package..."
if command -v fakeroot &> /dev/null; then
    fakeroot dpkg-deb --build "$PKG_DIR" .
else
    dpkg-deb --build "$PKG_DIR" .
fi

# Check if build was successful
if [ -f "$DEB_FILE" ]; then
    echo ""
    echo -e "${GREEN}✓ Package built successfully!${NC}"
    echo ""
    echo "Package: $DEB_FILE"
    echo "Size: $(du -h $DEB_FILE | cut -f1)"
    echo ""
    
    # Show package info
    echo "Package contents:"
    echo "================"
    dpkg-deb -c "$DEB_FILE" | head -20
    echo ""
    
    echo "Package information:"
    echo "==================="
    dpkg-deb -I "$DEB_FILE"
    echo ""
    
    echo "Installation instructions:"
    echo "========================="
    echo "To install the package:"
    echo -e "${GREEN}sudo dpkg -i $DEB_FILE${NC}"
    echo ""
    echo "If you get dependency errors, run:"
    echo -e "${GREEN}sudo apt install -f${NC}"
    echo ""
    echo "Or install with apt (resolves dependencies automatically):"
    echo -e "${GREEN}sudo apt install ./$DEB_FILE${NC}"
    echo ""
    echo "To remove the package later:"
    echo "sudo apt remove ${PACKAGE_NAME}"
    echo ""
    
    # Clean up build directory
    echo "Cleaning up build files..."
    rm -rf build/
    
    echo -e "${GREEN}Done!${NC}"
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi