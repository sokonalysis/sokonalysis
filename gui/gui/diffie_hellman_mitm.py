# gui/diffie_hellman_mitm.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QFrame,
    QTabWidget, QTextBrowser, QProgressBar, QTextEdit,
    QLineEdit, QApplication, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QPoint, QThread, Signal, QSize
from PySide6.QtGui import (
    QPainter, QFont, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath, QIcon, QPixmap
)
import random
import math
import time
import os
import sys
from gui.layout_manager import layout_manager


class MITMWorker(QThread):
    """Worker for MITM brute force attack."""
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(dict)
    
    def __init__(self, g, p, A, B):
        super().__init__()
        self.g = g
        self.p = p
        self.A = A
        self.B = B
    
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
    
    def run(self):
        self.progress.emit(f"Brute Force: Finding A's Private Key")
        self.progress_value.emit(5)
        
        a_private = None
        for exp in range(self.p - 1, 0, -1):
            res = self.mod_exp(self.g, exp, self.p)
            if res == self.A:
                self.progress.emit(f"[#] g^{exp} mod {self.p} = {res}  <-- Match! Private key of A = {exp}")
                a_private = exp
                break
            else:
                self.progress.emit(f"[#] g^{exp} mod {self.p} = {res}")
            pct = 5 + int((1 - (exp / (self.p - 1))) * 40)
            self.progress_value.emit(pct)
            time.sleep(0.001)
        
        if not a_private:
            self.progress.emit("[x] Failed to find A's private key")
            self.finished.emit({'success': False, 'error': "Could not find A's private key"})
            return
        
        self.progress_value.emit(50)
        self.progress.emit(f"Brute Force: Finding B's Private Key")
        
        b_private = None
        for exp in range(self.p - 1, 0, -1):
            res = self.mod_exp(self.g, exp, self.p)
            if res == self.B:
                self.progress.emit(f"[#] g^{exp} mod {self.p} = {res}  <-- Match! Private key of B = {exp}")
                b_private = exp
                break
            else:
                self.progress.emit(f"[#] g^{exp} mod {self.p} = {res}")
            pct = 50 + int((1 - (exp / (self.p - 1))) * 40)
            self.progress_value.emit(pct)
            time.sleep(0.001)
        
        if not b_private:
            self.progress.emit("[x] Failed to find B's private key")
            self.finished.emit({'success': False, 'error': "Could not find B's private key"})
            return
        
        self.progress_value.emit(90)
        self.progress.emit(f"Shared Secret Computation")
        
        K1 = self.mod_exp(self.B, a_private, self.p)
        K2 = self.mod_exp(self.A, b_private, self.p)
        
        self.progress.emit(f"[#] B^a mod p = {self.B}^{a_private} mod {self.p} = {K1}")
        self.progress.emit(f"[#] A^b mod p = {self.A}^{b_private} mod {self.p} = {K2}")
        
        if K1 == K2:
            self.progress.emit(f"Success! Shared secret: {K1}")
            self.progress.emit(f">>> Attacker can now decrypt all communications.")
        else:
            self.progress.emit(f"Mismatch: Keys do not match.")
        
        self.progress_value.emit(100)
        
        self.finished.emit({
            'success': True,
            'a_private': a_private,
            'b_private': b_private,
            'K': K1,
            'K1': K1,
            'K2': K2,
            'match': K1 == K2
        })


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.uniform(2, 5)
        self.speed = random.uniform(0.5, 2)
        self.angle = random.uniform(0, 2 * math.pi)
        self.life = 1.0
        self.decay = random.uniform(0.01, 0.03)


