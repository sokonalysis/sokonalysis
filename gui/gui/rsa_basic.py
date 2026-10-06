# gui/rsa_basic.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QGroupBox, QFormLayout,
    QSpinBox, QTextBrowser, QStackedWidget, QScrollArea, QFrame,
    QApplication, QMessageBox, QProgressBar, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QMimeData, QSize
from PySide6.QtGui import QDrag, QPixmap, QPainter, QFont, QColor, QIcon
import math, os, sys
from gui.layout_manager import layout_manager


class RSACipher:
    @staticmethod
    def is_prime(num):
        if num <= 1:
            return False
        for i in range(2, int(math.sqrt(num)) + 1):
            if num % i == 0:
                return False
        return True
    
    @staticmethod
    def gcd(a, b):
        while b != 0:
            a, b = b, a % b
        return a
    
    @staticmethod
    def mod_inverse(e, m):
        m0, x0, x1 = m, 0, 1
        if m == 1:
            return 0
        while e > 1:
            q = e // m
            e, m = m, e % m
            x0, x1 = x1 - q * x0, x0
        if x1 < 0:
            x1 += m0
        return x1
    
    @staticmethod
    def mod_exp(base, exp, mod):
        result = 1
        base %= mod
        while exp > 0:
            if exp % 2 == 1:
                result = (result * base) % mod
            exp >>= 1
            base = (base * base) % mod
        return result
    
    @staticmethod
    def find_valid_e(phi):
        return [e for e in range(2, phi) if RSACipher.gcd(e, phi) == 1]
    
    @staticmethod
    def factorize(n):
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                p, q = i, n // i
                if RSACipher.is_prime(p) and RSACipher.is_prime(q):
                    return p, q
        return None, None
    
    @staticmethod
    def letter_to_number(letter, mapping):
        return (ord(letter.upper()) - ord('A') + 1) if mapping == 1 else (ord(letter.upper()) - ord('A'))
    
    @staticmethod
    def number_to_letter(num, mapping):
        return chr(num + ord('A') - 1) if mapping == 1 else chr(num + ord('A'))
    
    @staticmethod
    def encrypt(message, e, n, mapping):
        steps, nums = [], []
        for ch in message:
            if ch.isalpha():
                num = RSACipher.letter_to_number(ch, mapping)
                enc = RSACipher.mod_exp(num, e, n)
                steps.append({'letter': ch.upper(), 'num': num, 'enc': enc, 'n': n, 'e': e})
                nums.append(str(enc))
            elif ch == ' ':
                nums.append(' ')
        return ' '.join(nums), steps
    
    @staticmethod
    def decrypt(ciphertext, d, n, mapping):
        steps, result = [], []
        for part in ciphertext.split():
            if not part.strip():
                result.append(' ')
                continue
            try:
                cipher = int(part)
                m_full = RSACipher.mod_exp(cipher, d, n)
                m = m_full % 26
                letter = RSACipher.number_to_letter(m, mapping)
                steps.append({'cipher': cipher, 'm_full': m_full, 'm': m, 'letter': letter, 'n': n, 'd': d})
                result.append(letter)
            except ValueError:
                pass
        return ''.join(result), steps


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
        self._placeholder = "Drag option here"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
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
        except:
            pass
        p = self.parent()
        while p and not isinstance(p, RSABasicPage):
            p = p.parent()
        if p:
            p._on_slot_dropped(self)
    
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
        
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        fm = p.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        p.end()
    
    def mouseDoubleClickEvent(self, e):
        self.mode_id = None
        self.mode_name = None
        self._style_empty()
        self.update()
        self.repaint()
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.is_filled():
            self._style_filled()
        else:
            self._style_empty()
        self.update()
        self.repaint()


class DraggableEButton(QPushButton):
    def __init__(self, value, colors, parent=None):
        super().__init__(str(value), parent)
        self.value = value
        self.colors = colors
        self._apply_scaled_size()
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._style()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        self.setFixedSize(max(48, int(60 * scale)), max(32, int(38 * scale)))
    
    def _style(self):
        t = self.colors
        scale = layout_manager.font_scale()
        self.setStyleSheet(
            f"QPushButton{{background-color:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;"
            f"font-family:JetBrains Mono;font-size:{max(11, int(13 * scale))}px;"
            f"font-weight:bold;padding:4px 8px;}} "
            f"QPushButton:hover{{background-color:{t['surface0']};border-color:{t['surface2']};}}"
        )
    
    def update_theme(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        self._style()
        self.update()
        self.repaint()
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(str(self.value))
            drag.setMimeData(mime)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)


