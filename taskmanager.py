#!/usr/bin/env python3

"""
Linux Task Manager - A GTK+ system monitoring tool
Copyright (c) 2024
MIT License
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import subprocess
import threading
import os
import platform
import psutil
import time
from collections import deque
import pwd
import grp
import signal

class TaskManager(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Linux Task Manager")
        self.set_border_width(20)
        self.set_default_size(900, 700)
        
        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        # Add a toolbar for better visibility (matching vpn3gui style)
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        vbox.pack_start(toolbar, False, False, 0)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b><big>Linux Task Manager</big></b>")
        vbox.pack_start(title_label, False, False, 0)
        
        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 0)
        
        # Initialize data - must be before creating tabs
        self.current_user = os.environ.get('USER', 'unknown')
        self.init_performance_data()
        self.process_list_store = None
        self.users_list_store = None
        
        # Main notebook for tabs
        self.notebook = Gtk.Notebook()
        vbox.pack_start(self.notebook, True, True, 0)
        
        # Create tabs
        self.create_performance_tab()
        self.create_processes_tab()
        self.create_users_tab()
        
        # Status bar
        self.statusbar = Gtk.Statusbar()
        vbox.pack_start(self.statusbar, False, False, 0)
        
        # Toolbar buttons
        # Refresh button
        refresh_button = Gtk.ToolButton()
        refresh_button.set_label("Refresh")
        refresh_button.set_icon_name("view-refresh")
        refresh_button.set_tooltip_text("Refresh data")
        refresh_button.set_is_important(True)
        refresh_button.connect("clicked", self.refresh_all)
        toolbar.insert(refresh_button, 0)
        
        # Add separator
        separator = Gtk.SeparatorToolItem()
        separator.set_expand(True)
        separator.set_draw(False)
        toolbar.insert(separator, 1)
        
        # Settings button
        settings_button = Gtk.ToolButton()
        settings_button.set_label("Settings")
        settings_button.set_icon_name("preferences-system")
        settings_button.set_tooltip_text("Application settings")
        toolbar.insert(settings_button, 2)
        
        # Help button
        help_button = Gtk.ToolButton()
        help_button.set_label("Help")
        help_button.set_icon_name("help-about")
        help_button.set_tooltip_text("About this application")
        toolbar.insert(help_button, 3)
        
        def show_about(widget):
            dialog = Gtk.AboutDialog()
            dialog.set_transient_for(self)
            dialog.set_program_name("Linux Task Manager")
            dialog.set_version("1.0.0")
            dialog.set_comments("A GTK+ system monitoring tool for Linux\n\nCombining Linux top with Windows Task Manager style")
            dialog.set_authors(["Linux Task Manager Contributors"])
            dialog.set_license_type(Gtk.License.MIT_X11)
            dialog.run()
            dialog.destroy()
        
        help_button.connect("clicked", show_about)
        
        # Settings menu
        settings_menu = Gtk.Menu()
        
        def show_settings_menu(widget):
            settings_menu.show_all()
            settings_menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
        
        settings_button.connect("clicked", show_settings_menu)
        
        # Update interval menu items
        update_menu = Gtk.MenuItem(label="Update Interval")
        settings_menu.append(update_menu)
        
        update_submenu = Gtk.Menu()
        update_menu.set_submenu(update_submenu)
        
        # Radio menu items for update intervals
        self.update_interval = 2  # Default 2 seconds
        interval_group = None
        for interval, label in [(1, "1 second"), (2, "2 seconds"), (5, "5 seconds"), (10, "10 seconds")]:
            if interval_group is None:
                item = Gtk.RadioMenuItem(label=label)
                interval_group = item
            else:
                item = Gtk.RadioMenuItem(label=label, group=interval_group)
            if interval == self.update_interval:
                item.set_active(True)
            item.connect("toggled", self.on_interval_changed, interval)
            update_submenu.append(item)
        
        # Separator
        settings_menu.append(Gtk.SeparatorMenuItem())
        
        # Show system processes toggle
        self.show_system_processes = Gtk.CheckMenuItem(label="Show System Processes")
        self.show_system_processes.set_active(True)
        self.show_system_processes.connect("toggled", self.toggle_system_processes)
        settings_menu.append(self.show_system_processes)
        
        # Start update timers
        self.update_timer_id = None
        self.start_update_timer()
        
        # Initial data load
        self.refresh_all()
        
    def create_performance_tab(self):
        """Create the Performance tab"""
        # Main container
        performance_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        performance_box.set_border_width(10)
        
        # CPU info frame
        cpu_frame = Gtk.Frame(label="CPU Information")
        performance_box.pack_start(cpu_frame, False, False, 0)
        
        cpu_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cpu_info_box.set_border_width(10)
        cpu_frame.add(cpu_info_box)
        
        # CPU model and cores
        self.cpu_model_label = Gtk.Label()
        self.cpu_model_label.set_xalign(0)
        cpu_info_box.pack_start(self.cpu_model_label, False, False, 0)
        
        self.cpu_cores_label = Gtk.Label()
        self.cpu_cores_label.set_xalign(0)
        cpu_info_box.pack_start(self.cpu_cores_label, False, False, 0)
        
        self.cpu_freq_label = Gtk.Label()
        self.cpu_freq_label.set_xalign(0)
        cpu_info_box.pack_start(self.cpu_freq_label, False, False, 0)
        
        # CPU usage frame
        usage_frame = Gtk.Frame(label="CPU Usage")
        performance_box.pack_start(usage_frame, True, True, 0)
        
        usage_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        usage_box.set_border_width(10)
        usage_frame.add(usage_box)
        
        # CPU usage chart
        self.cpu_chart_area = Gtk.DrawingArea()
        self.cpu_chart_area.set_size_request(600, 300)
        self.cpu_chart_area.connect("draw", self.on_cpu_chart_draw)
        
        chart_frame = Gtk.Frame()
        chart_frame.add(self.cpu_chart_area)
        usage_box.pack_start(chart_frame, True, True, 0)
        
        # Current usage label
        self.cpu_usage_label = Gtk.Label()
        self.cpu_usage_label.set_markup("<b>Current CPU Usage: 0%</b>")
        usage_box.pack_start(self.cpu_usage_label, False, False, 0)
        
        # Memory info frame
        memory_frame = Gtk.Frame(label="Memory Information")
        performance_box.pack_start(memory_frame, False, False, 0)
        
        memory_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        memory_box.set_border_width(10)
        memory_frame.add(memory_box)
        
        # Memory labels
        self.memory_total_label = Gtk.Label()
        self.memory_total_label.set_xalign(0)
        memory_box.pack_start(self.memory_total_label, False, False, 0)
        
        self.memory_used_label = Gtk.Label()
        self.memory_used_label.set_xalign(0)
        memory_box.pack_start(self.memory_used_label, False, False, 0)
        
        self.memory_available_label = Gtk.Label()
        self.memory_available_label.set_xalign(0)
        memory_box.pack_start(self.memory_available_label, False, False, 0)
        
        # Add scrolled window for better handling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(performance_box)
        
        self.notebook.append_page(scrolled, Gtk.Label(label="Performance"))
        
    def create_processes_tab(self):
        """Create the Processes tab"""
        # Main container
        processes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        processes_box.set_border_width(10)
        
        # Control buttons
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        processes_box.pack_start(control_box, False, False, 0)
        
        # Search entry
        search_label = Gtk.Label(label="Search:")
        control_box.pack_start(search_label, False, False, 0)
        
        self.process_search_entry = Gtk.Entry()
        self.process_search_entry.set_placeholder_text("Filter processes...")
        self.process_search_entry.connect("changed", self.on_process_search_changed)
        control_box.pack_start(self.process_search_entry, True, True, 0)
        
        # End process button
        self.end_process_button = Gtk.Button(label="End Process")
        self.end_process_button.set_sensitive(False)
        self.end_process_button.connect("clicked", self.end_selected_process)
        control_box.pack_start(self.end_process_button, False, False, 0)
        
        # Process view with two sections
        paned = Gtk.VPaned()
        processes_box.pack_start(paned, True, True, 0)
        
        # My Processes section
        my_frame = Gtk.Frame(label=f"My Processes ({self.current_user})")
        
        my_scrolled = Gtk.ScrolledWindow()
        my_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        my_scrolled.set_min_content_height(200)
        
        # Create TreeView for my processes
        self.my_process_list_store = Gtk.ListStore(int, str, str, str, float, float, str, str)
        self.my_process_tree = Gtk.TreeView(model=self.my_process_list_store)
        
        # Add columns
        columns = [
            ("PID", 0, 60),
            ("Name", 1, 200),
            ("User", 2, 80),
            ("Status", 3, 80),
            ("CPU %", 4, 80),
            ("Memory %", 5, 80),
            ("Memory", 6, 100),
            ("Command", 7, 300)
        ]
        
        for title, index, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=index)
            column.set_resizable(True)
            column.set_min_width(width)
            column.set_sort_column_id(index)
            self.my_process_tree.append_column(column)
        
        self.my_process_tree.connect("row-activated", self.on_process_row_activated)
        self.my_process_tree.get_selection().connect("changed", self.on_process_selection_changed)
        
        my_scrolled.add(self.my_process_tree)
        my_frame.add(my_scrolled)
        paned.pack1(my_frame, resize=True, shrink=False)
        
        # System Processes section
        system_frame = Gtk.Frame(label="System Processes")
        
        system_scrolled = Gtk.ScrolledWindow()
        system_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        system_scrolled.set_min_content_height(200)
        
        # Create TreeView for system processes
        self.system_process_list_store = Gtk.ListStore(int, str, str, str, float, float, str, str)
        self.system_process_tree = Gtk.TreeView(model=self.system_process_list_store)
        
        # Add columns (same as my processes)
        for title, index, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=index)
            column.set_resizable(True)
            column.set_min_width(width)
            column.set_sort_column_id(index)
            self.system_process_tree.append_column(column)
        
        self.system_process_tree.connect("row-activated", self.on_process_row_activated)
        self.system_process_tree.get_selection().connect("changed", self.on_process_selection_changed)
        
        system_scrolled.add(self.system_process_tree)
        system_frame.add(system_scrolled)
        paned.pack2(system_frame, resize=True, shrink=False)
        
        # Set initial position
        paned.set_position(350)
        
        self.notebook.append_page(processes_box, Gtk.Label(label="Processes"))
        
    def create_users_tab(self):
        """Create the Users tab"""
        # Main container
        users_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        users_box.set_border_width(10)
        
        # Info frame
        info_frame = Gtk.Frame(label="Logged In Users")
        users_box.pack_start(info_frame, True, True, 0)
        
        # Scrolled window for users list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        info_frame.add(scrolled)
        
        # Create TreeView for users
        self.users_list_store = Gtk.ListStore(str, str, str, str, str, str)
        users_tree = Gtk.TreeView(model=self.users_list_store)
        
        # Add columns
        columns = [
            ("User", 0, 100),
            ("Terminal", 1, 100),
            ("From", 2, 150),
            ("Login Time", 3, 150),
            ("Idle", 4, 100),
            ("What", 5, 300)
        ]
        
        for title, index, width in columns:
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=index)
            column.set_resizable(True)
            column.set_min_width(width)
            self.users_tree = users_tree
            users_tree.append_column(column)
        
        scrolled.add(users_tree)
        
        # System info frame
        system_info_frame = Gtk.Frame(label="System Information")
        users_box.pack_start(system_info_frame, False, False, 0)
        
        system_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        system_info_box.set_border_width(10)
        system_info_frame.add(system_info_box)
        
        # System info labels
        self.hostname_label = Gtk.Label()
        self.hostname_label.set_xalign(0)
        system_info_box.pack_start(self.hostname_label, False, False, 0)
        
        self.kernel_label = Gtk.Label()
        self.kernel_label.set_xalign(0)
        system_info_box.pack_start(self.kernel_label, False, False, 0)
        
        self.uptime_label = Gtk.Label()
        self.uptime_label.set_xalign(0)
        system_info_box.pack_start(self.uptime_label, False, False, 0)
        
        self.load_avg_label = Gtk.Label()
        self.load_avg_label.set_xalign(0)
        system_info_box.pack_start(self.load_avg_label, False, False, 0)
        
        self.notebook.append_page(users_box, Gtk.Label(label="Users"))
        
    def init_performance_data(self):
        """Initialize performance data structures"""
        self.cpu_history_points = 60
        self.cpu_history = deque([0] * self.cpu_history_points, maxlen=self.cpu_history_points)
        self.memory_history = deque([0] * self.cpu_history_points, maxlen=self.cpu_history_points)
        
    def start_update_timer(self):
        """Start the update timer"""
        if self.update_timer_id:
            GLib.source_remove(self.update_timer_id)
        self.update_timer_id = GLib.timeout_add_seconds(self.update_interval, self.update_all_data)
        
    def on_interval_changed(self, widget, interval):
        """Handle update interval change"""
        if widget.get_active():
            self.update_interval = interval
            self.start_update_timer()
            self.update_status(f"Update interval changed to {interval} second(s)")
            
    def toggle_system_processes(self, widget):
        """Toggle visibility of system processes"""
        # This would be implemented to filter the process list
        self.refresh_processes()
        
    def refresh_all(self, widget=None):
        """Refresh all data"""
        self.update_all_data()
        self.update_status("Data refreshed")
        
    def update_all_data(self):
        """Update all data (called by timer)"""
        # Update based on current tab
        current_page = self.notebook.get_current_page()
        
        if current_page == 0:  # Performance tab
            self.update_performance_data()
        elif current_page == 1:  # Processes tab
            self.refresh_processes()
        elif current_page == 2:  # Users tab
            self.refresh_users()
            
        # Always update performance data for the graph
        self.update_performance_data()
        
        return True  # Continue timer
        
    def update_performance_data(self):
        """Update performance data"""
        try:
            # CPU info
            cpu_info = self.get_cpu_info()
            self.cpu_model_label.set_text(f"Model: {cpu_info['model']}")
            self.cpu_cores_label.set_text(f"Cores: {cpu_info['cores']} (Physical: {cpu_info['physical_cores']})")
            
            # CPU frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                self.cpu_freq_label.set_text(f"Frequency: {cpu_freq.current:.2f} MHz (Max: {cpu_freq.max:.2f} MHz)")
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_history.append(cpu_percent)
            self.cpu_usage_label.set_markup(f"<b>Current CPU Usage: {cpu_percent:.1f}%</b>")
            
            # Memory info
            memory = psutil.virtual_memory()
            self.memory_history.append(memory.percent)
            
            total_gb = memory.total / (1024**3)
            used_gb = memory.used / (1024**3)
            available_gb = memory.available / (1024**3)
            
            self.memory_total_label.set_text(f"Total: {total_gb:.2f} GB")
            self.memory_used_label.set_text(f"Used: {used_gb:.2f} GB ({memory.percent:.1f}%)")
            self.memory_available_label.set_text(f"Available: {available_gb:.2f} GB")
            
            # Redraw chart
            self.cpu_chart_area.queue_draw()
            
        except Exception as e:
            print(f"Error updating performance data: {e}")
            
    def get_cpu_info(self):
        """Get CPU information from /proc/cpuinfo"""
        cpu_info = {
            'model': 'Unknown',
            'cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False)
        }
        
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        cpu_info['model'] = line.split(':')[1].strip()
                        break
        except:
            pass
            
        return cpu_info
        
    def on_cpu_chart_draw(self, widget, cr):
        """Draw the CPU usage chart"""
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height
        
        if width <= 0 or height <= 0:
            return False
            
        # Background
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        
        # Draw grid
        cr.set_source_rgba(0.8, 0.8, 0.8, 0.5)
        cr.set_line_width(0.5)
        
        # Horizontal grid lines
        for i in range(5):
            y = int(height * i / 4)
            cr.move_to(0, y)
            cr.line_to(width, y)
        cr.stroke()
        
        # Vertical grid lines
        for i in range(0, self.cpu_history_points + 1, 10):
            x = int(width * i / self.cpu_history_points)
            cr.move_to(x, 0)
            cr.line_to(x, height)
        cr.stroke()
        
        # Draw axes
        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.set_line_width(1.5)
        cr.move_to(0, height - 1)
        cr.line_to(width, height - 1)
        cr.move_to(1, 0)
        cr.line_to(1, height)
        cr.stroke()
        
        # Draw CPU usage
        if len(self.cpu_history) > 1:
            point_spacing = width / max(1, (self.cpu_history_points - 1))
            
            # Draw filled area
            cr.set_source_rgba(0.13, 0.59, 0.95, 0.3)
            cr.move_to(0, height)
            for i, value in enumerate(self.cpu_history):
                x = i * point_spacing
                y = height - (value / 100 * height * 0.9)
                cr.line_to(x, y)
            cr.line_to(width, height)
            cr.close_path()
            cr.fill()
            
            # Draw line
            cr.set_source_rgb(0.13, 0.59, 0.95)
            cr.set_line_width(2)
            for i, value in enumerate(self.cpu_history):
                x = i * point_spacing
                y = height - (value / 100 * height * 0.9)
                if i == 0:
                    cr.move_to(x, y)
                else:
                    cr.line_to(x, y)
            cr.stroke()
            
            # Draw memory usage line
            cr.set_source_rgb(0.30, 0.69, 0.31)
            cr.set_line_width(2)
            for i, value in enumerate(self.memory_history):
                x = i * point_spacing
                y = height - (value / 100 * height * 0.9)
                if i == 0:
                    cr.move_to(x, y)
                else:
                    cr.line_to(x, y)
            cr.stroke()
            
        # Draw legend
        cr.set_source_rgb(0.13, 0.59, 0.95)
        cr.rectangle(10, 10, 15, 10)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 0)
        cr.set_font_size(12)
        cr.move_to(30, 20)
        cr.show_text("CPU")
        
        cr.set_source_rgb(0.30, 0.69, 0.31)
        cr.rectangle(80, 10, 15, 10)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        cr.move_to(100, 20)
        cr.show_text("Memory")
        
        # Draw border
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.set_line_width(1)
        cr.rectangle(0.5, 0.5, width - 1, height - 1)
        cr.stroke()
        
        return False
        
    def refresh_processes(self):
        """Refresh the process list"""
        try:
            # Clear existing data
            self.my_process_list_store.clear()
            self.system_process_list_store.clear()
            
            # Get search filter
            search_text = self.process_search_entry.get_text().lower()
            
            # Get all processes
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 
                                           'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    info = proc.info
                    
                    # Filter by search text
                    if search_text and search_text not in info['name'].lower():
                        continue
                        
                    # Format memory
                    if info['memory_info']:
                        memory_mb = info['memory_info'].rss / (1024 * 1024)
                        memory_str = f"{memory_mb:.1f} MB"
                    else:
                        memory_str = "N/A"
                        
                    # Get command line
                    try:
                        cmdline = ' '.join(proc.cmdline())[:100]
                        if not cmdline:
                            cmdline = info['name']
                    except:
                        cmdline = info['name']
                        
                    # Create row data
                    row_data = [
                        info['pid'],
                        info['name'],
                        info['username'] or 'N/A',
                        info['status'],
                        info['cpu_percent'] or 0,
                        info['memory_percent'] or 0,
                        memory_str,
                        cmdline
                    ]
                    
                    # Add to appropriate list
                    if info['username'] == self.current_user:
                        self.my_process_list_store.append(row_data)
                    elif self.show_system_processes.get_active():
                        self.system_process_list_store.append(row_data)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            print(f"Error refreshing processes: {e}")
            
    def refresh_users(self):
        """Refresh the users list"""
        try:
            # Clear existing data
            self.users_list_store.clear()
            
            # Run 'w' command
            result = subprocess.run(['w', '-h'], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line:
                        parts = line.split(None, 7)
                        if len(parts) >= 5:
                            user = parts[0]
                            tty = parts[1]
                            from_host = parts[2]
                            login_time = parts[3]
                            idle = parts[4] if len(parts) > 4 else ''
                            what = parts[7] if len(parts) > 7 else parts[6] if len(parts) > 6 else ''
                            
                            self.users_list_store.append([
                                user, tty, from_host, login_time, idle, what
                            ])
                            
            # Update system info
            self.hostname_label.set_text(f"Hostname: {platform.node()}")
            self.kernel_label.set_text(f"Kernel: {platform.release()}")
            
            # Uptime
            uptime_seconds = time.time() - psutil.boot_time()
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            self.uptime_label.set_text(f"Uptime: {days} days, {hours} hours, {minutes} minutes")
            
            # Load average
            load_avg = os.getloadavg()
            self.load_avg_label.set_text(f"Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
            
        except Exception as e:
            print(f"Error refreshing users: {e}")
            
    def on_process_search_changed(self, widget):
        """Handle process search text change"""
        self.refresh_processes()
        
    def on_process_row_activated(self, tree_view, path, column):
        """Handle double-click on process"""
        # Could show process details dialog
        pass
        
    def on_process_selection_changed(self, selection):
        """Handle process selection change"""
        model, treeiter = selection.get_selected()
        self.end_process_button.set_sensitive(treeiter is not None)
        
    def end_selected_process(self, widget):
        """End the selected process"""
        # Get selected process from either tree
        selection = None
        for tree in [self.my_process_tree, self.system_process_tree]:
            sel = tree.get_selection()
            model, treeiter = sel.get_selected()
            if treeiter:
                selection = (model, treeiter)
                break
                
        if not selection:
            return
            
        model, treeiter = selection
        pid = model[treeiter][0]
        name = model[treeiter][1]
        
        # Confirm dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"End Process?"
        )
        dialog.format_secondary_text(
            f"Do you want to end the process '{name}' (PID: {pid})?\n\n"
            "This will terminate the process and may cause data loss."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                os.kill(pid, signal.SIGTERM)
                self.update_status(f"Process {name} (PID: {pid}) terminated")
                # Refresh process list
                GLib.timeout_add(500, self.refresh_processes)
            except ProcessLookupError:
                self.show_error("Process no longer exists")
            except PermissionError:
                self.show_error("Permission denied. Cannot terminate this process.")
            except Exception as e:
                self.show_error(f"Failed to terminate process: {str(e)}")
                
    def update_status(self, message):
        """Update status bar"""
        context_id = self.statusbar.get_context_id("main")
        self.statusbar.push(context_id, message)
        
    def show_error(self, message):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        print("Error: psutil module not found.")
        print("Please install it with: pip install psutil")
        print("or: sudo apt install python3-psutil")
        exit(1)
        
    win = TaskManager()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()