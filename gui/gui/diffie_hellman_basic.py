# gui/diffie_hellman_basic.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QFrame,
    QTabWidget, QTextBrowser, QLineEdit,
    QApplication, QMessageBox, QScrollArea, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize
from PySide6.QtGui import (
    QPainter, QFont, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath, QIcon, QPixmap
)
import random, math, os, sys
from gui.layout_manager import layout_manager


class DiffieHellmanCipher:
    """Diffie-Hellman key exchange."""
    
    @staticmethod
    def is_prime(num):
        if num <= 1:
            return False
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                return False
        return True
    
    @staticmethod
    def find_primitive_root(p):
        if not DiffieHellmanCipher.is_prime(p):
            return 2
        phi = p - 1
        factors = []
        n = phi
        i = 2
        while i * i <= n:
            if n % i == 0:
                factors.append(i)
            while n % i == 0:
                n //= i
            i += 1
        if n > 1:
            factors.append(n)
        for g in range(2, min(p, 100)):
            if all(pow(g, phi // f, p) != 1 for f in factors):
                return g
        return 2
    
    @staticmethod
    def generate_public_key(g, p, secret):
        result = 1
        for _ in range(secret):
            result = (result * g) % p
        return result
    
    @staticmethod
    def compute_shared_key(received_public_key, p, secret):
        result = 1
        for _ in range(secret):
            result = (result * received_public_key) % p
        return result


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


class AnimatedDevice(QFrame):
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.particles = []
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(33)
        self._rotation = 0
        self._pulse = 0
        self._data_flow = 0
        self.private_key = None
        self.public_key = None
        self.shared_key = None
        # Scale min/max sizes so the device cards grow/shrink with the layout
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
        self._rotation += 0.5
        self._pulse = (math.sin(self._rotation * 0.05) + 1) / 2
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
            cx, cy = self.width() // 2, 190
            for _ in range(2):
                self.particles.append(
                    Particle(
                        cx + random.uniform(-40, 40),
                        cy + random.uniform(-20, 20),
                        QColor(t['success'])
                    )
                )
        self.update()
    
    def set_keys(self, private, public, shared=None):
        self.private_key = private
        self.public_key = public
        self.shared_key = shared
        if shared:
            for _ in range(15):
                self.particles.append(
                    Particle(self.width() // 2, 190, QColor(self.theme.current['success']))
                )
    
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_device(p)
        for particle in self.particles:
            a = int(255 * particle.life)
            particle.color.setAlpha(a)
            p.setBrush(QBrush(particle.color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPoint(int(particle.x), int(particle.y)), int(particle.size), int(particle.size))
        p.end()
    
    def _draw_device(self, p):
        raise NotImplementedError
    
    def _draw_key_info(self, p, y):
        t = self.theme.current
        w = self.width()
        scale = layout_manager.font_scale()
        # Floors so key text stays legible in compact mode
        key_font = max(9, int(10 * scale))
        shared_font = max(11, int(13 * scale))
        row_h = max(20, int(22 * scale))
        icon_size = max(14, int(16 * scale))
        
        priv_icon = self._get_icon("private.png")
        if not priv_icon.isNull():
            priv_pixmap = priv_icon.pixmap(icon_size, icon_size)
            p.drawPixmap(int(16 * scale), y + 2, priv_pixmap)
            p.setFont(QFont("JetBrains Mono", key_font))
            p.setPen(QColor(t['text']) if self.private_key else QColor(t['text_tertiary']))
            p.drawText(
                int(38 * scale), y,
                w - int(54 * scale), row_h,
                Qt.AlignmentFlag.AlignLeft,
                f"Private:  {self.private_key if self.private_key else '--'}"
            )
        else:
            p.setFont(QFont("JetBrains Mono", key_font))
            p.setPen(QColor(t['text']) if self.private_key else QColor(t['text_tertiary']))
            p.drawText(
                int(16 * scale), y,
                w - int(32 * scale), row_h,
                Qt.AlignmentFlag.AlignLeft,
                f"Private:  {self.private_key if self.private_key else '--'}"
            )
        
        pub_icon = self._get_icon("public.png")
        if not pub_icon.isNull():
            pub_pixmap = pub_icon.pixmap(icon_size, icon_size)
            p.drawPixmap(int(16 * scale), y + int(28 * scale), pub_pixmap)
            p.setFont(QFont("JetBrains Mono", key_font))
            p.setPen(QColor(t['text']) if self.public_key else QColor(t['text_tertiary']))
            p.drawText(
                int(38 * scale), y + int(26 * scale),
                w - int(54 * scale), row_h,
                Qt.AlignmentFlag.AlignLeft,
                f"Public:   {self.public_key if self.public_key else '--'}"
            )
        else:
            p.setFont(QFont("JetBrains Mono", key_font))
            p.setPen(QColor(t['text']) if self.public_key else QColor(t['text_tertiary']))
            p.drawText(
                int(16 * scale), y + int(26 * scale),
                w - int(32 * scale), row_h,
                Qt.AlignmentFlag.AlignLeft,
                f"Public:   {self.public_key if self.public_key else '--'}"
            )
        
        if self.shared_key:
            sym_icon = self._get_icon("symmetric.png")
            if not sym_icon.isNull():
                sym_pixmap = sym_icon.pixmap(int(icon_size * 1.25), int(icon_size * 1.25))
                p.drawPixmap(w // 2 - int(70 * scale), y + int(52 * scale), sym_pixmap)
                p.setPen(QColor(t['success']))
                p.setFont(QFont("JetBrains Mono", shared_font, QFont.Weight.Bold))
                p.drawText(
                    w // 2 - int(44 * scale), y + int(56 * scale),
                    w // 2 + int(44 * scale), max(28, int(32 * scale)),
                    Qt.AlignmentFlag.AlignCenter,
                    f"Shared: {self.shared_key}"
                )
            else:
                p.setPen(QColor(t['success']))
                p.setFont(QFont("JetBrains Mono", shared_font, QFont.Weight.Bold))
                p.drawText(
                    int(16 * scale), y + int(56 * scale),
                    w - int(32 * scale), max(28, int(32 * scale)),
                    Qt.AlignmentFlag.AlignCenter,
                    f"Shared: {self.shared_key}"
                )
        else:
            p.setPen(QColor(t['text_tertiary']))
            p.setFont(QFont("JetBrains Mono", key_font))
            p.drawText(
                int(16 * scale), y + int(56 * scale),
                w - int(32 * scale), row_h,
                Qt.AlignmentFlag.AlignCenter,
                "Awaiting exchange..."
            )


class ServerDevice(AnimatedDevice):
    def _draw_device(self, p):
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
        tg.setColorAt(0, QColor(t['success']))
        tg.setColorAt(1, QColor(t['success']).darker(150))
        p.setBrush(QBrush(tg))
        p.setPen(Qt.PenStyle.NoPen)
        pt = QPainterPath()
        pt.addRoundedRect(8, 8, w - 16, 48, 18, 18)
        pt.addRect(8, 38, w - 16, 18)
        p.drawPath(pt)
        
        server_icon = self._get_icon("server.png")
        if not server_icon.isNull():
            server_pixmap = server_icon.pixmap(22, 22)
            p.drawPixmap(18, 16, server_pixmap)
        
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Inter", max(12, int(14 * scale)), QFont.Weight.Bold))
        p.drawText(44, 10, w - 60, 42, Qt.AlignmentFlag.AlignCenter, "ALICE")
        
        rx, ry, rw, rh = w // 2 - 55, 70, 110, 90
        rg = QLinearGradient(rx, 0, rx + rw, 0)
        for i, c in enumerate(["#1a1a2e", "#16213e", "#1a1a2e", "#0f3460", "#1a1a2e"]):
            rg.setColorAt(i * 0.25, QColor(c))
        p.setBrush(QBrush(rg))
        p.setPen(QPen(QColor(t['surface2']), 1.5))
        p.drawRoundedRect(rx, ry, rw, rh, 10, 10)
        
        for i in range(5):
            sy = ry + 8 + i * 16
            sg = QLinearGradient(0, sy, 0, sy + 10)
            sg.setColorAt(0, QColor("#0a0a1a"))
            sg.setColorAt(1, QColor("#1a1a2e"))
            p.setBrush(QBrush(sg))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rx + 10, sy, rw - 20, 10, 3, 3)
            led = [QColor(t['success']), QColor(t['success']).lighter(130),
                   QColor(t['warning']), QColor(t['success']), QColor(t['accent'])][i]
            if i == int(self._data_flow * 3) % 5:
                led = led.lighter(180)
            p.setBrush(QBrush(led))
            p.drawEllipse(QPoint(rx + rw - 18, sy + 5), 4, 4)
        
        gl = QRadialGradient(w // 2, ry + rh // 2, 80)
        gl.setColorAt(0, QColor(t['success']).lighter(180))
        gl.setColorAt(0.3, QColor(t['success']))
        gl.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(gl))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(w // 2, ry + rh // 2), 70, 70)
        
        self._draw_key_info(p, ry + rh + 14)


class ClientDevice(AnimatedDevice):
    def _draw_device(self, p):
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
        tg.setColorAt(0, QColor(t['warning']))
        tg.setColorAt(1, QColor(t['warning']).darker(150))
        p.setBrush(QBrush(tg))
        p.setPen(Qt.PenStyle.NoPen)
        pt = QPainterPath()
        pt.addRoundedRect(8, 8, w - 16, 48, 18, 18)
        pt.addRect(8, 38, w - 16, 18)
        p.drawPath(pt)
        
        laptop_icon = self._get_icon("laptop.png")
        if not laptop_icon.isNull():
            laptop_pixmap = laptop_icon.pixmap(22, 22)
            p.drawPixmap(18, 16, laptop_pixmap)
        
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Inter", max(12, int(14 * scale)), QFont.Weight.Bold))
        p.drawText(44, 10, w - 60, 42, Qt.AlignmentFlag.AlignCenter, "BOB")
        
        lx, ly = w // 2 - 52, 68
        sg = QLinearGradient(lx, ly, lx + 104, ly + 65)
        for i, c in enumerate(["#0a1628", "#0f2444", "#162d50", "#0f2444", "#0a1628"]):
            sg.setColorAt(i * 0.25, QColor(c))
        p.setBrush(QBrush(sg))
        p.setPen(QPen(QColor(t['surface2']), 2))
        p.drawRoundedRect(lx, ly, 104, 68, 8, 8)
        
        for i in range(4):
            off = int(self._data_flow * 20) % 60
            yp = ly + 16 + i * 12 + off
            if yp > ly + 60:
                yp -= 60
            if ly < yp < ly + 60:
                a = max(40, min(180, int(150 - abs(yp - (ly + 30)) * 3)))
                c = QColor(t['accent'])
                c.setAlpha(a)
                p.setPen(QPen(c, 1.5))
                p.drawLine(lx + 16, yp, lx + 88, yp)
        
        ky = ly + 72
        kg = QLinearGradient(0, ky, 0, ky + 10)
        kg.setColorAt(0, QColor("#1a1a2e"))
        kg.setColorAt(1, QColor("#0f0f1a"))
        p.setBrush(QBrush(kg))
        p.setPen(QPen(QColor(t['surface2']), 1))
        p.drawRoundedRect(lx - 8, ky, 120, 10, 3, 3)
        
        by = ky + 14
        bsg = QLinearGradient(0, by, 0, by + 7)
        bsg.setColorAt(0, QColor("#16213e"))
        bsg.setColorAt(1, QColor("#0a0a1a"))
        p.setBrush(QBrush(bsg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(lx + 20, by, 64, 7, 4, 4)
        
        cm = QColor(t['success']) if self._pulse > 0.5 else QColor(t['success']).darker(150)
        p.setBrush(QBrush(cm))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(w // 2, ly + 7), 3, 3)
        
        gl = QRadialGradient(w // 2, ly + 40, 70)
        gl.setColorAt(0, QColor(t['warning']).lighter(180))
        gl.setColorAt(0.3, QColor(t['warning']))
        gl.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(gl))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(w // 2, ly + 40), 60, 60)
        
        self._draw_key_info(p, by + 20)


class DataFlowPipe(QFrame):
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.particles = []
        self._offset = 0
        self.value_a = None
        self.value_b = None
        self.anim = QTimer()
        self.anim.timeout.connect(self._tick)
        self.anim.start(30)
        scale = layout_manager.font_scale()
        self.setMinimumWidth(max(120, int(140 * scale)))
        self.setMaximumWidth(max(160, int(200 * scale)))
    
    def _tick(self):
        self._offset = (self._offset + 2) % 20
        if self.value_a and random.random() < 0.4:
            t = self.theme.current
            self.particles.append(Particle(30, self.height() // 2, QColor(t['accent'])))
            self.particles.append(Particle(self.width() - 30, self.height() // 2, QColor(t['accent'])))
        for p in self.particles[:]:
            p.life -= p.decay
            if p.life <= 0:
                self.particles.remove(p)
            else:
                p.x += math.cos(p.angle) * p.speed * (1 if p.x < self.width() // 2 else -1)
        self.update()
    
    def set_values(self, a, b):
        self.value_a = a
        self.value_b = b
    
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.theme.current
        scale = layout_manager.font_scale()
        w, h = self.width(), self.height()
        mid = h // 2
        
        for i, d in enumerate([1, -1]):
            pen = QPen(QColor(t['accent']), 2.5)
            pen.setDashPattern([8, 6])
            pen.setDashOffset(self._offset * d)
            p.setPen(pen)
            p.drawLine(20, mid - 15 + i * 30, w - 20, mid - 15 + i * 30)
        
        p.setPen(QPen(QColor(t['accent']), 2.5))
        p.setBrush(QColor(t['accent']))
        p.drawLine(w - 20, mid - 10, w - 30, mid - 10)
        p.drawLine(w - 20, mid - 10, w - 25, mid - 14)
        p.drawLine(w - 20, mid - 10, w - 25, mid - 6)
        p.drawLine(20, mid + 10, 30, mid + 10)
        p.drawLine(20, mid + 10, 25, mid + 6)
        p.drawLine(20, mid + 10, 25, mid + 14)
        
        box_font = max(9, int(10 * scale))
        box_h = max(22, int(26 * scale))
        for val, y_off in [(self.value_a, -48), (self.value_b, 20)]:
            if val:
                bw = min(w - 40, 110)
                p.setBrush(QColor(t['accent']))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(w // 2 - bw // 2, mid + y_off, bw, box_h, 13, 13)
                p.setPen(QColor("#ffffff"))
                p.setFont(QFont("JetBrains Mono", box_font, QFont.Weight.Bold))
                p.drawText(
                    w // 2 - bw // 2, mid + y_off, bw, box_h,
                    Qt.AlignmentFlag.AlignCenter,
                    f"{'A' if y_off == -48 else 'B'}={val}"
                )
        
        for pt in self.particles:
            a = int(255 * pt.life)
            pt.color.setAlpha(a)
            p.setBrush(QBrush(pt.color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPoint(int(pt.x), int(pt.y)), int(pt.size), int(pt.size))
        p.end()


class DiffieHellmanBasicPage(QWidget):
    """Diffie-Hellman Key Exchange page."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.g = None
        self.p = None
        self.a = None
        self.b = None
        self.A = None
        self.B = None
        self.K_a = None
        self.K_b = None
        self.match = False
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
        
        title = QLabel("Diffie-Hellman Key Exchange")
        title.setObjectName("pageTitle")
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_public(), "Public Keys")
        
        layout.addLayout(header)
        layout.addWidget(self.tabs, 1)
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {t['border']};
                border-radius: 8px;
                background: {t['base']};
            }}
            QTabBar::tab {{
                background: {t['crust']};
                color: {t['text_secondary']};
                border: 1px solid {t['border']};
                padding: 10px 28px;
                margin-right: 2px;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                font-size: {int(13 * scale)}px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {t['base']};
                color: {t['text']};
                border-bottom-color: transparent;
            }}
        """)
        
        input_stl = f"""
            QLineEdit {{
                background: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: {max(12, int(13 * scale))}px;
            }}
        """
        for attr in ['g_input', 'p_input', 'a_input', 'b_input']:
            if hasattr(self, attr) and getattr(self, attr) is not None:
                try:
                    getattr(self, attr).setStyleSheet(input_stl)
                except RuntimeError:
                    pass
        
        gs = f"""
            QGroupBox {{
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                margin-top: 14px;
                padding: 20px 16px 16px;
                font-weight: 600;
                font-size: {int(13 * scale)}px;
            }}
            QGroupBox::title {{
                left: 14px;
                padding: 0 8px;
                color: {t['text']};
            }}
        """
        for attr in ['params_grp', 'keys_grp']:
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
                self.status_output.setStyleSheet(f"""
                    QTextEdit {{
                        background: {t['crust']};
                        color: {t['text']};
                        border: 1px solid {t['border']};
                        border-radius: 6px;
                        padding: 10px;
                        font-family: JetBrains Mono;
                        font-size: {int(13 * scale)}px;
                    }}
                """)
            except RuntimeError:
                pass
        
        if hasattr(self, 'status_progress') and self.status_progress is not None:
            try:
                self.status_progress.setStyleSheet(f"""
                    QProgressBar {{
                        background: {t['surface0']};
                        border: none;
                        border-radius: 4px;
                        height: {int(14 * scale)}px;
                        text-align: center;
                        font-size: {int(10 * scale)}px;
                        font-weight: 600;
                    }}
                    QProgressBar::chunk {{
                        background: {t['success']};
                        border-radius: 4px;
                    }}
                """)
            except RuntimeError:
                pass
        
        for btn in self.findChildren(QPushButton):
            try:
                if btn.objectName() == "actionButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['crust']};
                            color: {t['text']};
                            border: 1px solid {t['border']};
                            border-radius: 10px;
                            padding: {int(14 * scale)}px;
                            font-weight: 700;
                            font-size: {int(15 * scale)}px;
                        }}
                        QPushButton:hover {{
                            background-color: {t['surface0']};
                        }}
                    """)
                elif btn.objectName() == "dangerButton":
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {t['crust']};
                            color: {t['error']};
                            border: 1px solid {t['border']};
                            border-radius: 10px;
                            padding: {int(14 * scale)}px;
                            font-weight: 700;
                            font-size: {int(15 * scale)}px;
                        }}
                        QPushButton:hover {{
                            background-color: {t['surface0']};
                        }}
                    """)
            except RuntimeError:
                pass
        
        # Refresh device cards so the animation colors track the theme
        if hasattr(self, 'alice_dev') and self.alice_dev is not None:
            try:
                self.alice_dev.update()
            except RuntimeError:
                pass
        if hasattr(self, 'bob_dev') and self.bob_dev is not None:
            try:
                self.bob_dev.update()
            except RuntimeError:
                pass
        if hasattr(self, 'pipe') and self.pipe is not None:
            try:
                self.pipe.update()
            except RuntimeError:
                pass
    
    def _tab_public(self):
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
        
        cont_btn = QPushButton("Continue to Private Keys")
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
        """Validate and store public parameters, then add private keys tab."""
        try:
            self.g = int(self.g_input.text().strip())
            self.p = int(self.p_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integers for g and p.")
            return
        
        if self.p <= 1:
            QMessageBox.warning(self, "Invalid Input", "p must be greater than 1.")
            return
        
        if self.g < 2:
            QMessageBox.warning(self, "Invalid Input", "g must be at least 2.")
            return
        
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Private Keys":
                self.tabs.removeTab(i)
                break
        
        self.tabs.addTab(self._tab_private(), "Private Keys")
        self.tabs.setCurrentIndex(1)
        self._apply_theme()
    
    def _tab_private(self):
        w = QWidget()
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setStyleSheet("border:none;background:transparent;")
        c = QWidget()
        l = QVBoxLayout(c)
        l.setContentsMargins(20, 16, 20, 16)
        l.setSpacing(14)
        
        self.info_label = QLabel(f"g = {self.g}    p = {self.p}")
        l.addWidget(self.info_label)
        
        self.keys_grp = QGroupBox("Private Keys")
        kl = QVBoxLayout()
        kl.setSpacing(8)
        
        a_row = QHBoxLayout()
        a_row.setSpacing(8)
        a_lbl = QLabel("a:")
        a_lbl.setMinimumWidth(30)
        a_row.addWidget(a_lbl)
        self.a_input = QLineEdit()
        self.a_input.setPlaceholderText("Alice's private key...")
        a_row.addWidget(self.a_input, 1)
        a_paste = QPushButton("Paste")
        a_paste.setObjectName("actionButton")
        a_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        a_paste.clicked.connect(lambda: self._paste_line(self.a_input))
        a_clear = QPushButton("Clear")
        a_clear.setObjectName("dangerButton")
        a_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        a_clear.clicked.connect(self.a_input.clear)
        a_row.addWidget(a_paste)
        a_row.addWidget(a_clear)
        kl.addLayout(a_row)
        
        b_row = QHBoxLayout()
        b_row.setSpacing(8)
        b_lbl = QLabel("b:")
        b_lbl.setMinimumWidth(30)
        b_row.addWidget(b_lbl)
        self.b_input = QLineEdit()
        self.b_input.setPlaceholderText("Bob's private key...")
        b_row.addWidget(self.b_input, 1)
        b_paste = QPushButton("Paste")
        b_paste.setObjectName("actionButton")
        b_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        b_paste.clicked.connect(lambda: self._paste_line(self.b_input))
        b_clear = QPushButton("Clear")
        b_clear.setObjectName("dangerButton")
        b_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        b_clear.clicked.connect(self.b_input.clear)
        b_row.addWidget(b_paste)
        b_row.addWidget(b_clear)
        kl.addLayout(b_row)
        
        self.keys_grp.setLayout(kl)
        l.addWidget(self.keys_grp)
        
        compute_btn = QPushButton("Compute Shared Key")
        compute_btn.setObjectName("actionButton")
        compute_btn.setMinimumHeight(48)
        compute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        compute_btn.clicked.connect(self._compute_all)
        l.addWidget(compute_btn)
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
        self.status_output.setPlaceholderText("Activity log and details...")
        
        l.addWidget(self.status_progress)
        l.addWidget(self.status_output, 1)
        return w
    
    def _tab_shared_key(self):
        t = self.theme.current
        scale = layout_manager.font_scale()
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(16)
        
        if not hasattr(self, 'K_a') or self.K_a is None:
            lbl = QLabel("Complete previous steps first.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"color:{t['text_tertiary']};font-size:{int(15 * scale)}px;"
                f"padding:40px;background:transparent;"
            )
            l.addWidget(lbl)
            return w
        
        dev = QHBoxLayout()
        dev.setSpacing(0)
        
        self.alice_dev = ServerDevice(self.theme)
        self.pipe = DataFlowPipe(self.theme)
        self.bob_dev = ClientDevice(self.theme)
        
        self.alice_dev.set_keys(self.a, self.A, self.K_a if self.match else None)
        self.bob_dev.set_keys(self.b, self.B, self.K_b if self.match else None)
        self.pipe.set_values(self.A, self.B)
        
        dev.addWidget(self.alice_dev)
        dev.addWidget(self.pipe)
        dev.addWidget(self.bob_dev)
        l.addLayout(dev)
        
        result_layout = QHBoxLayout()
        result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_icon_label = QLabel()
        icon_name = "yes.png" if self.match else "no.png"
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
        
        r = QLabel()
        r.setAlignment(Qt.AlignmentFlag.AlignCenter)
        r.setWordWrap(True)
        if self.match:
            r.setText(f"Shared Secret:  {self.K_a}\nAlice and Bob now share a secret key.")
            r.setStyleSheet(
                f"color:{t['success']};font-size:{int(20 * scale)}px;font-weight:bold;"
                f"background:{t['accent_light']};border:2px solid {t['success']}44;"
                f"border-radius:14px;padding:20px;"
            )
        else:
            r.setText(f"Alice: {self.K_a}  |  Bob: {self.K_b}")
            r.setStyleSheet(
                f"color:{t['error']};font-size:{int(14 * scale)}px;font-weight:bold;"
                f"background:{t['error']}12;border:2px solid {t['error']}44;"
                f"border-radius:14px;padding:20px;"
            )
        result_layout.addWidget(r)
        l.addLayout(result_layout)
        
        l.addStretch()
        return w
    
    def _paste_line(self, w):
        c = QApplication.clipboard().text()
        if c:
            w.setText(c.strip())
    
    def _compute_all(self):
        """Compute public keys, shared secrets, and show results."""
        try:
            self.a = int(self.a_input.text().strip())
            self.b = int(self.b_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integers for a and b.")
            return
        
        if self.a < 1 or self.b < 1:
            QMessageBox.warning(self, "Invalid Input", "Private keys must be positive integers.")
            return
        
        self.A = DiffieHellmanCipher.generate_public_key(self.g, self.p, self.a)
        self.B = DiffieHellmanCipher.generate_public_key(self.g, self.p, self.b)
        
        self.K_a = DiffieHellmanCipher.compute_shared_key(self.B, self.p, self.a)
        self.K_b = DiffieHellmanCipher.compute_shared_key(self.A, self.p, self.b)
        self.match = self.K_a == self.K_b
        
        for i in range(self.tabs.count() - 1, -1, -1):
            tab_text = self.tabs.tabText(i)
            if tab_text in ["Status", "Shared Key"]:
                self.tabs.removeTab(i)
        
        self.tabs.addTab(self._tab_status(), "Status")
        self.tabs.addTab(self._tab_shared_key(), "Shared Key")
        
        self.status_output.clear()
        self.status_progress.setValue(0)
        self.status_output.append(f"[*] Public Parameters: g={self.g}, p={self.p}")
        self.status_progress.setValue(20)
        self.status_output.append(f"[*] Private Keys: a={self.a}, b={self.b}")
        self.status_progress.setValue(40)
        self.status_output.append(f"\n[*] Public Keys:")
        self.status_progress.setValue(60)
        self.status_output.append(f"  A = g^a mod p = {self.g}^{self.a} mod {self.p} = {self.A}")
        self.status_output.append(f"  B = g^b mod p = {self.g}^{self.b} mod {self.p} = {self.B}")
        self.status_output.append(f"\n[*] Shared Secrets:")
        self.status_progress.setValue(80)
        self.status_output.append(f"  Alice: K = B^a mod p = {self.B}^{self.a} mod {self.p} = {self.K_a}")
        self.status_output.append(f"  Bob:   K = A^b mod p = {self.A}^{self.b} mod {self.p} = {self.K_b}")
        self.status_output.append(f"\n[{'✓' if self.match else '✗'}] {'MATCH - Keys Verified' if self.match else 'MISMATCH'}")
        self.status_progress.setValue(100)
        
        self.tabs.setCurrentIndex(self.tabs.count() - 2)
        QTimer.singleShot(300, lambda: self.tabs.setCurrentIndex(self.tabs.count() - 1))
        
        self._apply_theme()
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()