# gui/ctf_rsa_multiprime.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit,
    QTabWidget, QTextEdit, QProgressBar,
    QApplication, QMessageBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon
import os, sys
from gui.layout_manager import layout_manager


def egcd(a, b):
    if a == 0:
        return b, 0, 1
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


class MultiPrimeWorker(QThread):
    
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
            import urllib.request, urllib.error, json
            
            self.progress.emit("[*] Querying FactorDB...")
            self.progress_value.emit(10)
            
            url = f"http://factordb.com/api?query={self.n}"
            req = urllib.request.Request(url, headers={'User-Agent': 'sokonalysis/3.5'})
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
            
            factors = data.get('factors', [])
            
            if len(factors) < 2:
                self.progress_value.emit(100)
                self.finished.emit(False, "FactorDB could not factorize n completely")
                return
            
            self.progress_value.emit(30)
            
            primes = []
            for f in factors:
                for _ in range(f[1]):
                    val = f[0]
                    if not val.isdigit():
                        url2 = f"http://factordb.com/api?query={val}"
                        req2 = urllib.request.Request(url2, headers={'User-Agent': 'sokonalysis/3.5'})
                        with urllib.request.urlopen(req2, timeout=10) as resp2:
                            data2 = json.loads(resp2.read().decode())
                            val = data2.get('number', val)
                    primes.append(int(val))
            
            self.progress.emit(f"[*] Found {len(primes)} prime factors")
            for i, p in enumerate(primes):
                self.progress.emit(f"  p{i+1} = {p}")
            
            self.progress_value.emit(50)
            
            phi = 1
            for p in primes:
                phi *= (p - 1)
            
            self.progress.emit(f"[*] φ(n) = {phi}")
            self.progress_value.emit(70)
            
            d = modinv(self.e, phi)
            
            if d is None:
                self.progress_value.emit(100)
                self.finished.emit(False, "e is not invertible mod φ(n)")
                return
            
            self.progress.emit(f"[*] d = {d}")
            self.progress_value.emit(85)
            
            m = pow(self.c, d, self.n)
            
            try:
                plaintext = int_to_string(m)
            except:
                plaintext = str(m)
            
            self.progress_value.emit(100)
            self.progress.emit("[✓] Done!")
            self.finished.emit(True, plaintext)
            
        except Exception as e:
            self.progress_value.emit(100)
            self.finished.emit(False, f"Error: {str(e)}")


