import sys
import psutil
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import pyqtgraph as pg
import numpy as np
from datetime import datetime

class ThemeColors:
    DARK = {
        'primary_bg': '#1E1E2E',
        'secondary_bg': '#282A36',
        'text': '#EAEAEA',
        'border': '#4A4A4A',
        'progress_normal': '#4CAF50',
        'progress_warning': '#FFA500',
        'progress_critical': '#FF4C4C'
    }
    
    LIGHT = {
        'primary_bg': '#F5F5F5',
        'secondary_bg': '#E0E0E0',
        'text': '#212121',
        'border': '#BDBDBD',
        'progress_normal': '#008000',
        'progress_warning': '#FF8C00',
        'progress_critical': '#D32F2F'
    }
    
    CYBERPUNK = {
        'primary_bg': '#0D1117',
        'secondary_bg': '#161B22',
        'text': '#39FF14',
        'border': '#00FFFF',
        'progress_normal': '#39FF14',
        'progress_warning': '#FFBF00',
        'progress_critical': '#FF3131'
    }

class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.current_theme = ThemeColors.DARK
        self.setup_ui()
        self.apply_theme(self.current_theme)
        
    def setup_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
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
        
        cpu_layout.addLayout(cpu_header)
        cpu_layout.addWidget(self.cpu_progress)
        
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
        
        mem_layout.addLayout(mem_header)
        mem_layout.addWidget(self.mem_progress)
        
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
        
        process_layout.addWidget(process_label)
        process_layout.addWidget(self.process_table)
        
        # Add all components to main layout
        layout.addLayout(theme_layout)
        layout.addWidget(cpu_frame)
        layout.addWidget(mem_frame)
        layout.addWidget(process_frame)
        
        # Setup update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        
        # Window settings
        self.setMinimumSize(800, 600)
        
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
        
    def update_stats(self):
        # Update CPU
        cpu_percent = psutil.cpu_percent()
        self.cpu_value.setText(f"{cpu_percent}%")
        self.cpu_progress.setValue(int(cpu_percent))
        
        # Update Memory
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        self.mem_value.setText(f"{mem_percent}%")
        self.mem_progress.setValue(int(mem_percent))
        
        # Update progress bar colors
        self.update_progress_colors()
        
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