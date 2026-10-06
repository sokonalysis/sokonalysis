# gui/ctf_rsa_coppersmith.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon
from Crypto.Util.number import long_to_bytes
import os
import sys
from gui.layout_manager import layout_manager

try:
    import gmpy2
    HAS_GMPY2 = True
except ImportError:
    HAS_GMPY2 = False


class CoppersmithWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, dict)
    
    def __init__(self, n_str, e_str, c_str):
        super().__init__()
        self.n_str = n_str
        self.e_str = e_str
        self.c_str = c_str
    
    def _parse_number(self, num_str):
        num_str = num_str.strip().replace(' ', '').replace('\n', '').replace('\r', '')
        if not num_str:
            return 0
        if num_str.startswith('0x') or num_str.startswith('0X'):
            return int(num_str, 16)
        hex_chars = set('0123456789abcdefABCDEF')
        if all(c in hex_chars for c in num_str):
            if any(c in 'abcdefABCDEF' for c in num_str):
                return int(num_str, 16)
            return int(num_str)
        return int(num_str)
    
    def run(self):
        try:
            self.progress.emit("Parsing inputs...")
            self.progress_value.emit(10)
            
            n = self._parse_number(self.n_str)
            e = self._parse_number(self.e_str) if self.e_str.strip() else 65537
            c = self._parse_number(self.c_str)
            
            self.progress.emit(f"n: {n.bit_length()} bits")
            self.progress.emit(f"e: {e}")
            self.progress_value.emit(20)
            
            self.progress.emit(f"Attempting direct {e}-th root attack...")
            self.progress.emit(f"Checking if m^{e} < n...")
            
            if HAS_GMPY2:
                m, exact = gmpy2.iroot(c, e)
            else:
                m = int(round(c ** (1.0 / e)))
                exact = (pow(m, e) == c)
                if not exact:
                    for offset in range(-100, 101):
                        test_m = m + offset
                        if pow(test_m, e) == c:
                            m = test_m
                            exact = True
                            break
            
            if exact:
                self.progress.emit(f"Exact {e}-th root found!")
                self.progress.emit(f"m^{e} < n confirmed")
                
                try:
                    m_bytes = long_to_bytes(m)
                    plaintext = m_bytes.decode('utf-8', errors='replace')
                    is_text = True
                except:
                    plaintext = f"0x{m:x}"
                    is_text = False
                
                self.progress.emit("Plaintext recovered!")
                self.progress_value.emit(100)
                self.finished.emit(True, plaintext, {
                    'n_bits': n.bit_length(),
                    'is_text': is_text,
                    'method': f'Direct {e}-th Root'
                })
            else:
                self.progress.emit(f"No exact {e}-th root found.")
                self.progress.emit(f"m^{e} >= n, need full Coppersmith with SageMath.")
                self.progress_value.emit(100)
                self.finished.emit(
                    False,
                    "Direct root attack failed.\n\n"
                    "m^e >= n, the modulo wraps around.\n\n"
                    "Options:\n"
                    "1. Use SageMath for full Coppersmith attack\n"
                    "2. Try with known plaintext prefix\n"
                    "3. Try factoring n if e is small enough",
                    {'n_bits': n.bit_length()}
                )
                    
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(e), {})


