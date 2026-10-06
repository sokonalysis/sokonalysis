# gui/caesar_basic.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QLineEdit,
    QGridLayout, QScrollArea, QSizePolicy, QSpinBox,
    QApplication, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QSize, QMimeData, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPixmap, QDrag, QPainter
import string
import os, sys
from gui.layout_manager import layout_manager


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
        self._build()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        self.setMinimumSize(int(140 * scale), int(56 * scale))
        self.setMaximumSize(int(220 * scale), int(84 * scale))
    
    def _build(self):
        t = self.colors
        scale = layout_manager.font_scale()
        if self.name_label is None:
            l = QVBoxLayout(self)
            l.setContentsMargins(
                int(14 * scale), int(12 * scale),
                int(14 * scale), int(12 * scale)
            )
            l.setSpacing(int(4 * scale))
            self.name_label = QLabel(self.mode_name)
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setWordWrap(True)
            l.addWidget(self.name_label)
        self.name_label.setStyleSheet(
            f"color: {t['text']}; font-size: {int(13 * scale)}px; "
            f"font-weight: 600; background: transparent;"
        )
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:2px solid {t['border']};border-radius:8px;}} "
            f"QFrame:hover{{border-color:{t['accent']}88;background-color:{t['surface0']};}}"
        )
    
    def update_theme(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        self._build()
        self.update()
        self.repaint()
    
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(e)
    
    def mouseReleaseEvent(self, e):
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(e)
    
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"{self.mode_id}:{self.mode_name}")
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(e.pos())
            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(Qt.CursorShape.OpenHandCursor)


