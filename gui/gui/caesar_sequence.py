# gui/caesar_sequence.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QGridLayout,
    QScrollArea, QSpinBox, QFrame, QProgressBar,
    QApplication, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QMimeData, QTimer, QSize
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor, QFont, QIcon
import string
import os
import sys
from gui.layout_manager import layout_manager


class PolyCipher:
    def __init__(self, shifts, sequence):
        self.shiftValues = list(shifts)
        self.keySequence = list(sequence)
    
    def shiftChar(self, c, shift):
        if not c.isalpha():
            return None
        base = ord('A') if c.isupper() else ord('a')
        return chr((ord(c) - base + shift + 26) % 26 + base)
    
    def encrypt(self, plaintext):
        result = []
        seq_idx = 0
        seq_len = len(self.keySequence)
        for char in plaintext:
            if char.isspace() or not char.isalpha():
                result.append(char)
                continue
            idx = self.keySequence[seq_idx % seq_len]
            result.append(self.shiftChar(char, self.shiftValues[idx]))
            seq_idx += 1
        return ''.join(result)
    
    def decrypt(self, ciphertext):
        result = []
        seq_idx = 0
        seq_len = len(self.keySequence)
        for char in ciphertext:
            if char.isspace() or not char.isalpha():
                result.append(char)
                continue
            idx = self.keySequence[seq_idx % seq_len]
            result.append(self.shiftChar(char, -self.shiftValues[idx]))
            seq_idx += 1
        return ''.join(result)


