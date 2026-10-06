# gui/transposition_railfence.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox,
    QGridLayout, QScrollArea, QSpinBox,
    QApplication, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon

import os
import sys
from gui.layout_manager import layout_manager


class RailFenceCipher:
    @staticmethod
    def encrypt(plaintext, rails):
        if rails <= 1:
            return plaintext
        text = plaintext.replace(" ", "").upper()
        n = len(text)
        fence = [['' for _ in range(n)] for _ in range(rails)]
        rail = 0
        direction = 1
        for col, char in enumerate(text):
            fence[rail][col] = char
            rail += direction
            if rail == 0 or rail == rails - 1:
                direction *= -1
        result = []
        for row in range(rails):
            for col in range(n):
                if fence[row][col]:
                    result.append(fence[row][col])
        return ''.join(result)
    
    @staticmethod
    def decrypt(ciphertext, rails):
        if rails <= 1:
            return ciphertext
        text = ciphertext.replace(" ", "").upper()
        n = len(text)
        fence = [['' for _ in range(n)] for _ in range(rails)]
        rail = 0
        direction = 1
        for col in range(n):
            fence[rail][col] = '*'
            rail += direction
            if rail == 0 or rail == rails - 1:
                direction *= -1
        idx = 0
        for row in range(rails):
            for col in range(n):
                if fence[row][col] == '*' and idx < n:
                    fence[row][col] = text[idx]
                    idx += 1
        result = []
        rail = 0
        direction = 1
        for col in range(n):
            result.append(fence[rail][col])
            rail += direction
            if rail == 0 or rail == rails - 1:
                direction *= -1
        return ''.join(result)
    
    @staticmethod
    def get_fence_grid(text, rails):
        text_upper = text.replace(" ", "").upper()
        n = len(text_upper)
        fence = [['' for _ in range(n)] for _ in range(rails)]
        rail = 0
        direction = 1
        for col, char in enumerate(text_upper):
            fence[rail][col] = char
            rail += direction
            if rail == 0 or rail == rails - 1:
                direction *= -1
        return fence


class RailFenceGrid(QScrollArea):
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
        self.grid.setSpacing(2)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self.container)
    
    def update_colors(self, tc):
        self.colors = tc
    
    def update_grid(self, text, rails, is_encrypt):
        t = self.colors
        scale = layout_manager.font_scale()
        
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not text or rails <= 1:
            return
        
        fence = RailFenceCipher.get_fence_grid(text, rails)
        n = len(fence[0])
        
        # Cell sizing: fit into viewport when possible, but with floors and a
        # sensible max so it doesn't get absurdly large on wide screens
        avail_width = max(400, self.viewport().width() - 16)
        max_cols = min(n, 50)
        computed_w = (avail_width - max_cols * 2) // max_cols
        cell_w = max(int(22 * scale), min(int(36 * scale), computed_w))
        cell_h = cell_w
        font_size = max(9, int(cell_w / 3))
        dot_font = max(8, int(cell_w / 4))
        
        for row in range(rails):
            for col in range(max_cols):
                ch = fence[row][col]
                lbl = QLabel(ch if ch else "")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if ch:
                    lbl.setStyleSheet(
                        f"background:{t['base']};color:{t['text']};font-weight:bold;"
                        f"font-size:{font_size}px;border-radius:3px;"
                        f"border:1px solid {t['border']};"
                    )
                else:
                    lbl.setStyleSheet(
                        f"background:transparent;color:{t['text_tertiary']};"
                        f"font-size:{dot_font}px;"
                    )
                    lbl.setText(".")
                lbl.setFixedSize(cell_w, cell_h)
                self.grid.addWidget(lbl, row, col)


class TranspositionRailFencePage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self._last_operation = None
        self._last_text = ""
        self._last_rails = 3
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
        
        title = QLabel("Transposition - Rail Fence")
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
        
        if hasattr(self, 'rails_spin') and self.rails_spin is not None:
            sp = max(12, int(13 * scale))
            arrow_w = max(18, int(20 * scale))
            self.rails_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rails_spin.setFixedHeight(max(32, int(36 * scale)))
            self.rails_spin.setStyleSheet(
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
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            self.status_progress.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        
        if hasattr(self, 'rail_grid') and self.rail_grid is not None:
            self.rail_grid.update_colors(t)
            if self._last_operation and self._last_text:
                self.rail_grid.update_grid(
                    self._last_text, self._last_rails,
                    self._last_operation == 'encrypt'
                )
    
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
        rails_lbl = QLabel("Rails:")
        rails_lbl.setMinimumWidth(90)
        kw_row.addWidget(rails_lbl)
        self.rails_spin = QSpinBox()
        self.rails_spin.setRange(2, 20)
        self.rails_spin.setValue(3)
        self.rails_spin.setMinimumWidth(90)
        self.rails_spin.setMaximumWidth(120)
        self.rails_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kw_row.addWidget(self.rails_spin)
        kw_row.addStretch()
        kl.addLayout(kw_row)
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
        self.status_output.setPlaceholderText("Activity log...")
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
        self.rail_grid = RailFenceGrid(self.theme.current)
        l.addWidget(self.rail_grid, 1)
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
    
    def _encrypt(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return
        self._last_operation = 'encrypt'
        self._last_text = text
        self._last_rails = self.rails_spin.value()
        result = RailFenceCipher.encrypt(text, self._last_rails)
        self.results_output.setPlainText(result)
        self.rail_grid.update_grid(text, self._last_rails, True)
        self._update_status(text, self._last_rails, True, result)
        self.tabs.setCurrentIndex(1)
        QTimer.singleShot(200, lambda: self.tabs.setCurrentIndex(2))
    
    def _decrypt(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return
        self._last_operation = 'decrypt'
        self._last_text = text
        self._last_rails = self.rails_spin.value()
        result = RailFenceCipher.decrypt(text, self._last_rails)
        self.results_output.setPlainText(result)
        self.rail_grid.update_grid(text, self._last_rails, False)
        self._update_status(text, self._last_rails, False, result)
        self.tabs.setCurrentIndex(1)
        QTimer.singleShot(200, lambda: self.tabs.setCurrentIndex(2))
    
    def _update_status(self, text, rails, is_encrypt, result):
        n = len(text.replace(" ", ""))
        op = "Encryption" if is_encrypt else "Decryption"
        
        self.status_output.clear()
        self.status_progress.setValue(100)
        self.status_output.append(f"[*] {op} completed")
        self.status_output.append(f"\nInput length: {n} characters")
        self.status_output.append(f"Rails: {rails}")
        self.status_output.append(f"\nProcess:")
        self.status_output.append(f"  1. Write text in zigzag pattern across {rails} rails")
        if is_encrypt:
            self.status_output.append(f"  2. Read row by row to get ciphertext")
        else:
            self.status_output.append(f"  2. Fill zigzag positions with ciphertext")
            self.status_output.append(f"  3. Read zigzag to recover plaintext")
        self.status_output.append(f"\nResult: {result}")
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()