class ModeDropSlot(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.mode_id = None
        self.mode_name = None
        self._placeholder = "Drag mapping here"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        # Ensure slot is wide enough for the placeholder text at the current scale
        text_w = int(len(self._placeholder) * 8 * scale) + int(40 * scale)
        min_w = max(200, text_w)
        max_w = min_w + int(80 * scale)
        self.setMinimumSize(min_w, int(80 * scale))
        self.setMaximumSize(max_w, int(110 * scale))
    
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
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    
    def dropEvent(self, e):
        data = e.mimeData().text()
        try:
            mid, mn = data.split(':', 1)
            self.mode_id = int(mid)
            self.mode_name = mn
            self._style_filled()
            self.update()
            self.repaint()
            e.acceptProposedAction()
            p = self.parent()
            while p and not isinstance(p, CaesarBasicPage):
                p = p.parent()
            if p:
                p._on_mode_dropped()
        except:
            pass
    
    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        scale = layout_manager.font_scale()
        
        if self.is_filled():
            font_size = max(10, int(13 * scale))
            p.setPen(QColor(t['accent']))
            p.setFont(QFont("JetBrains Mono", font_size, QFont.Weight.Bold))
            text = self.mode_name
        else:
            font_size = max(9, int(10 * scale))
            p.setPen(QColor(t['text_tertiary']))
            p.setFont(QFont("JetBrains Mono", font_size))
            text = self._placeholder
        
        # Inset rect so text never clips against the border
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        
        # Safety: elide if it still doesn't fit
        fm = p.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        p.end()
    
    def mouseDoubleClickEvent(self, e):
        self.clear_slot()
        p = self.parent()
        while p and not isinstance(p, CaesarBasicPage):
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


class ShiftTableGrid(QScrollArea):
    def __init__(self, theme_colors):
        super().__init__()
        self.colors = theme_colors
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("border: none; background: transparent;")
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(1)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.setWidget(self.container)
    
    def update_colors(self, tc):
        self.colors = tc
    
    def update_table(self, shift):
        t = self.colors
        scale = layout_manager.font_scale()
        
        cell_w = max(22, int(32 * scale))
        cell_h = max(22, int(30 * scale))
        label_w = max(28, int(38 * scale))
        label_h = max(24, int(32 * scale))
        header_font = max(9, int(12 * scale))
        small_font = max(8, int(10 * scale))
        base_font = max(10, int(14 * scale))
        
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        alphabet = string.ascii_uppercase
        
        pos_lbl = QLabel("Pos")
        pos_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pos_lbl.setStyleSheet(
            f"background:{t['surface0']};color:{t['text']};font-weight:bold;padding:4px;"
            f"font-family:JetBrains Mono;font-size:{header_font}px;border-radius:4px;"
        )
        pos_lbl.setFixedSize(label_w, cell_h)
        self.grid.addWidget(pos_lbl, 0, 0)
        
        for i in range(26):
            lbl = QLabel(str(i + 1))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background:{t['surface0']};color:{t['text_secondary']};padding:2px;"
                f"font-family:JetBrains Mono;font-size:{small_font}px;border-radius:3px;"
            )
            lbl.setFixedSize(cell_w, cell_h)
            self.grid.addWidget(lbl, 0, i + 1)
        
        plain_lbl = QLabel("Plain")
        plain_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plain_lbl.setStyleSheet(
            f"background:{t['surface0']};color:{t['text']};font-weight:bold;padding:4px;"
            f"font-family:JetBrains Mono;font-size:{header_font}px;border-radius:4px;"
        )
        plain_lbl.setFixedSize(label_w, label_h)
        self.grid.addWidget(plain_lbl, 1, 0)
        
        for i, letter in enumerate(alphabet):
            lbl = QLabel(letter)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"background:transparent;color:{t['text']};font-weight:bold;padding:3px;"
                f"font-family:JetBrains Mono;font-size:{base_font}px;border-radius:3px;"
            )
            lbl.setFixedSize(cell_w, label_h)
            self.grid.addWidget(lbl, 1, i + 1)
        
        shifted = alphabet[shift:] + alphabet[:shift]
        cipher_lbl = QLabel(f"S{shift}")
        cipher_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cipher_lbl.setStyleSheet(
            f"background:{t['surface0']};color:{t['success']};font-weight:bold;padding:4px;"
            f"font-family:JetBrains Mono;font-size:{header_font}px;border-radius:4px;"
        )
        cipher_lbl.setFixedSize(label_w, label_h)
        self.grid.addWidget(cipher_lbl, 2, 0)
        
        for i, letter in enumerate(shifted):
            lbl = QLabel(letter)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if letter == alphabet[i]:
                lbl.setStyleSheet(
                    f"background:{t['success']}22;color:{t['success']};font-weight:bold;"
                    f"padding:3px;font-family:JetBrains Mono;font-size:{base_font}px;"
                    f"border-radius:3px;border:1px solid {t['success']}44;"
                )
            else:
                lbl.setStyleSheet(
                    f"background:transparent;color:{t['success']};padding:3px;"
                    f"font-family:JetBrains Mono;font-size:{base_font}px;border-radius:3px;"
                )
            lbl.setFixedSize(cell_w, label_h)
            self.grid.addWidget(lbl, 2, i + 1)
        
        self.container.setMinimumHeight(int(120 * scale))


class CaesarBasicPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
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
        
        title = QLabel("Caesar Cipher - Basic Shift")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Setup")
        self.tabs.addTab(self._tab_results(), "Result")
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
        for attr in ['map_grp', 'in_grp']:
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
        if hasattr(self, 'shift_spin') and self.shift_spin is not None:
            self.shift_spin.setStyleSheet(
                f"QSpinBox{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:8px 12px;"
                f"font-size:{int(14 * scale)}px;}}"
            )
        
        if hasattr(self, 'mode_slot') and self.mode_slot is not None:
            self.mode_slot.update_colors(t)
        if hasattr(self, 'shift_grid') and self.shift_grid is not None:
            self.shift_grid.update_colors(t)
            if hasattr(self, 'shift_spin'):
                self.shift_grid.update_table(self.shift_spin.value())
        
        for card in self.mode_cards:
            try:
                card.update_theme(t)
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
        
        self.map_grp = QGroupBox("1. Mapping Style (Drag & Drop)")
        ml = QVBoxLayout()
        ml.setSpacing(10)
        cr = QHBoxLayout()
        cr.setSpacing(12)
        t = self.theme.current
        for mid, mn in [(0, "A=0, B=1..."), (1, "A=1, B=2...")]:
            card = DraggableModeCard(mid, mn, t)
            self.mode_cards.append(card)
            cr.addWidget(card)
        cr.addStretch()
        ml.addLayout(cr)
        dr = QHBoxLayout()
        self.mode_slot = ModeDropSlot(t)
        dr.addWidget(self.mode_slot)
        dr.addStretch()
        ml.addLayout(dr)
        self.map_grp.setLayout(ml)
        l.addWidget(self.map_grp)
        
        self.in_grp = QGroupBox("2. Input")
        self.in_grp.setVisible(False)
        il = QVBoxLayout()
        il.setSpacing(10)
        
        shift_row = QHBoxLayout()
        shift_row.addWidget(QLabel("Shift:"))
        self.shift_spin = QSpinBox()
        self.shift_spin.setRange(1, 25)
        self.shift_spin.setValue(3)
        self.shift_spin.valueChanged.connect(self._on_shift_changed)
        shift_row.addWidget(self.shift_spin)
        shift_row.addStretch()
        il.addLayout(shift_row)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text to encrypt or decrypt...")
        self.text_input.setMaximumHeight(100)
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
        encrypt_btn = QPushButton("Encrypt")
        encrypt_btn.setObjectName("actionButton")
        encrypt_btn.setMinimumHeight(42)
        encrypt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        encrypt_btn.clicked.connect(self._encrypt)
        encrypt_btn.setVisible(False)
        br.addWidget(encrypt_btn)
        
        decrypt_btn = QPushButton("Decrypt")
        decrypt_btn.setObjectName("actionButton")
        decrypt_btn.setMinimumHeight(42)
        decrypt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        decrypt_btn.clicked.connect(self._decrypt)
        decrypt_btn.setVisible(False)
        br.addWidget(decrypt_btn)
        
        self.enc_btn = encrypt_btn
        self.dec_btn = decrypt_btn
        l.addLayout(br)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _on_mode_dropped(self):
        self.in_grp.setVisible(True)
        self.enc_btn.setVisible(True)
        self.dec_btn.setVisible(True)
    
    def _on_mode_cleared(self):
        self.in_grp.setVisible(False)
        self.enc_btn.setVisible(False)
        self.dec_btn.setVisible(False)
    
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
        self.shift_grid = ShiftTableGrid(self.theme.current)
        # Build table after event loop starts so page opens instantly
        QTimer.singleShot(0, lambda: self.shift_grid.update_table(3))
        l.addWidget(self.shift_grid, 1)
        return w
    
    def _on_shift_changed(self, value):
        if hasattr(self, 'shift_grid'):
            self.shift_grid.update_table(value)
    
    def _paste_to(self, w):
        c = QApplication.clipboard().text()
        if c:
            if isinstance(w, QTextEdit):
                w.setPlainText(c)
            else:
                w.setText(c)
    
    def _clear_all(self):
        self.text_input.clear()
        self.results_output.clear()
    
    def _copy_results(self):
        t = self.results_output.toPlainText()
        if t:
            QApplication.clipboard().setText(t)
            QMessageBox.information(self, "Copied", "Results copied!")
    
    def _caesar_encrypt(self, text, shift):
        r = []
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                r.append(chr((ord(c) - base + shift) % 26 + base))
            else:
                r.append(c)
        return ''.join(r)
    
    def _caesar_decrypt(self, text, shift):
        r = []
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                r.append(chr((ord(c) - base - shift + 26) % 26 + base))
            else:
                r.append(c)
        return ''.join(r)
    
    def _encrypt(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return
        shift = self.shift_spin.value()
        result = self._caesar_encrypt(text, shift)
        self.results_output.setPlainText(result)
        self.tabs.setCurrentIndex(1)
    
    def _decrypt(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            return
        shift = self.shift_spin.value()
        result = self._caesar_decrypt(text, shift)
        self.results_output.setPlainText(result)
        self.tabs.setCurrentIndex(1)
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()