# Installation Guide for Linux Task Manager

## For Linux Mint 22.1 Users

### Quick Install (Recommended)

1. **Build the Debian package:**
   ```bash
   ./build-simple-deb.sh
   ```

2. **Install the package:**
   ```bash
   sudo apt install ./linux-taskman_1.0.0_all.deb
   ```

   This will automatically install all dependencies including:
   - python3-gi
   - python3-gi-cairo
   - gir1.2-gtk-3.0
   - python3-psutil

### Alternative Build Method

If you have dpkg-dev installed, you can use the full build script:

```bash
# Install build tools (one-time)
sudo apt install dpkg-dev devscripts lintian

# Build the package
./build-deb.sh

# Install the package
sudo dpkg -i ../linux-taskman_1.0.0-1_all.deb
```

### Manual Installation

If you prefer not to use the Debian package:

1. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-psutil
   ```

2. **Make the script executable:**
   ```bash
   chmod +x taskmanager.py
   ```

3. **Run directly:**
   ```bash
   ./taskmanager.py
   ```

4. **Optional - Install to system:**
   ```bash
   # Copy to system bin
   sudo cp taskmanager.py /usr/local/bin/linux-taskman
   
   # Install desktop file
   sudo cp taskmanager.desktop /usr/share/applications/linux-taskman.desktop
   sudo update-desktop-database
   ```

## Troubleshooting

### Missing psutil module

If you get an error about psutil not being found:

```bash
# For system-wide installation (recommended)
sudo apt install python3-psutil

# Alternative: using pip (not recommended for system apps)
pip3 install --user psutil
```

### Missing GTK dependencies

If the application fails to start with GTK errors:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### Permission denied when ending processes

Some system processes require elevated privileges to terminate. The application will show an error message for these cases. This is normal behavior for security reasons.

## Uninstallation

### If installed via Debian package:
```bash
sudo apt remove linux-taskman
```

### If installed manually:
```bash
sudo rm /usr/local/bin/linux-taskman
sudo rm /usr/share/applications/linux-taskman.desktop
sudo update-desktop-database
```

## Compatibility

This application is designed for:
- Linux Mint 22.1 (primary target)
- Linux Mint 21.x
- Ubuntu 24.04 LTS (Noble Numbat)
- Ubuntu 22.04 LTS (Jammy Jellyfish)
- Debian 12 (Bookworm)
- Any distribution with GTK+ 3.0 and Python 3.6+

## Features After Installation

Once installed, Linux Task Manager will be available:
- In your application menu under "System Tools"
- Via terminal command: `linux-taskman`
- Through the desktop search (search for "Task Manager")

The application provides:
- Real-time CPU and memory monitoring
- Process management with search and termination
- User session monitoring
- System information display
- Configurable update intervals