import sys
import psutil
import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import pyqtgraph as pg
import numpy as np
from datetime import datetime
import platform

class ThemeColors:
    DARK = {
        'primary_bg': '#1E1E2E',
        'secondary_bg': '#282A36',
        'text': '#EAEAEA',
        'border': '#4A4A4A',
        'progress_normal': '#4CAF50',
        'progress_warning': '#FFA500',
        'progress_critical': '#FF4C4C',
        'graph_cpu': '#00BFFF',
        'graph_memory': '#FFD700',
        'button_refresh': '#4CAF50',
        'button_kill': '#FF4C4C',
        'button_settings': '#8A2BE2'
    }
    
    LIGHT = {
        'primary_bg': '#F5F5F5',
        'secondary_bg': '#E0E0E0',
        'text': '#212121',
        'border': '#BDBDBD',
        'progress_normal': '#008000',
        'progress_warning': '#FF8C00',
        'progress_critical': '#D32F2F',
        'graph_cpu': '#1976D2',
        'graph_memory': '#FFD700',
        'button_refresh': '#1976D2',
        'button_kill': '#D32F2F',
        'button_settings': '#673AB7'
    }
    
    CYBERPUNK = {
        'primary_bg': '#0D1117',
        'secondary_bg': '#161B22',
        'text': '#39FF14',
        'border': '#00FFFF',
        'progress_normal': '#39FF14',
        'progress_warning': '#FFBF00',
        'progress_critical': '#FF3131',
        'graph_cpu': '#FF007F',
        'graph_memory': '#00FFFF',
        'button_refresh': '#00FFFF',
        'button_kill': '#FF3131',
        'button_settings': '#8A2BE2'
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
        
        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Theme", "Light Theme", "Cyberpunk Theme"])
        
        # Buttons
        self.refresh_btn = QPushButton("⟳ Refresh")
        self.kill_btn = QPushButton("⚠ Kill Process")
        self.settings_btn = QPushButton("⚙ Settings")
        
        layout.addWidget(self.theme_combo)
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
        
        self.theme_combo.setStyleSheet(f"""
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

class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.setup_ui()
        
    def setup_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # CPU Usage Display
        cpu_frame = QFrame()
        cpu_layout = QVBoxLayout(cpu_frame)
        
        self.cpu_label = QLabel("CPU Usage")
        self.cpu_value = QLabel("0%")
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_value)
        cpu_layout.addWidget(self.cpu_progress)
        
        # Memory Usage Display
        mem_frame = QFrame()
        mem_layout = QVBoxLayout(mem_frame)
        
        self.mem_label = QLabel("Memory Usage")
        self.mem_value = QLabel("0%")
        self.mem_progress = QProgressBar()
        self.mem_progress.setRange(0, 100)
        
        mem_layout.addWidget(self.mem_label)
        mem_layout.addWidget(self.mem_value)
        mem_layout.addWidget(self.mem_progress)
        
        # Add frames to main layout
        layout.addWidget(cpu_frame)
        layout.addWidget(mem_frame)
        
        # Setup update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec())