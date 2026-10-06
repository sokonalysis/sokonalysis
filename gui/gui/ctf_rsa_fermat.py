# gui/ctf_rsa_fermat.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QMessageBox, QProgressBar, QScrollArea, QTextBrowser,
    QFrame, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QSize
from PySide6.QtGui import QPixmap, QDrag, QPainter, QColor, QFont, QIcon
from Crypto.Util.number import inverse, long_to_bytes
import os
import sys
import math
from gui.layout_manager import layout_manager


class FermatWorker(QThread):
    """Worker thread for Fermat's factorization + decryption."""
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
    
    def _is_perfect_square(self, x):
        if x < 0:
            return False
        root = int(math.isqrt(x))
        return root * root == x
    
    def run(self):
        try:
            self.progress.emit("Parsing inputs...")
            self.progress_value.emit(5)
            
            n = self._parse_number(self.n_str)
            e = self._parse_number(self.e_str) if self.e_str.strip() else 65537
            c = self._parse_number(self.c_str) if self.c_str.strip() else None
            
            self.progress.emit(f"n bits: {n.bit_length()}")
            self.progress.emit(f"e = {e}")
            if c:
                self.progress.emit(f"c provided ({c.bit_length()} bits)")
            self.progress_value.emit(10)
            
            if n % 2 == 0:
                p = 2
                q = n // 2
                self.progress.emit("n is even! Trivially factored.")
                self._finish_with_factors(n, e, c, p, q, 1)
                return
            
            a = math.isqrt(n)
            if a * a < n:
                a += 1
            
            self.progress.emit("Starting Fermat factorization...")
            self.progress.emit(f"a = ceil(sqrt(n)) = {a}")
            self.progress_value.emit(15)
            
            max_iterations = 1000000
            iteration = 0
            found = False
            p = q = 0
            
            while iteration < max_iterations:
                b2 = a * a - n
                
                if self._is_perfect_square(b2):
                    b = int(math.isqrt(b2))
                    p = a + b
                    q = a - b
                    
                    if p * q == n and p > 1 and q > 1:
                        found = True
                        self.progress.emit(f"Found after {iteration + 1} iterations!")
                        self.progress.emit(f"|p-q| = {abs(p - q)}")
                        break
                
                a += 1
                iteration += 1
                
                if iteration % 50000 == 0:
                    progress = min(15 + int((iteration / max_iterations) * 80), 90)
                    self.progress_value.emit(progress)
                    self.progress.emit(f"Iteration {iteration}...")
            
            if found:
                self._finish_with_factors(n, e, c, p, q, iteration + 1)
            else:
                self.progress_value.emit(100)
                result = (
                    f"Fermat factorization failed after {max_iterations} iterations.\n"
                    f"This suggests p and q are not close together."
                )
                self.finished.emit(False, result, {})
            
        except Exception as ex:
            self.progress.emit(f"Error: {str(ex)}")
            self.progress_value.emit(100)
            self.finished.emit(False, str(ex), {})
    
    def _finish_with_factors(self, n, e, c, p, q, iterations):
        self.progress_value.emit(80)
        
        has_ciphertext = c is not None
        
        if has_ciphertext:
            self.progress.emit("Computing private key d...")
            phi = (p - 1) * (q - 1)
            d = inverse(e, phi)
            m = pow(c, d, n)
            
            self.progress.emit(f"p = {p}")
            self.progress.emit(f"q = {q}")
            self.progress.emit(f"|p-q| = {abs(p - q)}")
            self.progress.emit(f"Iterations: {iterations}")
            
            try:
                m_bytes = long_to_bytes(m)
                plaintext = m_bytes.decode('utf-8', errors='replace')
                result = plaintext
            except:
                result = f"0x{m:x}"
            
            self.progress.emit("Decryption complete!")
        else:
            result = "Fermat Factorization Successful!\n\n"
            result += f"n bits = {n.bit_length()}\n\n"
            result += f"p = {p}\n\n"
            result += f"q = {q}\n\n"
            result += f"|p-q| = {abs(p - q)}\n"
            result += f"Iterations: {iterations}\n"
            result += "✓ p * q = n"
        
        self.progress.emit("Done!")
        self.progress_value.emit(100)
        info = {
            'n_bits': n.bit_length(),
            'diff': abs(p - q),
            'iterations': iterations,
            'is_text': has_ciphertext
        }
        self.finished.emit(True, result, info)


