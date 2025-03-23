import sys
import psutil
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import pyqtgraph as pg
import numpy as np
from datetime import datetime

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
        
        # Process List
        process_frame = QFrame()
        process_layout = QVBoxLayout(process_frame)
        
        process_label = QLabel("Active Processes")
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "CPU %", "Memory %", "Status", "User", "Start Time"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        process_layout.addWidget(process_label)
        process_layout.addWidget(self.process_table)
        
        # Add frames to main layout
        layout.addWidget(cpu_frame)
        layout.addWidget(mem_frame)
        layout.addWidget(process_frame)
        
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