# gui/ctf_dh_small_numbers.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QTabWidget, QTextEdit, QProgressBar, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer
from PySide6.QtGui import (
    QPainter, QFont, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath, QIcon, QPixmap
)
import os, sys, math, random, hashlib


def int_to_bytes(n):
    result = []
    while n > 0:
        result.insert(0, n & 0xFF)
        n >>= 8
    return bytes(result)


class Particle:
    def __init__(self, x, y, color):
        self.x = x; self.y = y; self.color = color
        self.size = random.uniform(2, 5); self.speed = random.uniform(0.5, 2)
        self.angle = random.uniform(0, 2 * math.pi); self.life = 1.0
        self.decay = random.uniform(0.01, 0.03)


class AttackerDevice(QFrame):
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme; self.particles = []
        self.timer = QTimer(); self.timer.timeout.connect(self._tick); self.timer.start(33)
        self._pulse = 0; self._data_flow = 0
        self.private_key = None; self.shared_key = None
        self.setMinimumSize(250, 320); self.setMaximumSize(300, 380)
    
    def _get_icon(self, name):
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        path = os.path.join(icons_dir, name)
        if os.path.exists(path): return QIcon(path)
        return QIcon()
    
    def _tick(self):
        self._pulse = (math.sin(self._data_flow * 2) + 1) / 2; self._data_flow += 0.03
        for p in self.particles[:]:
            p.life -= p.decay
            if p.life <= 0: self.particles.remove(p)
            else: p.x += math.cos(p.angle) * p.speed; p.y += math.sin(p.angle) * p.speed
        if self.shared_key and random.random() < 0.3:
            t = self.theme.current; cx, cy = self.width() // 2, 200
            self.particles.append(Particle(cx + random.uniform(-30, 30), cy + random.uniform(-20, 20), QColor(t['error'])))
        self.update()
    
    def set_keys(self, private, shared):
        self.private_key = private; self.shared_key = shared
        if shared:
            for _ in range(10):
                self.particles.append(Particle(self.width() // 2, 200, QColor(self.theme.current['error'])))
    
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.theme.current; w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(0,0,0,25)); p.drawRoundedRect(10,10,w-20,h-20,20,20)
        bg = QLinearGradient(0,0,w,0); bg.setColorAt(0,QColor(t['crust']).lighter(105)); bg.setColorAt(0.3,QColor(t['base']))
        bg.setColorAt(0.7,QColor(t['base'])); bg.setColorAt(1,QColor(t['crust']).darker(105))
        p.setBrush(QBrush(bg)); p.setPen(QPen(QColor(t['border']),2)); p.drawRoundedRect(6,6,w-12,h-12,18,18)
        tg = QLinearGradient(0,0,0,50); tg.setColorAt(0,QColor(t['error'])); tg.setColorAt(1,QColor(t['error']).darker(150))
        p.setBrush(QBrush(tg)); p.setPen(Qt.PenStyle.NoPen)
        pt = QPainterPath(); pt.addRoundedRect(8,8,w-16,48,18,18); pt.addRect(8,38,w-16,18); p.drawPath(pt)
        trudy_icon = self._get_icon("trudy.png")
        if not trudy_icon.isNull(): p.drawPixmap(18, 16, trudy_icon.pixmap(22, 22))
        p.setPen(QColor("#ffffff")); p.setFont(QFont("Inter",14,QFont.Weight.Bold))
        p.drawText(44,10,w-60,42,Qt.AlignmentFlag.AlignCenter,"TRUDY")
        cx, cy = w//2, 110
        fg = QRadialGradient(cx,cy,40); fg.setColorAt(0,QColor("#1a1a2e")); fg.setColorAt(1,QColor("#0a0a1a"))
        p.setBrush(QBrush(fg)); p.setPen(QPen(QColor(t['error']),2)); p.drawEllipse(cx-35,cy-35,70,70)
        eye = QColor(t['error']) if self._pulse > 0.5 else QColor(t['error']).darker(200)
        p.setBrush(QBrush(eye)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx-16,cy-10,12,12); p.drawEllipse(cx+4,cy-10,12,12)
        p.setPen(QPen(QColor(t['error']),2))
        smirk = QPainterPath(); smirk.moveTo(cx-12,cy+12); smirk.quadTo(cx,cy+22,cx+12,cy+12); p.drawPath(smirk)
        gl = QRadialGradient(cx,cy,60); gl.setColorAt(0,QColor(t['error']).lighter(150)); gl.setColorAt(0.5,QColor(t['error'])); gl.setColorAt(1,QColor(0,0,0,0))
        p.setBrush(QBrush(gl)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(cx-55,cy-55,110,110)
        info_y = 170; p.setFont(QFont("JetBrains Mono",10))
        decrypt_icon = self._get_icon("decrypt.png")
        if not decrypt_icon.isNull(): p.drawPixmap(16, info_y + 2, decrypt_icon.pixmap(16, 16))
        p.setPen(QColor(t['text']) if self.private_key else QColor(t['text_tertiary']))
        p.drawText(38, info_y, w - 54, 22, Qt.AlignmentFlag.AlignLeft, f"Cracked Key:  {self.private_key if self.private_key else '--'}")
        if self.shared_key:
            sym_icon = self._get_icon("symmetric.png")
            if not sym_icon.isNull(): p.drawPixmap(16, info_y + 28, sym_icon.pixmap(16, 16))
            shared_str = str(self.shared_key)
            if len(shared_str) > 40:
                display = shared_str[:20] + "..." + shared_str[-20:]
            else:
                display = shared_str
            p.setPen(QColor(t['error'])); p.setFont(QFont("JetBrains Mono", 10, QFont.Weight.Bold))
            p.drawText(38, info_y + 30, w - 54, 28, Qt.AlignmentFlag.AlignLeft, f"Stolen Key: {display}")
        else:
            p.setPen(QColor(t['text_tertiary'])); p.setFont(QFont("JetBrains Mono", 10))
            p.drawText(16, info_y + 30, w - 32, 22, Qt.AlignmentFlag.AlignCenter, "Waiting...")
        for pt in self.particles:
            a = int(255*pt.life); pt.color.setAlpha(a)
            p.setBrush(QBrush(pt.color)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(pt.x),int(pt.y),int(pt.size),int(pt.size))
        p.end()


class DataFlowPipe(QFrame):
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme; self.particles = []; self._offset = 0
        self.value_a = None; self.value_b = None; self.is_attack = False
        self.anim = QTimer(); self.anim.timeout.connect(self._tick); self.anim.start(30)
        self.setMinimumWidth(140); self.setMaximumWidth(200)
    
    def _tick(self):
        self._offset = (self._offset + 2) % 20
        if self.value_a and random.random() < 0.3:
            t = self.theme.current
            c = QColor(t['error']) if self.is_attack else QColor(t['accent'])
            self.particles.append(Particle(30,self.height()//2,c))
            self.particles.append(Particle(self.width()-30,self.height()//2,c))
        for p in self.particles[:]:
            p.life -= p.decay
            if p.life <= 0: self.particles.remove(p)
            else: p.x += math.cos(p.angle)*p.speed*(1 if p.x<self.width()//2 else -1)
        self.update()
    
    def set_values(self, a, b, is_attack=False):
        self.value_a = a; self.value_b = b; self.is_attack = is_attack
    
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.theme.current; w, h, mid = self.width(), self.height(), self.height()//2
        for i, d in enumerate([1,-1]):
            pen = QPen(QColor(t['error']) if self.is_attack else QColor(t['accent']),2.5)
            pen.setDashPattern([8,6]); pen.setDashOffset(self._offset*d)
            p.setPen(pen); p.drawLine(20,mid-15+i*30,w-20,mid-15+i*30)
        c = QColor(t['error']) if self.is_attack else QColor(t['accent'])
        p.setPen(QPen(c,2.5)); p.setBrush(c)
        p.drawLine(w-20,mid-10,w-30,mid-10); p.drawLine(w-20,mid-10,w-25,mid-14); p.drawLine(w-20,mid-10,w-25,mid-6)
        p.drawLine(20,mid+10,30,mid+10); p.drawLine(20,mid+10,25,mid+6); p.drawLine(20,mid+10,25,mid+14)
        for val, y_off, lbl in [(self.value_a,-48,'A'),(self.value_b,20,'B')]:
            if val is not None:
                val_str = str(val)
                if len(val_str) > 20: val_str = val_str[:10] + "..." + val_str[-10:]
                bw = min(w-40,130)
                p.setBrush(c); p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(w//2-bw//2,mid+y_off,bw,26,13,13)
                p.setPen(QColor("#ffffff")); p.setFont(QFont("JetBrains Mono",8,QFont.Weight.Bold))
                p.drawText(w//2-bw//2,mid+y_off,bw,26,Qt.AlignmentFlag.AlignCenter,f"{lbl}={val_str}")
        for pt in self.particles:
            a = int(255*pt.life); pt.color.setAlpha(a)
            p.setBrush(QBrush(pt.color)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(pt.x),int(pt.y),int(pt.size),int(pt.size))
        p.end()


class DHWorker(QThread):
    progress = Signal(str)
    progress_value = Signal(int)
    finished = Signal(bool, str, str)
    
    def __init__(self, g, p, A, B, a, b):
        super().__init__()
        self.g = int(g); self.p = int(p)
        self.A = int(A) if A else None
        self.B = int(B) if B else None
        self.a = int(a) if a else None
        self.b = int(b) if b else None
    
    def run(self):
        try:
            s = None
            if self.b:
                self.progress.emit("[*] Computing s = A^b mod p...")
                self.progress_value.emit(40)
                s = pow(self.A, self.b, self.p)
            elif self.a and self.B:
                self.progress.emit("[*] Computing s = B^a mod p...")
                self.progress_value.emit(40)
                s = pow(self.B, self.a, self.p)
            elif self.A and self.B:
                self.progress.emit("[*] BSGS: finding discrete log of A...")
                self.progress_value.emit(20)
                m = int(math.isqrt(self.p)) + 1
                self.progress.emit(f"[#] BSGS: m = {m}")
                self.progress_value.emit(30)
                baby = {}; val = 1
                for j in range(m):
                    if j % 100000 == 0: self.progress.emit(f"[#] Baby step {j}/{m}")
                    baby[val] = j; val = (val * self.g) % self.p
                self.progress_value.emit(60)
                factor = pow(self.g, -m, self.p); val = self.A
                for i in range(m):
                    if i % 100000 == 0: self.progress.emit(f"[#] Giant step {i}/{m}")
                    if val in baby:
                        self.a = i * m + baby[val]
                        self.progress.emit(f"[#] g^{self.a} mod {self.p} = {pow(self.g,self.a,self.p)}  <-- Match! a = {self.a}")
                        break
                    val = (val * factor) % self.p
                if not self.a:
                    self.finished.emit(False, "Could not find private key - key too large", "0"); return
                self.progress_value.emit(80)
                self.progress.emit(f"[#] Shared Secret: s = B^a mod p = {self.B}^{self.a} mod {self.p}")
                s = pow(self.B, self.a, self.p)
            elif self.A:
                self.progress.emit("[*] BSGS on A (need B for shared secret)...")
                self.progress_value.emit(20)
                m = int(math.isqrt(self.p)) + 1
                baby = {}; val = 1
                for j in range(m): baby[val] = j; val = (val * self.g) % self.p
                self.progress_value.emit(60)
                factor = pow(self.g, -m, self.p); val = self.A
                for i in range(m):
                    if val in baby:
                        self.a = i * m + baby[val]
                        self.progress.emit(f"[#] Found a = {self.a}")
                        break
                    val = (val * factor) % self.p
                self.finished.emit(False, "Found a but need B for shared secret", str(self.a or 0)); return
            elif self.B:
                self.progress.emit("[*] BSGS on B (need A for shared secret)...")
                self.progress_value.emit(20)
                m = int(math.isqrt(self.p)) + 1
                baby = {}; val = 1
                for j in range(m): baby[val] = j; val = (val * self.g) % self.p
                self.progress_value.emit(60)
                factor = pow(self.g, -m, self.p); val = self.B
                for i in range(m):
                    if val in baby:
                        self.b = i * m + baby[val]
                        self.progress.emit(f"[#] Found b = {self.b}")
                        break
                    val = (val * factor) % self.p
                self.finished.emit(False, "Found b but need A for shared secret", str(self.b or 0)); return
            else:
                self.finished.emit(False, "Need at least one public key", "0"); return
            
            self.progress.emit(f"[#] Success! Shared secret: {s}")
            self.progress.emit(f">>> Attacker can now decrypt all communications.")
            self.progress_value.emit(100)
            self.finished.emit(True, "Shared secret computed", str(s))
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}", "0")


class CTF_DH_SmallNumbersPage(QWidget):
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager; self.back_callback = back_callback
        self.worker = None; self.result_data = None
        self._init_ui()
    
    def _get_icon(self, name):
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        path = os.path.join(icons_dir, name)
        if os.path.exists(path): return QIcon(path)
        return QIcon()
    
    def _init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(40, 24, 40, 24); layout.setSpacing(12)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        back_btn.setObjectName("backButton")
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
        back_icon_path = os.path.join(icons_dir, "back.png")
        if os.path.exists(back_icon_path):
            back_btn.setIcon(QIcon(back_icon_path)); back_btn.setIconSize(QSize(16, 16))
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor); back_btn.clicked.connect(self.back_callback); back_btn.setMaximumWidth(100)
        title = QLabel("CTF - DH - Small Numbers"); title.setObjectName("pageTitle")
        header.addWidget(back_btn); header.addWidget(title); header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_public_keys(), "Public Keys")
        self.tabs.addTab(self._tab_placeholder(), "Intercepted Keys")
        self.tabs.addTab(self._tab_placeholder(), "Status")
        self.tabs.addTab(self._tab_placeholder(), "Attack")
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
        le.setStyleSheet(f"QLineEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:5px;padding:10px 14px;font-family:JetBrains Mono;font-size:14px;}} QLineEdit:focus{{border-color:{t['border_focus']};}}")
        return le
    
    def _group(self, title):
        t = self.theme.current
        g = QGroupBox(title)
        g.setStyleSheet(f"QGroupBox{{color:{t['text']};border:1px solid {t['border']};border-radius:8px;margin-top:14px;padding:16px;font-weight:600;font-size:13px;}} QGroupBox::title{{left:14px;padding:0 8px;color:{t['text']};}}")
        return g
    
    def _btn(self, text):
        t = self.theme.current
        btn = QPushButton(text)
        btn.setObjectName("actionButton"); btn.setMinimumHeight(46); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton{{background-color:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:10px;padding:14px;font-weight:700;font-size:15px;}} QPushButton:hover{{background-color:{t['surface0']};}}")
        return btn
    
    def _tab_placeholder(self):
        t = self.theme.current; w = QWidget(); l = QVBoxLayout(w)
        lbl = QLabel("Complete previous steps first."); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{t['text_tertiary']};font-size:15px;padding:40px;background:transparent;")
        l.addWidget(lbl); return w
    
    def _tab_public_keys(self):
        t = self.theme.current; w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30); l.setSpacing(16)
        desc = QLabel("Enter public parameters g and p.")
        desc.setWordWrap(True); desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;"); l.addWidget(desc)
        g = self._group("Public Parameters"); f = QFormLayout(); f.setSpacing(14)
        self.g_input = self._line_edit(); self.g_input.setPlaceholderText("Generator g..."); self.g_input.setText("2")
        self.p_input = self._line_edit(); self.p_input.setPlaceholderText("Prime modulus p...")
        f.addRow("g:", self.g_input); f.addRow("p:", self.p_input); g.setLayout(f); l.addWidget(g)
        br = QHBoxLayout(); br.addStretch()
        btn = self._btn("Continue"); btn.clicked.connect(self._go_intercepted); br.addWidget(btn)
        l.addLayout(br); l.addStretch(); return w
    
    def _go_intercepted(self):
        g = self.g_input.text().strip(); p = self.p_input.text().strip()
        if not g or not p: QMessageBox.warning(self, "Missing", "Enter g and p."); return
        self.g = g; self.p = p
        self.tabs.removeTab(1); self.tabs.insertTab(1, self._tab_intercepted(), "Intercepted Keys")
        self.tabs.setCurrentIndex(1)
    
    def _tab_intercepted(self):
        t = self.theme.current; w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30); l.setSpacing(16)
        info = QLabel(f"g = {self.g}  |  p = {self.p}")
        info.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;font-family:JetBrains Mono;"); l.addWidget(info)
        desc = QLabel("Enter at least one public key (A or B). Private keys optional — BSGS will find missing ones.")
        desc.setWordWrap(True); desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;"); l.addWidget(desc)
        g = self._group("Intercepted Keys"); f = QFormLayout(); f.setSpacing(14)
        self.A_input = self._line_edit(); self.A_input.setPlaceholderText("A (public)...")
        self.B_input = self._line_edit(); self.B_input.setPlaceholderText("B (public)...")
        self.a_input = self._line_edit(); self.a_input.setPlaceholderText("a (private, optional)...")
        self.b_input = self._line_edit(); self.b_input.setPlaceholderText("b (private, optional)...")
        f.addRow("A:", self.A_input); f.addRow("B:", self.B_input)
        f.addRow("a:", self.a_input); f.addRow("b:", self.b_input); g.setLayout(f); l.addWidget(g)
        br = QHBoxLayout(); br.addStretch()
        btn = self._btn("Launch Attack"); btn.clicked.connect(self._run_attack); br.addWidget(btn)
        l.addLayout(br); l.addStretch(); return w
    
    def _run_attack(self):
        A = self.A_input.text().strip() or None; B = self.B_input.text().strip() or None
        a = self.a_input.text().strip() or None; b = self.b_input.text().strip() or None
        if not A and not B: QMessageBox.warning(self, "Missing", "Enter at least A or B."); return
        self.A = A; self.B = B; self.a_val = a; self.b_val = b
        self.tabs.removeTab(2); self.tabs.insertTab(2, self._tab_status(), "Status")
        self.tabs.setCurrentIndex(2)
        self.status_output.clear(); self.attack_progress.setValue(0)
        self.worker = DHWorker(self.g, self.p, A, B, a, b)
        self.worker.progress.connect(self._on_progress)
        self.worker.progress_value.connect(self.attack_progress.setValue)
        self.worker.finished.connect(self._on_attack_finished)
        self.worker.start()
    
    def _on_progress(self, msg): self.status_output.append(msg)
    
    def _on_attack_finished(self, success, msg, shared_secret_str):
        try: shared_secret = int(shared_secret_str)
        except: shared_secret = 0
        self.result_data = {'success': success, 'message': msg, 'shared_secret': shared_secret}
        self.tabs.removeTab(3); self.tabs.insertTab(3, self._tab_attack(), "Attack")
        self.tabs.removeTab(4); self.tabs.insertTab(4, self._tab_communication(), "Communication")
        if success: QTimer.singleShot(500, lambda: self.tabs.setCurrentIndex(3))
    
    def _tab_status(self):
        t = self.theme.current; w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(20, 16, 20, 16); l.setSpacing(12)
        self.attack_progress = QProgressBar()
        self.attack_progress.setRange(0, 100); self.attack_progress.setValue(0)
        self.attack_progress.setTextVisible(True); self.attack_progress.setFormat("%p%"); self.attack_progress.setMinimumHeight(28)
        self.attack_progress.setStyleSheet(f"QProgressBar{{background:{t['surface0']};border:none;border-radius:4px;height:14px;text-align:center;font-size:10px;font-weight:600;color:{t['text']};}} QProgressBar::chunk{{background:{t['error']};border-radius:4px;}}")
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True); self.status_output.setPlaceholderText("Attack log...")
        self.status_output.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:10px;font-family:JetBrains Mono;font-size:12px;}}")
        l.addWidget(self.attack_progress); l.addWidget(self.status_output); return w
    
    def _tab_attack(self):
        t = self.theme.current; w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(16, 16, 16, 16); l.setSpacing(16)
        if not self.result_data:
            lbl = QLabel("Run the attack first."); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{t['text_tertiary']};font-size:15px;padding:40px;background:transparent;"); l.addWidget(lbl); return w
        
        dev = QHBoxLayout(); dev.setSpacing(0)
        self.attacker = AttackerDevice(self.theme)
        self.pipe1 = DataFlowPipe(self.theme); self.pipe2 = DataFlowPipe(self.theme)
        a_pub = self.A if self.A else "--"; b_pub = self.B if self.B else "--"
        if self.result_data['success']:
            cracked_key = getattr(self.worker, 'a', self.a_val) or getattr(self.worker, 'b', self.b_val)
            self.attacker.set_keys(cracked_key, self.result_data['shared_secret'])
            self.pipe1.set_values(a_pub, b_pub, True); self.pipe2.set_values(b_pub, a_pub, True)
        else:
            self.pipe1.set_values(a_pub, b_pub); self.pipe2.set_values(b_pub, a_pub)
        dev.addWidget(self.pipe1); dev.addWidget(self.attacker); dev.addWidget(self.pipe2)
        l.addLayout(dev)
        
        result_layout = QHBoxLayout(); result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_name = "yes.png" if self.result_data['success'] else "no.png"
        icon_path = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons', icon_name)
        if os.path.exists(icon_path):
            il = QLabel(); il.setPixmap(QIcon(icon_path).pixmap(32, 32)); il.setStyleSheet("background:transparent;"); result_layout.addWidget(il)
        sym_path = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons', 'symmetric.png')
        if os.path.exists(sym_path):
            sl = QLabel(); sl.setPixmap(QIcon(sym_path).pixmap(32, 32)); sl.setStyleSheet("background:transparent;"); result_layout.addWidget(sl)
        res = QLabel(); res.setAlignment(Qt.AlignmentFlag.AlignCenter); res.setWordWrap(True)
        if self.result_data['success']:
            shared_str = str(self.result_data['shared_secret'])
            if len(shared_str) > 80:
                display = shared_str[:40] + "..." + shared_str[-40:]
            else:
                display = shared_str
            res.setText(f"Stolen Shared Key:\n{display}")
            res.setToolTip(f"Full key: {shared_str}")
            res.setStyleSheet(f"color:{t['error']};font-size:13px;font-weight:bold;background:{t['error']}15;border:2px solid {t['error']}44;border-radius:14px;padding:16px;font-family:JetBrains Mono,Consolas,monospace;")
        else:
            res.setText(self.result_data.get('message', 'Attack failed.'))
            res.setStyleSheet(f"color:{t['text_tertiary']};font-size:14px;padding:20px;")
        result_layout.addWidget(res); l.addLayout(result_layout); l.addStretch(); return w
    
    def _tab_communication(self):
        t = self.theme.current; w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30); l.setSpacing(16)
        if not self.result_data or not self.result_data['success']:
            lbl = QLabel("Complete the attack first."); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{t['text_tertiary']};font-size:15px;padding:40px;background:transparent;"); l.addWidget(lbl); return w
        desc = QLabel("Decrypt a captured message using the cracked shared secret.")
        desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;"); l.addWidget(desc)
        g = self._group("Decrypt Message"); f = QFormLayout(); f.setSpacing(14)
        self.enc_input = self._line_edit(); self.enc_input.setPlaceholderText("Encrypted message (hex)...")
        self.enc_type = QComboBox(); self.enc_type.addItems(["Auto-detect", "XOR shared % 256", "XOR full shared", "XOR SHA256", "XOR MD5", "AES (hex)"])
        self.enc_type.setStyleSheet(f"QComboBox{{background:{t['crust']};color:{t['text']};border:1px solid {t['border']};border-radius:6px;padding:8px 12px;font-size:13px;}}")
        f.addRow("Encrypted:", self.enc_input); f.addRow("Method:", self.enc_type); g.setLayout(f); l.addWidget(g)
        br = QHBoxLayout(); br.addStretch()
        btn = self._btn("Decrypt"); btn.clicked.connect(self._decrypt); br.addWidget(btn)
        l.addLayout(br); l.addStretch(); return w
    
    def _decrypt(self):
        enc = self.enc_input.text().strip(); enc_type = self.enc_type.currentText()
        if not enc: return
        s = self.result_data['shared_secret']
        result = None
        enc_bytes = bytes.fromhex(enc) if all(c in '0123456789abcdefABCDEF' for c in enc) else None
        if enc_bytes:
            if enc_type in ("Auto-detect", "XOR shared % 256"):
                plaintext = bytes([b ^ (s % 256) for b in enc_bytes])
                try: result = plaintext.decode('utf-8')
                except: pass
            if not result and enc_type in ("Auto-detect", "XOR full shared"):
                key_bytes = int_to_bytes(s)
                plaintext = bytes([enc_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(enc_bytes))])
                try: result = plaintext.decode('utf-8')
                except: pass
            if not result and enc_type in ("Auto-detect", "XOR SHA256"):
                key = hashlib.sha256(str(s).encode()).digest()
                plaintext = bytes([enc_bytes[i] ^ key[i % len(key)] for i in range(len(enc_bytes))])
                try: result = plaintext.decode('utf-8')
                except: pass
            if not result and enc_type in ("Auto-detect", "XOR MD5"):
                key = hashlib.md5(str(s).encode()).digest()
                plaintext = bytes([enc_bytes[i] ^ key[i % len(key)] for i in range(len(enc_bytes))])
                try: result = plaintext.decode('utf-8')
                except: pass
            if not result and enc_type in ("Auto-detect", "AES (hex)") and len(enc_bytes) >= 16:
                try:
                    from Crypto.Cipher import AES; from Crypto.Util.Padding import unpad
                    key = hashlib.sha256(str(s).encode()).digest()[:16]
                    cipher = AES.new(key, AES.MODE_ECB)
                    plaintext = unpad(cipher.decrypt(enc_bytes), 16)
                    result = plaintext.decode('utf-8')
                except: pass
        if result:
            self.decrypted_text = result
            self.tabs.removeTab(5); self.tabs.insertTab(5, self._tab_results(), "Results"); self.tabs.setCurrentIndex(5)
        else:
            QMessageBox.warning(self, "Failed", "Could not decrypt with selected method.")
    
    def _tab_results(self):
        t = self.theme.current; w = QWidget(); l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30); l.setSpacing(16)
        if not hasattr(self, 'decrypted_text'):
            lbl = QLabel("Decrypt a message first."); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{t['text_tertiary']};font-size:15px;padding:40px;background:transparent;"); l.addWidget(lbl); return w
        res_grp = self._group("Decrypted Output"); rl = QVBoxLayout()
        result_output = QTextEdit(); result_output.setReadOnly(True)
        result_output.setText(self.decrypted_text)
        result_output.setStyleSheet(f"QTextEdit{{background:{t['crust']};color:{t['success']};border:1px solid {t['border']};border-radius:6px;padding:16px;font-family:JetBrains Mono;font-size:18px;font-weight:700;}}")
        result_output.setMinimumHeight(80); result_output.setMaximumHeight(120)
        rl.addWidget(result_output); res_grp.setLayout(rl); l.addWidget(res_grp); l.addStretch(); return w
    
    def refresh_theme(self):
        self.setStyleSheet(""); self._apply_theme()