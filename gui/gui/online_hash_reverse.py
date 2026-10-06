# gui/online_hash_reverse.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit,
    QTabWidget, QTextEdit, QProgressBar, QTextBrowser,
    QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon
import os, sys, re, urllib.request, urllib.error, json
from gui.layout_manager import layout_manager


class HashIdentifier:
    """Identify hash type from hash string."""
    
    @staticmethod
    def identify(hash_value):
        hash_value = hash_value.strip()
        hlen = len(hash_value)
        is_hex = bool(re.match(r'^[0-9a-fA-F]+$', hash_value))
        
        if hash_value.startswith('$2a$') or hash_value.startswith('$2b$') or hash_value.startswith('$2y$'):
            return "bcrypt"
        if hash_value.startswith('$6$'):
            return "sha512crypt"
        if hash_value.startswith('$5$'):
            return "sha256crypt"
        if hash_value.startswith('$1$'):
            return "md5crypt"
        if hash_value.startswith('$P$') or hash_value.startswith('$H$'):
            return "phpass"
        if hash_value.startswith('$S$'):
            return "drupal7"
        if hlen == 32 and is_hex:
            return "md5"
        if hlen == 40 and is_hex:
            return "sha1"
        if hlen == 56 and is_hex:
            return "sha224"
        if hlen == 64 and is_hex:
            return "sha256"
        if hlen == 96 and is_hex:
            return "sha384"
        if hlen == 128 and is_hex:
            return "sha512"
        if hlen == 16 and is_hex:
            return "lm"
        if hlen == 13:
            return "mysql"
        if hlen == 41 and hash_value.startswith('*'):
            return "mysql5"
        return "md5"


