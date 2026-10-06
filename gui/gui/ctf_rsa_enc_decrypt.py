# gui/ctf_rsa_enc_decrypt.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QFileDialog,
    QTabWidget, QTextEdit, QMessageBox, QProgressBar,
    QApplication, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon, QFont
import os, sys, base64, re, tempfile
from gui.layout_manager import layout_manager


# ============================================================
# Crypto helpers
# ============================================================
def hex_to_pem(hex_string):
    """Convert hex-encoded key to PEM format."""
    hex_clean = hex_string.replace(' ', '').replace('\n', '').replace('\r', '')
    try:
        raw = bytes.fromhex(hex_clean)
        text = raw.decode('ascii', errors='ignore')
        if '-----BEGIN' in text:
            return text
        return raw.decode('utf-8', errors='ignore')
    except:
        return None


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


def bytes_to_int(b):
    return int.from_bytes(b, 'big')


def parse_pem_private_key(pem_data):
    """Extract d and n from PEM private key."""
    pem = pem_data.replace('\r', '')
    
    def read_length(data, pos):
        length = data[pos]
        pos += 1
        if length & 0x80:
            num_bytes = length & 0x7F
            length = int.from_bytes(data[pos:pos+num_bytes], 'big')
            pos += num_bytes
        return length, pos
    
    match = re.search(
        r'-----BEGIN RSA PRIVATE KEY-----(.*?)-----END RSA PRIVATE KEY-----',
        pem, re.DOTALL
    )
    if match:
        der = base64.b64decode(match.group(1))
        pos = 0
        if der[pos] == 0x30:
            pos += 1
            _, pos = read_length(der, pos)
        if der[pos] == 0x02:
            pos += 1
            length, pos = read_length(der, pos)
            pos += length
        if der[pos] == 0x02:
            pos += 1
            length, pos = read_length(der, pos)
            n = int.from_bytes(der[pos:pos+length], 'big')
            pos += length
        if der[pos] == 0x02:
            pos += 1
            length, pos = read_length(der, pos)
            pos += length
        if der[pos] == 0x02:
            pos += 1
            length, pos = read_length(der, pos)
            d = int.from_bytes(der[pos:pos+length], 'big')
            return n, d
    
    match = re.search(
        r'-----BEGIN PRIVATE KEY-----(.*?)-----END PRIVATE KEY-----',
        pem, re.DOTALL
    )
    if match:
        der = base64.b64decode(match.group(1))
        pos = 0
        if der[pos] == 0x30:
            pos += 1
            _, pos = read_length(der, pos)
        if der[pos] == 0x02:
            pos += 1
            length, pos = read_length(der, pos)
            pos += length
        if der[pos] == 0x30:
            pos += 1
            length, pos = read_length(der, pos)
            pos += length
        if der[pos] == 0x04:
            pos += 1
            length, pos = read_length(der, pos)
            inner = der[pos:pos+length]
            pos = 0
            if inner[pos] == 0x30:
                pos += 1
                _, pos = read_length(inner, pos)
            if inner[pos] == 0x02:
                pos += 1
                length, pos = read_length(inner, pos)
                pos += length
            if inner[pos] == 0x02:
                pos += 1
                length, pos = read_length(inner, pos)
                n = int.from_bytes(inner[pos:pos+length], 'big')
                pos += length
            if inner[pos] == 0x02:
                pos += 1
                length, pos = read_length(inner, pos)
                pos += length
            if inner[pos] == 0x02:
                pos += 1
                length, pos = read_length(inner, pos)
                d = int.from_bytes(inner[pos:pos+length], 'big')
                return n, d
    
    return None, None


def parse_pem_public_key(pem_data):
    """Extract n and e from PEM public key."""
    pem = pem_data.replace('\r', '')
    
    def read_length(data, pos):
        length = data[pos]
        pos += 1
        if length & 0x80:
            num_bytes = length & 0x7F
            length = int.from_bytes(data[pos:pos+num_bytes], 'big')
            pos += num_bytes
        return length, pos
    
    match = re.search(
        r'-----BEGIN PUBLIC KEY-----(.*?)-----END PUBLIC KEY-----',
        pem, re.DOTALL
    )
    if match:
        der = base64.b64decode(match.group(1))
        pos = 0
        if der[pos] == 0x30:
            pos += 1
            _, pos = read_length(der, pos)
        if der[pos] == 0x30:
            pos += 1
            _, pos = read_length(der, pos)
        if der[pos] == 0x06:
            pos += 1
            length, pos = read_length(der, pos)
            pos += length
        if der[pos] == 0x03:
            pos += 1
            _, pos = read_length(der, pos)
            if der[pos] == 0x00:
                pos += 1
            if der[pos] == 0x30:
                pos += 1
                _, pos = read_length(der, pos)
            if der[pos] == 0x02:
                pos += 1
                length, pos = read_length(der, pos)
                n = int.from_bytes(der[pos:pos+length], 'big')
                pos += length
            if der[pos] == 0x02:
                pos += 1
                length, pos = read_length(der, pos)
                e = int.from_bytes(der[pos:pos+length], 'big')
                return n, e
    
    return None, None


