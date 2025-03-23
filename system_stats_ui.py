import sys
import psutil
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import pyqtgraph as pg
import numpy as np

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