# gui/ctf_rsa_low_exponent.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit,
    QTabWidget, QTextEdit, QProgressBar,
    QApplication, QMessageBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon, QTextOption
import os, sys
from gui.layout_manager import layout_manager


def int_to_string(n):
    result = []
    while n > 0:
        result.insert(0, chr(n & 0xFF))
        n >>= 8
    return ''.join(result)


def nth_root(value, n):
    if value < 0:
        return None
    if value == 0 or value == 1:
        return value
    low, high = 0, value
    while low <= high:
        mid = (low + high) // 2
        power = mid ** n
        if power == value:
            return mid
        elif power < value:
            low = mid + 1
        else:
            high = mid - 1
    return None


class LowExponentWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, c, e, n=None):
        super().__init__()
        self.c = int(c)
        self.e = int(e)
        self.n = int(n) if n else None
    
    def run(self):
        try:
            self.progress.emit(f"[*] Low exponent attack (e = {self.e})")
            self.progress_value.emit(20)
            if self.n and self.c < self.n:
                self.progress.emit("[*] c < n, computing direct eth root...")
            self.progress_value.emit(50)
            m = nth_root(self.c, self.e)
            self.progress_value.emit(80)
            if m is None:
                self.finished.emit(False, "Failed to compute nth root")
                return
            self.progress.emit(f"[*] m = {m}")
            try:
                plaintext = int_to_string(m)
            except:
                plaintext = str(m)
            self.progress_value.emit(100)
            self.progress.emit("[✓] Done!")
            self.finished.emit(True, plaintext)
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class CTF_RSA_LowExponentPage(QWidget):
    
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
        
        title = QLabel("CTF - RSA - Low Exponent Attack")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.setMinimumHeight(400)
        
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
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        if hasattr(self, 'in_grp') and self.in_grp is not None:
            try:
                self.in_grp.setStyleSheet(gs)
            except RuntimeError:
                pass
        
        input_style = (
            f"QLineEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:6px 10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['c_input', 'e_input', 'n_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    widget = getattr(self, attr)
                    widget.setStyleSheet(input_style)
                    widget.setMinimumHeight(max(34, int(38 * scale)))
                except RuntimeError:
                    pass
        
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
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(
                        f"QPushButton{{background-color:{t['crust']};color:{t['error']};"
                        f"border:1px solid {t['border']};border-radius:10px;"
                        f"padding:{max(6, int(8 * scale))}px {int(14 * scale)}px;"
                        f"font-weight:700;font-size:{max(11, int(14 * scale))}px;}} "
                        f"QPushButton:hover{{background-color:{t['surface0']};}}"
                    )
            except RuntimeError:
                pass
        
        if hasattr(self, 'run_btn') and self.run_btn is not None:
            self.run_btn.setMinimumHeight(max(48, int(56 * scale)))
        
        ts = (
            f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
        )
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(ts)
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
                    f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                    f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                    f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
                )
                self.status_progress.setMinimumHeight(max(22, int(28 * scale)))
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
        
        cl = QHBoxLayout()
        cl.setSpacing(8)
        self.c_input = QLineEdit()
        self.c_input.setPlaceholderText("Enter ciphertext (c)...")
        self.c_input.setMinimumHeight(38)
        self.c_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        cl.addWidget(self.c_input, 1)
        paste_c = QPushButton("Paste")
        paste_c.setObjectName("actionButton")
        paste_c.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_c.clicked.connect(lambda: self._paste_to(self.c_input))
        paste_c.setMaximumWidth(90)
        cl.addWidget(paste_c)
        clear_c = QPushButton("Clear")
        clear_c.setObjectName("dangerButton")
        clear_c.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_c.clicked.connect(self.c_input.clear)
        clear_c.setMaximumWidth(90)
        cl.addWidget(clear_c)
        il.addWidget(QLabel("Ciphertext (c):"))
        il.addLayout(cl)
        
        el = QHBoxLayout()
        el.setSpacing(8)
        self.e_input = QLineEdit()
        self.e_input.setPlaceholderText("Enter public exponent (e)...")
        self.e_input.setText("3")
        self.e_input.setMinimumHeight(38)
        self.e_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        el.addWidget(self.e_input, 1)
        paste_e = QPushButton("Paste")
        paste_e.setObjectName("actionButton")
        paste_e.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_e.clicked.connect(lambda: self._paste_to(self.e_input))
        paste_e.setMaximumWidth(90)
        el.addWidget(paste_e)
        clear_e = QPushButton("Clear")
        clear_e.setObjectName("dangerButton")
        clear_e.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_e.clicked.connect(lambda: self.e_input.setText("3"))
        clear_e.setMaximumWidth(90)
        el.addWidget(clear_e)
        il.addWidget(QLabel("Public exponent (e):"))
        il.addLayout(el)
        
        nl = QHBoxLayout()
        nl.setSpacing(8)
        self.n_input = QLineEdit()
        self.n_input.setPlaceholderText("Enter modulus (n) - optional...")
        self.n_input.setMinimumHeight(38)
        self.n_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        nl.addWidget(self.n_input, 1)
        paste_n = QPushButton("Paste")
        paste_n.setObjectName("actionButton")
        paste_n.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_n.clicked.connect(lambda: self._paste_to(self.n_input))
        paste_n.setMaximumWidth(90)
        nl.addWidget(paste_n)
        clear_n = QPushButton("Clear")
        clear_n.setObjectName("dangerButton")
        clear_n.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_n.clicked.connect(self.n_input.clear)
        clear_n.setMaximumWidth(90)
        nl.addWidget(clear_n)
        il.addWidget(QLabel("Modulus (n):"))
        il.addLayout(nl)
        
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
            widget.setText(clipboard.strip())
    
    def _run(self):
        c = self.c_input.text().strip()
        e = self.e_input.text().strip()
        n = self.n_input.text().strip()
        if not c or not e:
            QMessageBox.warning(self, "No Input", "Please enter ciphertext (c) and exponent (e).")
            return
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.status_progress.setValue(0)
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Decrypting...")
        self.worker = LowExponentWorker(c, e, n if n else None)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
    
    def _on_finished(self, success, plaintext):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("Decrypt")
        if success:
            self.results_output.setPlainText(plaintext)
            self.status_progress.setValue(100)
            self.tabs.setCurrentIndex(2)
        else:
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
        self.status_output.setPlaceholderText("Activity log...")
        self.status_output.setMinimumHeight(200)
        # ensure top-left flow for the activity log too
        self.status_output.document().setDefaultTextOption(
            QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        )
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output, 1)
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
        # Force top-left text flow — this is what the Caesar page effectively does.
        # Do NOT call setAlignment(AlignLeft): on QTextEdit that sets block alignment
        # and can vertically center a single-line document in some Qt versions.
        self.results_output.document().setDefaultTextOption(
            QTextOption(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        )
        self.results_output.setPlaceholderText("Decrypted flag will appear here...")
        self.results_output.setMinimumHeight(200)
        self.results_output.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        l.addWidget(self.results_output, 1)
        
        return w
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
        else:
            QMessageBox.warning(self, "Nothing to Copy", "No results to copy yet.")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()