# ============================================================
# Worker thread — now emits progress percentage
# ============================================================
class EncDecryptWorker(QThread):
    
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, enc_path, n=None, e=None, d=None, p=None, q=None):
        super().__init__()
        self.enc_path = enc_path
        self.n = int(n) if n else None
        self.e = int(e) if e else None
        self.d = int(d) if d else None
        self.p = int(p) if p else None
        self.q = int(q) if q else None
    
    def run(self):
        try:
            self.progress_value.emit(5)
            
            with open(self.enc_path, 'rb') as f:
                ciphertext = bytes_to_int(f.read())
            
            self.progress.emit(f"[*] Ciphertext loaded ({len(str(ciphertext))} digits)")
            self.progress_value.emit(25)
            
            d = self.d
            n = self.n
            
            if d is None:
                if self.p and self.q:
                    self.progress.emit("[*] Computing d from p, q, e...")
                    phi = (self.p - 1) * (self.q - 1)
                    n = self.p * self.q
                    d = modinv(self.e, phi)
                    if d is None:
                        self.progress_value.emit(100)
                        self.finished.emit(False, "e is not invertible mod φ(n)")
                        return
                    self.progress_value.emit(50)
                else:
                    self.progress_value.emit(100)
                    self.finished.emit(False, "Need either d or p & q to decrypt")
                    return
            
            self.progress.emit(f"[*] n = {n}")
            self.progress.emit(f"[*] d = {d}")
            self.progress_value.emit(65)
            
            self.progress.emit("[*] Decrypting...")
            self.progress_value.emit(80)
            
            m = pow(ciphertext, d, n)
            
            self.progress_value.emit(95)
            
            try:
                plaintext = int_to_string(m)
            except:
                plaintext = f"Integer value:\n{m}"
            
            self.progress.emit("[✓] Done!")
            self.progress_value.emit(100)
            self.finished.emit(True, plaintext)
            
        except Exception as e:
            self.progress_value.emit(100)
            self.finished.emit(False, f"Error: {str(e)}")


# ============================================================
# Main page
# ============================================================
class CTF_RSA_EncDecryptPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.enc_path = ""
        self.pem_path = ""
        self._init_ui()
        self.setAcceptDrops(True)
    
    # ----------------------------------------------------------
    # Drag & drop
    # ----------------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            if not filepath or not os.path.isfile(filepath):
                continue
            try:
                with open(filepath, 'rb') as f:
                    head = f.read(200)
                head_text = head.decode('utf-8', errors='ignore')
            except Exception:
                head_text = ""
            if filepath.endswith(('.pem', '.key')) or 'BEGIN' in head_text:
                self.pem_path = filepath
                self.pem_input.setText(filepath)
                self._update_pem_preview(filepath)
            else:
                self.enc_path = filepath
                self.enc_path_input.setText(filepath)
                self._update_enc_preview(filepath)
    
    # ----------------------------------------------------------
    # Preview updaters
    # ----------------------------------------------------------
    def _update_enc_preview(self, filepath):
        if not filepath or not os.path.exists(filepath):
            self.enc_drop_label.setText(
                "Drag & drop encrypted file here\nor click Browse to select"
            )
            return
        try:
            size = os.path.getsize(filepath)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1048576:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/1048576:.1f} MB"
            self.enc_drop_label.setText(f"{os.path.basename(filepath)}\n{size_str}")
        except Exception:
            self.enc_drop_label.setText(os.path.basename(filepath))
    
    def _update_pem_preview(self, filepath):
        if not filepath or not os.path.exists(filepath):
            self.pem_drop_label.setText(
                "Drag & drop PEM file here\nor click Browse to select"
            )
            return
        try:
            size = os.path.getsize(filepath)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1048576:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/1048576:.1f} MB"
            self.pem_drop_label.setText(f"{os.path.basename(filepath)}\n{size_str}")
        except Exception:
            self.pem_drop_label.setText(os.path.basename(filepath))
    
    # ----------------------------------------------------------
    # UI setup
    # ----------------------------------------------------------
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
        
        title = QLabel("CTF - RSA - Decrypt File")
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
    # Per-input row
    # ----------------------------------------------------------
    def _make_input_row(self, label_text, placeholder, default_text=""):
        row = QHBoxLayout()
        row.setSpacing(8)
        
        lbl = QLabel(label_text)
        lbl.setMinimumWidth(40)
        row.addWidget(lbl)
        
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        if default_text:
            inp.setText(default_text)
        inp.setMinimumHeight(36)
        inp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row.addWidget(inp, 1)
        
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(inp))
        paste_btn.setMaximumWidth(80)
        row.addWidget(paste_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(inp.clear)
        clear_btn.setMaximumWidth(80)
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
        
        t = self.theme.current
        
        # Encrypted file
        self.enc_grp = QGroupBox("Encrypted File")
        el = QVBoxLayout()
        el.setSpacing(8)
        
        self.enc_drop_label = QLabel(
            "Drag & drop encrypted file here\nor click Browse to select"
        )
        self.enc_drop_label.setFixedHeight(80)
        self.enc_drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.enc_drop_label.setStyleSheet(
            f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
            f"color:{t['text_tertiary']};font-size:13px;"
        )
        el.addWidget(self.enc_drop_label)
        
        enc_row = QHBoxLayout()
        self.enc_path_input = QLineEdit()
        self.enc_path_input.setReadOnly(True)
        self.enc_path_input.setPlaceholderText(
            "Select encrypted file (.enc, .bin, or any file)..."
        )
        self.enc_path_input.setMinimumHeight(36)
        browse_enc = QPushButton("Browse")
        browse_enc.setObjectName("actionButton")
        browse_enc.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_enc.clicked.connect(self._browse_enc)
        browse_enc.setMaximumWidth(90)
        enc_row.addWidget(self.enc_path_input, 1)
        enc_row.addWidget(browse_enc)
        el.addLayout(enc_row)
        
        self.enc_grp.setLayout(el)
        
        # Key material
        self.key_grp = QGroupBox("Key Material")
        kl = QVBoxLayout()
        kl.setSpacing(10)
        
        self.key_combo = QComboBox()
        self.key_combo.addItems([
            "Private Key (d, n)",
            "Private Key PEM File",
            "Hex-Encoded Private Key",
            "Public Key PEM + Factors (p, q)",
            "Factors Only (p, q, e)"
        ])
        self.key_combo.currentIndexChanged.connect(self._on_key_type_changed)
        self.key_combo.setMinimumHeight(36)
        kl.addWidget(self.key_combo)
        
        # d, n
        self.dn_widget = QWidget()
        dnl = QVBoxLayout(self.dn_widget)
        dnl.setContentsMargins(0, 0, 0, 0)
        dnl.setSpacing(8)
        row_n, self.n_input = self._make_input_row("n:", "Modulus (n)...")
        row_d, self.d_input = self._make_input_row("d:", "Private exponent (d)...")
        dnl.addLayout(row_n)
        dnl.addLayout(row_d)
        
        # PEM file
        self.pem_widget = QWidget()
        pwl = QVBoxLayout(self.pem_widget)
        pwl.setContentsMargins(0, 0, 0, 0)
        pwl.setSpacing(8)
        self.pem_drop_label = QLabel(
            "Drag & drop PEM file here\nor click Browse to select"
        )
        self.pem_drop_label.setFixedHeight(60)
        self.pem_drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pem_drop_label.setStyleSheet(
            f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
            f"color:{t['text_tertiary']};font-size:12px;"
        )
        pwl.addWidget(self.pem_drop_label)
        pem_row = QHBoxLayout()
        self.pem_input = QLineEdit()
        self.pem_input.setReadOnly(True)
        self.pem_input.setPlaceholderText("Select .pem/.key file or drag & drop...")
        self.pem_input.setMinimumHeight(36)
        pem_browse = QPushButton("Browse")
        pem_browse.setObjectName("actionButton")
        pem_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        pem_browse.clicked.connect(self._browse_pem)
        pem_browse.setMaximumWidth(90)
        pem_row.addWidget(self.pem_input, 1)
        pem_row.addWidget(pem_browse)
        pwl.addLayout(pem_row)
        self.pem_widget.hide()
        
        # Hex key
        self.hex_widget = QWidget()
        hwl = QVBoxLayout(self.hex_widget)
        hwl.setContentsMargins(0, 0, 0, 0)
        hwl.setSpacing(6)
        hwl.addWidget(QLabel("Paste hex-encoded private key:"))
        self.hex_input = QTextEdit()
        self.hex_input.setPlaceholderText("2d2d2d2d2d424547494e...")
        self.hex_input.setMinimumHeight(70)
        self.hex_input.setMaximumHeight(120)
        hwl.addWidget(self.hex_input)
        hex_row = QHBoxLayout()
        hex_paste = QPushButton("Paste")
        hex_paste.setObjectName("actionButton")
        hex_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        hex_paste.clicked.connect(lambda: self._paste_to(self.hex_input))
        hex_paste.setMaximumWidth(80)
        hex_clear = QPushButton("Clear")
        hex_clear.setObjectName("dangerButton")
        hex_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        hex_clear.clicked.connect(self.hex_input.clear)
        hex_clear.setMaximumWidth(80)
        hex_row.addWidget(hex_paste)
        hex_row.addWidget(hex_clear)
        hex_row.addStretch()
        hwl.addLayout(hex_row)
        self.hex_widget.hide()
        
        # p, q, e
        self.pqe_widget = QWidget()
        pqel = QVBoxLayout(self.pqe_widget)
        pqel.setContentsMargins(0, 0, 0, 0)
        pqel.setSpacing(8)
        row_p, self.p_input = self._make_input_row("p:", "Prime p...")
        row_q, self.q_input = self._make_input_row("q:", "Prime q...")
        row_e, self.e_input = self._make_input_row(
            "e:", "Public exponent e...", default_text="65537"
        )
        pqel.addLayout(row_p)
        pqel.addLayout(row_q)
        pqel.addLayout(row_e)
        self.pqe_widget.hide()
        
        kl.addWidget(self.dn_widget)
        kl.addWidget(self.pem_widget)
        kl.addWidget(self.hex_widget)
        kl.addWidget(self.pqe_widget)
        self.key_grp.setLayout(kl)
        
        br = QHBoxLayout()
        br.addStretch()
        self.run_btn = QPushButton("Decrypt")
        self.run_btn.setObjectName("actionButton")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run)
        br.addWidget(self.run_btn)
        
        l.addWidget(self.enc_grp)
        l.addWidget(self.key_grp)
        l.addLayout(br)
        l.addStretch()
        
        scroll.setWidget(content)
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return w
    
    def _on_key_type_changed(self, index):
        self.dn_widget.hide()
        self.pem_widget.hide()
        self.hex_widget.hide()
        self.pqe_widget.hide()
        
        if index == 0:
            self.dn_widget.show()
        elif index == 1 or index == 3:
            self.pem_widget.show()
        elif index == 2:
            self.hex_widget.show()
        elif index == 4:
            self.pqe_widget.show()
    
    def _browse_enc(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Encrypted File", "", "All Files (*.*)"
        )
        if file_path:
            self.enc_path = file_path
            self.enc_path_input.setText(file_path)
            self._update_enc_preview(file_path)
    
    def _browse_pem(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PEM File", "", "PEM Files (*.pem *.key);;All Files (*)"
        )
        if file_path:
            self.pem_path = file_path
            self.pem_input.setText(file_path)
            self._update_pem_preview(file_path)
    
    def _get_pem_data(self):
        key_type = self.key_combo.currentIndex()
        if key_type == 2:
            hex_str = self.hex_input.toPlainText().strip()
            if not hex_str:
                return None
            pem = hex_to_pem(hex_str)
            if pem:
                self.status_output.append("[*] Converted hex to PEM")
                return pem
            else:
                self.status_output.append("[!] Failed to convert hex to PEM")
                return None
        elif key_type in (1, 3):
            pem_path = self.pem_input.text().strip()
            if not pem_path:
                return None
            with open(pem_path, 'r') as f:
                return f.read()
        return None
    
    def _run(self):
        if not self.enc_path:
            QMessageBox.warning(self, "No File", "Please select an encrypted file first.")
            return
        
        key_type = self.key_combo.currentIndex()
        n, d, e, p, q = None, None, None, None, None
        
        try:
            if key_type == 0:
                n = int(self.n_input.text().strip())
                d = int(self.d_input.text().strip())
            elif key_type in (1, 2):
                pem = self._get_pem_data()
                if not pem:
                    QMessageBox.warning(self, "No Key", "Please provide a private key.")
                    return
                n, d = parse_pem_private_key(pem)
                if n is None:
                    self.tabs.setCurrentIndex(1)
                    self.status_progress.setValue(0)
                    self.status_output.clear()
                    self.status_output.append("[!] Failed to parse private key")
                    return
            elif key_type == 3:
                pem = self._get_pem_data()
                if not pem:
                    QMessageBox.warning(self, "No PEM", "Please provide a public key PEM.")
                    return
                n, e = parse_pem_public_key(pem)
                if n is None:
                    self.tabs.setCurrentIndex(1)
                    self.status_progress.setValue(0)
                    self.status_output.clear()
                    self.status_output.append("[!] Failed to parse public key")
                    return
                p = int(self.p_input.text().strip())
                q = int(self.q_input.text().strip())
            elif key_type == 4:
                p = int(self.p_input.text().strip())
                q = int(self.q_input.text().strip())
                e = int(self.e_input.text().strip())
        except Exception as ex:
            self.tabs.setCurrentIndex(1)
            self.status_progress.setValue(0)
            self.status_output.clear()
            self.status_output.append(f"[!] Parse error: {str(ex)}")
            return
        
        # Switch to Status tab, reset progress bar, show immediate feedback
        self.tabs.setCurrentIndex(1)
        self.status_progress.setValue(0)
        self.status_output.clear()
        self.status_output.append("[*] Initializing decryption...")
        self.status_output.append(f"[*] Encrypted file: {os.path.basename(self.enc_path)}")
        self.status_output.append(f"[*] Key mode: {self.key_combo.currentText()}")
        self.status_output.append("[*] Starting worker...")
        
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
        
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Decrypting...")
        
        self.worker = EncDecryptWorker(self.enc_path, n=n, e=e, d=d, p=p, q=q)
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
            self.status_output.append("[✓] Decryption complete")
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
    
    # ----------------------------------------------------------
    # Status tab — NOW WITH THE GREEN PROGRESS BAR
    # ----------------------------------------------------------
    def _tab_status(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        # The green progress bar — same as every other cracking page
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
        hdr.addWidget(QLabel("Decrypted Text:"))
        hdr.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        hdr.addWidget(copy_btn)
        rl.addLayout(hdr)
        
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setPlaceholderText("Decrypted text will appear here...")
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
    
    # ----------------------------------------------------------
    # Theme — including the green progress bar styling
    # ----------------------------------------------------------
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
        for attr in ['enc_grp', 'key_grp', 'res_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:8px;"
                        f"padding:{max(6, int(8 * scale))}px {int(12 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(13 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:8px;"
                        f"padding:{max(6, int(8 * scale))}px {int(12 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(13 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        if hasattr(self, 'run_btn') and self.run_btn is not None:
            self.run_btn.setMinimumHeight(max(42, int(52 * scale)))
        
        input_style = (
            f"QLineEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:6px 10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['n_input', 'e_input', 'd_input', 'p_input', 'q_input',
                     'enc_path_input', 'pem_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                    getattr(self, attr).setMinimumHeight(max(34, int(36 * scale)))
                except RuntimeError:
                    pass
        
        if hasattr(self, 'hex_input') and self.hex_input is not None:
            try:
                self.hex_input.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{max(11, int(11 * scale))}px;}}"
                )
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
        
        # ===== GREEN PROGRESS BAR STYLING — matches every other page =====
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
        
        if hasattr(self, 'key_combo') and self.key_combo is not None:
            try:
                self.key_combo.setStyleSheet(f"""
                    QComboBox {{
                        background-color: {t['crust']};
                        color: {t['text']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                        padding: 6px 28px 6px 14px;
                        font-size: {max(12, int(13 * scale))}px;
                        font-weight: 500;
                    }}
                    QComboBox:hover {{ border-color: {t['accent']}; }}
                    QComboBox::drop-down {{ border: none; width: 24px; }}
                    QComboBox QAbstractItemView {{
                        background-color: {t['base']};
                        color: {t['text']};
                        border: 1px solid {t['border']};
                        border-radius: 8px;
                        padding: 8px;
                        selection-background-color: {t['hover']};
                        selection-color: {t['text']};
                        outline: none;
                    }}
                    QComboBox QAbstractItemView::item {{
                        color: {t['text']};
                        background-color: transparent;
                        padding: 8px 16px;
                        border-radius: 4px;
                    }}
                    QComboBox QAbstractItemView::item:hover {{
                        background-color: {t['hover']};
                        color: {t['text']};
                    }}
                """)
            except RuntimeError:
                pass
        
        dash_style = (
            f"border:2px dashed {t['border']};border-radius:8px;background:transparent;"
            f"color:{t['text_tertiary']};font-size:{int(13 * scale)}px;"
        )
        if hasattr(self, 'enc_drop_label') and self.enc_drop_label is not None:
            try:
                self.enc_drop_label.setStyleSheet(dash_style)
            except RuntimeError:
                pass
        if hasattr(self, 'pem_drop_label') and self.pem_drop_label is not None:
            try:
                self.pem_drop_label.setStyleSheet(dash_style)
            except RuntimeError:
                pass
    
    def refresh_theme(self):
        self._apply_theme()