class CTF_RSA_MultiPrimePage(QWidget):
    
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
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
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
        
        title = QLabel("CTF - RSA - Multi-Prime Attack")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_input(), "Input")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.setMinimumHeight(420)
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        
        self._apply_theme()
    
    # ----------------------------------------------------------
    # Per-input row builder:  Label  [input]  [Paste] [Clear]
    # ----------------------------------------------------------
    def _make_input_row(self, label_text, placeholder, default_text=""):
        row = QHBoxLayout()
        row.setSpacing(8)
        
        lbl = QLabel(label_text)
        lbl.setMinimumWidth(150)
        row.addWidget(lbl)
        
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        if default_text:
            inp.setText(default_text)
        inp.setMinimumHeight(36)
        inp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row.addWidget(inp, 1)
        
        btn_min_w = max(70, int(84 * layout_manager.font_scale()))
        
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(inp))
        paste_btn.setMinimumWidth(btn_min_w)
        row.addWidget(paste_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(inp.clear)
        clear_btn.setMinimumWidth(btn_min_w)
        row.addWidget(clear_btn)
        
        return row, inp
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if not clipboard:
            return
        if isinstance(widget, QTextEdit):
            widget.setPlainText(clipboard)
        else:
            widget.setText(clipboard.strip())
    
    def _tab_input(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        l = QVBoxLayout(content)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.in_grp = QGroupBox("RSA Parameters")
        il = QVBoxLayout()
        il.setSpacing(8)
        
        row_c, self.c_input = self._make_input_row(
            "Ciphertext (c):", "Enter ciphertext (c)..."
        )
        row_e, self.e_input = self._make_input_row(
            "Public exponent (e):", "Enter public exponent (e)...",
            default_text="65537"
        )
        row_n, self.n_input = self._make_input_row(
            "Modulus (n):", "Enter modulus (n)..."
        )
        
        il.addLayout(row_c)
        il.addLayout(row_e)
        il.addLayout(row_n)
        
        self.in_grp.setLayout(il)
        
        br = QHBoxLayout()
        br.addStretch()
        self.run_btn = QPushButton("Decrypt")
        self.run_btn.setObjectName("actionButton")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run)
        br.addWidget(self.run_btn)
        
        l.addWidget(self.in_grp)
        l.addLayout(br)
        l.addStretch()
        
        scroll.setWidget(content)
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return w
    
    def _run(self):
        c = self.c_input.text().strip()
        e = self.e_input.text().strip()
        n = self.n_input.text().strip()
        
        if not c or not e or not n:
            QMessageBox.warning(self, "No Input", "Please fill in c, e, and n.")
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_progress.setValue(0)
        self.status_output.clear()
        self.result_output.clear()
        
        # Immediate feedback
        self.status_output.append("[*] Initializing multi-prime attack...")
        self.status_output.append(f"[*] Modulus chars: {len(n)}")
        self.status_output.append("[*] Starting worker...")
        
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
        
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Decrypting...")
        
        self.worker = MultiPrimeWorker(c, e, n)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, message):
        self.status_output.append(message)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_finished(self, success, plaintext):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Decrypt")
        if success:
            self.status_progress.setValue(100)
            self.status_output.append("✓ SUCCESS!")
            sb = self.status_output.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
            self.result_output.setText(plaintext)
            self.tabs.setCurrentIndex(2)
        else:
            self.status_progress.setValue(100)
            self.status_output.append(f"[!] {plaintext}")
            sb = self.status_output.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
    
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
        self.status_output.setPlaceholderText("Solver status...")
        self.status_output.setMinimumHeight(200)
        
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output, 1)
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.res_grp = QGroupBox("Decrypted Output")
        rl = QVBoxLayout()
        rl.setSpacing(10)
        
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Plaintext:"))
        hdr.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        hdr.addWidget(copy_btn)
        rl.addLayout(hdr)
        
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setPlaceholderText("Decrypted flag will appear here...")
        self.result_output.setMinimumHeight(200)
        self.result_output.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        rl.addWidget(self.result_output, 1)
        
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp, 1)
        return w
    
    def _copy_results(self):
        text = self.result_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No results to copy yet.")
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 20px;margin-right:2px;border-radius:7px 7px 0 0;
            font-size:{int(12 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for g in [self.in_grp, self.res_grp]:
            try:
                g.setStyleSheet(gs)
            except RuntimeError:
                pass
        
        # Buttons — min widths scale so Paste/Clear never clip
        btn_min_w = max(70, int(84 * scale))
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{max(6, int(8 * scale))}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                    if btn.text() in ("Paste", "Copy"):
                        btn.setMinimumWidth(btn_min_w)
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{max(6, int(8 * scale))}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                    if btn.text() == "Clear":
                        btn.setMinimumWidth(btn_min_w)
            except RuntimeError:
                pass
        
        if hasattr(self, 'run_btn') and self.run_btn is not None:
            self.run_btn.setMinimumHeight(max(42, int(52 * scale)))
        
        input_style = (
            f"QLineEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:6px 10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['c_input', 'e_input', 'n_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                    getattr(self, attr).setMinimumHeight(max(34, int(36 * scale)))
                except RuntimeError:
                    pass
        
        if hasattr(self, 'result_output') and self.result_output is not None:
            try:
                self.result_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(12 * scale)}px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(
                    f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                    f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                    f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
                )
                self.status_progress.setMinimumHeight(max(22, int(28 * scale)))
            except RuntimeError:
                pass
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()