import sys
import psutil
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import pyqtgraph as pg
import numpy as np
from datetime import datetime
import platform
import time

class ThemeColors:
    DARK = {
        'primary_bg': '#1E1E2E',
        'secondary_bg': '#282A36',
        'text': '#EAEAEA',
        'border': '#4A4A4A',
        'progress_normal': '#4CAF50',
        'progress_warning': '#FFA500',
        'progress_critical': '#FF4C4C',
        'button_refresh': '#4CAF50',
        'button_kill': '#FF4C4C',
        'button_settings': '#8A2BE2',
        'graph_cpu': '#00BFFF',
        'graph_memory': '#FFD700',
        'graph_network': '#FF69B4',
        'graph_temperature': '#FF4500'
    }
    
    LIGHT = {
        'primary_bg': '#F5F5F5',
        'secondary_bg': '#E0E0E0',
        'text': '#212121',
        'border': '#BDBDBD',
        'progress_normal': '#008000',
        'progress_warning': '#FF8C00',
        'progress_critical': '#D32F2F',
        'button_refresh': '#1976D2',
        'button_kill': '#D32F2F',
        'button_settings': '#673AB7',
        'graph_cpu': '#1976D2',
        'graph_memory': '#FFD700',
        'graph_network': '#E91E63',
        'graph_temperature': '#F44336'
    }
    
    CYBERPUNK = {
        'primary_bg': '#0D1117',
        'secondary_bg': '#161B22',
        'text': '#39FF14',
        'border': '#00FFFF',
        'progress_normal': '#39FF14',
        'progress_warning': '#FFBF00',
        'progress_critical': '#FF3131',
        'button_refresh': '#00FFFF',
        'button_kill': '#FF3131',
        'button_settings': '#8A2BE2',
        'graph_cpu': '#FF007F',
        'graph_memory': '#00FFFF',
        'graph_network': '#FF00FF',
        'graph_temperature': '#FF1493'
    }

class AlertPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Alert settings
        self.cpu_threshold = 80
        self.memory_threshold = 70
        
        # Header with minimize button
        header_layout = QHBoxLayout()
        header_label = QLabel("Alerts & Notifications")
        header_label.setStyleSheet("font-weight: bold;")
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFixedSize(20, 20)
        
        header_layout.addWidget(header_label)
        header_layout.addWidget(self.minimize_btn)
        
        # Alerts list
        self.alerts_list = QListWidget()
        self.alerts_list.setMaximumHeight(150)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.alerts_list)
        
    def add_alert(self, message, level="warning"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{timestamp}] {message}")
        if level == "critical":
            item.setForeground(QColor("#FF4C4C"))
        elif level == "warning":
            item.setForeground(QColor("#FFA500"))
        self.alerts_list.insertItem(0, item)
        if self.alerts_list.count() > 100:
            self.alerts_list.takeItem(self.alerts_list.count() - 1)
            
    def apply_theme(self, colors):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['secondary_bg']};
                border: 1px solid {colors['border']};
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QPushButton {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
            QListWidget {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
            }}
        """)

class ProcessControlPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Buttons
        self.refresh_btn = QPushButton("⟳ Refresh")
        self.kill_btn = QPushButton("⚠ Kill Process")
        self.settings_btn = QPushButton("⚙ Settings")
        
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.kill_btn)
        layout.addWidget(self.settings_btn)
        layout.addStretch()
        
    def apply_theme(self, colors):
        button_style = f"""
            QPushButton {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px 15px;
                border-radius: 5px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_settings']};
            }}
        """
        
        self.refresh_btn.setStyleSheet(button_style.replace(colors['button_settings'], colors['button_refresh']))
        self.kill_btn.setStyleSheet(button_style.replace(colors['button_settings'], colors['button_kill']))
        self.settings_btn.setStyleSheet(button_style)

class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.current_theme = ThemeColors.DARK
        self.setup_ui()
        self.apply_theme(self.current_theme)
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        
    def setup_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QGridLayout(main_widget)
        layout.setSpacing(10)
        
        # Theme selector
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Theme", "Light Theme", "Cyberpunk Theme"])
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        # System Information Panel
        sys_info_frame = QFrame()
        sys_info_layout = QVBoxLayout(sys_info_frame)
        sys_info_layout.setSpacing(5)
        
        sys_info_label = QLabel("SYSTEM INFORMATION")
        sys_info_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.sys_info_table = QTableWidget()
        self.sys_info_table.setColumnCount(2)
        self.sys_info_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.sys_info_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sys_info_table.setMaximumHeight(150)
        
        sys_info_layout.addWidget(sys_info_label)
        sys_info_layout.addWidget(self.sys_info_table)
        
        # CPU Usage Display
        cpu_frame = QFrame()
        cpu_layout = QVBoxLayout(cpu_frame)
        cpu_layout.setSpacing(5)
        
        cpu_header = QHBoxLayout()
        self.cpu_label = QLabel("CPU USAGE")
        self.cpu_value = QLabel("0%")
        self.cpu_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        cpu_header.addWidget(self.cpu_label)
        cpu_header.addWidget(self.cpu_value)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        
        # CPU Graph
        self.cpu_plot = pg.PlotWidget(background=None)
        self.cpu_plot.setMaximumHeight(100)
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.showGrid(True, True, alpha=0.3)
        self.cpu_data = np.zeros(30)
        
        self.cpu_bars = pg.BarGraphItem(
            x=range(len(self.cpu_data)),
            height=self.cpu_data,
            width=0.8,
            brush=self.current_theme['graph_cpu'],
            pen=None
        )
        self.cpu_plot.addItem(self.cpu_bars)
        self.cpu_plot.getAxis('bottom').setStyle(showValues=False)
        
        cpu_layout.addLayout(cpu_header)
        cpu_layout.addWidget(self.cpu_progress)
        cpu_layout.addWidget(self.cpu_plot)
        
        # Memory Usage Display
        mem_frame = QFrame()
        mem_layout = QVBoxLayout(mem_frame)
        mem_layout.setSpacing(5)
        
        mem_header = QHBoxLayout()
        self.mem_label = QLabel("MEMORY USAGE")
        self.mem_value = QLabel("0%")
        self.mem_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        mem_header.addWidget(self.mem_label)
        mem_header.addWidget(self.mem_value)
        
        self.mem_progress = QProgressBar()
        self.mem_progress.setRange(0, 100)
        
        # Memory Graph
        self.mem_plot = pg.PlotWidget(background=None)
        self.mem_plot.setMaximumHeight(100)
        self.mem_plot.setYRange(0, 100)
        self.mem_plot.showGrid(True, True, alpha=0.3)
        self.mem_data = np.zeros(30)
        
        self.mem_bars = pg.BarGraphItem(
            x=range(len(self.mem_data)),
            height=self.mem_data,
            width=0.8,
            brush=self.current_theme['graph_memory'],
            pen=None
        )
        self.mem_plot.addItem(self.mem_bars)
        self.mem_plot.getAxis('bottom').setStyle(showValues=False)
        
        mem_layout.addLayout(mem_header)
        mem_layout.addWidget(self.mem_progress)
        mem_layout.addWidget(self.mem_plot)
        
        # Disk Usage Display
        disk_frame = QFrame()
        disk_layout = QVBoxLayout(disk_frame)
        disk_layout.setSpacing(5)
        
        disk_header = QHBoxLayout()
        self.disk_label = QLabel("DISK USAGE")
        self.disk_value = QLabel("0%")
        self.disk_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        disk_header.addWidget(self.disk_label)
        disk_header.addWidget(self.disk_value)
        
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        
        # Disk Graph
        self.disk_plot = pg.PlotWidget(background=None)
        self.disk_plot.setMaximumHeight(100)
        self.disk_plot.setYRange(0, 100)
        self.disk_plot.showGrid(True, True, alpha=0.3)
        self.disk_data = np.zeros(30)
        
        self.disk_bars = pg.BarGraphItem(
            x=range(len(self.disk_data)),
            height=self.disk_data,
            width=0.8,
            brush=self.current_theme['graph_memory'],
            pen=None
        )
        self.disk_plot.addItem(self.disk_bars)
        self.disk_plot.getAxis('bottom').setStyle(showValues=False)
        
        disk_layout.addLayout(disk_header)
        disk_layout.addWidget(self.disk_progress)
        disk_layout.addWidget(self.disk_plot)
        
        # Network Usage Display
        network_frame = QFrame()
        network_layout = QVBoxLayout(network_frame)
        network_layout.setSpacing(5)
        
        network_header = QHBoxLayout()
        self.network_label = QLabel("NETWORK USAGE")
        self.network_value = QLabel("0 MB/s")
        self.network_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        network_header.addWidget(self.network_label)
        network_header.addWidget(self.network_value)
        
        self.network_progress = QProgressBar()
        self.network_progress.setRange(0, 100)
        
        # Network Graph
        self.network_plot = pg.PlotWidget(background=None)
        self.network_plot.setMaximumHeight(100)
        self.network_plot.setYRange(0, 100)
        self.network_plot.showGrid(True, True, alpha=0.3)
        self.network_data = np.zeros(30)
        
        self.network_bars = pg.BarGraphItem(
            x=range(len(self.network_data)),
            height=self.network_data,
            width=0.8,
            brush=self.current_theme['graph_network'],
            pen=None
        )
        self.network_plot.addItem(self.network_bars)
        self.network_plot.getAxis('bottom').setStyle(showValues=False)
        
        network_layout.addLayout(network_header)
        network_layout.addWidget(self.network_progress)
        network_layout.addWidget(self.network_plot)
        
        # Temperature Display
        temp_frame = QFrame()
        temp_layout = QVBoxLayout(temp_frame)
        temp_layout.setSpacing(5)
        
        temp_header = QHBoxLayout()
        self.temp_label = QLabel("CPU TEMPERATURE")
        self.temp_value = QLabel("0°C")
        self.temp_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        temp_header.addWidget(self.temp_label)
        temp_header.addWidget(self.temp_value)
        
        self.temp_progress = QProgressBar()
        self.temp_progress.setRange(0, 100)
        
        # Temperature Graph
        self.temp_plot = pg.PlotWidget(background=None)
        self.temp_plot.setMaximumHeight(100)
        self.temp_plot.setYRange(0, 100)
        self.temp_plot.showGrid(True, True, alpha=0.3)
        self.temp_data = np.zeros(30)
        
        self.temp_bars = pg.BarGraphItem(
            x=range(len(self.temp_data)),
            height=self.temp_data,
            width=0.8,
            brush=self.current_theme['graph_temperature'],
            pen=None
        )
        self.temp_plot.addItem(self.temp_bars)
        self.temp_plot.getAxis('bottom').setStyle(showValues=False)
        
        temp_layout.addLayout(temp_header)
        temp_layout.addWidget(self.temp_progress)
        temp_layout.addWidget(self.temp_plot)
        
        # Process List
        process_frame = QFrame()
        process_layout = QVBoxLayout(process_frame)
        
        process_label = QLabel("ACTIVE PROCESSES")
        process_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "CPU %", "Memory %", "Status", "User", "Start Time"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        process_layout.addWidget(process_label)
        process_layout.addWidget(self.process_table)
        
        # Control Panel
        self.control_panel = ProcessControlPanel()
        
        # Alert Panel
        self.alert_panel = AlertPanel()
        self.alert_panel.setMaximumWidth(300)
        
        # Connect signals
        self.control_panel.refresh_btn.clicked.connect(self.update_stats)
        self.control_panel.kill_btn.clicked.connect(self.kill_selected_process)
        
        # Add all components to main layout
        layout.addLayout(theme_layout, 0, 0, 1, 2)
        layout.addWidget(sys_info_frame, 1, 0)
        layout.addWidget(cpu_frame, 1, 1)
        layout.addWidget(mem_frame, 2, 0)
        layout.addWidget(disk_frame, 2, 1)
        layout.addWidget(network_frame, 3, 0)
        layout.addWidget(temp_frame, 3, 1)
        layout.addWidget(process_frame, 4, 0)
        layout.addWidget(self.control_panel, 4, 1)
        layout.addWidget(self.alert_panel, 5, 0, 1, 2)
        
        # Update system information
        self.update_system_info()
        
        # Setup update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        
        # Window settings
        self.setMinimumSize(1200, 1000)
        
    def change_theme(self, theme_name):
        if theme_name == "Dark Theme":
            self.current_theme = ThemeColors.DARK
        elif theme_name == "Light Theme":
            self.current_theme = ThemeColors.LIGHT
        else:
            self.current_theme = ThemeColors.CYBERPUNK
        self.apply_theme(self.current_theme)
        
    def apply_theme(self, colors):
        # Main window theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['primary_bg']};
            }}
            QWidget {{
                background-color: {colors['primary_bg']};
                color: {colors['text']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QFrame {{
                background-color: {colors['secondary_bg']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
            }}
            QTableWidget {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                gridline-color: {colors['border']};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px;
            }}
            QProgressBar {{
                border: 1px solid {colors['border']};
                border-radius: 5px;
                text-align: center;
                background-color: {colors['secondary_bg']};
                max-height: 15px;
            }}
            QProgressBar::chunk {{
                background-color: {colors['progress_normal']};
                border-radius: 5px;
            }}
            QComboBox {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px;
                border-radius: 5px;
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid {colors['border']};
                height: 10px;
            }}
        """)
        
        # Update progress bar colors based on usage
        self.update_progress_colors()
        
        # Apply theme to panels
        self.alert_panel.apply_theme(colors)
        self.control_panel.apply_theme(colors)
        
        # Update plot colors
        self.cpu_plot.setBackground(colors['secondary_bg'])
        self.mem_plot.setBackground(colors['secondary_bg'])
        self.disk_plot.setBackground(colors['secondary_bg'])
        self.network_plot.setBackground(colors['secondary_bg'])
        self.temp_plot.setBackground(colors['secondary_bg'])
        
        # Update bar colors
        self.cpu_bars.setOpts(brush=colors['graph_cpu'])
        self.mem_bars.setOpts(brush=colors['graph_memory'])
        self.disk_bars.setOpts(brush=colors['graph_memory'])
        self.network_bars.setOpts(brush=colors['graph_network'])
        self.temp_bars.setOpts(brush=colors['graph_temperature'])
        
    def update_progress_colors(self):
        # CPU Progress Bar
        cpu_value = self.cpu_progress.value()
        if cpu_value >= 90:
            color = self.current_theme['progress_critical']
        elif cpu_value >= 80:
            color = self.current_theme['progress_warning']
        else:
            color = self.current_theme['progress_normal']
        self.cpu_progress.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        
        # Memory Progress Bar
        mem_value = self.mem_progress.value()
        if mem_value >= 90:
            color = self.current_theme['progress_critical']
        elif mem_value >= 80:
            color = self.current_theme['progress_warning']
        else:
            color = self.current_theme['progress_normal']
        self.mem_progress.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        
    def kill_selected_process(self):
        selected_items = self.process_table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        pid = int(self.process_table.item(row, 0).text())
        try:
            psutil.Process(pid).terminate()
            self.alert_panel.add_alert(f"Process {pid} terminated", "warning")
        except psutil.NoSuchProcess:
            self.alert_panel.add_alert(f"Process {pid} not found", "critical")
        except psutil.AccessDenied:
            self.alert_panel.add_alert(f"Access denied to terminate process {pid}", "critical")
        
    def update_system_info(self):
        # Get system information
        info = [
            ["OS", f"{platform.system()} {platform.release()}"],
            ["CPU", platform.processor()],
            ["CPU Cores", str(psutil.cpu_count())],
            ["Total Memory", f"{psutil.virtual_memory().total / (1024**3):.1f} GB"],
            ["Boot Time", datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")],
            ["Python Version", platform.python_version()],
            ["Machine", platform.machine()],
            ["Node", platform.node()]
        ]
        
        self.sys_info_table.setRowCount(len(info))
        for i, (key, value) in enumerate(info):
            key_item = QTableWidgetItem(key)
            value_item = QTableWidgetItem(value)
            key_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            value_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.sys_info_table.setItem(i, 0, key_item)
            self.sys_info_table.setItem(i, 1, value_item)
        
    def update_stats(self):
        # Update CPU
        cpu_percent = psutil.cpu_percent()
        self.cpu_value.setText(f"{cpu_percent}%")
        self.cpu_progress.setValue(int(cpu_percent))
        self.cpu_data = np.roll(self.cpu_data, -1)
        self.cpu_data[-1] = cpu_percent
        self.cpu_bars.setOpts(height=self.cpu_data)
        
        # Update Memory
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        self.mem_value.setText(f"{mem_percent}%")
        self.mem_progress.setValue(int(mem_percent))
        self.mem_data = np.roll(self.mem_data, -1)
        self.mem_data[-1] = mem_percent
        self.mem_bars.setOpts(height=self.mem_data)
        
        # Update Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        self.disk_value.setText(f"{disk_percent}%")
        self.disk_progress.setValue(int(disk_percent))
        self.disk_data = np.roll(self.disk_data, -1)
        self.disk_data[-1] = disk_percent
        self.disk_bars.setOpts(height=self.disk_data)
        
        # Update Network
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        time_diff = current_time - self.last_net_time
        
        if time_diff > 0:
            bytes_sent = current_net_io.bytes_sent - self.last_net_io.bytes_sent
            bytes_recv = current_net_io.bytes_recv - self.last_net_io.bytes_recv
            total_bytes = bytes_sent + bytes_recv
            mb_per_sec = total_bytes / (1024 * 1024 * time_diff)
            
            self.network_value.setText(f"{mb_per_sec:.1f} MB/s")
            self.network_progress.setValue(min(int(mb_per_sec * 10), 100))
            
            self.network_data = np.roll(self.network_data, -1)
            self.network_data[-1] = min(mb_per_sec * 10, 100)
            self.network_bars.setOpts(height=self.network_data)
            
            if mb_per_sec > 10:  # Alert if network usage is high
                self.alert_panel.add_alert(f"High Network usage: {mb_per_sec:.1f} MB/s", "warning")
        
        self.last_net_io = current_net_io
        self.last_net_time = current_time
        
        # Update Temperature
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Get the first available temperature sensor
                for name, entries in temps.items():
                    if entries:
                        temp = entries[0].current
                        self.temp_value.setText(f"{temp:.1f}°C")
                        self.temp_progress.setValue(min(int(temp), 100))
                        
                        self.temp_data = np.roll(self.temp_data, -1)
                        self.temp_data[-1] = min(temp, 100)
                        self.temp_bars.setOpts(height=self.temp_data)
                        
                        if temp > 80:  # Alert if temperature is high
                            self.alert_panel.add_alert(f"High CPU Temperature: {temp:.1f}°C", "critical")
                        break
        except:
            self.temp_value.setText("N/A")
            self.temp_progress.setValue(0)
        
        # Update progress bar colors
        self.update_progress_colors()
        
        # Check CPU threshold
        if cpu_percent > self.alert_panel.cpu_threshold:
            self.alert_panel.add_alert(f"High CPU usage: {cpu_percent}%", "critical")
        
        # Check Memory threshold
        if mem_percent > self.alert_panel.memory_threshold:
            self.alert_panel.add_alert(f"High Memory usage: {mem_percent}%", "critical")
        
        # Check Disk threshold
        if disk_percent > self.alert_panel.memory_threshold:
            self.alert_panel.add_alert(f"High Disk usage: {disk_percent}%", "critical")
        
        # Update Process List
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username', 'create_time']):
            try:
                pinfo = proc.info
                cpu_percent = pinfo['cpu_percent'] if pinfo['cpu_percent'] is not None else 0.0
                mem_percent = pinfo['memory_percent'] if pinfo['memory_percent'] is not None else 0.0
                create_time = datetime.fromtimestamp(pinfo['create_time']).strftime('%H:%M:%S')
                processes.append([
                    str(pinfo['pid']),
                    pinfo['name'],
                    f"{cpu_percent:.1f}",
                    f"{mem_percent:.1f}",
                    pinfo['status'],
                    pinfo['username'],
                    create_time
                ])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processes.sort(key=lambda x: float(x[2]), reverse=True)
        self.process_table.setRowCount(min(len(processes), 15))
        
        for i, proc in enumerate(processes[:15]):
            for j, value in enumerate(proc):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.process_table.setItem(i, j, item)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec())