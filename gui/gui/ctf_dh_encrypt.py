# gui/ctf_dh_encrypt.py - Final version
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QTabWidget, QTextEdit, QTextBrowser, QFrame
)
from PySide6.QtCore import Qt, QSize, QTimer, QPoint, QThread, Signal
from PySide6.QtGui import (
    QPainter, QFont, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath, QIcon, QPixmap
)
import os, sys, math, random, hashlib


def is_prime(n, k=10):
    if n < 2: return False
    if n in (2, 3): return True
    if n % 2 == 0: return False
    r, d = 0, n - 1
    while d % 2 == 0: r += 1; d //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1: break
        else: return False
    return True


def int_to_bytes(n):
    result = []
    while n > 0: result.insert(0, n & 0xFF); n >>= 8
    return bytes(result)


class PrimeGenWorker(QThread):
    finished = Signal(str, str)
    
    def __init__(self, bits=256):
        super().__init__()
        self.bits = bits
    
    def run(self):
        while True:
            n = random.getrandbits(self.bits)
            n |= 1
            if is_prime(n): break
        p = n; g = 2; phi = p - 1
        for test_g in range(2, min(p, 50)):
            if pow(test_g, phi // 2, p) != 1: g = test_g; break
        self.finished.emit(str(p), str(g))


class Particle:
    def __init__(self, x, y, color):
        self.x = x; self.y = y; self.color = color
        self.size = random.uniform(2, 5); self.speed = random.uniform(0.5, 2)
        self.angle = random.uniform(0, 2 * math.pi); self.life = 1.0
        self.decay = random.uniform(0.01, 0.03)


class AnimatedDevice(QFrame):
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme; self.particles = []
        self.anim_timer = QTimer(); self.anim_timer.timeout.connect(self._tick); self.anim_timer.start(33)
        self._rotation = 0; self._pulse = 0; self._data_flow = 0
        self.private_key = None; self.public_key = None; self.shared_key = None
        self.setMinimumSize(250, 320); self.setMaximumSize(300, 380)
    
    def _get_icon(self, name):
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        path = os.path.join(icons_dir, name)
        if os.path.exists(path): return QIcon(path)
        return QIcon()
    
    def _tick(self):
        self._rotation += 0.5; self._pulse = (math.sin(self._rotation * 0.05) + 1) / 2; self._data_flow += 0.03
        for p in self.particles[:]:
            p.life -= p.decay
            if p.life <= 0: self.particles.remove(p)
            else: p.x += math.cos(p.angle) * p.speed; p.y += math.sin(p.angle) * p.speed
        if self.shared_key and random.random() < 0.3:
            t = self.theme.current; cx, cy = self.width() // 2, 190
            for _ in range(2): self.particles.append(Particle(cx + random.uniform(-40, 40), cy + random.uniform(-20, 20), QColor(t['success'])))
        self.update()
    
    def set_keys(self, private, public, shared=None):
        self.private_key = private; self.public_key = public; self.shared_key = shared
        if shared:
            for _ in range(15): self.particles.append(Particle(self.width() // 2, 190, QColor(self.theme.current['success'])))
    
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_device(p)
        for particle in self.particles:
            a = int(255 * particle.life); particle.color.setAlpha(a)
            p.setBrush(QBrush(particle.color)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPoint(int(particle.x), int(particle.y)), int(particle.size), int(particle.size))
        p.end()
    
    def _draw_device(self, p): raise NotImplementedError
    
    def _draw_key_info(self, p, y):
        t = self.theme.current; w = self.width()
        
        priv_icon = self._get_icon("private.png")
        if not priv_icon.isNull():
            priv_pixmap = priv_icon.pixmap(16, 16)
            p.drawPixmap(16, y + 2, priv_pixmap)
            p.setFont(QFont("JetBrains Mono", 10))
            p.setPen(QColor(t['text']) if self.private_key else QColor(t['text_tertiary']))
            p.drawText(38, y, w - 54, 22, Qt.AlignmentFlag.AlignLeft, f"Private:  {self.private_key if self.private_key else '--'}")
        else:
            p.setFont(QFont("JetBrains Mono", 10))
            p.setPen(QColor(t['text']) if self.private_key else QColor(t['text_tertiary']))
            p.drawText(16, y, w - 32, 22, Qt.AlignmentFlag.AlignLeft, f"Private:  {self.private_key if self.private_key else '--'}")
        
        pub_icon = self._get_icon("public.png")
        if not pub_icon.isNull():
            pub_pixmap = pub_icon.pixmap(16, 16)
            p.drawPixmap(16, y + 28, pub_pixmap)
            p.setFont(QFont("JetBrains Mono", 10))
            p.setPen(QColor(t['text']) if self.public_key else QColor(t['text_tertiary']))
            p.drawText(38, y + 26, w - 54, 22, Qt.AlignmentFlag.AlignLeft, f"Public:   {self.public_key if self.public_key else '--'}")
        else:
            p.setFont(QFont("JetBrains Mono", 10))
            p.setPen(QColor(t['text']) if self.public_key else QColor(t['text_tertiary']))
            p.drawText(16, y + 26, w - 32, 22, Qt.AlignmentFlag.AlignLeft, f"Public:   {self.public_key if self.public_key else '--'}")


class ServerDevice(AnimatedDevice):
    def _draw_device(self, p):
        t = self.theme.current; w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0, 0, 0, 25)); p.drawRoundedRect(10, 10, w - 20, h - 20, 20, 20)
        bg = QLinearGradient(0, 0, w, 0); bg.setColorAt(0, QColor(t['crust']).lighter(105)); bg.setColorAt(0.3, QColor(t['base']))
        bg.setColorAt(0.7, QColor(t['base'])); bg.setColorAt(1, QColor(t['crust']).darker(105))
        p.setBrush(QBrush(bg)); p.setPen(QPen(QColor(t['border']), 2)); p.drawRoundedRect(6, 6, w - 12, h - 12, 18, 18)
        tg = QLinearGradient(0, 0, 0, 50); tg.setColorAt(0, QColor(t['success'])); tg.setColorAt(1, QColor(t['success']).darker(150))
        p.setBrush(QBrush(tg)); p.setPen(Qt.PenStyle.NoPen)
        pt = QPainterPath(); pt.addRoundedRect(8, 8, w - 16, 48, 18, 18); pt.addRect(8, 38, w - 16, 18); p.drawPath(pt)
        
        server_icon = self._get_icon("server.png")
        if not server_icon.isNull():
            server_pixmap = server_icon.pixmap(22, 22)
            p.drawPixmap(18, 16, server_pixmap)
        p.setPen(QColor("#ffffff")); p.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        p.drawText(44, 10, w - 60, 42, Qt.AlignmentFlag.AlignCenter, "ALICE")
        
        rx, ry, rw, rh = w // 2 - 55, 70, 110, 90
        rg = QLinearGradient(rx, 0, rx + rw, 0)
        for i, c in enumerate(["#1a1a2e", "#16213e", "#1a1a2e", "#0f3460", "#1a1a2e"]): rg.setColorAt(i * 0.25, QColor(c))
        p.setBrush(QBrush(rg)); p.setPen(QPen(QColor(t['surface2']), 1.5)); p.drawRoundedRect(rx, ry, rw, rh, 10, 10)
        for i in range(5):
            sy = ry + 8 + i * 16
            sg = QLinearGradient(0, sy, 0, sy + 10); sg.setColorAt(0, QColor("#0a0a1a")); sg.setColorAt(1, QColor("#1a1a2e"))
            p.setBrush(QBrush(sg)); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(rx + 10, sy, rw - 20, 10, 3, 3)
            led = [QColor(t['success']), QColor(t['success']).lighter(130), QColor(t['warning']), QColor(t['success']), QColor(t['accent'])][i]
            if i == int(self._data_flow * 3) % 5: led = led.lighter(180)
            p.setBrush(QBrush(led)); p.drawEllipse(QPoint(rx + rw - 18, sy + 5), 4, 4)
        gl = QRadialGradient(w // 2, ry + rh // 2, 80); gl.setColorAt(0, QColor(t['success']).lighter(180)); gl.setColorAt(0.3, QColor(t['success'])); gl.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(gl)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(QPoint(w // 2, ry + rh // 2), 70, 70)
        self._draw_key_info(p, ry + rh + 14)


class ClientDevice(AnimatedDevice):
    def _draw_device(self, p):
        t = self.theme.current; w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0, 0, 0, 25)); p.drawRoundedRect(10, 10, w - 20, h - 20, 20, 20)
        bg = QLinearGradient(0, 0, w, 0); bg.setColorAt(0, QColor(t['crust']).lighter(105)); bg.setColorAt(0.3, QColor(t['base']))
        bg.setColorAt(0.7, QColor(t['base'])); bg.setColorAt(1, QColor(t['crust']).darker(105))
        p.setBrush(QBrush(bg)); p.setPen(QPen(QColor(t['border']), 2)); p.drawRoundedRect(6, 6, w - 12, h - 12, 18, 18)
        tg = QLinearGradient(0, 0, 0, 50); tg.setColorAt(0, QColor(t['warning'])); tg.setColorAt(1, QColor(t['warning']).darker(150))
        p.setBrush(QBrush(tg)); p.setPen(Qt.PenStyle.NoPen)
        pt = QPainterPath(); pt.addRoundedRect(8, 8, w - 16, 48, 18, 18); pt.addRect(8, 38, w - 16, 18); p.drawPath(pt)
        
        laptop_icon = self._get_icon("laptop.png")
        if not laptop_icon.isNull():
            laptop_pixmap = laptop_icon.pixmap(22, 22)
            p.drawPixmap(18, 16, laptop_pixmap)
        p.setPen(QColor("#ffffff")); p.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        p.drawText(44, 10, w - 60, 42, Qt.AlignmentFlag.AlignCenter, "BOB")
        
        lx, ly = w // 2 - 52, 68
        sg = QLinearGradient(lx, ly, lx + 104, ly + 65)
        for i, c in enumerate(["#0a1628", "#0f2444", "#162d50", "#0f2444", "#0a1628"]): sg.setColorAt(i * 0.25, QColor(c))
        p.setBrush(QBrush(sg)); p.setPen(QPen(QColor(t['surface2']), 2)); p.drawRoundedRect(lx, ly, 104, 68, 8, 8)
        for i in range(4):
            off = int(self._data_flow * 20) % 60; yp = ly + 16 + i * 12 + off
            if yp > ly + 60: yp -= 60
            if ly < yp < ly + 60:
                a = max(40, min(180, int(150 - abs(yp - (ly + 30)) * 3))); c = QColor(t['accent']); c.setAlpha(a)
                p.setPen(QPen(c, 1.5)); p.drawLine(lx + 16, yp, lx + 88, yp)
        ky = ly + 72; kg = QLinearGradient(0, ky, 0, ky + 10); kg.setColorAt(0, QColor("#1a1a2e")); kg.setColorAt(1, QColor("#0f0f1a"))
        p.setBrush(QBrush(kg)); p.setPen(QPen(QColor(t['surface2']), 1)); p.drawRoundedRect(lx - 8, ky, 120, 10, 3, 3)
        by = ky + 14; bsg = QLinearGradient(0, by, 0, by + 7); bsg.setColorAt(0, QColor("#16213e")); bsg.setColorAt(1, QColor("#0a0a1a"))
        p.setBrush(QBrush(bsg)); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(lx + 20, by, 64, 7, 4, 4)
        cm = QColor(t['success']) if self._pulse > 0.5 else QColor(t['success']).darker(150)
        p.setBrush(QBrush(cm)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(QPoint(w // 2, ly + 7), 3, 3)
        gl = QRadialGradient(w // 2, ly + 40, 70); gl.setColorAt(0, QColor(t['warning']).lighter(180)); gl.setColorAt(0.3, QColor(t['warning'])); gl.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(gl)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(QPoint(w // 2, ly + 40), 60, 60)
        self._draw_key_info(p, by + 20)


class DataFlowPipe(QFrame):
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme; self.particles = []; self._offset = 0
        self.value_a = None; self.value_b = None
        self.anim = QTimer(); self.anim.timeout.connect(self._tick); self.anim.start(30)
        self.setMinimumWidth(140); self.setMaximumWidth(200)
    
    def _tick(self):
        self._offset = (self._offset + 2) % 20
        if self.value_a and random.random() < 0.4:
            t = self.theme.current
            self.particles.append(Particle(30, self.height() // 2, QColor(t['accent'])))
            self.particles.append(Particle(self.width() - 30, self.height() // 2, QColor(t['accent'])))
        for p in self.particles[:]:
            p.life -= p.decay
            if p.life <= 0: self.particles.remove(p)
            else: p.x += math.cos(p.angle) * p.speed * (1 if p.x < self.width() // 2 else -1)
        self.update()
    
    def set_values(self, a, b): self.value_a = a; self.value_b = b
    
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.theme.current; w, h, mid = self.width(), self.height(), self.height() // 2
        for i, d in enumerate([1, -1]):
            pen = QPen(QColor(t['accent']), 2.5); pen.setDashPattern([8, 6]); pen.setDashOffset(self._offset * d)
            p.setPen(pen); p.drawLine(20, mid - 15 + i * 30, w - 20, mid - 15 + i * 30)
        p.setPen(QPen(QColor(t['accent']), 2.5)); p.setBrush(QColor(t['accent']))
        p.drawLine(w - 20, mid - 10, w - 30, mid - 10); p.drawLine(w - 20, mid - 10, w - 25, mid - 14); p.drawLine(w - 20, mid - 10, w - 25, mid - 6)
        p.drawLine(20, mid + 10, 30, mid + 10); p.drawLine(20, mid + 10, 25, mid + 6); p.drawLine(20, mid + 10, 25, mid + 14)
        for val, y_off in [(self.value_a, -48), (self.value_b, 20)]:
            if val:
                bw = min(w - 40, 110)
                p.setBrush(QColor(t['accent'])); p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(w // 2 - bw // 2, mid + y_off, bw, 26, 13, 13)
                p.setPen(QColor("#ffffff")); p.setFont(QFont("JetBrains Mono", 10, QFont.Weight.Bold))
                p.drawText(w // 2 - bw // 2, mid + y_off, bw, 26, Qt.AlignmentFlag.AlignCenter, f"{'A' if y_off == -48 else 'B'}={val}")
        for pt in self.particles:
            a = int(255 * pt.life); pt.color.setAlpha(a)
            p.setBrush(QBrush(pt.color)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPoint(int(pt.x), int(pt.y)), int(pt.size), int(pt.size))
        p.end()


class CTF_DH_EncryptPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager; self.back_callback = back_callback
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(40, 24, 40, 24); layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path)); back_btn.setIconSize(QSize(16, 16))
        back_btn.setObjectName("backButton"); back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_callback); back_btn.setMaximumWidth(100)
        title = QLabel("CTF - DH - Encrypt Message"); title.setObjectName("pageTitle")
        header.addWidget(back_btn); header.addWidget(title); header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_public_keys(), "Public Keys")
        self.tabs.addTab(self._tab_private_keys(), "Private Keys")
        self.tabs.addTab(self._tab_placeholder(), "Shared Key")
        self.tabs.addTab(self._tab_placeholder(), "Communication")
        self.tabs.addTab(self._tab_placeholder(), "Results")
        
        layout.addLayout(header); layout.addWidget(self.tabs)
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        self.setStyleSheet(f"background:{t['base']};")
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 20px;margin-right:2px;border-radius:7px 7px 0 0;font-size:12px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """)
    
    def _line_edit(self):
        t = self.theme.current
        le = QLineEdit()
        le.setStyleSheet(f"""
            QLineEdit {{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:5px;padding:10px 14px;font-family:JetBrains Mono;font-size:14px;}}
            QLineEdit:focus {{border-color:{t['border_focus']};}}
        """)
        return le
    
    def _group(self, title):
        t = self.theme.current
        g = QGroupBox(title)
        g.setStyleSheet(f"""
            QGroupBox {{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:16px;font-weight:600;font-size:13px;}}
            QGroupBox::title {{left:14px;padding:0 8px;color:{t['text']};}}
        """)
        return g
    
    def _tab_placeholder(self):
        t = self.theme.current
        w = QWidget(); l = QVBoxLayout(w)
        lbl = QLabel("Complete previous steps first."); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{t['text_tertiary']};font-size:15px;padding:40px;background:transparent;")
        l.addWidget(lbl)
        return w
    
    def _tab_public_keys(self):
        t = self.theme.current
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 30, 40, 30); l.setSpacing(16)
        desc = QLabel("Enter public parameters g (generator) and p (prime modulus).")
        desc.setWordWrap(True); desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;"); l.addWidget(desc)
        g = self._group("Public Parameters"); f = QFormLayout(); f.setSpacing(14)
        gen_row = QHBoxLayout()
        self.g_input = self._line_edit(); self.g_input.setPlaceholderText("Generator g..."); self.g_input.setText("2")
        self.gen_btn = QPushButton("Gen"); self.gen_btn.setMinimumHeight(42)
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.gen_btn.clicked.connect(self._generate_params)
        self.gen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 10px;
                padding: 14px;
                font-weight: 700;
                font-size: 15px;
            }}
            QPushButton:hover {{background-color: {t['surface0']};}}
        """)
        gen_row.addWidget(self.g_input); gen_row.addWidget(self.gen_btn)
        self.p_input = self._line_edit(); self.p_input.setPlaceholderText("Prime modulus p...")
        f.addRow("g:", gen_row); f.addRow("p:", self.p_input); g.setLayout(f); l.addWidget(g)
        br = QHBoxLayout(); br.addStretch()
        btn = QPushButton("Continue →"); btn.setMinimumHeight(42); btn.setMaximumWidth(130)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 10px;
                padding: 14px;
                font-weight: 700;
                font-size: 15px;
            }}
            QPushButton:hover {{background-color: {t['surface0']};}}
        """)
        br.addWidget(btn); l.addLayout(br); l.addStretch(); return w
    
    def _generate_params(self):
        self.gen_btn.setEnabled(False); self.gen_btn.setText("...")
        self.prime_worker = PrimeGenWorker(256)
        self.prime_worker.finished.connect(self._on_prime_generated)
        self.prime_worker.start()
    
    def _on_prime_generated(self, p_str, g_str):
        self.p_input.setText(p_str); self.g_input.setText(g_str)
        self.gen_btn.setEnabled(True); self.gen_btn.setText("Gen")
    
    def _tab_private_keys(self):
        t = self.theme.current
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 30, 40, 30); l.setSpacing(16)
        desc = QLabel("Enter private keys for Alice and Bob.")
        desc.setWordWrap(True); desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;"); l.addWidget(desc)
        g = self._group("Private Keys"); f = QFormLayout(); f.setSpacing(14)
        self.a_input = self._line_edit(); self.a_input.setPlaceholderText("Alice's private key a...")
        self.b_input = self._line_edit(); self.b_input.setPlaceholderText("Bob's private key b...")
        f.addRow("Alice (a):", self.a_input); f.addRow("Bob (b):", self.b_input); g.setLayout(f); l.addWidget(g)
        
        # Button row with Generate and Compute side by side
        br = QHBoxLayout()
        gen_btn = QPushButton("Generate Random Keys"); gen_btn.setMinimumHeight(42)
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor); gen_btn.clicked.connect(self._generate_private); br.addWidget(gen_btn)
        gen_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 10px;
                padding: 14px;
                font-weight: 700;
                font-size: 15px;
            }}
            QPushButton:hover {{background-color: {t['surface0']};}}
        """)
        br.addStretch()
        compute_btn = QPushButton("Compute →"); compute_btn.setMinimumHeight(42); compute_btn.setMaximumWidth(130)
        compute_btn.setCursor(Qt.CursorShape.PointingHandCursor); compute_btn.clicked.connect(self._compute_keys); br.addWidget(compute_btn)
        compute_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 10px;
                padding: 14px;
                font-weight: 700;
                font-size: 15px;
            }}
            QPushButton:hover {{background-color: {t['surface0']};}}
        """)
        l.addLayout(br); l.addStretch(); return w
    
    def _generate_private(self):
        try:
            p = int(self.p_input.text().strip())
            self.a_input.setText(str(random.randint(2, p-2)))
            self.b_input.setText(str(random.randint(2, p-2)))
        except: pass
    
    def _compute_keys(self):
        try:
            self.g = int(self.g_input.text().strip()); self.p = int(self.p_input.text().strip())
            self.a = int(self.a_input.text().strip()); self.b = int(self.b_input.text().strip())
            self.A = pow(self.g, self.a, self.p); self.B = pow(self.g, self.b, self.p)
            self.s_a = pow(self.B, self.a, self.p); self.s_b = pow(self.A, self.b, self.p)
            self.match = self.s_a == self.s_b
            self.tabs.removeTab(2); self.tabs.removeTab(2); self.tabs.removeTab(2)
            self.tabs.insertTab(2, self._tab_shared_key(), "Shared Key")
            self.tabs.insertTab(3, self._tab_communication(), "Communication")
            self.tabs.insertTab(4, self._tab_placeholder(), "Results")
            self.tabs.setCurrentIndex(2)
        except: pass
    
    def _tab_shared_key(self):
        t = self.theme.current
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(16, 16, 16, 16); l.setSpacing(16)
        if not hasattr(self, 's_a'): return self._tab_placeholder()
        
        # Device visualization row
        dev = QHBoxLayout(); dev.setSpacing(0)
        self.alice_dev = ServerDevice(self.theme); self.pipe = DataFlowPipe(self.theme); self.bob_dev = ClientDevice(self.theme)
        self.alice_dev.set_keys(self.a, self.A)
        self.bob_dev.set_keys(self.b, self.B)
        self.pipe.set_values(self.A, self.B)
        dev.addWidget(self.alice_dev); dev.addWidget(self.pipe); dev.addWidget(self.bob_dev); l.addLayout(dev)
        
        # Shared key result display - just the number with big font
        result_layout = QHBoxLayout(); result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_name = "yes.png" if self.match else "no.png"
        icon_path = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons', icon_name)
        if os.path.exists(icon_path):
            icon_lbl = QLabel(); icon_lbl.setPixmap(QIcon(icon_path).pixmap(32, 32)); icon_lbl.setStyleSheet("background:transparent;")
            result_layout.addWidget(icon_lbl)
        
        # Symmetric key icon
        sym_icon_path = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons', 'symmetric.png')
        if os.path.exists(sym_icon_path):
            sym_icon_label = QLabel()
            sym_icon_label.setPixmap(QIcon(sym_icon_path).pixmap(32, 32))
            sym_icon_label.setStyleSheet("background:transparent;")
            result_layout.addWidget(sym_icon_label)
        
        r = QLabel(); r.setAlignment(Qt.AlignmentFlag.AlignCenter); r.setWordWrap(True)
        if self.match:
            r.setText(str(self.s_a))
            r.setStyleSheet(f"color:{t['success']};font-size:20px;font-weight:bold;background:{t['accent_light']};border:2px solid {t['success']}44;border-radius:14px;padding:20px;font-family:JetBrains Mono,Consolas,monospace;")
        else:
            r.setText("Key mismatch! Shared keys do not match.")
            r.setStyleSheet(f"color:{t['error']};font-size:14px;font-weight:bold;background:{t['error']}12;border:2px solid {t['error']}44;border-radius:14px;padding:20px;")
        result_layout.addWidget(r)
        l.addLayout(result_layout); l.addStretch(); return w
    
    def _tab_communication(self):
        t = self.theme.current
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(40, 30, 40, 30); l.setSpacing(16)
        if not hasattr(self, 's_a'): return self._tab_placeholder()
        desc = QLabel("Enter a message to encrypt using the shared secret.")
        desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;"); l.addWidget(desc)
        g = self._group("Message"); f = QFormLayout(); f.setSpacing(14)
        self.msg_input = self._line_edit(); self.msg_input.setPlaceholderText("Enter message to encrypt...")
        self.enc_type = QComboBox(); self.enc_type.addItems(["XOR shared % 256", "XOR full shared", "XOR SHA256"])
        self.enc_type.setStyleSheet(f"QComboBox{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 12px;font-size:13px;}}")
        f.addRow("Message:", self.msg_input); f.addRow("Method:", self.enc_type); g.setLayout(f); l.addWidget(g)
        br = QHBoxLayout(); br.addStretch()
        btn = QPushButton("Encrypt →"); btn.setMinimumHeight(42); btn.setMaximumWidth(130)
        btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.clicked.connect(self._encrypt); br.addWidget(btn)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 10px;
                padding: 14px;
                font-weight: 700;
                font-size: 15px;
            }}
            QPushButton:hover {{background-color: {t['surface0']};}}
        """)
        l.addLayout(br); l.addStretch(); return w
    
    def _encrypt(self):
        try:
            flag_text = self.msg_input.text().strip(); enc_type = self.enc_type.currentText()
            if not flag_text: return
            s = self.s_a; flag_bytes = flag_text.encode()
            if enc_type == "XOR shared % 256":
                enc_bytes = bytes([b ^ (s % 256) for b in flag_bytes])
            elif enc_type == "XOR full shared":
                key_bytes = int_to_bytes(s)
                enc_bytes = bytes([flag_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(flag_bytes))])
            elif enc_type == "XOR SHA256":
                key = hashlib.sha256(str(s).encode()).digest()
                enc_bytes = bytes([flag_bytes[i] ^ key[i % len(key)] for i in range(len(flag_bytes))])
            self.enc_hex = enc_bytes.hex(); self.enc_flag = flag_text; self.enc_method = enc_type
            self.tabs.removeTab(4); self.tabs.insertTab(4, self._tab_results(), "Results"); self.tabs.setCurrentIndex(4)
        except: pass
    
    def _tab_results(self):
        t = self.theme.current
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(20, 16, 20, 16); l.setSpacing(14)
        if not hasattr(self, 'enc_hex'): return self._tab_placeholder()
        res_grp = QGroupBox("Encrypted Output")
        rl = QVBoxLayout()
        result_output = QTextEdit(); result_output.setReadOnly(True)
        result_output.setText(self.enc_hex)
        result_output.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono,Consolas,monospace;font-size:18px;font-weight:700;}}")
        result_output.setMinimumHeight(80); result_output.setMaximumHeight(120)
        rl.addWidget(result_output); res_grp.setLayout(rl); l.addWidget(res_grp); l.addStretch(); return w
    
    def refresh_theme(self):
        self.setStyleSheet(""); self._apply_theme()