# Process Visualization Tool

A modern, real-time process monitoring tool built with PySide6 and pyqtgraph. This tool provides a beautiful and intuitive interface for monitoring system resources and processes.

## Features

- Real-time CPU and Memory usage monitoring
- Dynamic bar graphs for resource visualization
- Process list with detailed information
- Alert system for high resource usage
- Multiple theme options (Dark, Light, and Cyberpunk)
- Process control capabilities (terminate processes)
- Responsive and modern UI design

## Requirements

- Python 3.6+
- PySide6
- psutil
- pyqtgraph
- numpy

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd process-visualization-tool
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python system_stats_ui.py
```

### Features

- **Theme Selection**: Use the dropdown menu to switch between Dark, Light, and Cyberpunk themes
- **Process Control**: Select a process and use the "Kill Process" button to terminate it
- **Real-time Updates**: The UI updates every second with current system statistics
- **Alert System**: Get notified when CPU or Memory usage exceeds thresholds

## License

This project is licensed under the MIT License - see the LICENSE file for details. 