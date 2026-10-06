# gui/transposition_columnar.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox,
    QGridLayout, QScrollArea, QLineEdit,
    QApplication, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon

import os
import sys
from gui.layout_manager import layout_manager


class ColumnarCipher:
    @staticmethod
    def get_order(keyword):
        keyword = keyword.upper()
        indexed = [(letter, i) for i, letter in enumerate(keyword)]
        indexed.sort(key=lambda x: (x[0], x[1]))
        order = [0] * len(keyword)
        for order_num, (_, original_idx) in enumerate(indexed):
            order[original_idx] = order_num
        return order
    
    @staticmethod
    def encrypt(plaintext, keyword):
        if not keyword:
            return plaintext
        text = plaintext.replace(" ", "").upper()
        key_len = len(keyword)
        rows = (len(text) + key_len - 1) // key_len
        order = ColumnarCipher.get_order(keyword)
        grid = [['' for _ in range(key_len)] for _ in range(rows)]
        idx = 0
        for row in range(rows):
            for col in range(key_len):
                if idx < len(text):
                    grid[row][col] = text[idx]
                    idx += 1
        result = []
        for col_idx in range(key_len):
            col = order.index(col_idx)
            for row in range(rows):
                if grid[row][col]:
                    result.append(grid[row][col])
        return ''.join(result)
    
    @staticmethod
    def decrypt(ciphertext, keyword):
        if not keyword:
            return ciphertext
        text = ciphertext.replace(" ", "").upper()
        key_len = len(keyword)
        rows = (len(text) + key_len - 1) // key_len
        order = ColumnarCipher.get_order(keyword)
        total = len(text)
        base = total // key_len
        extra = total % key_len
        col_lengths = []
        for i in range(key_len):
            col = order.index(i)
            col_lengths.append(base + (1 if col < extra else 0))
        grid = [['' for _ in range(key_len)] for _ in range(rows)]
        idx = 0
        for col_idx in range(key_len):
            col = order.index(col_idx)
            length = col_lengths[col_idx]
            for row in range(length):
                grid[row][col] = text[idx]
                idx += 1
        result = []
        for row in range(rows):
            for col in range(key_len):
                if grid[row][col]:
                    result.append(grid[row][col])
        return ''.join(result)


class ColumnarGrid(QScrollArea):
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
    
    def update_grid(self, text, keyword, is_encrypt):
        t = self.colors
        scale = layout_manager.font_scale()
        
        # Floors so cells stay readable in compact mode
        cell_w = max(28, int(34 * scale))
        cell_h = max(26, int(32 * scale))
        kw_h = max(24, int(28 * scale))
        order_h = max(20, int(22 * scale))
        kw_font = max(11, int(13 * scale))
        order_font = max(9, int(11 * scale))
        cell_font = max(11, int(13 * scale))
        
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not text or not keyword:
            return
        
        text_upper = text.replace(" ", "").upper()
        keyword_upper = keyword.upper()
        key_len = len(keyword_upper)
        rows = (len(text_upper) + key_len - 1) // key_len
        order = ColumnarCipher.get_order(keyword_upper)
        
        # Keyword row
        for col, ch in enumerate(keyword_upper):
            lbl = QLabel(ch)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background:{t['surface0']};color:{t['text']};font-weight:bold;"
                f"font-size:{kw_font}px;border-radius:3px;"
            )
            lbl.setFixedSize(cell_w, kw_h)
            self.grid.addWidget(lbl, 0, col)
        
        # Order row
        for col in range(key_len):
            lbl = QLabel(str(order[col] + 1))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background:{t['surface0']};color:{t['text_secondary']};font-weight:bold;"
                f"font-size:{order_font}px;border-radius:3px;"
            )
            lbl.setFixedSize(cell_w, order_h)
            self.grid.addWidget(lbl, 1, col)
        
        # Grid data
        grid_data = [['' for _ in range(key_len)] for _ in range(rows)]
        if is_encrypt:
            idx = 0
            for row in range(rows):
                for col in range(key_len):
                    if idx < len(text_upper):
                        grid_data[row][col] = text_upper[idx]
                        idx += 1
        else:
            total = len(text_upper)
            base = total // key_len
            extra = total % key_len
            col_lengths = []
            for i in range(key_len):
                col = order.index(i)
                col_lengths.append(base + (1 if col < extra else 0))
            idx = 0
            for col_idx in range(key_len):
                col = order.index(col_idx)
                length = col_lengths[col_idx]
                for row in range(length):
                    grid_data[row][col] = text_upper[idx]
                    idx += 1
        
        for row in range(rows):
            for col in range(key_len):
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
                self.grid.addWidget(lbl, row + 2, col)


class TranspositionColumnarPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self._last_operation = None
        self._last_text = ""
        self._last_keyword = ""
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
        
        title = QLabel("Transposition - Columnar")
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
        if hasattr(self, 'keyword_input') and self.keyword_input is not None:
            self.keyword_input.setStyleSheet(
                f"QLineEdit{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:8px 12px;"
                f"font-family:JetBrains Mono,monospace;font-size:{max(12, int(14 * scale))}px;}}"
            )
        if hasattr(self, 'order_label') and self.order_label is not None:
            self.order_label.setStyleSheet(
                f"color:{t['text_secondary']};font-size:{int(12 * scale)}px;background:transparent;"
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
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            self.status_progress.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        
        if hasattr(self, 'columnar_grid') and self.columnar_grid is not None:
            self.columnar_grid.update_colors(t)
            if self._last_operation and self._last_text and self._last_keyword:
                is_encrypt = (self._last_operation == 'encrypt')
                self.columnar_grid.update_grid(self._last_text, self._last_keyword, is_encrypt)
    
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
        kw_row = QHBoxLayout()
        kw_lbl = QLabel("Keyword:")
        kw_lbl.setMinimumWidth(80)
        kw_row.addWidget(kw_lbl)
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("e.g., ZEBRAS")
        self.keyword_input.textChanged.connect(self._on_keyword_changed)
        kw_row.addWidget(self.keyword_input, 1)
        kl.addLayout(kw_row)
        self.order_label = QLabel("")
        self.order_label.setWordWrap(True)
        kl.addWidget(self.order_label)
        self.key_grp.setLayout(kl)
        l.addWidget(self.key_grp)
        
        self.in_grp = QGroupBox("Input Text")
        il = QVBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text to encrypt or decrypt...")
        self.text_input.setMaximumHeight(120)
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
        self.columnar_grid = ColumnarGrid(self.theme.current)
        l.addWidget(self.columnar_grid, 1)
        return w
    
    def _on_keyword_changed(self):
        keyword = self.keyword_input.text().strip()
        if keyword and keyword.isalpha():
            order = ColumnarCipher.get_order(keyword)
            order_str = ', '.join(str(o + 1) for o in order)
            self.order_label.setText(f"Column Order: {order_str}")
        else:
            self.order_label.setText("")
    
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
    
    def _encrypt(self):
        text = self.text_input.toPlainText().strip()
        keyword = self.keyword_input.text().strip()
        if not text or not keyword or not keyword.isalpha():
            return
        self._last_operation = 'encrypt'
        self._last_text = text
        self._last_keyword = keyword
        result = ColumnarCipher.encrypt(text, keyword)
        self.results_output.setPlainText(result)
        self.columnar_grid.update_grid(text, keyword, True)
        self._update_status(text, keyword, True, result)
        self.tabs.setCurrentIndex(1)
        QTimer.singleShot(200, lambda: self.tabs.setCurrentIndex(2))
    
    def _decrypt(self):
        text = self.text_input.toPlainText().strip()
        keyword = self.keyword_input.text().strip()
        if not text or not keyword or not keyword.isalpha():
            return
        self._last_operation = 'decrypt'
        self._last_text = text
        self._last_keyword = keyword
        result = ColumnarCipher.decrypt(text, keyword)
        self.results_output.setPlainText(result)
        self.columnar_grid.update_grid(text, keyword, False)
        self._update_status(text, keyword, False, result)
        self.tabs.setCurrentIndex(1)
        QTimer.singleShot(200, lambda: self.tabs.setCurrentIndex(2))
    
    def _update_status(self, text, keyword, is_encrypt, result):
        text_no_spaces = text.replace(" ", "").upper()
        keyword_upper = keyword.upper()
        n = len(text_no_spaces)
        key_len = len(keyword_upper)
        rows = (n + key_len - 1) // key_len
        order = ColumnarCipher.get_order(keyword_upper)
        order_str = ', '.join(str(o + 1) for o in order)
        
        op = "Encryption" if is_encrypt else "Decryption"
        fill = "row by row" if is_encrypt else "column by column (by order)"
        read = "column by order" if is_encrypt else "row by row"
        
        self.status_output.clear()
        self.status_progress.setValue(100)
        self.status_output.append(f"[*] {op} completed")
        self.status_output.append(f"\nInput: {text_no_spaces}")
        self.status_output.append(f"Length: {n} characters")
        self.status_output.append(f"Keyword: {keyword_upper}")
        self.status_output.append(f"Column Order: {order_str}")
        self.status_output.append(f"Grid: {rows} rows x {key_len} columns")
        self.status_output.append(f"\nProcess:")
        self.status_output.append(f"  1. Write text {fill} into grid")
        self.status_output.append(f"  2. Read {read}")
        self.status_output.append(f"\nResult: {result}")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()