# gui/ctf_rsa_common_modulus.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QSize
from PySide6.QtGui import QPixmap, QDrag, QPainter, QColor, QFont, QIcon
from Crypto.Util.number import inverse, long_to_bytes
import os
import sys
import math


class CommonModulusWorker(QThread):
    """Worker thread for Common Modulus Attack."""
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, dict)
    
    def __init__(self, n_str, pairs, d_str=""):
        super().__init__()
        self.n_str = n_str
        self.pairs = pairs
        self.d_str = d_str
    
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
    
    def _extended_gcd(self, a, b):
        if a == 0:
            return 0, 1, b
        x1, y1, gcd = self._extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return x, y, gcd
    
    def _extended_gcd_multi(self, numbers):
        if len(numbers) == 1:
            return [1], numbers[0]
        coeffs = [0] * len(numbers)
        current_gcd = numbers[0]
        coeffs[0] = 1
        for i in range(1, len(numbers)):
            x, y, g = self._extended_gcd(current_gcd, numbers[i])
            for j in range(i):
                coeffs[j] = coeffs[j] * x
            coeffs[i] = y
            current_gcd = g
        return coeffs, current_gcd
    
    def run(self):
        try:
            self.progress.emit("Parsing inputs...")
            self.progress_value.emit(10)
            
            n = self._parse_number(self.n_str)
            
            # If d is provided, just decrypt directly
            d = self._parse_number(self.d_str) if self.d_str.strip() else None
            
            if d and len(self.pairs) >= 1:
                self.progress.emit("Private key d provided - decrypting directly...")
                self.progress_value.emit(30)
                
                e_str, c_str = self.pairs[0]
                c = self._parse_number(c_str)
                
                self.progress.emit(f"n bits: {n.bit_length()}")
                self.progress.emit(f"d bits: {d.bit_length()}")
                self.progress_value.emit(50)
                
                m = pow(c, d, n)
                
                self.progress_value.emit(80)
                
                try:
                    m_bytes = long_to_bytes(m)
                    plaintext = m_bytes.decode('utf-8', errors='replace')
                    is_text = True
                except:
                    plaintext = f"0x{m:x}"
                    is_text = False
                
                self.progress.emit("Decryption complete!")
                self.progress_value.emit(100)
                self.finished.emit(True, plaintext, {'n_bits': n.bit_length(), 'is_text': is_text, 'mode': 'Direct d'})
                return
            
            # Common Modulus Attack
            exponents = []
            ciphertexts = []
            
            for i, (e_str, c_str) in enumerate(self.pairs):
                e = self._parse_number(e_str)
                c = self._parse_number(c_str)
                exponents.append(e)
                ciphertexts.append(c)
                self.progress.emit(f"Pair {i+1}: e={e} ({e.bit_length()} bits)")
            
            self.progress.emit(f"Modulus: {n.bit_length()} bits")
            self.progress_value.emit(20)
            
            g = exponents[0]
            for e in exponents[1:]:
                g = math.gcd(g, e)
            
            self.progress.emit(f"GCD of all exponents = {g}")
            if g != 1:
                self.progress.emit(f"Warning: GCD = {g}, will recover m^{g} mod n")
            self.progress_value.emit(40)
            
            self.progress.emit("Computing extended GCD...")
            coeffs, bezout_gcd = self._extended_gcd_multi(exponents)
            
            verification = sum(c * e for c, e in zip(coeffs, exponents))
            self.progress.emit(f"Verification: sum(ci*ei) = {verification}")
            for i, coeff in enumerate(coeffs):
                self.progress.emit(f"  Coefficient for e{i+1}: {coeff}")
            self.progress_value.emit(60)
            
            self.progress.emit("Recovering plaintext...")
            result = 1
            
            for i, (coeff, c) in enumerate(zip(coeffs, ciphertexts)):
                if coeff < 0:
                    self.progress.emit(f"  Negative coefficient, using inverse of c{i+1}")
                    c_inv = inverse(c, n)
                    result = (result * pow(c_inv, -coeff, n)) % n
                else:
                    result = (result * pow(c, coeff, n)) % n
            
            self.progress_value.emit(80)
            
            if bezout_gcd == 1:
                m = result
                self.progress.emit("Plaintext recovered!")
                
                try:
                    m_bytes = long_to_bytes(m)
                    plaintext = m_bytes.decode('utf-8', errors='replace')
                    is_text = True
                except:
                    plaintext = f"0x{m:x}"
                    is_text = False
                
                info = {'n_bits': n.bit_length(), 'gcd': g, 'is_text': is_text, 'pairs': len(exponents), 'mode': 'Common Modulus'}
                self.progress_value.emit(100)
                self.finished.emit(True, plaintext, info)
            else:
                result_str = f"Recovered m^{bezout_gcd} mod n:\n\n0x{result:x}\n\nGCD = {bezout_gcd}, compute the {bezout_gcd}-th root."
                self.progress_value.emit(100)
                self.finished.emit(True, result_str, {'n_bits': n.bit_length(), 'gcd': g, 'is_text': False, 'pairs': len(exponents), 'mode': 'Common Modulus'})
                    
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(e), {})


