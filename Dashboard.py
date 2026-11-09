# =================================================================================
# Dashboard.py - Real-Time Telemetry Dashboard & Logging Suite
# Developed and refined with assistance from ChatGPT.
# =================================================================================
import sys, csv, time, os, serial
import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets, QtGui
from datetime import datetime

SERIAL_PORT = 'COM5' 
BAUD_RATE = 115200
FULL_SCALE = 8388608.0 

RREFS = {'A': 2000, 'B': 5000, 'C': 5000, 'D': 10000, 'E': 5000, 'F': 100000, 'G': 100000, 'H': 100000}
GAINS = {'A': 16, 'B': 32, 'C': 4, 'D': 8, 'E': 1, 'F': 1, 'G': 1, 'H': 1}

A_COEFFS = np.array([-2.13534729, 3.18324720, -1.80143597, 0.71727204, 0.50344027, -0.61899395, -0.05332322, 0.28021362, 0.10715224, -0.29302865, 0.04459872, 0.11868632, -0.05248134])
C_COEFFS = np.array([2.781572544, 1.64650916, -0.13714390, -0.00649767, -0.00234444, 0.00511868, 0.00187982, -0.00204472, -0.00046122, 0.00045724])

def Wr_low(TK):
    x = np.log(TK/273.16)
    u = (x + 1.5)/1.5
    poly = A_COEFFS[0] + sum(A_COEFFS[i] * (u**i) for i in range(1, len(A_COEFFS)))
    return np.exp(poly)

def Wr_high(TK):
    z = (TK - 754.15)/481.0
    poly = C_COEFFS[0] + sum(C_COEFFS[i] * (z**i) for i in range(1, len(C_COEFFS)))
    return poly

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(SCRIPT_DIR, "data")
if not os.path.exists(DATA_FOLDER): os.makedirs(DATA_FOLDER)
SAVE_FILENAME = os.path.join(DATA_FOLDER, f"Log_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")

