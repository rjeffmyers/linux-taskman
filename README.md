# Linux Task Manager

A GTK+ system monitoring application that combines the functionality of Linux's `top` command with the user interface style of Windows Task Manager.

## Features

### Performance Tab
- Real-time CPU usage graph
- Memory usage monitoring
- CPU information from /proc/cpuinfo
- CPU frequency monitoring
- Visual charts showing historical data

### Processes Tab
- Separated view for user processes and system processes
- Process filtering/search capability
- End process functionality
- Shows PID, name, user, status, CPU%, memory%, and command
- Sort by any column

### Users Tab
- Shows logged-in users (using `w` command)
- System information display
- Hostname, kernel version, uptime
- Load average monitoring

## Requirements

- Python 3
- GTK+ 3.0
- python3-psutil

## Installation

1. Install dependencies:
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-psutil
```

2. Make the script executable:
```bash
chmod +x taskmanager.py
```

3. Run the application:
```bash
./taskmanager.py
```

## Desktop Integration

To add the application to your application menu:

```bash
cp taskmanager.desktop ~/.local/share/applications/
```

## Usage

- **Refresh**: Click the Refresh button or data auto-refreshes based on the selected interval
- **Update Interval**: Settings menu allows changing update frequency (1, 2, 5, or 10 seconds)
- **End Process**: Select a process and click "End Process" to terminate it
- **Search**: Use the search box in the Processes tab to filter processes by name
- **System Processes**: Toggle visibility of system processes in Settings

## Design Consistency

This application follows the same UI patterns and style as vpn3gui:
- Consistent toolbar with icon buttons
- Framed sections for organization
- Status bar for feedback
- Settings menu for configuration options
- About dialog with application information

## License

MIT License# linux-taskman