class DraggableModeCard(QFrame):
    def __init__(self, mode_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.mode_name = name
        self.colors = theme_colors
        self.name_label = None
        self.setFixedSize(180, 70)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build(name)
    
    def _build(self, name):
        t = self.colors
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(f"color: {t['text']}; font-size: 13px; font-weight: 600; background: transparent;")
        layout.addWidget(self.name_label)
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
        t = self.colors
        if self.name_label:
            self.name_label.setStyleSheet(f"color: {t['text']}; font-size: 13px; font-weight: 600; background: transparent;")
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"{self.mode_id}:{self.mode_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class ModeDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.mode_id = None
        self.mode_name = None
        self.setFixedSize(240, 90)
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background-color:{t['crust']};border:3px dashed {t['border']};border-radius:10px;}}")
    
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(f"QFrame{{background-color:{t['accent']}15;border:3px solid {t['accent']}88;border-radius:10px;}}")
    
    def is_filled(self):
        return self.mode_id is not None
    
    def clear_slot(self):
        self.mode_id = None
        self.mode_name = None
        self._style_empty()
        self.update()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        data = event.mimeData().text()
        try:
            mode_id, mode_name = data.split(':', 1)
            self.mode_id = int(mode_id)
            self.mode_name = mode_name
            self._style_filled()
            self.update()
            event.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, CTF_RSA_CommonModulusPage):
                p = p.parent()
            if p:
                p._on_mode_dropped()
        except:
            pass
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        if self.is_filled():
            painter.setPen(QColor(t['accent']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", 13, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.mode_name)
        else:
            painter.setPen(QColor(t['text_tertiary']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", 10))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Drag operation here")
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
            p = self.parent()
            while p and not isinstance(p, CTF_RSA_CommonModulusPage):
                p = p.parent()
            if p:
                p._on_mode_cleared()


class CTF_RSA_CommonModulusPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.mode_cards = []
        self.pair_widgets = []
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
        
        title = QLabel("RSA Common Modulus Attack")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_setup_tab(), "Setup")
        self.tabs.addTab(self._create_status_tab(), "Status")
        self.tabs.addTab(self._create_results_tab(), "Results")
        self.tabs.addTab(self._create_help_tab(), "Help")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
        
        self._apply_theme()
    
    def _create_setup_tab(self):
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        
        # Step 1: Operation Mode
        self.mode_group = QGroupBox("1. Operation Mode")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)
        
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        t = self.theme.current
        for mode_id, name in [(1, "Single Cipher"), (2, "Multiple Pairs")]:
            card = DraggableModeCard(mode_id, name, t)
            self.mode_cards.append(card)
            cards_row.addWidget(card)
        cards_row.addStretch()
        mode_layout.addLayout(cards_row)
        
        drop_row = QHBoxLayout()
        self.mode_slot = ModeDropSlot(t)
        drop_row.addWidget(self.mode_slot)
        drop_row.addStretch()
        mode_layout.addLayout(drop_row)
        
        self.mode_group.setLayout(mode_layout)
        layout.addWidget(self.mode_group)
        
        # Step 2: Options (dynamically changed)
        self.options_group = QGroupBox("2. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        layout.addWidget(self.options_group)
        
        # Execute button
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("actionButton")
        self.execute_btn.setMinimumHeight(48)
        self.execute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.execute_btn.clicked.connect(self._execute)
        self.execute_btn.setEnabled(False)
        layout.addWidget(self.execute_btn)
        
        layout.addStretch()
        scroll.setWidget(content)
        
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return widget
    
    def _on_mode_dropped(self):
        mode_id = self.mode_slot.mode_id
        
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sl = item.layout()
                if sl is not None:
                    while sl.count():
                        si = sl.takeAt(0)
                        if si is not None:
                            sw = si.widget()
                            if sw is not None:
                                sw.setParent(None)
                                sw.deleteLater()
        
        if hasattr(self, 'n_input'):
            delattr(self, 'n_input')
        if hasattr(self, 'c_input'):
            delattr(self, 'c_input')
        if hasattr(self, 'd_input'):
            delattr(self, 'd_input')
        if hasattr(self, 'pairs_count_spin'):
            delattr(self, 'pairs_count_spin')
        self.pair_widgets = []
        
        # n input (common)
        n_label = QLabel("Modulus n:")
        self.n_input = QTextEdit()
        self.n_input.setPlaceholderText("Common modulus n (decimal or hex)...")
        self.n_input.setMinimumHeight(50)
        self.n_input.setMaximumHeight(80)
        self.options_layout.addWidget(n_label)
        self.options_layout.addWidget(self.n_input)
        
        n_btn_row = QHBoxLayout()
        n_paste = QPushButton("Paste")
        n_paste.setObjectName("actionButton")
        n_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        n_paste.clicked.connect(lambda: self._paste_to(self.n_input))
        n_clear = QPushButton("Clear")
        n_clear.setObjectName("dangerButton")
        n_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        n_clear.clicked.connect(self.n_input.clear)
        n_btn_row.addWidget(n_paste)
        n_btn_row.addWidget(n_clear)
        n_btn_row.addStretch()
        self.options_layout.addLayout(n_btn_row)
        
        # Private key d (optional)
        d_row = QHBoxLayout()
        d_label = QLabel("d (optional):")
        d_label.setFixedWidth(80)
        self.d_input = QLineEdit()
        self.d_input.setPlaceholderText("Private key d (leave empty for Common Modulus Attack)...")
        d_paste = QPushButton("Paste")
        d_paste.setObjectName("actionButton")
        d_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        d_paste.clicked.connect(lambda: self._paste_to(self.d_input))
        d_clear = QPushButton("Clear")
        d_clear.setObjectName("dangerButton")
        d_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        d_clear.clicked.connect(self.d_input.clear)
        d_row.addWidget(d_label)
        d_row.addWidget(self.d_input, 1)
        d_row.addWidget(d_paste)
        d_row.addWidget(d_clear)
        self.options_layout.addLayout(d_row)
        
        if mode_id == 1:  # Single Cipher
            c_row = QHBoxLayout()
            c_label = QLabel("c:")
            c_label.setFixedWidth(20)
            self.c_input = QLineEdit()
            self.c_input.setPlaceholderText("Single ciphertext (same m encrypted with all e's)...")
            c_paste = QPushButton("Paste")
            c_paste.setObjectName("actionButton")
            c_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            c_paste.clicked.connect(lambda: self._paste_to(self.c_input))
            c_clear = QPushButton("Clear")
            c_clear.setObjectName("dangerButton")
            c_clear.setCursor(Qt.CursorShape.PointingHandCursor)
            c_clear.clicked.connect(self.c_input.clear)
            c_row.addWidget(c_label)
            c_row.addWidget(self.c_input, 1)
            c_row.addWidget(c_paste)
            c_row.addWidget(c_clear)
            self.options_layout.addLayout(c_row)
            
            # Exponents count
            exp_header = QHBoxLayout()
            exp_label = QLabel("Exponents:")
            exp_label.setStyleSheet("font-weight: 600;")
            self.pairs_count_spin = QSpinBox()
            self.pairs_count_spin.setMinimum(2)
            self.pairs_count_spin.setMaximum(20)
            self.pairs_count_spin.setValue(2)
            self.pairs_count_spin.setToolTip("Number of different public exponents")
            self.pairs_count_spin.valueChanged.connect(self._update_exponents)
            exp_header.addWidget(exp_label)
            exp_header.addWidget(self.pairs_count_spin)
            exp_header.addStretch()
            self.options_layout.addLayout(exp_header)
            
            # Exponents container
            self.exp_group = QGroupBox("Public Exponents")
            self.exp_layout = QVBoxLayout()
            self.exp_layout.setSpacing(6)
            self.exp_group.setLayout(self.exp_layout)
            self.options_layout.addWidget(self.exp_group)
            
            self._update_exponents()
            self.execute_btn.setText("Run Attack")
            
        elif mode_id == 2:  # Multiple Pairs
            pairs_header = QHBoxLayout()
            pairs_label = QLabel("(e, c) Pairs:")
            pairs_label.setStyleSheet("font-weight: 600;")
            self.pairs_count_spin = QSpinBox()
            self.pairs_count_spin.setMinimum(2)
            self.pairs_count_spin.setMaximum(20)
            self.pairs_count_spin.setValue(2)
            self.pairs_count_spin.valueChanged.connect(self._update_pairs)
            pairs_header.addWidget(pairs_label)
            pairs_header.addWidget(self.pairs_count_spin)
            pairs_header.addStretch()
            self.options_layout.addLayout(pairs_header)
            
            self.pairs_group = QGroupBox("e, c Pairs")
            self.pairs_layout = QVBoxLayout()
            self.pairs_layout.setSpacing(8)
            self.pairs_group.setLayout(self.pairs_layout)
            self.options_layout.addWidget(self.pairs_group)
            
            self._update_pairs()
            self.execute_btn.setText("Run Attack")
        
        self.options_group.setVisible(True)
        self.execute_btn.setEnabled(True)
        self._apply_theme()
    
    def _on_mode_cleared(self):
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sl = item.layout()
                if sl is not None:
                    while sl.count():
                        si = sl.takeAt(0)
                        if si is not None:
                            sw = si.widget()
                            if sw is not None:
                                sw.setParent(None)
                                sw.deleteLater()
        
        if hasattr(self, 'n_input'):
            delattr(self, 'n_input')
        if hasattr(self, 'c_input'):
            delattr(self, 'c_input')
        if hasattr(self, 'd_input'):
            delattr(self, 'd_input')
        if hasattr(self, 'pairs_count_spin'):
            delattr(self, 'pairs_count_spin')
        self.pair_widgets = []
        
        self.options_group.setVisible(False)
        self.execute_btn.setText("Execute")
        self.execute_btn.setEnabled(False)
    
    def _update_exponents(self):
        if not hasattr(self, 'exp_layout'):
            return
        
        while self.exp_layout.count():
            item = self.exp_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sl = item.layout()
                if sl is not None:
                    while sl.count():
                        si = sl.takeAt(0)
                        if si is not None:
                            sw = si.widget()
                            if sw is not None:
                                sw.setParent(None)
                                sw.deleteLater()
        
        count = self.pairs_count_spin.value()
        self.pair_widgets = []
        
        for i in range(count):
            e_row = QHBoxLayout()
            e_label = QLabel(f"e{i+1}:")
            e_label.setFixedWidth(35)
            e_input = QLineEdit()
            e_input.setPlaceholderText(f"e{i+1} (e.g. 3, 5, 65537)")
            e_paste = QPushButton("Paste")
            e_paste.setObjectName("actionButton")
            e_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            e_paste.clicked.connect(lambda checked, w=e_input: self._paste_to(w))
            e_row.addWidget(e_label)
            e_row.addWidget(e_input, 1)
            e_row.addWidget(e_paste)
            self.exp_layout.addLayout(e_row)
            self.pair_widgets.append(e_input)
        
        self._apply_theme()
    
    def _update_pairs(self):
        if not hasattr(self, 'pairs_layout'):
            return
        
        while self.pairs_layout.count():
            item = self.pairs_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sl = item.layout()
                if sl is not None:
                    while sl.count():
                        si = sl.takeAt(0)
                        if si is not None:
                            sw = si.widget()
                            if sw is not None:
                                sw.setParent(None)
                                sw.deleteLater()
        
        count = self.pairs_count_spin.value()
        self.pair_widgets = []
        
        for i in range(count):
            pair_frame = QFrame()
            pair_layout = QHBoxLayout(pair_frame)
            pair_layout.setContentsMargins(0, 0, 0, 0)
            pair_layout.setSpacing(8)
            
            idx_label = QLabel(f"Pair {i+1}:")
            idx_label.setFixedWidth(45)
            idx_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            e_input = QLineEdit()
            e_input.setPlaceholderText(f"e{i+1}")
            e_input.setMinimumWidth(120)
            
            c_input = QLineEdit()
            c_input.setPlaceholderText(f"c{i+1}")
            
            e_paste = QPushButton("P")
            e_paste.setObjectName("actionButton")
            e_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            e_paste.setMaximumWidth(35)
            e_paste.clicked.connect(lambda checked, w=e_input: self._paste_to(w))
            
            c_paste = QPushButton("P")
            c_paste.setObjectName("actionButton")
            c_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            c_paste.setMaximumWidth(35)
            c_paste.clicked.connect(lambda checked, w=c_input: self._paste_to(w))
            
            pair_layout.addWidget(idx_label)
            pair_layout.addWidget(e_input)
            pair_layout.addWidget(e_paste)
            pair_layout.addWidget(c_input)
            pair_layout.addWidget(c_paste)
            
            self.pairs_layout.addWidget(pair_frame)
            self.pair_widgets.append((e_input, c_input))
        
        self._apply_theme()
    
    def _paste_to(self, widget):
        clipboard = QApplication.clipboard().text()
        if clipboard:
            if isinstance(widget, QTextEdit):
                widget.setPlainText(clipboard)
            else:
                widget.setText(clipboard)
    
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
        layout.addWidget(self.status_progress)
        layout.addWidget(self.status_output)
        return widget
    
    def _create_results_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        results_header = QHBoxLayout()
        results_label = QLabel("Result:")
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
        self.results_output.setPlaceholderText("Result will appear here...")
        layout.addWidget(self.results_output)
        
        self.results_info = QLabel("")
        layout.addWidget(self.results_info)
        return widget
    
    def _create_help_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        self.help_group = QGroupBox("Common Modulus Attack Help")
        help_layout = QVBoxLayout()
        help_layout.setSpacing(10)
        
        help_text = QTextBrowser()
        help_text.setOpenExternalLinks(False)
        help_text.setHtml("""
            <h3>Common Modulus Attack</h3>
            <p>When the <b>same message m</b> is encrypted with <b>different public exponents</b> 
            using the <b>same modulus n</b>, and GCD of all exponents is 1, 
            the plaintext can be recovered <b>without the private key</b>.</p>
            
            <h3>Two Modes</h3>
            <ul>
                <li><b>Single Cipher:</b> One ciphertext encrypted with multiple e values</li>
                <li><b>Multiple Pairs:</b> Multiple different (e, c) pairs</li>
            </ul>
            
            <h3>Optional d</h3>
            <p>If you have the private key d, enter it to decrypt directly without the attack.</p>
        """)
        help_layout.addWidget(help_text)
        
        self.help_group.setLayout(help_layout)
        layout.addWidget(self.help_group)
        return widget
    
    def _execute(self):
        if not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Drag an operation mode into the slot")
            return
        
        if not hasattr(self, 'n_input') or not self.n_input.toPlainText().strip():
            QMessageBox.warning(self, "No Input", "Please enter the modulus n.")
            return
        
        n = self.n_input.toPlainText().strip()
        d = self.d_input.text().strip() if hasattr(self, 'd_input') else ""
        mode_id = self.mode_slot.mode_id
        
        pairs = []
        if mode_id == 1:  # Single Cipher
            c = self.c_input.text().strip() if hasattr(self, 'c_input') else ""
            if not c and not d:
                QMessageBox.warning(self, "No Input", "Please enter ciphertext c or private key d.")
                return
            for e_input in self.pair_widgets:
                e = e_input.text().strip()
                if not e:
                    QMessageBox.warning(self, "Missing Input", "Please fill in all exponent values.")
                    return
                pairs.append((e, c))
        else:  # Multiple Pairs
            for e_input, c_input in self.pair_widgets:
                e = e_input.text().strip()
                c = c_input.text().strip()
                if not e or not c:
                    QMessageBox.warning(self, "Missing Input", "Please fill in all e and c values.")
                    return
                pairs.append((e, c))
        
        if not pairs and not d:
            QMessageBox.warning(self, "No Input", "Please provide either pairs or private key d.")
            return
        
        self.tabs.setCurrentIndex(1)
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        self.execute_btn.setEnabled(False)
        
        self.worker = CommonModulusWorker(n, pairs, d)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg):
        self.status_output.append(msg)
    
    def _on_finished(self, success, message, info):
        self.execute_btn.setEnabled(True)
        if success:
            self.status_output.append("\u2713 SUCCESS!")
            self.status_progress.setValue(100)
            self.results_output.setText(message)
            if info:
                parts = [f"n bits: {info.get('n_bits', 'N/A')}"]
                if info.get('mode'):
                    parts.append(f"Mode: {info['mode']}")
                if info.get('is_text'):
                    parts.append("Text decoded")
                self.results_info.setText(" | ".join(str(p) for p in parts))
            self.tabs.setCurrentIndex(2)
        else:
            self.status_output.append(f"\u2717 Error: {message}")
    
    def _copy_results(self):
        text = self.results_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _apply_theme(self):
        t = self.theme.current
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background-color:{t['base']};}}
            QTabBar::tab {{background-color:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;font-size:13px;font-weight:600;}}
            QTabBar::tab:selected {{background-color:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
        
        gs = f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        for attr in ['mode_group', 'options_group', 'exp_group', 'pairs_group', 'help_group']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:10px 14px;font-weight:700;font-size:13px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['error']};border:1px solid {t['border']};border-radius:10px;padding:10px 14px;font-weight:700;font-size:13px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
            except RuntimeError:
                pass
        
        ts = f"QTextEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono,monospace;font-size:13px;}}"
        for attr in ['n_input', 'status_output']:
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
        
        input_style = f"QLineEdit{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 10px;font-size:13px;}}"
        for attr in ['c_input', 'd_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                except RuntimeError:
                    pass
        
        for widget in self.pair_widgets:
            try:
                if isinstance(widget, tuple):
                    for w in widget:
                        w.setStyleSheet(input_style)
                else:
                    widget.setStyleSheet(input_style)
            except RuntimeError:
                pass
        
        if hasattr(self, 'pairs_count_spin') and self.pairs_count_spin is not None:
            try:
                self.pairs_count_spin.setStyleSheet(f"""
                    QSpinBox {{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:6px 10px;font-size:13px;}}
                    QSpinBox::up-button, QSpinBox::down-button {{background-color:{t['surface0']};border:none;border-radius:3px;width:18px;}}
                """)
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(f"QProgressBar{{background-color:{t['surface0']};border:none;border-radius:4px;height:14px;text-align:center;font-size:10px;font-weight:600;}} QProgressBar::chunk{{background-color:{t['success']};border-radius:4px;}}")
            except RuntimeError:
                pass
        
        if hasattr(self, 'results_info') and self.results_info is not None:
            try:
                self.results_info.setStyleSheet(f"color:{t['text_secondary']};font-size:12px;")
            except RuntimeError:
                pass
        
        if hasattr(self, 'mode_slot') and self.mode_slot is not None:
            try:
                self.mode_slot.colors = t
                if self.mode_slot.is_filled():
                    self.mode_slot._style_filled()
                else:
                    self.mode_slot._style_empty()
                self.mode_slot.update()
            except RuntimeError:
                pass
        
        for card in self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
    
    def refresh_theme(self):
        self._apply_theme()