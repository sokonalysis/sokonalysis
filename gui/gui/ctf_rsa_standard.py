# gui/ctf_rsa_standard.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QFrame,
    QTabWidget, QTextBrowser, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
import random

from PySide6.QtGui import QIcon

import os
import sys


class CTF_RSA_StandardPage(QWidget):
    """CTF > RSA > Standard RSA - Encrypt/Decrypt using p, q, e."""
    
    def __init__(self, theme_manager, back_callback):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
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
        
        title = QLabel("CTF - RSA - Standard")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        self.main_tabs = QTabWidget()
        self.main_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_tabs.addTab(self._decryption_section(), "Decryption")
        self.main_tabs.addTab(self._encryption_section(), "Encryption")
        
        layout.addLayout(header)
        layout.addWidget(self.main_tabs, 1)
        self._apply_theme()
    
    def _apply_theme(self):
        t = self.theme.current
        self.setStyleSheet(f"background:{t['base']};")
        
        tab_style = f"""
            QTabWidget::pane {{border:1px solid {t['border']};border-radius:8px;background:{t['base']};}}
            QTabBar::tab {{background:{t['crust']};color:{t['text_secondary']};border:1px solid {t['border']};padding:10px 20px;margin-right:2px;border-radius:7px 7px 0 0;font-size:12px;font-weight:600;}}
            QTabBar::tab:selected {{background:{t['base']};color:{t['text']};border-bottom-color:transparent;}}
        """
        self.main_tabs.setStyleSheet(tab_style)
        if hasattr(self, 'dec_tabs'):
            self.dec_tabs.setStyleSheet(tab_style)
        if hasattr(self, 'enc_tabs'):
            self.enc_tabs.setStyleSheet(tab_style)
    
    def _line_edit(self):
        t = self.theme.current
        le = QLineEdit()
        le.setStyleSheet(f"""
            QLineEdit {{
                background: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 5px;
                padding: 10px 14px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 14px;
                min-width: 300px;
            }}
            QLineEdit:focus {{border-color: {t['border_focus']};}}
        """)
        return le
    
    def _group(self, title):
        t = self.theme.current
        g = QGroupBox(title)
        g.setStyleSheet(f"""
            QGroupBox {{
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                margin-top: 14px;
                padding: 16px;
                font-weight: 600;
                font-size: 13px;
            }}
            QGroupBox::title {{
                left: 14px;
                padding: 0 8px;
                color: {t['text']};
            }}
        """)
        return g
    
    @staticmethod
    def is_prime(n):
        if n < 2: return False
        if n in (2, 3): return True
        if n % 2 == 0: return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0: return False
        return True
    
    @staticmethod
    def egcd(a, b):
        if a == 0: return b, 0, 1
        g, x1, y1 = CTF_RSA_StandardPage.egcd(b % a, a)
        return g, y1 - (b // a) * x1, x1
    
    @staticmethod
    def modinv(a, m):
        g, x, _ = CTF_RSA_StandardPage.egcd(a, m)
        return None if g != 1 else x % m
    
    @staticmethod
    def mod_exp(base, exp, mod):
        result = 1
        base %= mod
        while exp > 0:
            if exp & 1:
                result = (result * base) % mod
            exp >>= 1
            base = (base * base) % mod
        return result
    
    @staticmethod
    def int_to_string(n):
        result = []
        while n > 0:
            result.insert(0, chr(n & 0xFF))
            n >>= 8
        return ''.join(result)
    
    @staticmethod
    def string_to_int(s):
        result = 0
        for c in s:
            result = (result << 8) | ord(c)
        return result
    
    @staticmethod
    def generate_prime(bits=64):
        while True:
            n = random.getrandbits(bits)
            n |= 1
            if CTF_RSA_StandardPage.is_prime(n):
                return n
    
    # ═══════════════════════════════════════════════════════════
    # DECRYPTION SECTION
    # ═══════════════════════════════════════════════════════════
    def _decryption_section(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        self.dec_tabs = QTabWidget()
        self.dec_tabs.addTab(self._dec_tab_ciphertext(), "Cipher Text")
        self.dec_tabs.addTab(self._dec_tab_public_key(), "Public Key")
        self.dec_tabs.addTab(self._dec_tab_factors(), "Factors")
        self.dec_tabs.addTab(self._dec_tab_result(), "Result")
        
        l.addWidget(self.dec_tabs)
        return w
    
    def _dec_tab_ciphertext(self):
        t = self.theme.current
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(16)
        
        desc = QLabel("Enter the RSA ciphertext that you want to decrypt.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;")
        l.addWidget(desc)
        
        g = self._group("Ciphertext")
        f = QFormLayout()
        f.setSpacing(14)
        self.dc_input = self._line_edit()
        self.dc_input.setPlaceholderText("Enter ciphertext (c)...")
        f.addRow("Ciphertext (c):", self.dc_input)
        g.setLayout(f)
        l.addWidget(g)
        
        btn = QPushButton("Confirm & Continue  →")
        btn.setObjectName("actionButton")
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
            background-color: {t['surface0']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 14px;
            font-weight: 700;
            font-size: 15px;
        }}
        QPushButton:hover {{background-color: {t['hover']};}}
    """)
        btn.clicked.connect(lambda: self.dec_tabs.setCurrentIndex(1))
        l.addWidget(btn)
        l.addStretch()
        return w
    
    def _dec_tab_public_key(self):
        t = self.theme.current
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(16)
        
        desc = QLabel("Enter the public exponent (e) used for encryption.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;")
        l.addWidget(desc)
        
        g = self._group("Public Key")
        f = QFormLayout()
        f.setSpacing(14)
        self.de_input = self._line_edit()
        self.de_input.setPlaceholderText("Enter public exponent (e)...")
        f.addRow("Public exponent (e):", self.de_input)
        g.setLayout(f)
        l.addWidget(g)
        
        btn = QPushButton("Confirm & Continue  →")
        btn.setObjectName("actionButton")
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
            background-color: {t['surface0']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 14px;
            font-weight: 700;
            font-size: 15px;
        }}
        QPushButton:hover {{background-color: {t['hover']};}}
    """)
        btn.clicked.connect(lambda: self.dec_tabs.setCurrentIndex(2))
        l.addWidget(btn)
        l.addStretch()
        return w
    
    def _dec_tab_factors(self):
        t = self.theme.current
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(16)
        
        desc = QLabel("Enter the prime factors p and q (from factorizing n).")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;")
        l.addWidget(desc)
        
        g = self._group("Prime Factors")
        f = QFormLayout()
        f.setSpacing(14)
        self.dp_input = self._line_edit()
        self.dp_input.setPlaceholderText("Enter prime p...")
        self.dq_input = self._line_edit()
        self.dq_input.setPlaceholderText("Enter prime q...")
        f.addRow("Prime factor (p):", self.dp_input)
        f.addRow("Prime factor (q):", self.dq_input)
        g.setLayout(f)
        l.addWidget(g)
        
        btn = QPushButton("Decrypt  →")
        btn.setObjectName("actionButton")
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
            background-color: {t['surface0']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 14px;
            font-weight: 700;
            font-size: 15px;
        }}
        QPushButton:hover {{background-color: {t['hover']};}}
    """)
        btn.clicked.connect(self._do_decrypt)
        l.addWidget(btn)
        l.addStretch()
        return w
    
    def _do_decrypt(self):
        c = self.dc_input.text().strip()
        e = self.de_input.text().strip()
        p = self.dp_input.text().strip()
        q = self.dq_input.text().strip()
        
        try:
            c_int = int(c)
            e_int = int(e)
            p_int = int(p)
            q_int = int(q)
            n = p_int * q_int
            phi = (p_int - 1) * (q_int - 1)
            d = self.modinv(e_int, phi)
            
            if d is None:
                self.dec_result = "Error: e is not invertible mod φ(n)"
            else:
                m = self.mod_exp(c_int, d, n)
                try:
                    self.dec_result = self.int_to_string(m)
                except:
                    self.dec_result = f"[Cannot decode as text]\nInteger value: {m}"
        except Exception as ex:
            self.dec_result = f"Error: {str(ex)}"
        
        self.dec_tabs.removeTab(3)
        self.dec_tabs.insertTab(3, self._dec_tab_result(), "Result")
        self.dec_tabs.setCurrentIndex(3)
    
    def _dec_tab_result(self):
        t = self.theme.current
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 20, 24, 20)
        l.setSpacing(16)
        
        if not hasattr(self, 'dec_result'):
            lbl = QLabel("Complete all steps first.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{t['text_tertiary']};font-size:15px;padding:40px;background:transparent;")
            l.addWidget(lbl)
            return w
        
        tb = QTextBrowser()
        tb.setStyleSheet(f"""
            QTextBrowser {{
                background: {t['crust']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 24px;
                font-family: 'JetBrains Mono', monospace;
            }}
        """)
        
        if self.dec_result.startswith("Error"):
            tb.setHtml(f"<p style='color:{t['error']};font-size:16px;'>{self.dec_result}</p>")
        else:
            tb.setHtml(f"<p style='color:{t['success']};font-size:28px;font-weight:700;text-align:center;padding:20px;'>{self.dec_result}</p>")
        
        l.addWidget(tb)
        return w
    
    # ═══════════════════════════════════════════════════════════
    # ENCRYPTION SECTION
    # ═══════════════════════════════════════════════════════════
    def _encryption_section(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        
        self.enc_tabs = QTabWidget()
        self.enc_tabs.addTab(self._enc_tab_factors(), "Factors")
        self.enc_tabs.addTab(self._enc_tab_public_key(), "Public Key")
        self.enc_tabs.addTab(self._enc_tab_message(), "Message")
        self.enc_tabs.addTab(self._enc_tab_result(), "Result")
        
        l.addWidget(self.enc_tabs)
        return w
    
    def _enc_tab_factors(self):
        t = self.theme.current
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(16)
        
        desc = QLabel("Enter prime factors p and q to generate the modulus n.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;")
        l.addWidget(desc)
        
        g = self._group("Prime Factors")
        f = QFormLayout()
        f.setSpacing(14)
        self.ep_input = self._line_edit()
        self.ep_input.setPlaceholderText("Enter prime p...")
        self.eq_input = self._line_edit()
        self.eq_input.setPlaceholderText("Enter prime q...")
        f.addRow("Prime factor (p):", self.ep_input)
        f.addRow("Prime factor (q):", self.eq_input)
        g.setLayout(f)
        l.addWidget(g)
        
        gen_btn = QPushButton("🎲  Generate Random Primes")
        gen_btn.setObjectName("actionButton")
        gen_btn.setMinimumHeight(38)
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.clicked.connect(lambda: (
            self.ep_input.setText(str(self.generate_prime(32))),
            self.eq_input.setText(str(self.generate_prime(32)))
        ))
        l.addWidget(gen_btn)
        
        btn = QPushButton("Confirm & Continue  →")
        btn.setObjectName("actionButton")
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
            background-color: {t['surface0']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 14px;
            font-weight: 700;
            font-size: 15px;
        }}
        QPushButton:hover {{background-color: {t['hover']};}}
    """)
        btn.clicked.connect(self._compute_n)
        l.addWidget(btn)
        l.addStretch()
        return w
    
    def _compute_n(self):
        try:
            self.enc_p = int(self.ep_input.text())
            self.enc_q = int(self.eq_input.text())
            self.enc_n = self.enc_p * self.enc_q
            self.enc_phi = (self.enc_p - 1) * (self.enc_q - 1)
        except:
            return
        
        self.enc_tabs.removeTab(1)
        self.enc_tabs.insertTab(1, self._enc_tab_public_key(), "Public Key")
        self.enc_tabs.setCurrentIndex(1)
    
    def _enc_tab_public_key(self):
        t = self.theme.current
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(16)
        
        info = QLabel("Modulus n computed:")
        info.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;")
        l.addWidget(info)
        
        n_lbl = QLabel()
        if hasattr(self, 'enc_n') and self.enc_n:
            n_lbl.setText(str(self.enc_n))
        else:
            n_lbl.setText("Generate factors first")
        n_lbl.setWordWrap(True)
        n_lbl.setStyleSheet(f"color:{t['text']};font-family:'JetBrains Mono';font-size:14px;background:{t['crust']};padding:10px;border-radius:5px;border:1px solid {t['border']};")
        l.addWidget(n_lbl)
        
        desc = QLabel("Enter the public exponent (e). Must be coprime with φ(n).")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;")
        l.addWidget(desc)
        
        g = self._group("Public Key")
        f = QFormLayout()
        f.setSpacing(14)
        self.ee_input = self._line_edit()
        self.ee_input.setPlaceholderText("Enter public exponent (e)...")
        self.ee_input.setText("65537")
        f.addRow("Public exponent (e):", self.ee_input)
        g.setLayout(f)
        l.addWidget(g)
        
        btn = QPushButton("Confirm & Continue  →")
        btn.setObjectName("actionButton")
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
            background-color: {t['surface0']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 14px;
            font-weight: 700;
            font-size: 15px;
        }}
        QPushButton:hover {{background-color: {t['hover']};}}
    """)
        btn.clicked.connect(lambda: self.enc_tabs.setCurrentIndex(2))
        l.addWidget(btn)
        l.addStretch()
        return w
    
    def _enc_tab_message(self):
        t = self.theme.current
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(40, 30, 40, 30)
        l.setSpacing(16)
        
        desc = QLabel("Enter the message you want to encrypt.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{t['text_secondary']};background:transparent;font-size:13px;")
        l.addWidget(desc)
        
        g = self._group("Message")
        g_l = QVBoxLayout()
        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Enter message to encrypt...")
        self.msg_input.setMaximumHeight(100)
        self.msg_input.setStyleSheet(f"""
            QTextEdit {{
                background: {t['crust']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 5px;
                padding: 10px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 14px;
            }}
        """)
        g_l.addWidget(self.msg_input)
        g.setLayout(g_l)
        l.addWidget(g)
        
        btn = QPushButton("Encrypt  →")
        btn.setObjectName("actionButton")
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
            background-color: {t['surface0']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 10px;
            padding: 14px;
            font-weight: 700;
            font-size: 15px;
        }}
        QPushButton:hover {{background-color: {t['hover']};}}
    """)
        btn.clicked.connect(self._do_encrypt)
        l.addWidget(btn)
        l.addStretch()
        return w
    
    def _do_encrypt(self):
        try:
            e = int(self.ee_input.text().strip())
            msg = self.msg_input.toPlainText().strip()
            
            if not msg:
                return
            
            m = self.string_to_int(msg)
            c = self.mod_exp(m, e, self.enc_n)
            self.enc_result = str(c)
        except Exception as ex:
            self.enc_result = f"Error: {str(ex)}"
        
        self.enc_tabs.removeTab(3)
        self.enc_tabs.insertTab(3, self._enc_tab_result(), "Result")
        self.enc_tabs.setCurrentIndex(3)
    
    def _enc_tab_result(self):
        t = self.theme.current
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(24, 20, 24, 20)
        l.setSpacing(16)
        
        if not hasattr(self, 'enc_result'):
            lbl = QLabel("Complete all steps first.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{t['text_tertiary']};font-size:15px;padding:40px;background:transparent;")
            l.addWidget(lbl)
            return w
        
        tb = QTextBrowser()
        tb.setStyleSheet(f"""
            QTextBrowser {{
                background: {t['crust']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 24px;
                font-family: 'JetBrains Mono', monospace;
            }}
        """)
        
        if self.enc_result.startswith("Error"):
            tb.setHtml(f"<p style='color:{t['error']};font-size:16px;'>{self.enc_result}</p>")
        else:
            tb.setHtml(f"""
            <p style='color:{t['success']};font-size:14px;margin-bottom:12px;'>Encrypted Ciphertext:</p>
            <p style='color:{t['success']};font-size:20px;font-weight:700;word-break:break-all;'>{self.enc_result}</p>
            """)
        
        l.addWidget(tb)
        return w
    
    def refresh_theme(self):
        self.setStyleSheet("")
        self._apply_theme()