class MasterCryoDashboard(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mechatronics Thesis - Master Command Center")
        self.resize(1920, 1080)

        t_range = np.linspace(13.8, 350, 30000)
        self.its_t = t_range
        self.its_wr = np.where(t_range < 273.16, Wr_low(t_range), Wr_high(t_range))
        
        tc = t_range - 273.15
        A_cvd, B_cvd, C_cvd = 3.9083e-3, -5.775e-7, -4.183e-12
        self.cvd_w = np.where(tc >= 0, 1 + A_cvd*tc + B_cvd*tc**2, 1 + A_cvd*tc + B_cvd*tc**2 + C_cvd*(tc - 100)*tc**3)
        self.cvd_t = t_range

        self.cw = QtWidgets.QWidget(); self.setCentralWidget(self.cw)
        self.main_layout = QtWidgets.QHBoxLayout(self.cw)
        self.main_layout.setContentsMargins(2, 2, 2, 2); self.main_layout.setSpacing(0)

        self.win = pg.GraphicsLayoutWidget(); self.main_layout.addWidget(self.win, stretch=95)
        
        self.side_container = QtWidgets.QWidget()
        self.side_container.setStyleSheet("background-color: #ffffff; border-left: 1px solid #ddd;")
        self.side_grid = QtWidgets.QVBoxLayout(self.side_container)
        self.side_grid.setContentsMargins(10, 0, 10, 0); self.side_grid.setSpacing(0)
        self.main_layout.addWidget(self.side_container, stretch=5)

        self.sensor_defs = [
            ('A', 'PT100', '#e74c3c', 'Ohm'), ('B', 'PT100', '#3498db', 'Ohm'),
            ('C', 'PT1000', '#2ecc71', 'Ohm'), ('D', 'PT1000', '#f1c40f', 'Ohm'),
            ('E', 'TIP32C', '#9b59b6', 'V'), ('F', 'Diode', '#ecf0f1', 'V'),
            ('G', 'Cernox', '#1abc9c', 'Ohm'), ('H', 'Diode', '#95a5a6', 'V')
        ]

        self.curves_raw, self.curves_temp, self.overlays_raw, self.overlays_temp, self.side_labels = {}, {}, {}, {}, {}
        self.history = {s[0]: {'x': [], 'raw': [], 'k': []} for s in self.sensor_defs}

        for i, (ch, s_type, col, unit) in enumerate(self.sensor_defs):
            p_raw = self.win.addPlot(); p_raw.showGrid(x=True, y=True, alpha=0.3)
            self.curves_raw[ch] = p_raw.plot(pen=pg.mkPen(col, width=2))
            p_temp = self.win.addPlot(); p_temp.showGrid(x=True, y=True, alpha=0.3)
            self.curves_temp[ch] = p_temp.plot(pen=pg.mkPen(col, width=2))
            self.win.nextRow()

            t_raw = pg.TextItem(text="--", color=col, anchor=(0,0), fill=(0,0,0,180))
            t_temp = pg.TextItem(text="--", color=col, anchor=(0,0), fill=(0,0,0,180))
            p_raw.addItem(t_raw, ignoreBounds=True); p_temp.addItem(t_temp, ignoreBounds=True)
            self.overlays_raw[ch] = t_raw; self.overlays_temp[ch] = t_temp

            cell = QtWidgets.QWidget(); clayout = QtWidgets.QVBoxLayout(cell)
            lbl = QtWidgets.QLabel(f"<b>{ch}: {s_type}</b><br>R: -- Ω<br>V: -- V<br>T: -- K")
            lbl.setStyleSheet("color: black; font-family: 'Arial'; font-size: 10pt; border: none;")
            clayout.addWidget(lbl); self.side_grid.addWidget(cell, stretch=1); self.side_labels[ch] = lbl

        self.f = open(SAVE_FILENAME, 'w', newline=''); self.writer = csv.writer(self.f)
        self.writer.writerow(["Timestamp", "Mod", "Raw1", "Raw2", "Resistance", "Voltage", "T_CVD", "T_ITS90"])

        try: self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        except: self.ser = None; print("ERROR: COM5 not found.")

        self.timer = QtCore.QTimer(); self.timer.timeout.connect(self.update_data)
        self.timer.start(50); self.start_t = time.time()

    def calculate_physics(self, mod, r1, r2=0):
        g = GAINS.get(mod, 1); r_ref = RREFS.get(mod, 1)
        v_sens = (r1 / FULL_SCALE) * (2.048 / g)
        if mod in ['A', 'B', 'C', 'D']:
            res = r_ref * (r1 / FULL_SCALE) / g
            r0 = 100.00385 if mod in ['A', 'B'] else 1000.0385
            w = res / r0
            tk_its = np.interp(w, self.its_wr, self.its_t)
            tk_cvd = np.interp(w, self.cvd_w, self.cvd_t)
            return res, v_sens, tk_cvd, tk_its
        elif mod == 'E':
            vh, vl = v_sens, (r2 / FULL_SCALE) * (2.048 / g)
            tk = abs(vh - vl) * 3860 
            return 0, vh, tk, tk
        else:
            res = r_ref * (r1 / FULL_SCALE) / g if mod == 'G' else 0
            tk = 300 - (v_sens * 150)
            return res, v_sens, tk, tk

    def update_data(self):
        if not self.ser or self.ser.in_waiting < 5: return
        try:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if not line.startswith("DATA"): return
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'); et = time.time() - self.start_t
            parts = line.split("|")[1:]; idx = 0
            while idx < len(parts):
                mod = parts[idx]; r1 = float(parts[idx+1])
                r2 = float(parts[idx+2]) if mod == 'E' else 0
                res, volt, tk_cvd, tk_its = self.calculate_physics(mod, r1, r2)
                
                h = self.history[mod]; h['x'].append(et); h['raw'].append(volt if res==0 else res); h['k'].append(tk_its)
                self.curves_raw[mod].setData(h['x'], h['raw']); self.curves_temp[mod].setData(h['x'], h['k'])

                vb_r = self.curves_raw[mod].getViewBox(); vb_k = self.curves_temp[mod].getViewBox()
                if vb_r and vb_k:
                    r_r = vb_r.viewRange(); r_k = vb_k.viewRange()
                    self.overlays_raw[mod].setPos(r_r[0][0], r_r[1][1])
                    self.overlays_temp[mod].setPos(r_k[0][0], r_k[1][1])

                res_str = f"{res:.3f} Ω" if res > 0 else "N/A"
                v_str = f"{volt*1000:.2f} mV" if volt < 1 else f"{volt:.4f} V"
                unit = 'Ω' if res > 0 else 'V'
                val_disp = res if res > 0 else volt

                self.overlays_raw[mod].setText(f" {val_disp:.3f} {unit}")
                self.overlays_temp[mod].setText(f" {tk_its:.2f} K")
                
                if mod in ['A', 'B', 'C', 'D']:
                    self.side_labels[mod].setText(f"<b>{mod}: {self.sensor_defs[ord(mod)-65][1]}</b><br>R: {res_str}<br>V: {v_str}<br>T(CVD): {tk_cvd:.2f} K<br>T(ITS90): {tk_its:.2f} K")
                else:
                    self.side_labels[mod].setText(f"<b>{mod}: {self.sensor_defs[ord(mod)-65][1]}</b><br>R: {res_str}<br>V: {v_str}<br>T: {tk_its:.2f} K")
                
                self.writer.writerow([ts, mod, r1, r2, res, volt, tk_cvd, tk_its])
                idx += 3 if mod == 'E' else 2
            self.f.flush()
        except: pass

    def closeEvent(self, event):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Security Lock', 'Type 12345 to exit:')
        if ok and text == '12345': self.f.close(); event.accept()
        else: event.ignore()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv); pg.setConfigOptions(antialias=True, background='k')
    gui = MasterCryoDashboard(); gui.show(); sys.exit(app.exec())