# gui/ctf_rsa_franklin_reiter.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit,
    QTabWidget, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon
import os, sys
from math import comb


def int_to_string(n):
    result = []
    while n > 0:
        result.insert(0, chr(n & 0xFF))
        n >>= 8
    return ''.join(result)


def poly_gcd_mod(a, b, mod):
    """Euclidean algorithm for polynomials over Z_mod."""
    a = [x % mod for x in a]
    b = [x % mod for x in b]
    
    while a and a[-1] == 0: a.pop()
    while b and b[-1] == 0: b.pop()
    
    if not a: return b
    if not b: return a
    
    while b:
        while b and b[-1] == 0: b.pop()
        if not b: break
        
        if len(a) < len(b):
            a, b = b, a
            continue
        
        inv = pow(b[-1], -1, mod)
        
        while len(a) >= len(b) and a:
            while a and a[-1] == 0: a.pop()
            if len(a) < len(b): break
            
            factor = (a[-1] * inv) % mod
            deg_diff = len(a) - len(b)
            for i in range(len(b)):
                a[deg_diff + i] = (a[deg_diff + i] - factor * b[i]) % mod
            a.pop()
        
        a, b = b, a
    
    while a and a[-1] == 0: a.pop()
    return a


def franklin_reiter(n, e, c1, c2, a, b):
    """Franklin-Reiter related message attack."""
    # P(x) = x^e - c1
    p1 = [0] * (e + 1)
    p1[0] = (-c1) % n
    p1[e] = 1
    
    # Q(x) = (a*x + b)^e - c2 using binomial theorem
    p2 = [0] * (e + 1)
    for k in range(e + 1):
        coeff = comb(e, k) * pow(a, k, n) * pow(b, e - k, n)
        p2[k] = coeff % n
    p2[0] = (p2[0] - c2) % n
    
    # GCD gives (x - m)
    g = poly_gcd_mod(p1, p2, n)
    
    if g and len(g) >= 2 and g[1] != 0:
        inv = pow(g[1], -1, n)
        m = (-g[0] * inv) % n
        return m
    
    return None


class FranklinReiterWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, n, e, c1, c2, a, b):
        super().__init__()
        self.n = int(n); self.e = int(e)
        self.c1 = int(c1); self.c2 = int(c2)
        self.a = int(a); self.b = int(b)
    
    def run(self):
        try:
            self.progress.emit("[*] Franklin-Reiter related message attack")
            self.progress.emit(f"[*] n = {self.n}")
            self.progress.emit(f"[*] e = {self.e}")
            self.progress.emit(f"[*] m2 = {self.a}*m1 + {self.b} (mod n)")
            self.progress_value.emit(20)
            
            self.progress.emit("[*] Computing polynomial GCD...")
            self.progress_value.emit(50)
            
            m = franklin_reiter(self.n, self.e, self.c1, self.c2, self.a, self.b)
            
            if m is None:
                self.finished.emit(False, "Attack failed — could not recover plaintext")
                return
            
            self.progress.emit(f"[=] Recovered m = {m}")
            self.progress_value.emit(80)
            
            try:
                plaintext = int_to_string(m)
            except:
                plaintext = str(m)
            
            self.progress_value.emit(100)
            self.progress.emit(f"[=] Plaintext: {plaintext}")
            self.finished.emit(True, plaintext)
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class CTF_RSA_FranklinReiterPage(QWidget):
    
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
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        
        title = QLabel("CTF - RSA - Franklin-Reiter")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_input(), "Input")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        self.setStyleSheet(f"background:{t['base']};")
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 20px;margin-right:2px;border-radius:7px 7px 0 0;font-size:12px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        if hasattr(self, 'in_grp'): self.in_grp.setStyleSheet(gs)
        if hasattr(self, 'res_grp'): self.res_grp.setStyleSheet(gs)
        
        le = f"QLineEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:5px;padding:10px 14px;font-family:JetBrains Mono;font-size:14px;}} QLineEdit:focus{{border-color:{t['border_focus']};}}"
        for a in ['n_input','e_input','c1_input','c2_input','a_input','b_input']:
            if hasattr(self, a): getattr(self, a).setStyleSheet(le)
        
        if hasattr(self, 'result_output'):
            self.result_output.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono;font-size:18px;font-weight:700;}}")
        if hasattr(self, 'status_output'):
            self.status_output.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono;font-size:12px;}}")
        if hasattr(self, 'status_progress'):
            self.status_progress.setStyleSheet(f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;height:14px;text-align:center;font-size:10px;font-weight:600;color:{t['text']};}} QProgressBar::chunk{{background:{t['error']};border-radius:4px;}}")
        if hasattr(self, 'run_btn'):
            self.run_btn.setStyleSheet(f"QPushButton{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background:{t['surface0']};}}")
    
    def _tab_input(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(16)
        
        desc = QLabel("Franklin-Reiter: when m2 = a*m1 + b (mod n), both encrypted with same key. Uses polynomial GCD over Z_n.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{self.theme.current['text_secondary']};background:transparent;font-size:13px;")
        l.addWidget(desc)
        
        self.in_grp = QGroupBox("RSA Parameters")
        f = QFormLayout()
        f.setSpacing(14)
        
        self.n_input = QLineEdit(); self.n_input.setPlaceholderText("Modulus n..."); self.n_input.setMaxLength(99999)
        self.e_input = QLineEdit(); self.e_input.setPlaceholderText("Public exponent e..."); self.e_input.setText("3")
        self.c1_input = QLineEdit(); self.c1_input.setPlaceholderText("c1 = m1^e mod n..."); self.c1_input.setMaxLength(99999)
        self.c2_input = QLineEdit(); self.c2_input.setPlaceholderText("c2 = m2^e mod n..."); self.c2_input.setMaxLength(99999)
        self.a_input = QLineEdit(); self.a_input.setPlaceholderText("Multiplier a..."); self.a_input.setText("1")
        self.b_input = QLineEdit(); self.b_input.setPlaceholderText("Additive b...")
        
        f.addRow("n:", self.n_input); f.addRow("e:", self.e_input)
        f.addRow("c1:", self.c1_input); f.addRow("c2:", self.c2_input)
        f.addRow("a:", self.a_input); f.addRow("b:", self.b_input)
        self.in_grp.setLayout(f)
        
        br = QHBoxLayout(); br.addStretch()
        self.run_btn = QPushButton("Attack")
        self.run_btn.setObjectName("actionButton"); self.run_btn.setMinimumHeight(46)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.run_btn.clicked.connect(self._run)
        br.addWidget(self.run_btn)
        
        l.addWidget(self.in_grp); l.addLayout(br); l.addStretch()
        return w
    
    def _run(self):
        n = self.n_input.text().strip(); e = self.e_input.text().strip()
        c1 = self.c1_input.text().strip(); c2 = self.c2_input.text().strip()
        a = self.a_input.text().strip(); b = self.b_input.text().strip()
        if not all([n, e, c1, c2, a, b]): return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear(); self.status_progress.setValue(0)
        self.run_btn.setEnabled(False)
        
        self.worker = FranklinReiterWorker(n, e, c1, c2, a, b)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg): self.status_output.append(msg)
    
    def _on_finished(self, success, plaintext):
        self.run_btn.setEnabled(True)
        if success: self.result_output.setText(plaintext); self.tabs.setCurrentIndex(2)
        else: self.status_output.append(f"[!] {plaintext}")
    
    def _tab_status(self):
        w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16); l.setSpacing(12)
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 100); self.status_progress.setValue(0)
        self.status_progress.setTextVisible(True); self.status_progress.setFormat("%p%"); self.status_progress.setMinimumHeight(28)
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True); self.status_output.setPlaceholderText("Attack status..."); self.status_output.setMinimumHeight(200)
        l.addWidget(self.status_progress); l.addWidget(self.status_output)
        return w
    
    def _tab_results(self):
        w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30); l.setSpacing(16)
        self.res_grp = QGroupBox("Decrypted Output"); rl = QVBoxLayout()
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True); self.result_output.setPlaceholderText("Decrypted flag will appear here...")
        self.result_output.setMinimumHeight(100); self.result_output.setMaximumHeight(120)
        rl.addWidget(self.result_output); self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp); l.addStretch()
        return w
    
    def refresh_theme(self):
        self.setStyleSheet(""); self._apply_theme()