class OnlineHashWorker(QThread):
    """Worker for online hash reversal using md5decrypt.net API."""
    
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    API_EMAIL = "s0k0j4m3s@gmail.com"
    API_KEY = "688501c75f1a0dfc"
    API_URL = "https://md5decrypt.net/en/Api/api.php"
    
    def __init__(self, hash_value):
        super().__init__()
        self.hash_value = hash_value.strip()
    
    def run(self):
        try:
            hash_type = HashIdentifier.identify(self.hash_value)
            
            self.progress.emit(f"[*] Hash: {self.hash_value}")
            self.progress.emit(f"[*] Detected type: {hash_type}")
            self.progress_value.emit(20)
            
            url = (
                f"{self.API_URL}?hash={self.hash_value}"
                f"&hash_type={hash_type}"
                f"&email={self.API_EMAIL}&code={self.API_KEY}"
            )
            
            self.progress.emit("[*] Querying online database...")
            self.progress_value.emit(40)
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) sokonalysis/3.5'
            })
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = response.read().decode('utf-8').strip()
            
            self.progress_value.emit(80)
            
            try:
                data = json.loads(result)
                if isinstance(data, dict) and "Plain" in data:
                    plaintext = data["Plain"]
                    self.progress.emit(f"[=] Found: {plaintext}")
                    self.progress_value.emit(100)
                    self.finished.emit(True, plaintext)
                elif isinstance(data, dict) and "error" in data:
                    self.finished.emit(False, data['error'])
                elif result == self.hash_value or result == "":
                    self.finished.emit(False, "Hash not found in online database")
                else:
                    self.finished.emit(False, result)
            except json.JSONDecodeError:
                if result and result != self.hash_value and len(result) < 200:
                    self.progress.emit(f"[=] Found: {result}")
                    self.progress_value.emit(100)
                    self.finished.emit(True, result)
                else:
                    self.finished.emit(False, "Hash not found in online database")
                
        except urllib.error.URLError as e:
            self.finished.emit(False, f"Connection error: {str(e)}")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class OnlineHashReversePage(QWidget):
    """Online hash reversal using md5decrypt.net API."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self._init_ui()
    
    def _paste_to(self, widget):
        c = QApplication.clipboard().text()
        if c:
            widget.setPlainText(c.strip())
    
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
        
        title = QLabel("Online Hash Reverse")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_input(), "Input")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.addTab(self._tab_formats(), "Supported Hashes")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;
            font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
                        f"border:1px solid {t['border']};border-radius:10px;padding:{int(14 * scale)}px;"
                        f"font-weight:700;font-size:{int(15 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;padding:{int(14 * scale)}px;"
                        f"font-weight:700;font-size:{int(15 * scale)}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for attr in ['in_grp', 'res_grp', 'formats_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'hash_input') and self.hash_input is not None:
            try:
                self.hash_input.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'result_output') and self.result_output is not None:
            try:
                self.result_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono;font-size:{int(18 * scale)}px;font-weight:700;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
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
            except RuntimeError:
                pass
        
        if hasattr(self, 'formats_output') and self.formats_output is not None:
            try:
                self.formats_output.setStyleSheet(
                    f"QTextBrowser{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:12px;"
                    f"font-family:JetBrains Mono;font-size:{int(12 * scale)}px;}}"
                )
            except RuntimeError:
                pass
    
    def _tab_input(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(16)
        
        self.in_grp = QGroupBox("Hash Input")
        il = QVBoxLayout()
        il.setSpacing(10)
        
        self.hash_input = QTextEdit()
        self.hash_input.setPlaceholderText("Paste your hash here...")
        self.hash_input.setMaximumHeight(100)
        self.hash_input.setMinimumHeight(80)
        il.addWidget(self.hash_input)
        
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.hash_input))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.hash_input.clear)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        il.addLayout(btn_row)
        
        self.in_grp.setLayout(il)
        l.addWidget(self.in_grp)
        
        br = QHBoxLayout()
        br.addStretch()
        self.run_btn = QPushButton("Reverse Lookup")
        self.run_btn.setObjectName("actionButton")
        self.run_btn.setMinimumHeight(48)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self._run)
        br.addWidget(self.run_btn)
        l.addLayout(br)
        l.addStretch()
        return w
    
    def _run(self):
        hash_value = self.hash_input.toPlainText().strip()
        if not hash_value:
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.status_progress.setValue(0)
        self.run_btn.setEnabled(False)
        
        self.worker = OnlineHashWorker(hash_value)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
    
    def _on_finished(self, success, plaintext):
        self.run_btn.setEnabled(True)
        if success:
            self.result_output.setText(plaintext)
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
        self.status_output.setPlaceholderText("Lookup status...")
        
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output, 1)
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        
        self.res_grp = QGroupBox("Result")
        rl = QVBoxLayout()
        
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Cracked Password:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_result)
        rh.addWidget(copy_btn)
        rl.addLayout(rh)
        
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setPlaceholderText("Reversed password will appear here...")
        rl.addWidget(self.result_output, 1)
        self.res_grp.setLayout(rl)
        l.addWidget(self.res_grp, 1)
        return w
    
    def _copy_result(self):
        text = self.result_output.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Password copied to clipboard!")
    
    def _tab_formats(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.formats_group = QGroupBox("Supported Hash Formats")
        fl = QVBoxLayout()
        self.formats_output = QTextBrowser()
        self.formats_output.setOpenExternalLinks(False)
        self.formats_output.setHtml(self._get_formats_html())
        fl.addWidget(self.formats_output, 1)
        self.formats_group.setLayout(fl)
        l.addWidget(self.formats_group, 1)
        return w
    
    def _get_formats_html(self):
        t = self.theme.current
        return f"""
        <table width="100%" cellpadding="6" cellspacing="0">
        <tr><td>MD5</td><td>MD4</td><td>SHA1</td><td>SHA256</td></tr>
        <tr><td>SHA512</td><td>SHA224</td><td>SHA384</td><td>RIPEMD160</td></tr>
        <tr><td>MySQL</td><td>MySQL5</td><td>LM</td><td>NTLM</td></tr>
        <tr><td>bcrypt</td><td>SHA256 Crypt</td><td>SHA512 Crypt</td><td>MD5 Crypt</td></tr>
        <tr><td>PHPass</td><td>Drupal 7</td><td>Joomla</td><td>WordPress</td></tr>
        <tr><td>Whirlpool</td><td>GOST</td><td>Snefru</td><td>Tiger</td></tr>
        <tr><td>Haval-128</td><td>Haval-160</td><td>Haval-192</td><td>Haval-224</td></tr>
        <tr><td>Haval-256</td><td>SHA-3 224</td><td>SHA-3 256</td><td>SHA-3 384</td></tr>
        <tr><td>SHA-3 512</td><td>Keccak</td><td>CRC32</td><td>CRC32B</td></tr>
        <tr><td>FNV-132</td><td>FNV-1a</td><td>Adler-32</td><td>AP hash</td></tr>
        </table>
        """
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()