class EDropZone(QFrame):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.colors = theme_colors
        self.e_val = None
        self._placeholder = "Drop e value here"
        self._apply_scaled_size()
        self.setAcceptDrops(True)
        self._style_empty()
    
    def _apply_scaled_size(self):
        scale = layout_manager.font_scale()
        self.setMinimumHeight(max(48, int(55 * scale)))
        self.setMaximumHeight(max(60, int(70 * scale)))
    
    def _style_empty(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['crust']};border:3px dashed {t['border']};border-radius:10px;}}"
        )
    
    def _style_filled(self):
        t = self.colors
        self.setStyleSheet(
            f"QFrame{{background-color:{t['success']}15;border:3px solid {t['success']}88;border-radius:10px;}}"
        )
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()
    
    def dropEvent(self, e):
        try:
            self.e_val = int(e.mimeData().text())
            self._style_filled()
            self.update()
            self.repaint()
            e.acceptProposedAction()
        except:
            return
        p = self.parent()
        while p and not isinstance(p, RSABasicPage):
            p = p.parent()
        if p:
            p._on_e_dropped()
    
    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.colors
        scale = layout_manager.font_scale()
        inset = int(12 * scale)
        text_rect = self.rect().adjusted(inset, inset, -inset, -inset)
        fm = p.fontMetrics()
        
        if self.e_val:
            font_size = max(13, int(16 * scale))
            p.setPen(QColor(t['success']))
            p.setFont(QFont("JetBrains Mono", font_size, QFont.Weight.Bold))
            text = f"e = {self.e_val}"
        else:
            font_size = max(10, int(11 * scale))
            p.setPen(QColor(t['text_tertiary']))
            p.setFont(QFont("JetBrains Mono", font_size))
            text = self._placeholder
        
        fm = p.fontMetrics()
        elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        p.end()
    
    def mouseDoubleClickEvent(self, e):
        self.e_val = None
        self._style_empty()
        self.update()
        self.repaint()
    
    def update_colors(self, tc):
        self.colors = tc
        self._apply_scaled_size()
        if self.e_val:
            self._style_filled()
        else:
            self._style_empty()
        self.update()
        self.repaint()


class RSABasicPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.current_n = 0
        self.current_e = 0
        self.current_d = 0
        self.current_phi = 0
        self.mode_cards = []
        self.map_cards = []
        self.e_buttons = []
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
        bp = os.path.join(icons_dir, "back.png")
        if os.path.exists(bp):
            back_btn.setIcon(QIcon(bp))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        title = QLabel("RSA - Basic")
        title.setObjectName("pageTitle")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_setup(), "Key Setup")
        self.tabs.addTab(self._tab_select_e(), "Select e")
        self.tabs.addTab(self._tab_input(), "Input")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_results(), "Result")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane{{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab{{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};
            padding:10px 28px;margin-right:2px;border-top-left-radius:7px;border-top-right-radius:7px;
            font-size:{int(13 * scale)}px;font-weight:600;}}
            QTabBar::tab:selected{{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
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
        for attr in ['mode_grp', 'key_grp', 'e_grp', 'map_grp', 'in_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'text_input') and self.text_input is not None:
            self.text_input.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
            )
        if hasattr(self, 'status_output') and self.status_output is not None:
            self.status_output.setStyleSheet(
                f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
            )
        if hasattr(self, 'results_output') and self.results_output is not None:
            self.results_output.setStyleSheet(
                f"QTextBrowser{{background:{t['crust']};color:{t['text']};"
                f"border:1px solid {t['border']};border-radius:6px;padding:12px;"
                f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
            )
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            self.status_progress.setStyleSheet(
                f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;"
                f"height:{int(14 * scale)}px;text-align:center;font-size:{int(10 * scale)}px;font-weight:600;}} "
                f"QProgressBar::chunk{{background:{t['success']};border-radius:4px;}}"
            )
        
        input_stl = (
            f"QLineEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;"
            f"padding:8px 10px;font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['p_input', 'q_input', 'n_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_stl)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'mode_slot') and self.mode_slot is not None:
            self.mode_slot.update_colors(t)
        if hasattr(self, 'e_drop_zone') and self.e_drop_zone is not None:
            self.e_drop_zone.update_colors(t)
        if hasattr(self, 'map_slot') and self.map_slot is not None:
            self.map_slot.update_colors(t)
        
        for card in self.mode_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        for card in self.map_cards:
            try:
                card.update_theme(t)
            except RuntimeError:
                pass
        for btn in self.e_buttons:
            try:
                btn.update_theme(t)
            except RuntimeError:
                pass
    
    def _clear_all_data(self):
        self.current_n = 0
        self.current_e = 0
        self.current_d = 0
        self.current_phi = 0
        self.status_output.clear()
        self.results_output.clear()
        self.status_progress.setValue(0)
        while self.e_layout.count():
            item = self.e_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.e_layout.addStretch()
        self.e_buttons.clear()
        self.e_drop_zone.e_val = None
        self.e_drop_zone._style_empty()
        self.e_drop_zone.update()
        if hasattr(self, 'map_slot'):
            self.map_slot.mode_id = None
            self.map_slot._style_empty()
            self.map_slot.update()
        if hasattr(self, 'in_grp'):
            self.in_grp.setVisible(False)
        if hasattr(self, 'text_input'):
            self.text_input.clear()
    
    def _tab_setup(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        t = self.theme.current
        
        self.mode_grp = QGroupBox("1. What do you have?")
        ml = QVBoxLayout()
        ml.setSpacing(10)
        cr = QHBoxLayout()
        cr.setSpacing(12)
        for mid, mn in [(0, "I have p & q"), (1, "I have n")]:
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
        self.mode_grp.setLayout(ml)
        l.addWidget(self.mode_grp)
        
        self.key_grp = QGroupBox("2. Key Values")
        self.key_grp.setVisible(False)
        kl = QVBoxLayout()
        kl.setSpacing(12)
        self.key_stack = QStackedWidget()
        
        # p & q page
        pq_w = QWidget()
        pq_l = QVBoxLayout(pq_w)
        pq_l.setSpacing(8)
        p_row = QHBoxLayout()
        p_row.setSpacing(8)
        p_lbl = QLabel("p:")
        p_lbl.setMinimumWidth(30)
        p_row.addWidget(p_lbl)
        self.p_input = QLineEdit()
        self.p_input.setPlaceholderText("Enter prime p...")
        p_row.addWidget(self.p_input, 1)
        p_paste = QPushButton("Paste")
        p_paste.setObjectName("actionButton")
        p_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        p_paste.clicked.connect(lambda: self._paste_line(self.p_input))
        p_clear = QPushButton("Clear")
        p_clear.setObjectName("dangerButton")
        p_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        p_clear.clicked.connect(self.p_input.clear)
        p_row.addWidget(p_paste)
        p_row.addWidget(p_clear)
        pq_l.addLayout(p_row)
        
        q_row = QHBoxLayout()
        q_row.setSpacing(8)
        q_lbl = QLabel("q:")
        q_lbl.setMinimumWidth(30)
        q_row.addWidget(q_lbl)
        self.q_input = QLineEdit()
        self.q_input.setPlaceholderText("Enter prime q...")
        q_row.addWidget(self.q_input, 1)
        q_paste = QPushButton("Paste")
        q_paste.setObjectName("actionButton")
        q_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        q_paste.clicked.connect(lambda: self._paste_line(self.q_input))
        q_clear = QPushButton("Clear")
        q_clear.setObjectName("dangerButton")
        q_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        q_clear.clicked.connect(self.q_input.clear)
        q_row.addWidget(q_paste)
        q_row.addWidget(q_clear)
        pq_l.addLayout(q_row)
        self.key_stack.addWidget(pq_w)
        
        # n page
        n_w = QWidget()
        n_l = QVBoxLayout(n_w)
        n_l.setSpacing(8)
        n_row = QHBoxLayout()
        n_row.setSpacing(8)
        n_lbl = QLabel("n:")
        n_lbl.setMinimumWidth(30)
        n_row.addWidget(n_lbl)
        self.n_input = QLineEdit()
        self.n_input.setPlaceholderText("Enter modulus n...")
        n_row.addWidget(self.n_input, 1)
        n_paste = QPushButton("Paste")
        n_paste.setObjectName("actionButton")
        n_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        n_paste.clicked.connect(lambda: self._paste_line(self.n_input))
        n_clear = QPushButton("Clear")
        n_clear.setObjectName("dangerButton")
        n_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        n_clear.clicked.connect(self.n_input.clear)
        n_row.addWidget(n_paste)
        n_row.addWidget(n_clear)
        n_l.addLayout(n_row)
        self.key_stack.addWidget(n_w)
        
        kl.addWidget(self.key_stack)
        self.key_grp.setLayout(kl)
        l.addWidget(self.key_grp)
        
        compute_btn = QPushButton("Compute Keys")
        compute_btn.setObjectName("actionButton")
        compute_btn.setMinimumHeight(48)
        compute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        compute_btn.clicked.connect(self._compute_keys)
        l.addWidget(compute_btn)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _tab_select_e(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        t = self.theme.current
        
        self.e_grp = QGroupBox("Choose Public Exponent (e)")
        el = QVBoxLayout()
        el.setSpacing(10)
        self.e_scroll = QScrollArea()
        self.e_scroll.setWidgetResizable(True)
        self.e_scroll.setMaximumHeight(75)
        self.e_scroll.setStyleSheet("border:none;background:transparent;")
        self.e_container = QWidget()
        self.e_layout = QHBoxLayout(self.e_container)
        self.e_layout.setSpacing(8)
        self.e_layout.setContentsMargins(4, 6, 4, 6)
        self.e_layout.addStretch()
        self.e_scroll.setWidget(self.e_container)
        el.addWidget(self.e_scroll)
        self.e_drop_zone = EDropZone(t)
        el.addWidget(self.e_drop_zone)
        self.e_grp.setLayout(el)
        l.addWidget(self.e_grp)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _tab_input(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        t = self.theme.current
        
        self.map_grp = QGroupBox("1. Letter Mapping")
        mpl = QVBoxLayout()
        mpl.setSpacing(10)
        mcr = QHBoxLayout()
        mcr.setSpacing(12)
        for mid, mn in [(0, "A=0, B=1..."), (1, "A=1, B=2...")]:
            card = DraggableModeCard(mid, mn, t)
            self.map_cards.append(card)
            mcr.addWidget(card)
        mcr.addStretch()
        mpl.addLayout(mcr)
        mdr = QHBoxLayout()
        self.map_slot = ModeDropSlot(t)
        mdr.addWidget(self.map_slot)
        mdr.addStretch()
        mpl.addLayout(mdr)
        self.map_grp.setLayout(mpl)
        l.addWidget(self.map_grp)
        
        self.in_grp = QGroupBox("2. Input Text")
        self.in_grp.setVisible(False)
        il = QVBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(100)
        self.text_input.setPlaceholderText("Letters to encrypt | Space-separated numbers to decrypt")
        il.addWidget(self.text_input)
        btn_row = QHBoxLayout()
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(lambda: self._paste_to(self.text_input))
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("dangerButton")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(paste_btn)
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
        dec_btn = QPushButton("Decrypt")
        dec_btn.setObjectName("actionButton")
        dec_btn.setMinimumHeight(48)
        dec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dec_btn.clicked.connect(self._decrypt)
        br.addWidget(enc_btn)
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
        self.status_output.setPlaceholderText("Activity log, steps, and explanation...")
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
        self.results_output = QTextBrowser()
        self.results_output.setOpenExternalLinks(False)
        l.addWidget(self.results_output, 1)
        return w
    
    def _on_slot_dropped(self, slot):
        if slot == self.mode_slot:
            self._clear_all_data()
            self.key_grp.setVisible(True)
            self.key_stack.setCurrentIndex(0 if self.mode_slot.mode_id == 0 else 1)
        elif slot == self.map_slot:
            self.in_grp.setVisible(True)
    
    def _on_e_dropped(self):
        if self.e_drop_zone.e_val and self.current_phi > 0:
            self.current_e = self.e_drop_zone.e_val
            if RSACipher.gcd(self.current_e, self.current_phi) != 1:
                return
            self.current_d = RSACipher.mod_inverse(self.current_e, self.current_phi)
            self.status_output.append(f"[*] e = {self.current_e}, d = {self.current_d}")
            self.status_output.append(f"[*] Public Key: (e={self.current_e}, n={self.current_n})")
            self.status_output.append(f"[*] Private Key: (d={self.current_d}, n={self.current_n})")
            self.status_progress.setValue(80)
            self.tabs.setCurrentIndex(2)
    
    def _paste_line(self, w):
        c = QApplication.clipboard().text()
        if c:
            w.setText(c.strip())
    
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
    
    def _compute_keys(self):
        self.status_output.clear()
        self.status_progress.setValue(0)
        if self.key_stack.currentIndex() == 0:
            try:
                p = int(self.p_input.text().strip())
                q = int(self.q_input.text().strip())
            except:
                return
            if p == 0 or q == 0:
                return
            if not RSACipher.is_prime(p):
                self.status_output.append(f"[!] p = {p} is not prime")
                return
            if not RSACipher.is_prime(q):
                self.status_output.append(f"[!] q = {q} is not prime")
                return
            n, phi = p * q, (p - 1) * (q - 1)
            self.status_output.append(f"[*] p = {p}, q = {q}")
        else:
            try:
                n = int(self.n_input.text().strip())
            except:
                return
            if n == 0:
                return
            p, q = RSACipher.factorize(n)
            if p is None:
                self.status_output.append(f"[!] Cannot factor n = {n}")
                return
            phi = (p - 1) * (q - 1)
            self.status_output.append(f"[*] n = {n}, p = {p}, q = {q}")
        
        self.current_n = n
        self.current_phi = phi
        self.status_output.append(f"[*] n = {n}, φ(n) = {phi}")
        self.status_progress.setValue(50)
        
        while self.e_layout.count():
            item = self.e_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.e_layout.addStretch()
        self.e_buttons.clear()
        valid = RSACipher.find_valid_e(phi)
        for v in valid[:20]:
            btn = DraggableEButton(v, self.theme.current)
            self.e_layout.addWidget(btn)
            self.e_buttons.append(btn)
        self.e_layout.addStretch()
        self.status_progress.setValue(60)
        self.tabs.setCurrentIndex(1)
    
    def _encrypt(self):
        text = self.text_input.toPlainText().strip()
        if not text or self.current_e == 0:
            return
        mapping = self.map_slot.mode_id if self.map_slot.is_filled() else 0
        nums, steps = RSACipher.encrypt(text, self.current_e, self.current_n, mapping)
        text_result = []
        for ch in text:
            if ch.isalpha():
                num = RSACipher.letter_to_number(ch, mapping)
                enc = RSACipher.mod_exp(num, self.current_e, self.current_n)
                text_result.append(RSACipher.number_to_letter(enc % 26, mapping))
            elif ch == ' ':
                text_result.append(' ')
        text_out = ''.join(text_result)
        t = self.theme.current
        self.results_output.setHtml(
            f"<p><b>Text Cipher:</b><br>"
            f"<span style='color:{t['success']};font-size:28px;font-weight:bold;'>{text_out}</span></p>"
            f"<hr>"
            f"<p><b>Numeric Cipher:</b><br>"
            f"<span style='color:{t['success']};font-size:18px;font-weight:bold;font-family:JetBrains Mono;'>{nums}</span></p>"
        )
        
        self.status_output.append(f"\n[*] Encryption complete (e={self.current_e}, n={self.current_n})")
        self.status_output.append(f"\n--- Encryption Steps ---")
        for s in steps:
            self.status_output.append(
                f"  {s['letter']}: m={s['num']} -> c = {s['num']}^{self.current_e} mod {self.current_n} = {s['enc']}"
            )
        self.status_output.append(f"\n--- Explanation ---")
        self.status_output.append(f"Public Key: (e={self.current_e}, n={self.current_n})")
        self.status_output.append(f"Formula: c = m^e mod n")
        self.status_progress.setValue(100)
        self.tabs.setCurrentIndex(3)
        QTimer.singleShot(200, lambda: self.tabs.setCurrentIndex(4))
    
    def _decrypt(self):
        text = self.text_input.toPlainText().strip()
        if not text or self.current_d == 0:
            return
        mapping = self.map_slot.mode_id if self.map_slot.is_filled() else 0
        plain, steps = RSACipher.decrypt(text, self.current_d, self.current_n, mapping)
        nums = [f"{s['cipher']}->{s['m']}" for s in steps]
        num_str = ' | '.join(nums)
        t = self.theme.current
        self.results_output.setHtml(
            f"<p><b>Plaintext:</b><br>"
            f"<span style='color:{t['success']};font-size:32px;font-weight:bold;'>{plain}</span></p>"
            f"<hr>"
            f"<p><b>Decryption Trace:</b><br>"
            f"<span style='color:{t['text_secondary']};font-size:13px;font-family:JetBrains Mono;'>{num_str}</span></p>"
        )
        
        self.status_output.append(f"\n[*] Decryption complete (d={self.current_d}, n={self.current_n})")
        self.status_output.append(f"\n--- Decryption Steps ---")
        for s in steps:
            self.status_output.append(
                f"  c={s['cipher']}: m = {s['cipher']}^{self.current_d} mod {self.current_n} = {s['m_full']}, m mod 26 = {s['m']} -> {s['letter']}"
            )
        self.status_output.append(f"\n--- Explanation ---")
        self.status_output.append(f"Private Key: (d={self.current_d}, n={self.current_n})")
        self.status_output.append(f"Formula: m = c^d mod n")
        self.status_progress.setValue(100)
        self.tabs.setCurrentIndex(3)
        QTimer.singleShot(200, lambda: self.tabs.setCurrentIndex(4))
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()