class DraggableModeCard(QFrame):
    def __init__(self, mode_id, name, theme_colors, parent=None):
        super().__init__(parent)
        self.mode_id = mode_id
        self.mode_name = name
        self.colors = theme_colors
        self.name_label = None
        self._apply_scaled_size()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._build(name)
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        w = max(140, int(180 * scale))
        h = max(56, int(70 * scale))
        self.setMinimumSize(w, h)
        self.setMaximumSize(w + int(40 * scale), h + int(20 * scale))
    
    def _build(self, name):
        t = self.colors
        scale = layout_manager.font_scale()
        if self.layout() is None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(
                int(14 * scale), int(12 * scale),
                int(14 * scale), int(12 * scale)
            )
            layout.setSpacing(int(4 * scale))
            self.name_label = QLabel(name)
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setWordWrap(True)
            layout.addWidget(self.name_label)
        else:
            if self.name_label is not None:
                self.name_label.setText(name)
        self.name_label.setStyleSheet(
            f"color: {t['text']}; font-size: {max(11, int(13 * scale))}px; "
            f"font-weight: 600; background: transparent;"
        )
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} "
            f"QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}"
        )
    
    def update_theme(self, theme_colors):
        self.colors = theme_colors
        self._apply_scaled_size()
        self._build(self.mode_name)
        self.update()
        self.repaint()
    
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
        self._placeholder = "Drag operation here"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        text_w = int(len(self._placeholder) * 8 * scale) + int(40 * scale)
        min_w = max(200, text_w)
        max_w = min_w + int(80 * scale)
        h = max(72, int(90 * scale))
        self.setMinimumSize(min_w, h)
        self.setMaximumSize(max_w, h + int(20 * scale))
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:3px dashed {t['border']};border-radius:10px;}}"
        )
    
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['accent']}15;border:3px solid {t['accent']}88;border-radius:10px;}}"
        )
    
    def is_filled(self):
        return self.mode_id is not None
    
    def clear_slot(self):
        self.mode_id = None
        self.mode_name = None
        self._style_empty()
        self.update()
        self.repaint()
    
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
            self.repaint()
            event.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, CTF_RSA_FermatPage):
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
        scale = layout_manager.font_scale()
        
        if self.is_filled():
            font_size = max(11, int(13 * scale))
            painter.setPen(QColor(t['accent']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", font_size, QFont.Weight.Bold))
            text = self.mode_name
        else:
            font_size = max(9, int(10 * scale))
            painter.setPen(QColor(t['text_tertiary']))
            painter.setFont(QFont("JetBrains Mono, Consolas, monospace", font_size))
            text = self._placeholder
        
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        fm = painter.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
            p = self.parent()
            while p and not isinstance(p, CTF_RSA_FermatPage):
                p = p.parent()
            if p:
                p._on_mode_cleared()
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.is_filled():
            self._style_filled()
        else:
            self._style_empty()
        self.update()
        self.repaint()


class CTF_RSA_FermatPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.mode_cards = []
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
        
        title = QLabel("Fermat's Factorization")
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
        for mode_id, name in [(1, "Factor Only"), (2, "Factor & Decrypt")]:
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
        
        # Step 2: Options
        self.options_group = QGroupBox("2. Options")
        self.options_layout = QVBoxLayout()
        self.options_layout.setSpacing(10)
        self.options_group.setLayout(self.options_layout)
        self.options_group.setVisible(False)
        layout.addWidget(self.options_group)
        
        # Execute button
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("actionButton")
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
    
    def _clear_options(self):
        """Safely clear the dynamic options layout."""
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
    
    def _on_mode_dropped(self):
        mode_id = self.mode_slot.mode_id
        scale = layout_manager.font_scale()
        # Button min width scales with the font so "Paste"/"Clear" are never clipped
        btn_min_w = max(70, int(84 * scale))
        
        self._clear_options()
        
        if hasattr(self, 'n_input'):
            delattr(self, 'n_input')
        if hasattr(self, 'e_input'):
            delattr(self, 'e_input')
        if hasattr(self, 'c_input'):
            delattr(self, 'c_input')
        
        # n input
        n_label = QLabel("Modulus n:")
        self.n_input = QTextEdit()
        self.n_input.setPlaceholderText(
            "RSA modulus n (decimal or hex with 0x prefix)..."
        )
        self.n_input.setMinimumHeight(80)
        self.n_input.setMaximumHeight(120)
        self.options_layout.addWidget(n_label)
        self.options_layout.addWidget(self.n_input)
        
        n_btn_row = QHBoxLayout()
        n_paste = QPushButton("Paste")
        n_paste.setObjectName("actionButton")
        n_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        n_paste.clicked.connect(lambda: self._paste_to(self.n_input))
        n_paste.setMinimumWidth(btn_min_w)
        n_clear = QPushButton("Clear")
        n_clear.setObjectName("dangerButton")
        n_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        n_clear.clicked.connect(self.n_input.clear)
        n_clear.setMinimumWidth(btn_min_w)
        n_btn_row.addWidget(n_paste)
        n_btn_row.addWidget(n_clear)
        n_btn_row.addStretch()
        self.options_layout.addLayout(n_btn_row)
        
        # e input — each button has its own min width
        e_row = QHBoxLayout()
        e_label = QLabel("e:")
        e_label.setFixedWidth(20)
        self.e_input = QLineEdit()
        self.e_input.setPlaceholderText("Public exponent (default: 65537)...")
        self.e_input.setText("65537")
        self.e_input.setMinimumHeight(36)
        e_paste = QPushButton("Paste")
        e_paste.setObjectName("actionButton")
        e_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        e_paste.clicked.connect(lambda: self._paste_to(self.e_input))
        e_paste.setMinimumWidth(btn_min_w)
        e_clear = QPushButton("Clear")
        e_clear.setObjectName("dangerButton")
        e_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        e_clear.clicked.connect(self.e_input.clear)
        e_clear.setMinimumWidth(btn_min_w)
        e_row.addWidget(e_label)
        e_row.addWidget(self.e_input, 1)
        e_row.addWidget(e_paste)
        e_row.addWidget(e_clear)
        self.options_layout.addLayout(e_row)
        
        if mode_id == 2:  # Factor & Decrypt
            c_row = QHBoxLayout()
            c_label = QLabel("c:")
            c_label.setFixedWidth(20)
            self.c_input = QLineEdit()
            self.c_input.setPlaceholderText("Ciphertext to decrypt...")
            self.c_input.setMinimumHeight(36)
            c_paste = QPushButton("Paste")
            c_paste.setObjectName("actionButton")
            c_paste.setCursor(Qt.CursorShape.PointingHandCursor)
            c_paste.clicked.connect(lambda: self._paste_to(self.c_input))
            c_paste.setMinimumWidth(btn_min_w)
            c_clear = QPushButton("Clear")
            c_clear.setObjectName("dangerButton")
            c_clear.setCursor(Qt.CursorShape.PointingHandCursor)
            c_clear.clicked.connect(self.c_input.clear)
            c_clear.setMinimumWidth(btn_min_w)
            c_row.addWidget(c_label)
            c_row.addWidget(self.c_input, 1)
            c_row.addWidget(c_paste)
            c_row.addWidget(c_clear)
            self.options_layout.addLayout(c_row)
            self.execute_btn.setText("Factor & Decrypt")
        else:
            self.execute_btn.setText("Factor")
        
        self.options_group.setVisible(True)
        self.execute_btn.setEnabled(True)
        self._apply_theme()
    
    def _on_mode_cleared(self):
        self._clear_options()
        
        if hasattr(self, 'n_input'):
            delattr(self, 'n_input')
        if hasattr(self, 'e_input'):
            delattr(self, 'e_input')
        if hasattr(self, 'c_input'):
            delattr(self, 'c_input')
        
        self.options_group.setVisible(False)
        self.execute_btn.setText("Execute")
        self.execute_btn.setEnabled(False)
    
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
        if not self.mode_slot.is_filled():
            QMessageBox.warning(self, "No Mode", "Drag an operation mode into the slot")
            return
        
        if not hasattr(self, 'n_input') or not self.n_input.toPlainText().strip():
            QMessageBox.warning(self, "No Input", "Please enter the modulus n.")
            return
        
        n = self.n_input.toPlainText().strip()
        e = self.e_input.text().strip() if hasattr(self, 'e_input') else "65537"
        c = self.c_input.text().strip() if hasattr(self, 'c_input') else ""
        
        self.tabs.setCurrentIndex(1)
        self.status_progress.setValue(0)
        self.status_output.clear()
        self.results_output.clear()
        
        self.status_output.append("[*] Initializing Fermat factorization...")
        self.status_output.append(f"[*] Modulus bits: {len(n)} chars")
        self.status_output.append("[*] Starting worker...")
        
        sb = self.status_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())
        
        self.execute_btn.setEnabled(False)
        self.execute_btn.setText("Running...")
        
        self.worker = FermatWorker(n, e, c)
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
        if self.mode_slot.is_filled() and self.mode_slot.mode_id == 2:
            self.execute_btn.setText("Factor & Decrypt")
        elif self.mode_slot.is_filled():
            self.execute_btn.setText("Factor")
        else:
            self.execute_btn.setText("Execute")
        
        if success:
            self.status_progress.setValue(100)
            self.status_output.append("✓ SUCCESS!")
            sb = self.status_output.verticalScrollBar()
            if sb:
                sb.setValue(sb.maximum())
            self.results_output.setText(message)
            if info:
                parts = [f"n bits: {info.get('n_bits', 'N/A')}"]
                if info.get('diff') is not None:
                    parts.append(f"|p-q|: {info['diff']}")
                if info.get('iterations'):
                    parts.append(f"Iterations: {info['iterations']}")
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
        for attr in ['mode_group', 'options_group']:
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
        
        if hasattr(self, 'execute_btn') and self.execute_btn is not None:
            self.execute_btn.setMinimumHeight(max(48, int(56 * scale)))
        
        ts = (
            f"QTextEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{int(13 * scale)}px;}}"
        )
        for attr in ['n_input', 'status_output']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(ts)
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
        
        input_style = (
            f"QLineEdit{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:6px 10px;"
            f"font-family:JetBrains Mono,monospace;font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['e_input', 'c_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_style)
                    getattr(self, attr).setMinimumHeight(max(34, int(36 * scale)))
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
        
        if hasattr(self, 'mode_slot') and self.mode_slot is not None:
            try:
                self.mode_slot.update_colors(t)
            except RuntimeError:
                pass
        
        for card in self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
    
    def refresh_theme(self):
        self._apply_theme()