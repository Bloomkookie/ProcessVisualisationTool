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
import random

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
        'primary_bg': '#FFFFFF',  # Pure White
        'secondary_bg': '#F5F5F5',  # Light Gray
        'text': '#333333',  # Dark Gray
        'border': '#D3D3D3',  # Light Gray for borders
        'progress_normal': '#32CD32',  # Lime Green for success
        'progress_warning': '#FFD700',  # Gold for warning
        'progress_critical': '#FF4500',  # Orange Red for error
        'graph_cpu': '#1E90FF',  # Dodger Blue
        'graph_memory': '#32CD32',  # Lime Green
        'button_refresh': '#1E90FF',  # Dodger Blue
        'button_kill': '#FF4500',  # Orange Red
        'button_settings': '#FF8C00'  # Dark Orange
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

class Process:
    def __init__(self, pid, name, burst_time, priority=0, arrival_time=0):
        self.pid = pid
        self.name = name
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.arrival_time = arrival_time
        self.waiting_time = 0
        self.turnaround_time = 0
        self.completed = False
        self.start_time = -1
        self.end_time = -1

class SchedulingWindow(QMainWindow):
    def __init__(self, algorithm, parent=None):
        super().__init__(parent)
        self.algorithm = algorithm
        self.processes = []
        self.setup_ui()
        self.load_processes()
        
    def setup_ui(self):
        self.setWindowTitle(f"CPU Scheduling - {self.algorithm}")
        self.setMinimumSize(800, 600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Control panel
        control_panel = QHBoxLayout()
        
        # Time Quantum input only for Round Robin
        if self.algorithm == "Round Robin":
            self.quantum_label = QLabel("Time Quantum:")
            self.quantum_input = QSpinBox()
            self.quantum_input.setRange(1, 10)
            self.quantum_input.setValue(2)
            control_panel.addWidget(self.quantum_label)
            control_panel.addWidget(self.quantum_input)
        
        self.start_btn = QPushButton("Start Simulation")
        self.reset_btn = QPushButton("Reset")
        control_panel.addWidget(self.start_btn)
        control_panel.addWidget(self.reset_btn)
        control_panel.addStretch()
        
        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "Burst Time", "Priority", "Arrival Time", "Waiting Time", "Turnaround Time"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Gantt chart
        self.gantt_chart = pg.PlotWidget(background=None)
        self.gantt_chart.setMinimumHeight(100)
        self.gantt_chart.showGrid(True, True, alpha=0.3)
        
        # Add all components to main layout
        layout.addLayout(control_panel)
        layout.addWidget(self.process_table)
        layout.addWidget(self.gantt_chart)
        
        # Connect signals
        self.start_btn.clicked.connect(self.start_simulation)
        self.reset_btn.clicked.connect(self.reset_simulation)
        
    def load_processes(self):
        # Get processes from parent window
        parent = self.parent()
        if parent and hasattr(parent, 'process_table'):
            for row in range(parent.process_table.rowCount()):
                pid = int(parent.process_table.item(row, 0).text())
                name = parent.process_table.item(row, 1).text()
                cpu_percent = float(parent.process_table.item(row, 2).text())
                
                # Convert CPU percentage to burst time (1-10)
                burst_time = max(1, min(10, int(cpu_percent / 10)))
                
                # Create process with random priority and arrival time
                process = Process(
                    pid=pid,
                    name=name,
                    burst_time=burst_time,
                    priority=random.randint(1, 5),
                    arrival_time=random.randint(0, 5)
                )
                self.processes.append(process)
        
        self.update_table()
        
    def update_table(self):
        self.process_table.setRowCount(len(self.processes))
        for i, proc in enumerate(self.processes):
            self.process_table.setItem(i, 0, QTableWidgetItem(str(proc.pid)))
            self.process_table.setItem(i, 1, QTableWidgetItem(proc.name))
            self.process_table.setItem(i, 2, QTableWidgetItem(str(proc.burst_time)))
            self.process_table.setItem(i, 3, QTableWidgetItem(str(proc.priority)))
            self.process_table.setItem(i, 4, QTableWidgetItem(str(proc.arrival_time)))
            self.process_table.setItem(i, 5, QTableWidgetItem(f"{proc.waiting_time:.2f}"))
            self.process_table.setItem(i, 6, QTableWidgetItem(f"{proc.turnaround_time:.2f}"))
            
    def start_simulation(self):
        # Reset process states
        for proc in self.processes:
            proc.remaining_time = proc.burst_time
            proc.waiting_time = 0
            proc.turnaround_time = 0
            proc.completed = False
        
        # Get time quantum for Round Robin
        quantum = self.quantum_input.value() if self.algorithm == "Round Robin" else 0
        
        # Run the selected algorithm
        if self.algorithm == "FCFS":
            self.run_fcfs()
        elif self.algorithm == "Round Robin":
            self.run_round_robin(quantum)
        elif self.algorithm == "Priority":
            self.run_priority()
        elif self.algorithm == "SJF":
            self.run_sjf()
            
        self.update_table()
        
    def reset_simulation(self):
        self.processes = []
        self.load_processes()
        self.gantt_chart.clear()
        self.update_table()

    def run_fcfs(self):
        self.gantt_chart.clear()
        
        # Sort processes by arrival time
        processes = sorted(self.processes, key=lambda x: x.arrival_time)
        
        current_time = 0
        gantt_bars = []
        gantt_labels = []
        
        # Execute each process in order of arrival
        for i, proc in enumerate(processes):
            # If there's a gap between processes, advance the clock
            if proc.arrival_time > current_time:
                current_time = proc.arrival_time
                
            # Process starts execution
            proc.start_time = current_time
            
            # Execute for burst time
            current_time += proc.burst_time
            
            # Process completes
            proc.end_time = current_time
            proc.turnaround_time = proc.end_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time
            proc.completed = True
            
            # Create gantt chart bar for this process
            color = QColor(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            bar = pg.BarGraphItem(
                x=[proc.start_time + proc.burst_time/2], 
                height=[0.8], 
                width=[proc.burst_time],
                brush=color
            )
            gantt_bars.append(bar)
            
            # Add label
            text = pg.TextItem(text=f"P{proc.pid}", anchor=(0.5, 0.5), color='k')
            text.setPos(proc.start_time + proc.burst_time/2, 0.4)
            gantt_labels.append(text)
        
        # Add all bars and labels to chart
        for bar in gantt_bars:
            self.gantt_chart.addItem(bar)
        for label in gantt_labels:
            self.gantt_chart.addItem(label)
            
        # Set chart range
        self.gantt_chart.setXRange(0, current_time)
        self.gantt_chart.setYRange(0, 1)
        
        # Add time markers
        for t in range(0, current_time + 1):
            time_label = pg.TextItem(text=str(t), anchor=(0.5, 0), color='w')
            time_label.setPos(t, -0.1)
            self.gantt_chart.addItem(time_label)
    
    def run_sjf(self):
        self.gantt_chart.clear()
        
        # Sort processes by arrival time initially
        processes = sorted(self.processes, key=lambda x: x.arrival_time)
        
        current_time = 0
        completed = 0
        gantt_bars = []
        gantt_labels = []
        total_processes = len(processes)
        remaining_processes = processes.copy()
        
        while completed < total_processes:
            # Find processes that have arrived
            available_processes = [p for p in remaining_processes if p.arrival_time <= current_time]
            
            if not available_processes:
                # No process available, advance time to next arrival
                if remaining_processes:
                    current_time = min(remaining_processes, key=lambda x: x.arrival_time).arrival_time
                continue
            
            # Select process with shortest burst time
            selected_process = min(available_processes, key=lambda x: x.burst_time)
            remaining_processes.remove(selected_process)
            
            # Process starts execution
            selected_process.start_time = current_time
            
            # Execute for burst time
            current_time += selected_process.burst_time
            
            # Process completes
            selected_process.end_time = current_time
            selected_process.turnaround_time = selected_process.end_time - selected_process.arrival_time
            selected_process.waiting_time = selected_process.turnaround_time - selected_process.burst_time
            selected_process.completed = True
            completed += 1
            
            # Create gantt chart bar for this process
            color = QColor(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            bar = pg.BarGraphItem(
                x=[selected_process.start_time + selected_process.burst_time/2], 
                height=[0.8], 
                width=[selected_process.burst_time],
                brush=color
            )
            gantt_bars.append(bar)
            
            # Add label
            text = pg.TextItem(text=f"P{selected_process.pid}", anchor=(0.5, 0.5), color='k')
            text.setPos(selected_process.start_time + selected_process.burst_time/2, 0.4)
            gantt_labels.append(text)
        
        # Add all bars and labels to chart
        for bar in gantt_bars:
            self.gantt_chart.addItem(bar)
        for label in gantt_labels:
            self.gantt_chart.addItem(label)
            
        # Set chart range
        self.gantt_chart.setXRange(0, current_time)
        self.gantt_chart.setYRange(0, 1)
        
        # Add time markers
        for t in range(0, current_time + 1):
            time_label = pg.TextItem(text=str(t), anchor=(0.5, 0), color='w')
            time_label.setPos(t, -0.1)
            self.gantt_chart.addItem(time_label)
    
    def run_priority(self):
        self.gantt_chart.clear()
        
        # Sort processes by arrival time initially
        processes = sorted(self.processes, key=lambda x: x.arrival_time)
        
        current_time = 0
        completed = 0
        gantt_bars = []
        gantt_labels = []
        total_processes = len(processes)
        remaining_processes = processes.copy()
        
        while completed < total_processes:
            # Find processes that have arrived
            available_processes = [p for p in remaining_processes if p.arrival_time <= current_time]
            
            if not available_processes:
                # No process available, advance time to next arrival
                if remaining_processes:
                    current_time = min(remaining_processes, key=lambda x: x.arrival_time).arrival_time
                continue
            
            # Select process with highest priority (higher number = higher priority)
            selected_process = max(available_processes, key=lambda x: x.priority)
            remaining_processes.remove(selected_process)
            
            # Process starts execution
            selected_process.start_time = current_time
            
            # Execute for burst time
            current_time += selected_process.burst_time
            
            # Process completes
            selected_process.end_time = current_time
            selected_process.turnaround_time = selected_process.end_time - selected_process.arrival_time
            selected_process.waiting_time = selected_process.turnaround_time - selected_process.burst_time
            selected_process.completed = True
            completed += 1
            
            # Create gantt chart bar for this process
            color = QColor(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            bar = pg.BarGraphItem(
                x=[selected_process.start_time + selected_process.burst_time/2], 
                height=[0.8], 
                width=[selected_process.burst_time],
                brush=color
            )
            gantt_bars.append(bar)
            
            # Add label
            text = pg.TextItem(text=f"P{selected_process.pid}", anchor=(0.5, 0.5), color='k')
            text.setPos(selected_process.start_time + selected_process.burst_time/2, 0.4)
            gantt_labels.append(text)
        
        # Add all bars and labels to chart
        for bar in gantt_bars:
            self.gantt_chart.addItem(bar)
        for label in gantt_labels:
            self.gantt_chart.addItem(label)
            
        # Set chart range
        self.gantt_chart.setXRange(0, current_time)
        self.gantt_chart.setYRange(0, 1)
        
        # Add time markers
        for t in range(0, current_time + 1):
            time_label = pg.TextItem(text=str(t), anchor=(0.5, 0), color='w')
            time_label.setPos(t, -0.1)
            self.gantt_chart.addItem(time_label)
    
    def run_round_robin(self, quantum):
        self.gantt_chart.clear()
        
        if quantum <= 0:
            return
            
        # Sort processes by arrival time initially
        processes = sorted(self.processes, key=lambda x: x.arrival_time)
        
        # Create temporary copies for simulation
        process_copies = []
        for p in processes:
            process_copy = Process(p.pid, p.name, p.burst_time, p.priority, p.arrival_time)
            process_copies.append(process_copy)
        
        current_time = 0
        ready_queue = []
        gantt_bars = []
        gantt_labels = []
        completed = 0
        total_processes = len(process_copies)
        process_colors = {}
        
        while completed < total_processes:
            # Add newly arrived processes to ready queue
            for proc in process_copies:
                if not proc.completed and proc.arrival_time <= current_time and proc not in ready_queue:
                    ready_queue.append(proc)
            
            if not ready_queue:
                # No process in ready queue, advance time
                arrived = False
                for proc in process_copies:
                    if not proc.completed and proc.arrival_time > current_time:
                        current_time = proc.arrival_time
                        arrived = True
                        break
                        
                if not arrived:
                    break
                continue
            
            # Get next process from ready queue
            current_proc = ready_queue.pop(0)
            
            # Set start time if first execution
            if current_proc.start_time == -1:
                current_proc.start_time = current_time
            
            # Determine execution time for this quantum
            execution_time = min(quantum, current_proc.remaining_time)
            
            # Execute for quantum time or until completion
            start_execution = current_time
            current_time += execution_time
            current_proc.remaining_time -= execution_time
            
            # Create color for the process if not already assigned
            if current_proc.pid not in process_colors:
                process_colors[current_proc.pid] = QColor(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            
            # Create gantt chart bar for this execution block
            bar = pg.BarGraphItem(
                x=[start_execution + execution_time/2], 
                height=[0.8], 
                width=[execution_time],
                brush=process_colors[current_proc.pid]
            )
            gantt_bars.append(bar)
            
            # Add label
            text = pg.TextItem(text=f"P{current_proc.pid}", anchor=(0.5, 0.5), color='k')
            text.setPos(start_execution + execution_time/2, 0.4)
            gantt_labels.append(text)
            
            # Check if process is completed
            if current_proc.remaining_time == 0:
                current_proc.end_time = current_time
                current_proc.turnaround_time = current_proc.end_time - current_proc.arrival_time
                current_proc.waiting_time = current_proc.turnaround_time - current_proc.burst_time
                current_proc.completed = True
                completed += 1
                
                # Update original process
                for orig_proc in self.processes:
                    if orig_proc.pid == current_proc.pid:
                        orig_proc.waiting_time = current_proc.waiting_time
                        orig_proc.turnaround_time = current_proc.turnaround_time
                        orig_proc.completed = True
                        break
            else:
                # Put back in ready queue if not completed
                ready_queue.append(current_proc)
        
        # Add all bars and labels to chart
        for bar in gantt_bars:
            self.gantt_chart.addItem(bar)
        for label in gantt_labels:
            self.gantt_chart.addItem(label)
            
        # Set chart range
        self.gantt_chart.setXRange(0, current_time)
        self.gantt_chart.setYRange(0, 1)
        
        # Add time markers (with fewer markers for longer timelines)
        step = max(1, current_time // 20)
        for t in range(0, current_time + 1, step):
            time_label = pg.TextItem(text=str(t), anchor=(0.5, 0), color='w')
            time_label.setPos(t, -0.1)
            self.gantt_chart.addItem(time_label)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Alert Thresholds
        alert_group = QGroupBox("Alert Thresholds")
        alert_layout = QFormLayout()
        
        self.cpu_threshold = QSpinBox()
        self.cpu_threshold.setRange(50, 100)
        self.cpu_threshold.setValue(80)
        alert_layout.addRow("CPU Threshold (%):", self.cpu_threshold)
        
        self.memory_threshold = QSpinBox()
        self.memory_threshold.setRange(50, 100)
        self.memory_threshold.setValue(70)
        alert_layout.addRow("Memory Threshold (%):", self.memory_threshold)
        
        alert_group.setLayout(alert_layout)
        
        # Display Settings
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout()
        
        self.update_interval = QSpinBox()
        self.update_interval.setRange(1, 60)
        self.update_interval.setValue(1)
        self.update_interval.setSuffix(" seconds")
        display_layout.addRow("Update Interval:", self.update_interval)
        
        self.max_processes = QSpinBox()
        self.max_processes.setRange(5, 50)
        self.max_processes.setValue(15)
        display_layout.addRow("Max Processes Display:", self.max_processes)
        
        display_group.setLayout(display_layout)
        
        # Process List Settings
        process_group = QGroupBox("Process List Settings")
        process_layout = QFormLayout()
        
        self.sort_by_cpu = QCheckBox("Sort by CPU Usage")
        self.sort_by_cpu.setChecked(True)
        process_layout.addRow(self.sort_by_cpu)
        
        self.show_system_processes = QCheckBox("Show System Processes")
        self.show_system_processes.setChecked(False)
        process_layout.addRow(self.show_system_processes)
        
        process_group.setLayout(process_layout)
        
        # Add all groups to main layout
        layout.addWidget(alert_group)
        layout.addWidget(display_group)
        layout.addWidget(process_group)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_settings(self):
        return {
            'cpu_threshold': self.cpu_threshold.value(),
            'memory_threshold': self.memory_threshold.value(),
            'update_interval': self.update_interval.value(),
            'max_processes': self.max_processes.value(),
            'sort_by_cpu': self.sort_by_cpu.isChecked(),
            'show_system_processes': self.show_system_processes.isChecked()
        }

class ProcessControlPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)  # Increased spacing
        
        # Theme selector with icon
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(5)
        self.theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["🌙 Dark Theme", "☀️ Light Theme", "🎮 Cyberpunk Theme"])
        self.theme_combo.setMinimumWidth(150)
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combo)
        
        # Buttons with icons and labels
        button_container = QHBoxLayout()
        button_container.setSpacing(10)  # Increased spacing
        
        # Create button containers with icons and labels
        self.refresh_container = QWidget()
        refresh_layout = QVBoxLayout(self.refresh_container)
        refresh_layout.setContentsMargins(0, 0, 0, 0)
        refresh_layout.setSpacing(2)
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedSize(50, 50)  # Increased size
        refresh_label = QLabel("Refresh")
        refresh_label.setAlignment(Qt.AlignCenter)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addWidget(refresh_label)
        
        self.kill_container = QWidget()
        kill_layout = QVBoxLayout(self.kill_container)
        kill_layout.setContentsMargins(0, 0, 0, 0)
        kill_layout.setSpacing(2)
        self.kill_btn = QPushButton("⚠")
        self.kill_btn.setFixedSize(50, 50)  # Increased size
        kill_label = QLabel("Kill")
        kill_label.setAlignment(Qt.AlignCenter)
        kill_layout.addWidget(self.kill_btn)
        kill_layout.addWidget(kill_label)
        
        self.settings_container = QWidget()
        settings_layout = QVBoxLayout(self.settings_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(2)
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(50, 50)  # Increased size
        settings_label = QLabel("Settings")
        settings_label.setAlignment(Qt.AlignCenter)
        settings_layout.addWidget(self.settings_btn)
        settings_layout.addWidget(settings_label)
        
        self.scheduling_container = QWidget()
        scheduling_layout = QVBoxLayout(self.scheduling_container)
        scheduling_layout.setContentsMargins(0, 0, 0, 0)
        scheduling_layout.setSpacing(2)
        self.scheduling_btn = QPushButton("⚡")
        self.scheduling_btn.setFixedSize(50, 50)  # Increased size
        scheduling_label = QLabel("Scheduling")
        scheduling_label.setAlignment(Qt.AlignCenter)
        scheduling_layout.addWidget(self.scheduling_btn)
        scheduling_layout.addWidget(scheduling_label)
        
        # Add containers to layout
        button_container.addWidget(self.refresh_container)
        button_container.addWidget(self.kill_container)
        button_container.addWidget(self.settings_container)
        button_container.addWidget(self.scheduling_container)
        
        layout.addLayout(theme_layout)
        layout.addLayout(button_container)
        layout.addStretch()
        
    def apply_theme(self, colors):
        button_style = f"""
            QPushButton {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 20px;
            }}
            QPushButton:hover {{
                background-color: {colors['button_settings']};
                border-color: {colors['text']};
            }}
            QPushButton:pressed {{
                background-color: {colors['primary_bg']};
            }}
            QPushButton::tooltip {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 8px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }}
            QLabel {{
                color: {colors['text']};
                font-size: 12px;
            }}
        """
        
        self.refresh_btn.setStyleSheet(button_style.replace(colors['button_settings'], colors['button_refresh']))
        self.kill_btn.setStyleSheet(button_style.replace(colors['button_settings'], colors['button_kill']))
        self.settings_btn.setStyleSheet(button_style)
        self.scheduling_btn.setStyleSheet(button_style.replace(colors['button_settings'], colors['button_refresh']))
        
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 5px;
                border-radius: 5px;
                min-width: 150px;
                font-weight: bold;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid {colors['border']};
                height: 10px;
            }}
            QComboBox:hover {{
                border-color: {colors['text']};
            }}
        """)
        
        # Style for theme label
        self.theme_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-weight: bold;
            }}
        """)

class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Visualization Tool")
        self.current_theme = ThemeColors.DARK
        self.settings = {
            'cpu_threshold': 80,
            'memory_threshold': 70,
            'update_interval': 1,
            'max_processes': 15,
            'sort_by_cpu': True,
            'show_system_processes': False
        }
        self.setup_ui()
        self.apply_theme(self.current_theme)
        
    def setup_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QGridLayout(main_widget)
        layout.setSpacing(10)
        
        # Top stats panel (CPU & Memory side by side)
        top_panel = QFrame()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(20)
        
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
        
        self.mem_label_detail = QLabel("Used: 0 GB / Total: 0 GB")
        self.mem_progress = QProgressBar()
        self.mem_progress.setRange(0, 100)
        
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
        mem_layout.addWidget(self.mem_label_detail)
        mem_layout.addWidget(self.mem_progress)
        mem_layout.addWidget(self.mem_plot)
        
        # Add CPU and Memory frames to top panel
        top_layout.addWidget(cpu_frame, stretch=1)
        top_layout.addWidget(mem_frame, stretch=1)
        
        # Process List
        process_frame = QFrame()
        process_layout = QVBoxLayout(process_frame)
        process_layout.setContentsMargins(10, 10, 10, 10)
        
        # Process header with controls
        process_header = QHBoxLayout()
        process_label = QLabel("ACTIVE PROCESSES")
        process_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.control_panel = ProcessControlPanel()
        process_header.addWidget(process_label)
        process_header.addWidget(self.control_panel)
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "CPU %", "Memory %", "Status", "User", "Start Time"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        process_layout.addLayout(process_header)
        process_layout.addWidget(self.process_table)
        
        # Right panel for alerts
        self.alert_panel = AlertPanel()
        self.alert_panel.setMaximumWidth(350)  # Reduced from 300 to 250
        
        # Connect signals
        self.control_panel.refresh_btn.clicked.connect(self.update_stats)
        self.control_panel.kill_btn.clicked.connect(self.kill_selected_process)
        self.control_panel.theme_combo.currentTextChanged.connect(self.change_theme)
        self.control_panel.scheduling_btn.clicked.connect(self.show_scheduling_dialog)
        self.control_panel.settings_btn.clicked.connect(self.show_settings_dialog)
        
        # Add all components to main layout
        layout.addWidget(top_panel, 0, 0, 1, 2)
        layout.addWidget(process_frame, 1, 0, 1, 1)
        layout.addWidget(self.alert_panel, 1, 1, 1, 1)
        
        # Set layout stretch factors
        layout.setColumnStretch(0, 8)  # Increased from 7 to 8
        layout.setColumnStretch(1, 2)  # Decreased from 3 to 2
        
        # Setup update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        
        # Window settings
        self.setMinimumSize(1400, 800)  # Increased width from 1200 to 1400
        
    def change_theme(self, theme_name):
        if "Dark Theme" in theme_name:
            self.current_theme = ThemeColors.DARK
        elif "Light Theme" in theme_name:
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
                border-radius: 5px;
            }}
            QHeaderView::section {{
                background-color: {colors['secondary_bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                padding: 8px;
                font-weight: bold;
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
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {colors['button_settings']};
                color: {colors['text']};
            }}
        """)
        
        # Update plot colors
        self.cpu_plot.setBackground(colors['secondary_bg'])
        self.mem_plot.setBackground(colors['secondary_bg'])
        
        # Update bar colors using setOpts
        self.cpu_bars.setOpts(brush=colors['graph_cpu'])
        self.mem_bars.setOpts(brush=colors['graph_memory'])
        
        # Update progress bar colors based on usage
        self.update_progress_colors()
        
        # Apply theme to panels
        self.alert_panel.apply_theme(colors)
        self.control_panel.apply_theme(colors)
        
        # Update CPU and Memory labels with larger font
        self.cpu_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {colors['text']};")
        self.mem_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {colors['text']};")
        self.cpu_value.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {colors['text']};")
        self.mem_value.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {colors['text']};")
        self.mem_label_detail.setStyleSheet(f"font-size: 14px; color: {colors['text']};")
        
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
        
    def update_stats(self):
        # Update CPU
        cpu_percent = psutil.cpu_percent()
        self.cpu_value.setText(f"{cpu_percent}%")
        self.cpu_progress.setValue(int(cpu_percent))
        self.cpu_data = np.roll(self.cpu_data, -1)
        self.cpu_data[-1] = cpu_percent
        self.cpu_bars.setOpts(height=self.cpu_data)
        
        # Update progress bar colors
        self.update_progress_colors()
        
        # Check CPU threshold
        if cpu_percent > self.alert_panel.cpu_threshold:
            self.alert_panel.add_alert(f"High CPU usage: {cpu_percent}%", "critical")
        
        # Update Memory
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        used_gb = mem.used / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)
        
        self.mem_value.setText(f"{mem_percent}%")
        self.mem_label_detail.setText(f"Used: {used_gb:.1f} GB / Total: {total_gb:.1f} GB")
        self.mem_progress.setValue(int(mem_percent))
        self.mem_data = np.roll(self.mem_data, -1)
        self.mem_data[-1] = mem_percent
        self.mem_bars.setOpts(height=self.mem_data)
        
        # Check Memory threshold
        if mem_percent > self.alert_panel.memory_threshold:
            self.alert_panel.add_alert(f"High Memory usage: {mem_percent}%", "critical")
        
        # Update Process List with settings
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username', 'create_time']):
            try:
                pinfo = proc.info
                if not self.settings['show_system_processes'] and pinfo['username'] == 'root':
                    continue
                    
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
        
        # Sort based on settings
        if self.settings['sort_by_cpu']:
            processes.sort(key=lambda x: float(x[2]), reverse=True)
        else:
            processes.sort(key=lambda x: float(x[3]), reverse=True)
            
        self.process_table.setRowCount(min(len(processes), self.settings['max_processes']))
        
        for i, proc in enumerate(processes[:self.settings['max_processes']]):
            for j, value in enumerate(proc):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.process_table.setItem(i, j, item)

    def show_scheduling_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select CPU Scheduling Algorithm")
        layout = QVBoxLayout(dialog)
        
        algorithms = ["FCFS", "Round Robin", "Priority", "SJF"]
        
        for algo in algorithms:
            btn = QPushButton(algo)
            # Create a closure to capture the algorithm name
            def make_callback(algorithm):
                def callback():
                    dialog.accept()
                    self.scheduling_window = SchedulingWindow(algorithm, self)
                    self.scheduling_window.show()
                return callback
            
            btn.clicked.connect(make_callback(algo))
            layout.addWidget(btn)
        
        dialog.exec()

    def show_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            self.alert_panel.cpu_threshold = self.settings['cpu_threshold']
            self.alert_panel.memory_threshold = self.settings['memory_threshold']
            self.timer.setInterval(self.settings['update_interval'] * 1000)
            self.update_stats()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec())
