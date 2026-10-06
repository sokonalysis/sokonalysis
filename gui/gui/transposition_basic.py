# gui/transposition_basic.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox,
    QGridLayout, QScrollArea, QSpinBox,
    QCheckBox, QApplication, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QSize, QTimer
import math
import os
import sys

from PySide6.QtGui import QIcon
from gui.layout_manager import layout_manager


class TranspositionCipher:
    @staticmethod
    def encrypt(message, key):
        if key <= 1:
            return message
        rows = (len(message) + key - 1) // key
        result = []
        for col in range(key):
            for row in range(rows):
                pos = row * key + col
                if pos < len(message):
                    result.append(message[pos])
        return ''.join(result)
    
    @staticmethod
    def decrypt(message, key):
        if key <= 1:
            return message
        rows = (len(message) + key - 1) // key
        result = [' '] * len(message)
        index = 0
        for col in range(key):
            for row in range(rows):
                pos = row * key + col
                if pos < len(message):
                    result[pos] = message[index]
                    index += 1
        return ''.join(result)
    
    @staticmethod
    def find_best_key(text):
        n = len(text)
        if n <= 2:
            return 2
        factors = []
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                factors.append(i)
                if i != n // i:
                    factors.append(n // i)
        if not factors:
            best = 2
            best_diff = float('inf')
            for key in range(2, min(n, 51)):
                rows = (n + key - 1) // key
                last_row_fill = n % key
                if last_row_fill == 0:
                    last_row_fill = key
                fill_ratio = last_row_fill / key
                ratio = max(rows, key) / min(rows, key)
                score = ratio + (1 - fill_ratio) * 2
                if score < best_diff:
                    best_diff = score
                    best = key
            return best
        sqrt_n = math.sqrt(n)
        return min(factors, key=lambda x: abs(x - sqrt_n))


class TranspositionGrid(QScrollArea):
    def __init__(self, theme_colors):
        super().__init__()
        self.colors = theme_colors
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("border: none; background: transparent;")
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(1)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.setWidget(self.container)
    
    def update_colors(self, tc):
        self.colors = tc
    
    def update_grid(self, text, key, is_encrypt):
        t = self.colors
        scale = layout_manager.font_scale()
        
        # Floors so cells stay readable in compact mode
        cell_w = max(28, int(34 * scale))
        cell_h = max(26, int(32 * scale))
        header_h = max(24, int(28 * scale))
        header_font = max(10, int(12 * scale))
        cell_font = max(11, int(13 * scale))
        
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not text or key <= 1:
            return
        
        text_upper = text.replace(" ", "").upper()
        n = len(text_upper)
        rows = (n + key - 1) // key
        
        for col in range(key):
            lbl = QLabel(str(col + 1))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background:{t['surface0']};color:{t['text']};font-weight:bold;"
                f"font-size:{header_font}px;border-radius:3px;"
            )
            lbl.setFixedSize(cell_w, header_h)
            self.grid.addWidget(lbl, 0, col)
        
        grid_data = [['' for _ in range(key)] for _ in range(rows)]
        
        if is_encrypt:
            idx = 0
            for row in range(rows):
                for col in range(key):
                    if idx < n:
                        grid_data[row][col] = text_upper[idx]
                        idx += 1
        else:
            idx = 0
            for col in range(key):
                for row in range(rows):
                    if idx < n:
                        grid_data[row][col] = text_upper[idx]
                        idx += 1
        
        for row in range(rows):
            for col in range(key):
                ch = grid_data[row][col]
                lbl = QLabel(ch if ch else "")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if ch:
                    lbl.setStyleSheet(
                        f"background:{t['base']};color:{t['text']};font-weight:bold;"
                        f"font-size:{cell_font}px;border-radius:3px;"
                        f"border:1px solid {t['border']};"
                    )
                else:
                    lbl.setStyleSheet(
                        f"background:transparent;color:{t['text_tertiary']};"
                        f"font-size:{cell_font}px;border-radius:3px;"
                        f"border:1px dashed {t['border']};"
                    )
                lbl.setFixedSize(cell_w, cell_h)
                self.grid.addWidget(lbl, row + 1, col)


class TranspositionBasicPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self._last_operation = None
        self._last_text = ""
        self._last_key = 5
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
        
        title = QLabel("Transposition - Basic")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.addTab(self._tab_grid(), "Grid View")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:{int(13 * scale)}px;font-weight:600;}}
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
        for attr in ['key_grp', 'in_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'text_input') and self.text_input is not None:
            self.text_input.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
            )
        if hasattr(self, 'status_output') and self.status_output is not None:
            self.status_output.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
            )
        if hasattr(self, 'results_output') and self.results_output is not None:
            self.results_output.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
            )
        
        # Spinbox: centered text, visible arrows drawn as CSS triangles
        if hasattr(self, 'key_spin') and self.key_spin is not None:
            sp = max(12, int(13 * scale))
            arrow_w = max(18, int(20 * scale))
            self.key_spin.setStyleSheet(
                f"QSpinBox{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;"
                f"padding:0px 10px;"
                f"font-size:{sp}px;}} "
                f"QSpinBox::up-button {{"
                f"  subcontrol-origin: border;"
                f"  subcontrol-position: top right;"
                f"  width:{arrow_w}px;"
                f"  background:{t['surface0']};"
                f"  border-left:1px solid {t['border']};"
                f"  border-top-right-radius:6px;"
                f"  border-bottom:1px solid {t['border']};"
                f"}} "
                f"QSpinBox::down-button {{"
                f"  subcontrol-origin: border;"
                f"  subcontrol-position: bottom right;"
                f"  width:{arrow_w}px;"
                f"  background:{t['surface0']};"
                f"  border-left:1px solid {t['border']};"
                f"  border-bottom-right-radius:6px;"
                f"}} "
                f"QSpinBox::up-arrow {{"
                f"  width:0; height:0;"
                f"  border-left:4px solid transparent;"
                f"  border-right:4px solid transparent;"
                f"  border-bottom:5px solid {t['text']};"
                f"}} "
                f"QSpinBox::down-arrow {{"
                f"  width:0; height:0;"
                f"  border-left:4px solid transparent;"
                f"  border-right:4px solid transparent;"
                f"  border-top:5px solid {t['text']};"
                f"}}"
            )
            self.key_spin.setFixedHeight(max(32, int(36 * scale)))
        
        if hasattr(self, 'auto_key_cb') and self.auto_key_cb is not None:
            self.auto_key_cb.setStyleSheet(
                f"QCheckBox{{color:{t['text']};font-size:{int(13 * scale)}px;}} "
                f"QCheckBox::indicator{{width:18px;height:18px;border:2px solid {t['border']};"
                f"border-radius:4px;background:{t['crust']};}} "
                f"QCheckBox::indicator:checked{{background:{t['success']};border-color:{t['success']};}}"
            )
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            self.status_progress.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        
        if hasattr(self, 'trans_grid') and self.trans_grid is not None:
            self.trans_grid.update_colors(t)
            if self._last_operation and self._last_text:
                is_encrypt = (self._last_operation == 'encrypt')
                self.trans_grid.update_grid(self._last_text, self._last_key, is_encrypt)
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.key_grp = QGroupBox("Key Settings")
        kl = QVBoxLayout()
        kl.setSpacing(10)
        key_row = QHBoxLayout()
        key_lbl = QLabel("Columns:")
        key_lbl.setMinimumWidth(90)
        key_row.addWidget(key_lbl)
        self.key_spin = QSpinBox()
        self.key_spin.setRange(2, 50)
        self.key_spin.setValue(5)
        self.key_spin.setMinimumWidth(90)
        self.key_spin.setMaximumWidth(120)
        # Center the number vertically and horizontally inside the spinbox
        self.key_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Fixed height so the text and arrows sit on the same visual line
        self.key_spin.setFixedHeight(36)
        key_row.addWidget(self.key_spin)
        self.auto_key_cb = QCheckBox("Auto-detect key")
        self.auto_key_cb.setChecked(True)
        self.auto_key_cb.toggled.connect(self._on_auto_key_toggled)
        key_row.addWidget(self.auto_key_cb)
        key_row.addStretch()
        kl.addLayout(key_row)
        self.key_grp.setLayout(kl)
        l.addWidget(self.key_grp)
        
        self.in_grp = QGroupBox("Input Text")
        il = QVBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text to encrypt or decrypt...")
        self.text_input.setMaximumHeight(120)
        self.text_input.textChanged.connect(self._on_text_changed)
        il.addWidget(self.text_input)
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.text_input))
        btn_row.addWidget(paste_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        il.addLayout(btn_row)
        self.in_grp.setLayout(il)
        l.addWidget(self.in_grp)
        
        br = QHBoxLayout()
        br.addStretch()
        enc_btn = QPushButton("Encrypt")
        enc_btn.setObjectName("actionButton")
        enc_btn.setMinimumHeight(48)
        enc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        enc_btn.clicked.connect(self._encrypt)
        br.addWidget(enc_btn)
        dec_btn = QPushButton("Decrypt")
        dec_btn.setObjectName("actionButton")
        dec_btn.setMinimumHeight(48)
        dec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dec_btn.clicked.connect(self._decrypt)
        br.addWidget(dec_btn)
        l.addLayout(br)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
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
        self.status_output.setPlaceholderText("Activity log and explanation...")
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output, 1)
        return w
    
    def _tab_results(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(12)
        rh = QHBoxLayout()
        rh.addWidget(QLabel("Result:"))
        rh.addStretch()
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("actionButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_results)
        rh.addWidget(copy_btn)
        l.addLayout(rh)
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        self.results_output.setPlaceholderText("Result will appear here...")
        l.addWidget(self.results_output, 1)
        return w
    
    def _tab_grid(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        self.trans_grid = TranspositionGrid(self.theme.current)
        l.addWidget(self.trans_grid, 1)
        return w
    
    def _paste_to(self, w):
        c = QApplication.clipboard().text()
        if c:
            if isinstance(w, QTextEdit):
                w.setPlainText(c)
            else:
                w.setText(c)
    
    def _clear_all(self):
        self.text_input.clear()
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
    
    def _copy_results(self):
        t = self.results_output.toPlainText()
        if t:
            QApplication.clipboard().setText(t)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _on_auto_key_toggled(self, checked):
        self.key_spin.setEnabled(not checked)
        if checked:
            self._auto_detect_key()
    
    def _on_text_changed(self):
        if self.auto_key_cb.isChecked():
            self._auto_detect_key()
    
    def _auto_detect_key(self):
        text = self.text_input.toPlainText().strip()
        text_no_spaces = text.replace(" ", "")
        if len(text_no_spaces) >= 4:
            best_key = TranspositionCipher.find_best_key(text_no_spaces)
            self.key_spin.setValue(best_key)
    
    def _get_key(self):
        return self.key_spin.value()
    
    def _encrypt(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return
        self._last_operation = 'encrypt'
        self._last_text = text
        self._last_key = self._get_key()
        text_no_spaces = text.replace(" ", "")
        result = TranspositionCipher.encrypt(text_no_spaces, self._last_key)
        self.results_output.setPlainText(result)
        self.trans_grid.update_grid(text, self._last_key, True)
        self._update_status(text, self._last_key, True, result)
        self.tabs.setCurrentIndex(1)
        QTimer.singleShot(200, lambda: self.tabs.setCurrentIndex(2))
    
    def _decrypt(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return
        self._last_operation = 'decrypt'
        self._last_text = text
        self._last_key = self._get_key()
        text_no_spaces = text.replace(" ", "")
        result = TranspositionCipher.decrypt(text_no_spaces, self._last_key)
        self.results_output.setPlainText(result)
        self.trans_grid.update_grid(text, self._last_key, False)
        self._update_status(text, self._last_key, False, result)
        self.tabs.setCurrentIndex(1)
        QTimer.singleShot(200, lambda: self.tabs.setCurrentIndex(2))
    
    def _update_status(self, text, key, is_encrypt, result):
        text_no_spaces = text.replace(" ", "").upper()
        n = len(text_no_spaces)
        rows = (n + key - 1) // key
        
        if is_encrypt:
            op = "Encryption"
            fill = "row by row"
            read = "column by column"
        else:
            op = "Decryption"
            fill = "column by column"
            read = "row by row"
        
        self.status_output.clear()
        self.status_progress.setValue(100)
        self.status_output.append(f"[*] {op} completed")
        self.status_output.append(f"\nInput: {text_no_spaces}")
        self.status_output.append(f"Length: {n} characters")
        self.status_output.append(f"Key (columns): {key}")
        self.status_output.append(f"Grid: {rows} rows x {key} columns")
        self.status_output.append(f"\nProcess:")
        self.status_output.append(f"  1. Write text {fill} into grid")
        self.status_output.append(f"  2. Read {read}")
        self.status_output.append(f"\nResult: {result}")
        self.status_output.append(f"\nFormula: rows = ceil({n}/{key}) = {rows}")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()