class AttackerDevice(QFrame):
    """Animated attacker device."""
    
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.particles = []
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)
        self._pulse = 0
        self._data_flow = 0
        self.private_key = None
        self.shared_key = None
        # Scale min/max so card matches the client/server devices in DH Basic
        scale = layout_manager.font_scale()
        self.setMinimumSize(max(200, int(250 * scale)), max(260, int(320 * scale)))
        self.setMaximumSize(max(240, int(300 * scale)), max(320, int(380 * scale)))
    
    def _get_icon(self, name):
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        path = os.path.join(icons_dir, name)
        if os.path.exists(path):
            return QIcon(path)
        return QIcon()
    
    def _tick(self):
        self._pulse = (math.sin(self._data_flow * 2) + 1) / 2
        self._data_flow += 0.03
        for p in self.particles[:]:
            p.life -= p.decay
            if p.life <= 0:
                self.particles.remove(p)
            else:
                p.x += math.cos(p.angle) * p.speed
                p.y += math.sin(p.angle) * p.speed
        if self.shared_key and random.random() < 0.3:
            t = self.theme.current
            cx, cy = self.width() // 2, 200
            self.particles.append(
                Particle(
                    cx + random.uniform(-30, 30),
                    cy + random.uniform(-20, 20),
                    QColor(t['error'])
                )
            )
        self.update()
    
    def set_keys(self, private, shared):
        self.private_key = private
        self.shared_key = shared
        if shared:
            for _ in range(10):
                self.particles.append(
                    Particle(self.width() // 2, 200, QColor(self.theme.current['error']))
                )
    
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.theme.current
        w, h = self.width(), self.height()
        scale = layout_manager.font_scale()
        
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 25))
        p.drawRoundedRect(10, 10, w - 20, h - 20, 20, 20)
        bg = QLinearGradient(0, 0, w, 0)
        bg.setColorAt(0, QColor(t['crust']).lighter(105))
        bg.setColorAt(0.3, QColor(t['base']))
        bg.setColorAt(0.7, QColor(t['base']))
        bg.setColorAt(1, QColor(t['crust']).darker(105))
        p.setBrush(QBrush(bg))
        p.setPen(QPen(QColor(t['border']), 2))
        p.drawRoundedRect(6, 6, w - 12, h - 12, 18, 18)
        
        tg = QLinearGradient(0, 0, 0, 50)
        tg.setColorAt(0, QColor(t['error']))
        tg.setColorAt(1, QColor(t['error']).darker(150))
        p.setBrush(QBrush(tg))
        p.setPen(Qt.PenStyle.NoPen)
        pt = QPainterPath()
        pt.addRoundedRect(8, 8, w - 16, 48, 18, 18)
        pt.addRect(8, 38, w - 16, 18)
        p.drawPath(pt)
        
        trudy_icon = self._get_icon("trudy.png")
        if not trudy_icon.isNull():
            trudy_pixmap = trudy_icon.pixmap(22, 22)
            p.drawPixmap(18, 16, trudy_pixmap)
        
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Inter", max(12, int(14 * scale)), QFont.Weight.Bold))
        p.drawText(44, 10, w - 60, 42, Qt.AlignmentFlag.AlignCenter, "TRUDY")
        
        cx, cy = w // 2, 110
        fg = QRadialGradient(cx, cy, 40)
        fg.setColorAt(0, QColor("#1a1a2e"))
        fg.setColorAt(1, QColor("#0a0a1a"))
        p.setBrush(QBrush(fg))
        p.setPen(QPen(QColor(t['error']), 2))
        p.drawEllipse(QPoint(cx, cy), 35, 35)
        
        eye = QColor(t['error']) if self._pulse > 0.5 else QColor(t['error']).darker(200)
        p.setBrush(QBrush(eye))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(cx - 10, cy - 5), 6, 6)
        p.drawEllipse(QPoint(cx + 10, cy - 5), 6, 6)
        p.setPen(QPen(QColor(t['error']), 2))
        smirk = QPainterPath()
        smirk.moveTo(cx - 12, cy + 12)
        smirk.quadTo(cx, cy + 22, cx + 12, cy + 12)
        p.drawPath(smirk)
        
        gl = QRadialGradient(cx, cy, 60)
        gl.setColorAt(0, QColor(t['error']).lighter(150))
        gl.setColorAt(0.5, QColor(t['error']))
        gl.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(gl))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(cx, cy), 55, 55)
        
        info_y = 170
        key_font = max(9, int(10 * scale))
        shared_font = max(10, int(12 * scale))
        icon_size = max(14, int(16 * scale))
        row_h = max(20, int(22 * scale))
        pad = int(16 * scale)
        icon_x = int(16 * scale)
        text_x = int(38 * scale)
        
        p.setFont(QFont("JetBrains Mono", key_font))
        
        decrypt_icon = self._get_icon("decrypt.png")
        if not decrypt_icon.isNull():
            decrypt_pixmap = decrypt_icon.pixmap(icon_size, icon_size)
            p.drawPixmap(icon_x, info_y + 2, decrypt_pixmap)
        p.setPen(QColor(t['text']) if self.private_key else QColor(t['text_tertiary']))
        p.drawText(
            text_x, info_y,
            w - int(54 * scale), row_h,
            Qt.AlignmentFlag.AlignLeft,
            f"Cracked Key:  {self.private_key if self.private_key else '--'}"
        )
        
        if self.shared_key:
            sym_icon = self._get_icon("symmetric.png")
            if not sym_icon.isNull():
                sym_pixmap = sym_icon.pixmap(icon_size, icon_size)
                p.drawPixmap(icon_x, info_y + int(28 * scale), sym_pixmap)
            p.setPen(QColor(t['error']))
            p.setFont(QFont("JetBrains Mono", shared_font, QFont.Weight.Bold))
            p.drawText(
                text_x, info_y + int(30 * scale),
                w - int(54 * scale), max(24, int(28 * scale)),
                Qt.AlignmentFlag.AlignLeft,
                f"Stolen Key: {self.shared_key}"
            )
        else:
            p.setPen(QColor(t['text_tertiary']))
            p.setFont(QFont("JetBrains Mono", key_font))
            p.drawText(
                pad, info_y + int(30 * scale),
                w - int(32 * scale), row_h,
                Qt.AlignmentFlag.AlignCenter,
                "Waiting..."
            )
        
        for pt in self.particles:
            a = int(255 * pt.life)
            pt.color.setAlpha(a)
            p.setBrush(QBrush(pt.color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPoint(int(pt.x), int(pt.y)), int(pt.size), int(pt.size))
        p.end()


class DataFlowPipe(QFrame):
    """Animated data flow pipe."""
    
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.particles = []
        self._offset = 0
        self.value_a = None
        self.value_b = None
        self.is_attack = False
        self.anim = QTimer()
        self.anim.timeout.connect(self._tick)
        self.anim.start(30)
        scale = layout_manager.font_scale()
        self.setMinimumWidth(max(120, int(140 * scale)))
        self.setMaximumWidth(max(160, int(200 * scale)))
    
    def _tick(self):
        self._offset = (self._offset + 2) % 20
        if self.value_a and random.random() < 0.3:
            t = self.theme.current
            c = QColor(t['error']) if self.is_attack else QColor(t['accent'])
            self.particles.append(Particle(30, self.height() // 2, c))
            self.particles.append(Particle(self.width() - 30, self.height() // 2, c))
        for p in self.particles[:]:
            p.life -= p.decay
            if p.life <= 0:
                self.particles.remove(p)
            else:
                p.x += math.cos(p.angle) * p.speed * (1 if p.x < self.width() // 2 else -1)
        self.update()
    
    def set_values(self, a, b, is_attack=False):
        self.value_a = a
        self.value_b = b
        self.is_attack = is_attack
    
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.theme.current
        scale = layout_manager.font_scale()
        w, h = self.width(), self.height()
        mid = h // 2
        
        for i, d in enumerate([1, -1]):
            pen = QPen(QColor(t['error']) if self.is_attack else QColor(t['accent']), 2.5)
            pen.setDashPattern([8, 6])
            pen.setDashOffset(self._offset * d)
            p.setPen(pen)
            p.drawLine(20, mid - 15 + i * 30, w - 20, mid - 15 + i * 30)
        
        c = QColor(t['error']) if self.is_attack else QColor(t['accent'])
        p.setPen(QPen(c, 2.5))
        p.setBrush(c)
        p.drawLine(w - 20, mid - 10, w - 30, mid - 10)
        p.drawLine(w - 20, mid - 10, w - 25, mid - 14)
        p.drawLine(w - 20, mid - 10, w - 25, mid - 6)
        p.drawLine(20, mid + 10, 30, mid + 10)
        p.drawLine(20, mid + 10, 25, mid + 6)
        p.drawLine(20, mid + 10, 25, mid + 14)
        
        box_font = max(8, int(9 * scale))
        box_h = max(22, int(26 * scale))
        for val, y_off, lbl in [(self.value_a, -48, 'A'), (self.value_b, 20, 'B')]:
            if val is not None:
                bw = min(w - 40, 110)
                p.setBrush(c)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(w // 2 - bw // 2, mid + y_off, bw, box_h, 13, 13)
                p.setPen(QColor("#ffffff"))
                p.setFont(QFont("JetBrains Mono", box_font, QFont.Weight.Bold))
                p.drawText(
                    w // 2 - bw // 2, mid + y_off, bw, box_h,
                    Qt.AlignmentFlag.AlignCenter,
                    f"{lbl}={val}"
                )
        
        for pt in self.particles:
            a = int(255 * pt.life)
            pt.color.setAlpha(a)
            p.setBrush(QBrush(pt.color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPoint(int(pt.x), int(pt.y)), int(pt.size), int(pt.size))
        p.end()


class DiffieHellmanMITMPage(QWidget):
    """Diffie-Hellman MITM Attack."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.worker = None
        self.result_data = None
        self.g = None
        self.p = None
        self.A = None
        self.B = None
        self._init_ui()
    
    def _get_icon(self, name):
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        path = os.path.join(icons_dir, name)
        if os.path.exists(path):
            return QIcon(path)
        return QIcon()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 24, 40, 24)
        layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        back_btn.setObjectName("backButton")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons'
        )
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path))
            back_btn.setIconSize(QSize(16, 16))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback)
        back_btn.setMaximumWidth(100)
        title = QLabel("Diffie-Hellman - MITM Attack")
        title.setObjectName("pageTitle")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_public_keys(), "Public Keys")
        self.tabs.addTab(self._tab_intercepted(), "Intercepted Keys")
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_attack(), "Attack")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs)
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
        
        input_stl = (
            f"QLineEdit{{background:{t['crust']};color:{t['text']};"
            f"border:1px solid {t['border']};border-radius:6px;padding:8px 10px;"
            f"font-size:{max(12, int(13 * scale))}px;}}"
        )
        for attr in ['g_input', 'p_input', 'A_input', 'B_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_stl)
                except RuntimeError:
                    pass
        
        gs = (
            f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;"
            f"margin-top:14px;padding:20px 16px 16px;font-weight:600;font-size:{int(13 * scale)}px;}} "
            f"QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}"
        )
        for attr in ['params_grp', 'intercepted_grp']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(gs)
                except RuntimeError:
                    pass
        
        if hasattr(self, 'info_label') and self.info_label is not None:
            try:
                self.info_label.setStyleSheet(
                    f"color:{t['text_secondary']};background:transparent;"
                    f"font-size:{int(13 * scale)}px;font-family:JetBrains Mono;"
                )
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_output') and self.status_output is not None:
            try:
                self.status_output.setStyleSheet(
                    f"QTextEdit{{background:{t['crust']};color:{t['text']};"
                    f"border:1px solid {t['border']};border-radius:6px;padding:10px;"
                    f"font-family:JetBrains Mono;font-size:{int(13 * scale)}px;}}"
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
            except RuntimeError:
                pass
        
        # Refresh animated devices so they track the current theme
        for attr in ['attacker', 'pipe1', 'pipe2']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).update()
                except RuntimeError:
                    pass
    
    def _paste_line(self, widget):
        c = QApplication.clipboard().text()
        if c:
            widget.setText(c.strip())
    
    def _tab_public_keys(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.params_grp = QGroupBox("Public Parameters")
        pl = QVBoxLayout()
        pl.setSpacing(8)
        
        g_row = QHBoxLayout()
        g_row.setSpacing(8)
        g_lbl = QLabel("g:")
        g_lbl.setMinimumWidth(30)
        g_row.addWidget(g_lbl)
        self.g_input = QLineEdit()
        self.g_input.setPlaceholderText("Primitive root...")
        g_row.addWidget(self.g_input, 1)
        g_paste = QPushButton("Paste")
        g_paste.setObjectName("actionButton")
        g_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        g_paste.clicked.connect(lambda: self._paste_line(self.g_input))
        g_clear = QPushButton("Clear")
        g_clear.setObjectName("dangerButton")
        g_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        g_clear.clicked.connect(self.g_input.clear)
        g_row.addWidget(g_paste)
        g_row.addWidget(g_clear)
        pl.addLayout(g_row)
        
        p_row = QHBoxLayout()
        p_row.setSpacing(8)
        p_lbl = QLabel("p:")
        p_lbl.setMinimumWidth(30)
        p_row.addWidget(p_lbl)
        self.p_input = QLineEdit()
        self.p_input.setPlaceholderText("Prime modulus...")
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
        pl.addLayout(p_row)
        
        self.params_grp.setLayout(pl)
        l.addWidget(self.params_grp)
        
        cont_btn = QPushButton("Continue to Intercepted Keys")
        cont_btn.setObjectName("actionButton")
        cont_btn.setMinimumHeight(48)
        cont_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cont_btn.clicked.connect(self._confirm_public)
        l.addWidget(cont_btn)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _confirm_public(self):
        try:
            self.g = int(self.g_input.text().strip())
            self.p = int(self.p_input.text().strip())
        except:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integers for g and p.")
            return
        self.tabs.removeTab(1)
        self.tabs.insertTab(1, self._tab_intercepted(), "Intercepted Keys")
        self.tabs.setCurrentIndex(1)
        self._apply_theme()
    
    def _tab_intercepted(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        if not self.g:
            lbl = QLabel("Set public parameters first.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"color:{self.theme.current['text_tertiary']};font-size:15px;"
                f"padding:40px;background:transparent;"
            )
            l.addWidget(lbl)
            s.setWidget(c)
            ow = QVBoxLayout(w)
            ow.setContentsMargins(0, 0, 0, 0)
            ow.addWidget(s)
            return w
        
        self.info_label = QLabel(f"g = {self.g}  |  p = {self.p}")
        l.addWidget(self.info_label)
        
        self.intercepted_grp = QGroupBox("Intercepted Public Keys")
        il = QVBoxLayout()
        il.setSpacing(8)
        
        A_row = QHBoxLayout()
        A_row.setSpacing(8)
        A_lbl = QLabel("A:")
        A_lbl.setMinimumWidth(30)
        A_row.addWidget(A_lbl)
        self.A_input = QLineEdit()
        self.A_input.setPlaceholderText("Alice's public key...")
        A_row.addWidget(self.A_input, 1)
        A_paste = QPushButton("Paste")
        A_paste.setObjectName("actionButton")
        A_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        A_paste.clicked.connect(lambda: self._paste_line(self.A_input))
        A_clear = QPushButton("Clear")
        A_clear.setObjectName("dangerButton")
        A_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        A_clear.clicked.connect(self.A_input.clear)
        A_row.addWidget(A_paste)
        A_row.addWidget(A_clear)
        il.addLayout(A_row)
        
        B_row = QHBoxLayout()
        B_row.setSpacing(8)
        B_lbl = QLabel("B:")
        B_lbl.setMinimumWidth(30)
        B_row.addWidget(B_lbl)
        self.B_input = QLineEdit()
        self.B_input.setPlaceholderText("Bob's public key...")
        B_row.addWidget(self.B_input, 1)
        B_paste = QPushButton("Paste")
        B_paste.setObjectName("actionButton")
        B_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        B_paste.clicked.connect(lambda: self._paste_line(self.B_input))
        B_clear = QPushButton("Clear")
        B_clear.setObjectName("dangerButton")
        B_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        B_clear.clicked.connect(self.B_input.clear)
        B_row.addWidget(B_paste)
        B_row.addWidget(B_clear)
        il.addLayout(B_row)
        
        self.intercepted_grp.setLayout(il)
        l.addWidget(self.intercepted_grp)
        
        launch_btn = QPushButton("Launch Attack")
        launch_btn.setObjectName("actionButton")
        launch_btn.setMinimumHeight(48)
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        launch_btn.clicked.connect(self._run_attack)
        l.addWidget(launch_btn)
        l.addStretch()
        
        s.setWidget(c)
        ow = QVBoxLayout(w)
        ow.setContentsMargins(0, 0, 0, 0)
        ow.addWidget(s)
        return w
    
    def _run_attack(self):
        try:
            self.A = int(self.A_input.text().strip())
            self.B = int(self.B_input.text().strip())
        except:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integers for A and B.")
            return
        self.tabs.removeTab(2)
        self.tabs.insertTab(2, self._tab_status(), "Status")
        self.tabs.setCurrentIndex(2)
        self.status_output.clear()
        self.status_progress.setValue(0)
        self.worker = MITMWorker(self.g, self.p, self.A, self.B)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.status_progress.setValue)
        self.worker.finished.connect(self._on_attack_finished)
        self.worker.start()
        self._apply_theme()
    
    def _on_progress(self, message):
        self.status_output.append(message)
    
    def _on_attack_finished(self, result):
        self.result_data = result
        self.status_output.append("")
        self.status_output.append("=" * 50)
        self.status_output.append("ATTACK SUMMARY")
        self.status_output.append("=" * 50)
        self.status_output.append(f"Eavesdropped: g={self.g}, p={self.p}, A={self.A}, B={self.B}")
        if result['success']:
            self.status_output.append(f"Alice's Private: {result['a_private']}")
            self.status_output.append(f"Bob's Private: {result['b_private']}")
            self.status_output.append(f"Stolen Key: {result['K']}")
            self.status_output.append(f"Brute force max tries: {self.p-1}")
        self.tabs.removeTab(3)
        self.tabs.insertTab(3, self._tab_attack(), "Attack")
        if result['success']:
            QTimer.singleShot(500, lambda: self.tabs.setCurrentIndex(3))
        self._apply_theme()
    
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
        self.status_output.setPlaceholderText("Activity log and details...")
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output, 1)
        return w
    
    def _tab_attack(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(16)
        
        if not self.result_data:
            lbl = QLabel("Launch the attack first.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:{int(15 * scale)}px;"
                f"padding:40px;background:transparent;"
            )
            l.addWidget(lbl)
            return w
        
        dev = QHBoxLayout()
        dev.setSpacing(0)
        self.attacker = AttackerDevice(self.theme)
        self.pipe1 = DataFlowPipe(self.theme)
        self.pipe2 = DataFlowPipe(self.theme)
        if self.result_data['success']:
            self.attacker.set_keys(self.result_data['a_private'], self.result_data['K'])
        self.pipe1.set_values(self.A, self.B, True)
        self.pipe2.set_values(self.B, self.A, True)
        dev.addWidget(self.pipe1)
        dev.addWidget(self.attacker)
        dev.addWidget(self.pipe2)
        l.addLayout(dev)
        
        result_layout = QHBoxLayout()
        result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_icon_label = QLabel()
        icon_name = "yes.png" if (self.result_data['success'] and self.result_data['match']) else "no.png"
        status_icon_path = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons', icon_name
        )
        if os.path.exists(status_icon_path):
            status_icon_label.setPixmap(QIcon(status_icon_path).pixmap(32, 32))
        status_icon_label.setStyleSheet("background:transparent;")
        result_layout.addWidget(status_icon_label)
        
        sym_icon_label = QLabel()
        sym_icon_path = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS')
            else os.path.join(os.path.dirname(__file__), '..'),
            'assets', 'icons', 'symmetric.png'
        )
        if os.path.exists(sym_icon_path):
            sym_icon_label.setPixmap(QIcon(sym_icon_path).pixmap(32, 32))
        sym_icon_label.setStyleSheet("background:transparent;")
        result_layout.addWidget(sym_icon_label)
        
        res = QLabel()
        res.setAlignment(Qt.AlignmentFlag.AlignCenter)
        res.setWordWrap(True)
        if self.result_data['success'] and self.result_data['match']:
            res.setText(
                f"Stolen Shared Key:  {self.result_data['K']}\n"
                f"The attacker can now decrypt all communications!"
            )
            res.setStyleSheet(
                f"color:{t['error']};font-size:{int(20 * scale)}px;font-weight:bold;"
                f"background:{t['error']}15;border:2px solid {t['error']}44;"
                f"border-radius:14px;padding:20px;"
            )
        else:
            res.setText("Attack failed.")
            res.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:{int(14 * scale)}px;padding:20px;"
            )
        result_layout.addWidget(res)
        l.addLayout(result_layout)
        l.addStretch()
        return w
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()