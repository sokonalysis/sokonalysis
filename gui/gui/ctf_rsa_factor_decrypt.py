# gui/ctf_rsa_factor_decrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit,
    QTabWidget, QTextEdit, QProgressBar,
    QApplication, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon
import os, sys, json, urllib.request, urllib.error


def egcd(a, b):
    if a == 0: return b, 0, 1
    g, x1, y1 = egcd(b % a, a)
    return g, y1 - (b // a) * x1, x1


def modinv(a, m):
    g, x, _ = egcd(a, m)
    return None if g != 1 else x % m


def int_to_string(n):
    result = []
    while n > 0:
        result.insert(0, chr(n & 0xFF))
        n >>= 8
    return ''.join(result)


class FactorDecryptWorker(QThread):
    
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, c, e, n):
        super().__init__()
        self.c = int(c)
        self.e = int(e)
        self.n = int(n)
    
    def run(self):
        try:
            self.progress.emit("[*] Querying FactorDB...")
            self.progress_value.emit(10)
            
            url = f"http://factordb.com/api?query={self.n}"
            req = urllib.request.Request(url, headers={'User-Agent': 'sokonalysis/3.5'})
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
            
            factors = data.get('factors', [])
            
            if len(factors) < 2:
                self.finished.emit(False, "FactorDB could not factorize n completely")
                return
            
            self.progress_value.emit(40)
            
            p = int(factors[0][0])
            q = 1
            for f in factors[1:]:
                q *= int(f[0])
            
            self.progress.emit(f"[*] p = {p}")
            self.progress.emit(f"[*] q = {q}")
            self.progress_value.emit(60)
            
            phi = (p - 1) * (q - 1)
            d = modinv(self.e, phi)
            
            if d is None:
                self.finished.emit(False, "e is not invertible mod φ(n)")
                return
            
            self.progress.emit(f"[*] φ(n) = {phi}")
            self.progress.emit(f"[*] d = {d}")
            self.progress_value.emit(80)
            
            m = pow(self.c, d, self.n)
            self.progress.emit(f"[*] m = {m}")
            
            try:
                plaintext = int_to_string(m)
            except:
                plaintext = str(m)
            
            self.progress_value.emit(100)
            self.progress.emit(f"[✓] Flag: {plaintext}")
            
            self.finished.emit(True, plaintext)
            
        except urllib.error.URLError as e:
            self.finished.emit(False, f"Connection error: {str(e)}")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class CTF_RSA_FactorDecryptPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("CTF - RSA - Factor & Decrypt")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:13px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for attr in ['in_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        input_style = f"QLineEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        for attr in ['n_input', 'e_input', 'c_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                except RuntimeError:
                    pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['error']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
            except RuntimeError:
                pass
        
        ts = f"QTextEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono,monospace;font-size:13px;}}"
        for attr in ['status_output']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(ts)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(f"QTextEdit{{background-color:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono,monospace;font-size:18px;font-weight:700;}}")
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;height:14px;text-align:center;font-size:10px;font-weight:600;}} QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}")
            except RuntimeError:
                pass
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.in_grp = QGroupBox("RSA Parameters")
        il = QVBoxLayout()
        il.setSpacing(14)
        
        # Modulus (n)
        nl = QHBoxLayout()
        self.n_input = QLineEdit()
        self.n_input.setPlaceholderText("Enter modulus (n)...")
        nl.addWidget(self.n_input, 1)
        paste_n = QPushButton("Paste")
        paste_n.setObjectName("actionButton")
        paste_n.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_n.clicked.connect(lambda: self._paste_to(self.n_input))
        nl.addWidget(paste_n)
        clear_n = QPushButton("Clear")
        clear_n.setObjectName("dangerButton")
        clear_n.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_n.clicked.connect(self.n_input.clear)
        nl.addWidget(clear_n)
        il.addWidget(QLabel("Modulus (n):"))
        il.addLayout(nl)
        
        # Public exponent (e)
        el = QHBoxLayout()
        self.e_input = QLineEdit()
        self.e_input.setPlaceholderText("Enter public exponent (e)...")
        self.e_input.setText("65537")
        el.addWidget(self.e_input, 1)
        paste_e = QPushButton("Paste")
        paste_e.setObjectName("actionButton")
        paste_e.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_e.clicked.connect(lambda: self._paste_to(self.e_input))
        el.addWidget(paste_e)
        clear_e = QPushButton("Clear")
        clear_e.setObjectName("dangerButton")
        clear_e.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_e.clicked.connect(lambda: self.e_input.setText("65537"))
        el.addWidget(clear_e)
        il.addWidget(QLabel("Public exponent (e):"))
        il.addLayout(el)
        
        # Ciphertext (c)
        cl = QHBoxLayout()
        self.c_input = QLineEdit()
        self.c_input.setPlaceholderText("Enter ciphertext (c)...")
        cl.addWidget(self.c_input, 1)
        paste_c = QPushButton("Paste")
        paste_c.setObjectName("actionButton")
        paste_c.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_c.clicked.connect(lambda: self._paste_to(self.c_input))
        cl.addWidget(paste_c)
        clear_c = QPushButton("Clear")
        clear_c.setObjectName("dangerButton")
        clear_c.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_c.clicked.connect(self.c_input.clear)
        cl.addWidget(clear_c)
        il.addWidget(QLabel("Ciphertext (c):"))
        il.addLayout(cl)
        
        self.in_grp.setLayout(il)
        l.addWidget(self.in_grp)
        
        br = QHBoxLayout()
        br.addStretch()
        self.run_btn = QPushButton("Decrypt")
        self.run_btn.setObjectName("actionButton")
        self.run_btn.setMinimumHeight(48)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run)
        br.addWidget(self.run_btn)
        l.addLayout(br)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            widget.setText(clipboard)
    
    def _run(self):
        c = self.c_input.text().strip()
        e = self.e_input.text().strip()
        n = self.n_input.text().strip()
        
        if not c or not e or not n:
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.status_progress.setValue(0)
        self.run_btn.setEnabled(False)
        
        self.worker = FactorDecryptWorker(c, e, n)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, message):
        self.status_output.append(message)
    
    def _on_finished(self, success, plaintext):
        self.run_btn.setEnabled(True)
        if success:
            self.results_output.setPlainText(plaintext)
            self.status_progress.setValue(100)
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"[!] {plaintext}")
    
    def _tab_status(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 100)
        self.status_progress.setValue(0)
        self.status_progress.setTextVisible(True)
        self.status_progress.setFormat("%p%")
        self.status_progress.setMinimumHeight(28)
        
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output)
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        results_header = QHBoxLayout()
        results_label = QLabel("Result:")
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(copy_btn)
        l.addLayout(results_header)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Decrypted flag will appear here...")
        l.addWidget(self.results_output)
        
        return w
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()