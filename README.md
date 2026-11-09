Cryogenic Sensor Readout & Dashboard

Academic data acquisition and real-time visualization software developed for Mechatronic Systems Engineering thesis research at Forschungszentrum Jülich. 

## Acknowledgement of AI Assistance
In accordance with academic integrity guidelines, parts of this software suite (specifically ads1220.py, main.py, and Dashboard.py) were developed, debugged, and modified with the assistance of ChatGPT. The hardware configuration parameters (config.py) were authored directly by me.

---

## Operating Environment & Setup Guide

### 1. Requirements
- IDE: Visual Studio Code (VS Code) recommended for project file inspection and workspace management.
- Microcontroller Environment: MicroPython runtime flashed onto the Raspberry Pi Pico.
- Host PC Environment: Python 3.10+ with the following libraries installed:
  pip install numpy PySide6 pyqtgraph pyserial

---

## Step-by-Step Instructions

1. PREREQUISITES & TOOLS
   - IDE: Visual Studio Code (VS Code)
   - Microcontroller: Raspberry Pi Pico running MicroPython
   - Host PC: Python 3.10+
   - Required Python Packages: numpy, PySide6, pyqtgraph, pyserial
     (Install via: pip install numpy PySide6 pyqtgraph pyserial)

2. CONFIGURING HARDWARE SETTINGS
   - Open the project workspace in VS Code.
   - Open 'config.py' and verify that your active channels match your physical layout (CHANNEL_ACTIVE).
   - Ensure SPI pins, chip select pins, and reference resistor values correspond to your actual hardware build.

3. UPLOADING FIRMWARE TO THE PICO
   - Connect your Raspberry Pi Pico to your PC via USB.
   - Upload the following three files directly to the root directory of the Pico:
     * ads1220.py
     * config.py
     * main.py
   - Once uploaded and powered, the Pico will initialize the ADCs and start streaming sensor data over UART.

4. CHECKING AND UPDATING THE COM PORT
   - Check your system's Device Manager (Windows) or terminal (Linux/macOS) to find the COM port assigned to the Pico (e.g., COM5).
   - Open 'Dashboard.py' in VS Code.
   - Locate the 'SERIAL_PORT' variable near the top of the file and change it to match your port:
     SERIAL_PORT = 'COM5'

5. RUNNING THE DASHBOARD
   - Ensure the Pico is plugged in and streaming data.
   - Run the monitoring suite from your terminal or VS Code:
     python Dashboard.py
   - The real-time PyQtGraph interface will open, plotting live sensor metrics and automatically saving timestamped CSV logs into the local 'data/' directory.