class DraggableKeyButton(QPushButton):
    def __init__(self, key_id, shift_value, theme_colors, parent=None):
        super().__init__(parent)
        self.key_id = key_id
        self.shift_value = shift_value
        self.colors = theme_colors
        self._apply_scaled_size()
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._apply_style()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        # Minimum floor of 52x32 so the label is always readable
        w = max(52, int(60 * scale))
        h = max(32, int(34 * scale))
        self.setFixedSize(w, h)
    
    def _apply_style(self):
        t = self.colors
        scale = layout_manager.font_scale()
        self.setText(f"C{self.key_id}")
        # Minimum font size 11px so C1 is never tiny
        font_size = max(11, int(12 * scale))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                font-family: JetBrains Mono, monospace;
                font-size: {font_size}px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {t['surface0']};
                border-color: {t['surface2']};
            }}
        """)
    
    def update_theme(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        self._apply_style()
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
            mime.setText(f"{self.key_id}:{self.shift_value}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class SequenceSlot(QFrame):
    def __init__(self, index, theme_colors, parent=None):
        super().__init__(parent)
        self.index = index
        self.colors = theme_colors
        self.key_id = None
        self.shift_value = None
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._apply_style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        # Floor at 48x32 so slot number / label is always visible
        w = max(48, int(56 * scale))
        h = max(32, int(34 * scale))
        self.setFixedSize(w, h)
    
    def _apply_style_empty(self):
        t = self.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t['crust']};
                border: 2px dashed {t['border']};
                border-radius: 6px;
            }}
        """)
    
    def _apply_style_filled(self):
        t = self.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t['crust']};
                border: 1px solid {t['border']};
                border-radius: 6px;
            }}
        """)
    
    def is_filled(self):
        return self.key_id is not None
    
    def get_data(self):
        return self.key_id, self.shift_value
    
    def clear_slot(self):
        self.key_id = None
        self.shift_value = None
        self._apply_style_empty()
        self.update()
        self.repaint()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        data = event.mimeData().text()
        key_id, shift_val = data.split(':')
        self.key_id = int(key_id)
        self.shift_value = int(shift_val)
        self._apply_style_filled()
        self.update()
        self.repaint()
        event.acceptProposedAction()
        p = self.parent()
        while p and not isinstance(p, CaesarSequencePage):
            p = p.parent()
        if p and p._check_all_slots_filled():
            p.setup_progress.setValue(100)
            QTimer.singleShot(300, lambda: p.tabs.setCurrentIndex(1))
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        scale = layout_manager.font_scale()
        if self.is_filled():
            painter.setPen(QColor(t['text']))
            # Floor at 11px so C1 is legible in compact mode
            font_size = max(11, int(11 * scale))
            painter.setFont(QFont("JetBrains Mono, monospace", font_size, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"C{self.key_id}")
        else:
            painter.setPen(QColor(t['text_tertiary']))
            # Floor at 10px so position number is legible
            font_size = max(10, int(8 * scale))
            painter.setFont(QFont("JetBrains Mono, monospace", font_size))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.index + 1))
        painter.end()
    
    def mouseDoubleClickEvent(self, event):
        if self.is_filled():
            self.clear_slot()
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.is_filled():
            self._apply_style_filled()
        else:
            self._apply_style_empty()
        self.update()
        self.repaint()


class SequenceShiftTableGrid(QScrollArea):
    """Shift table matching Basic Caesar style with scaled cells."""
    
    def __init__(self, theme_colors):
        super().__init__()
        self.colors = theme_colors
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("border: none; background: transparent;")
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(1)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.setWidget(self.container)
    
    def update_colors(self, tc):
        self.colors = tc
    
    def update_table(self, shifts_dict, sequence_ids, plaintext, ciphertext):
        t = self.colors
        scale = layout_manager.font_scale()
        
        # All floors so compact mode stays readable
        cell_w = max(22, int(30 * scale))
        cell_h = max(22, int(28 * scale))
        header_h = max(26, int(34 * scale))
        label_w = max(34, int(38 * scale))
        base_font = max(10, int(12 * scale))
        big_font = max(11, int(14 * scale))
        small_font = max(9, int(10 * scale))
        
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not sequence_ids:
            return
        
        alphabet = string.ascii_uppercase
        
        # Row 0: Position numbers
        pos_lbl = QLabel("Pos")
        pos_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pos_lbl.setStyleSheet(
            f"background:{t['surface0']};color:{t['text']};font-weight:bold;padding:4px;"
            f"font-family:JetBrains Mono;font-size:{base_font}px;border-radius:4px;"
        )
        pos_lbl.setFixedSize(label_w, header_h)
        self.grid.addWidget(pos_lbl, 0, 0)
        
        for i in range(26):
            lbl = QLabel(str(i + 1))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background:{t['surface0']};color:{t['text_secondary']};padding:2px;"
                f"font-family:JetBrains Mono;font-size:{small_font}px;border-radius:3px;"
            )
            lbl.setFixedSize(cell_w, header_h)
            self.grid.addWidget(lbl, 0, i + 1)
        
        # Row 1: Plain alphabet
        plain_lbl = QLabel("Plain")
        plain_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plain_lbl.setStyleSheet(
            f"background:{t['surface0']};color:{t['text']};font-weight:bold;padding:4px;"
            f"font-family:JetBrains Mono;font-size:{base_font}px;border-radius:4px;"
        )
        plain_lbl.setFixedSize(label_w, cell_h + 4)
        self.grid.addWidget(plain_lbl, 1, 0)
        
        for i, letter in enumerate(alphabet):
            lbl = QLabel(letter)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background:transparent;color:{t['text']};font-weight:bold;padding:3px;"
                f"font-family:JetBrains Mono;font-size:{big_font}px;border-radius:3px;"
            )
            lbl.setFixedSize(cell_w, cell_h + 4)
            self.grid.addWidget(lbl, 1, i + 1)
        
        # Cipher rows for each unique key
        row = 2
        seen = set()
        for kid in sequence_ids:
            if kid in seen:
                continue
            seen.add(kid)
            sv = shifts_dict.get(kid, 0)
            shifted = alphabet[sv % 26:] + alphabet[:sv % 26]
            
            row_lbl = QLabel(f"C{kid}")
            row_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_lbl.setStyleSheet(
                f"background:{t['surface0']};color:{t['text_secondary']};font-weight:bold;"
                f"padding:3px;font-family:JetBrains Mono;font-size:{base_font}px;border-radius:4px;"
            )
            row_lbl.setFixedSize(label_w, cell_h)
            self.grid.addWidget(row_lbl, row, 0)
            
            for col, char in enumerate(shifted):
                cell = QLabel(char)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if char == alphabet[col]:
                    cell.setStyleSheet(
                        f"background:{t['success']}22;color:{t['success']};font-weight:bold;"
                        f"padding:3px;font-family:JetBrains Mono;font-size:{big_font}px;"
                        f"border-radius:3px;border:1px solid {t['success']}44;"
                    )
                else:
                    cell.setStyleSheet(
                        f"background:transparent;color:{t['text']};padding:3px;"
                        f"font-family:JetBrains Mono;font-size:{big_font}px;border-radius:3px;"
                    )
                cell.setFixedSize(cell_w, cell_h)
                self.grid.addWidget(cell, row, col + 1)
            row += 1


class CaesarSequencePage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.key_buttons = []
        self.key_shift_spinners = []
        self.sequence_slots = []
        self._last_shifts = {}
        self._last_seq_ids = []
        self._last_pt = ""
        self._last_ct = ""
        self._init_ui()
        QTimer.singleShot(100, self._generate_keys)
    
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
        title = QLabel("Polyalphabetic - Sequence")
        title.setObjectName("pageTitle")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_input(), "Input")
        self.tabs.addTab(self._tab_results(), "Results")
        self.tabs.addTab(self._tab_shift_table(), "Shift Table")
        
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
        for attr in ['keys_grp', 'seq_grp', 'in_grp']:
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
        if hasattr(self, 'results_output') and self.results_output is not None:
            self.results_output.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['success']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:16px;"
                f"font-family:JetBrains Mono,monospace;font-size:{int(18 * scale)}px;font-weight:700;}}"
            )
        
        spin_style = (
            f"QSpinBox{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;"
            f"padding:6px 10px;font-size:{int(13 * scale)}px;}}"
        )
        if hasattr(self, 'num_keys_spin') and self.num_keys_spin is not None:
            self.num_keys_spin.setStyleSheet(spin_style)
        if hasattr(self, 'seq_length_spin') and self.seq_length_spin is not None:
            self.seq_length_spin.setStyleSheet(spin_style)
        
        if hasattr(self, 'setup_progress') and self.setup_progress is not None:
            self.setup_progress.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        
        if hasattr(self, 'shift_grid') and self.shift_grid is not None:
            self.shift_grid.update_colors(t)
            if self._last_seq_ids:
                self.shift_grid.update_table(
                    self._last_shifts, self._last_seq_ids,
                    self._last_pt, self._last_ct
                )
        
        for btn in self.key_buttons:
            btn.update_theme(t)
        for slot in self.sequence_slots:
            slot.update_colors(t)
        for sp in self.key_shift_spinners:
            sp.setStyleSheet(spin_style)
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.setup_progress = QProgressBar()
        self.setup_progress.setRange(0, 100)
        self.setup_progress.setValue(0)
        self.setup_progress.setMinimumHeight(28)
        self.setup_progress.setTextVisible(True)
        self.setup_progress.setFormat("%p%")
        l.addWidget(self.setup_progress)
        
        # Row 1: label + spin + generate — give the label a minimum width
        # so it doesn't compress, and keep the spinbox at a legible min
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        num_lbl = QLabel("Number of Keys:")
        num_lbl.setMinimumWidth(140)
        self.num_keys_spin = QSpinBox()
        self.num_keys_spin.setRange(1, 10)
        self.num_keys_spin.setValue(0)
        self.num_keys_spin.setSpecialValueText("--")
        self.num_keys_spin.setMinimumWidth(90)
        self.num_keys_spin.setMaximumWidth(120)
        gen_btn = QPushButton("Generate Keys")
        gen_btn.setObjectName("actionButton")
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.clicked.connect(self._generate_keys)
        row1.addWidget(num_lbl)
        row1.addWidget(self.num_keys_spin)
        row1.addWidget(gen_btn)
        row1.addStretch()
        l.addLayout(row1)
        
        self.keys_grp = QGroupBox("Cipher Keys")
        self.keys_layout = QVBoxLayout()
        self.keys_layout.setSpacing(10)
        self.keys_grp.setLayout(self.keys_layout)
        l.addWidget(self.keys_grp)
        
        self.seq_grp = QGroupBox("Encryption Sequence")
        svl = QVBoxLayout()
        svl.setSpacing(12)
        
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        seq_lbl = QLabel("Sequence Length:")
        seq_lbl.setMinimumWidth(140)
        self.seq_length_spin = QSpinBox()
        self.seq_length_spin.setRange(1, 30)
        self.seq_length_spin.setValue(0)
        self.seq_length_spin.setSpecialValueText("--")
        self.seq_length_spin.setMinimumWidth(90)
        self.seq_length_spin.setMaximumWidth(120)
        self.seq_length_spin.valueChanged.connect(self._on_seq_length_changed)
        clear_btn = QPushButton("Clear Slots")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all_slots)
        row2.addWidget(seq_lbl)
        row2.addWidget(self.seq_length_spin)
        row2.addWidget(clear_btn)
        row2.addStretch()
        svl.addLayout(row2)
        
        hint = QLabel("Drag C1, C2... into the slots to build the encryption order. Double-click a slot to clear it.")
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color:{self.theme.current['text_tertiary']};font-size:11px;background:transparent;"
        )
        svl.addWidget(hint)
        
        # Wrap the slots in a scrollable row so long sequences don't clip
        self.slots_scroll = QScrollArea()
        self.slots_scroll.setWidgetResizable(True)
        self.slots_scroll.setFixedHeight(70)
        self.slots_scroll.setStyleSheet("border:none;background:transparent;")
        self.slots_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.slots_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.slots_container = QWidget()
        self.slots_layout = QHBoxLayout(self.slots_container)
        self.slots_layout.setSpacing(6)
        self.slots_layout.setContentsMargins(4, 4, 4, 4)
        self.slots_layout.addStretch()
        self.slots_scroll.setWidget(self.slots_container)
        svl.addWidget(self.slots_scroll)
        
        self.seq_grp.setLayout(svl)
        l.addWidget(self.seq_grp)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _tab_input(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
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
        clear_input_btn = QPushButton("Clear")
        clear_input_btn.setObjectName("dangerButton")
        clear_input_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_input_btn.clicked.connect(self.text_input.clear)
        btn_row.addWidget(clear_input_btn)
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
    
    def _tab_shift_table(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        self.shift_grid = SequenceShiftTableGrid(self.theme.current)
        l.addWidget(self.shift_grid, 1)
        return w
    
    def _generate_keys(self):
        while self.keys_layout.count():
            item = self.keys_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.key_buttons.clear()
        self.key_shift_spinners.clear()
        
        num_keys = self.num_keys_spin.value()
        if num_keys == 0:
            self.setup_progress.setValue(0)
            return
        
        t = self.theme.current
        scale = layout_manager.font_scale()
        # Floor spinbox width so "Shift: 0" never truncates
        spin_w = max(110, int(105 * scale))
        
        for i in range(num_keys):
            kid = i + 1
            row = QHBoxLayout()
            row.setSpacing(10)
            lbl = QLabel(f"Key {kid}:")
            lbl.setMinimumWidth(70)
            sp = QSpinBox()
            sp.setRange(-25, 25)
            sp.setValue(0)
            sp.setSpecialValueText("--")
            sp.setPrefix("Shift: ")
            sp.setFixedWidth(spin_w)
            sp.setStyleSheet(
                f"QSpinBox{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;"
                f"padding:6px 10px;font-size:{max(12, int(13 * scale))}px;}}"
            )
            self.key_shift_spinners.append(sp)
            btn = DraggableKeyButton(kid, 0, t)
            self.key_buttons.append(btn)
            sp.valueChanged.connect(lambda val, b=btn, k=kid: self._update_key_shift(b, k, val))
            row.addWidget(lbl)
            row.addWidget(sp)
            row.addWidget(btn)
            row.addStretch()
            rw = QWidget()
            rw.setLayout(row)
            self.keys_layout.addWidget(rw)
        
        self._update_sequence_slots()
        self.setup_progress.setValue(30)
    
    def _update_key_shift(self, btn, key_id, new_shift):
        btn.shift_value = new_shift
        for slot in self.sequence_slots:
            if slot.key_id == key_id:
                slot.shift_value = new_shift
                slot.update()
    
    def _on_seq_length_changed(self, val):
        if val > 0:
            self._update_sequence_slots()
            self.setup_progress.setValue(50)
    
    def _update_sequence_slots(self):
        while self.slots_layout.count():
            item = self.slots_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.sequence_slots.clear()
        
        seq_len = self.seq_length_spin.value()
        if seq_len == 0:
            return
        
        t = self.theme.current
        self.slots_layout.addStretch()
        for i in range(seq_len):
            slot = SequenceSlot(i, t)
            self.sequence_slots.append(slot)
            self.slots_layout.addWidget(slot)
        self.slots_layout.addStretch()
    
    def _clear_all_slots(self):
        for slot in self.sequence_slots:
            slot.clear_slot()
        self.setup_progress.setValue(50)
    
    def _get_sequence_data(self):
        seq = []
        for slot in self.sequence_slots:
            if slot.is_filled():
                kid, _ = slot.get_data()
                seq.append(kid - 1)
            else:
                return None
        return seq
    
    def _build_shifts_dict(self):
        return {btn.key_id: btn.shift_value for btn in self.key_buttons}
    
    def _check_all_slots_filled(self):
        if not self.sequence_slots:
            return False
        return all(slot.is_filled() for slot in self.sequence_slots)
    
    def _paste_to(self, w):
        c = QApplication.clipboard().text()
        if c:
            if isinstance(w, QTextEdit):
                w.setPlainText(c)
            else:
                w.setText(c)
    
    def _copy_results(self):
        t = self.results_output.toPlainText()
        if t:
            QApplication.clipboard().setText(t)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _encrypt(self):
        seq = self._get_sequence_data()
        if seq is None:
            QMessageBox.warning(self, "Incomplete Setup", "Fill all sequence slots in Setup first.")
            self.tabs.setCurrentIndex(0)
            return
        text = self.text_input.toPlainText()
        if not text.strip():
            return
        shifts = self._build_shifts_dict()
        sv = [shifts.get(i + 1, 0) for i in range(len(self.key_buttons))]
        cipher = PolyCipher(sv, seq)
        self.results_output.setPlainText(cipher.encrypt(text))
        self._update_shift_table()
        self.tabs.setCurrentIndex(2)
    
    def _decrypt(self):
        seq = self._get_sequence_data()
        if seq is None:
            QMessageBox.warning(self, "Incomplete Setup", "Fill all sequence slots in Setup first.")
            self.tabs.setCurrentIndex(0)
            return
        text = self.text_input.toPlainText()
        if not text.strip():
            return
        shifts = self._build_shifts_dict()
        sv = [shifts.get(i + 1, 0) for i in range(len(self.key_buttons))]
        cipher = PolyCipher(sv, seq)
        self.results_output.setPlainText(cipher.decrypt(text))
        self._update_shift_table()
        self.tabs.setCurrentIndex(2)
    
    def _update_shift_table(self):
        if hasattr(self, 'shift_grid'):
            self._last_shifts = self._build_shifts_dict()
            self._last_seq_ids = []
            for slot in self.sequence_slots:
                if slot.is_filled():
                    kid, _ = slot.get_data()
                    self._last_seq_ids.append(kid)
            self._last_pt = self.text_input.toPlainText().strip()
            self._last_ct = self.results_output.toPlainText().strip()
            self.shift_grid.update_table(
                self._last_shifts, self._last_seq_ids,
                self._last_pt, self._last_ct
            )
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()