class CTF_RSA_CoppersmithPage(QWidget):
    
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
        
        title = QLabel("Coppersmith's Attack")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.setMinimumHeight(420)
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        
        self._apply_theme()
    
    # ----------------------------------------------------------
    # Per-input row builder:  Label  [input]  [Paste] [Clear]
    # ----------------------------------------------------------
    def _make_input_row(self, label_text, placeholder, default_text="", label_min_width=150):
        row = QHBoxLayout()
        row.setSpacing(8)
        
        lbl = QLabel(label_text)
        lbl.setMinimumWidth(label_min_width)
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
    
    def _create_setup_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        self.params_group = QGroupBox("RSA Parameters")
        pl = QVBoxLayout()
        pl.setSpacing(8)
        
        row_n, self.n_input = self._make_input_row(
            "Modulus n:", "RSA modulus n (decimal or hex)..."
        )
        row_e, self.e_input = self._make_input_row(
            "Public exponent e:", "e (default: 65537)...",
            default_text="65537"
        )
        row_c, self.c_input = self._make_input_row(
            "Ciphertext c:", "Ciphertext to decrypt..."
        )
        
        pl.addLayout(row_n)
        pl.addLayout(row_e)
        pl.addLayout(row_c)
        
        self.params_group.setLayout(pl)
        layout.addWidget(self.params_group)
        
        self.execute_btn = QPushButton("Run Attack")
        self.execute_btn.setObjectName("actionButton")
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute)
        layout.addWidget(self.execute_btn)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return widget
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if not clipboard:
            return
        if isinstance(widget, QTextEdit):
            widget.setPlainText(clipboard)
        else:
            widget.setText(clipboard.strip())
    
    def _create_status_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 100)
        self.status_progress.setValue(0)
        self.status_progress.setTextVisible(True)
        self.status_progress.setFormat("%p%")
        self.status_progress.setMinimumHeight(28)
        
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setPlaceholderText("Activity log...")
        self.status_output.setMinimumHeight(200)
        
        layout.addWidget(self.status_progress)
        layout.addWidget(self.status_output, 1)
        return widget
    
    def _create_results_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        results_header = QHBoxLayout()
        results_label = QLabel("Plaintext:")
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        results_header.addWidget(results_label)
        results_header.addStretch()
        results_header.addWidget(copy_btn)
        layout.addLayout(results_header)
        
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Plaintext will appear here...")
        self.results_output.setMinimumHeight(200)
        self.results_output.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.results_output, 1)
        
        self.results_info = QLabel("")
        self.results_info.setWordWrap(True)
        layout.addWidget(self.results_info)
        return widget
    
    def _execute(self):
        n = self.n_input.text().strip()
        if not n:
            QMessageBox.warning(self, "Missing Input", "Please enter modulus n.")
            return
        
        c = self.c_input.text().strip()
        if not c:
            QMessageBox.warning(self, "Missing Input", "Please enter ciphertext c.")
            return
        
        e = self.e_input.text().strip()
        
        self.tabs.setCurrentIndex(1)
        self.status_progress.setValue(0)
        self.status_output.clear()
        self.results_output.clear()
        
        # Immediate feedback so Status tab isn't frozen-looking
        self.status_output.append("[*] Initializing Coppersmith attack...")
        self.status_output.append(f"[*] Modulus chars: {len(n)}")
        self.status_output.append(f"[*] Public exponent: {e or '65537'}")
        self.status_output.append("[*] Starting worker...")
        
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
        
        self.execute_btn.setEnabled(False)
        self.execute_btn.setText("Running...")
        
        self.worker = CoppersmithWorker(n, e, c)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_finished(self, success, message, info):
        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("Run Attack")
        if success:
            self.status_progress.setValue(100)
            self.status_output.append("✓ SUCCESS!")
            sb = self.status_output.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
            self.results_output.setText(message)
            if info:
                parts = [f"n bits: {info.get('n_bits', 'N/A')}"]
                if info.get('method'):
                    parts.append(f"Method: {info['method']}")
                self.results_info.setText(" | ".join(str(p) for p in parts))
            self.tabs.setCurrentIndex(2)
        else:
            self.status_progress.setValue(100)
            self.status_output.append("✗ FAILED")
            sb = self.status_output.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
            self.results_output.setText(message)
            self.tabs.setCurrentIndex(2)
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No results to copy yet.")
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}}
            QTabBar::tab {{background-color:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;
            font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected {{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        if hasattr(self, 'params_group') and self.params_group is not None:
            try:
                self.params_group.setStyleSheet(gs)
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
        
        if hasattr(self, 'execute_btn') and self.execute_btn is not None:
            self.execute_btn.setMinimumHeight(max(48, int(56 * scale)))
        
        input_style = (
            f"QLineEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:6px 10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['n_input', 'e_input', 'c_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                    getattr(self, attr).setMinimumHeight(max(34, int(36 * scale)))
                except RuntimeError:
                    pass
        
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(
                    f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(12 * scale)}px;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_output') and self.results_output is not None:
            try:
                self.results_output.setStyleSheet(
                    f"QTextEdit{{background-color:{t['crust']};color:{t['success']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                    f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(
                    f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;"
                    f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                    f"QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}"
                )
                self.status_progress.setMinimumHeight(max(22, int(28 * scale)))
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_info') and self.results_info is not None:
            try:
                self.results_info.setStyleSheet(
                    f"color:{t['text_secondary']};font-size:{int(12 * scale)}px;"
                )
            except RuntimeError:
                pass
    
    def refresh_theme(self):
        self._apply_theme()