# gui/ctf_rsa_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from gui.card_grid import CardGrid

import os
import sys


class CTFRSAPage(QWidget):
    
    def __init__(self, theme_manager, back_callback, on_option_clicked):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.on_option_clicked = on_option_clicked
        self.card_grid = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 20)
        layout.setSpacing(20)
        
        header = QHBoxLayout()
        back_btn = QPushButton("  Back")
        icons_dir = os.path.join(
            sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'),
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
        header.addWidget(back_btn)
        header.addStretch()
        
        title = QLabel("RSA")
        title.setObjectName("pageTitle")
        
        desc = QLabel("RSA CTF tools for attacking and analyzing RSA implementations:")
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)
        
        separator = QFrame()
        separator.setObjectName("separator")
        
        options = [
            ("FactorDB", "Factorize RSA modulus into prime factors locally"),
            ("Factor & Decrypt", "Decrypt c using e & n by factoring (recommended)"),
            ("Fermat's Factorization", "Factor n when p and q are close together"),
            ("Coppersmith's Attack", "Find small roots of polynomials modulo n using LLL"),
            ("Multi-Prime", "Attack when n has more than 2 prime factors"),
            ("Franklin-Reiter", "Related message attack when m2 = a*m1 + b"),
            ("Low Exponent", "Attack when e is small (e=3,5,17...)"),
            ("Common Modulus", "Recover plaintext when same m encrypted with multiple e on same n"),
            ("Decrypt .enc", "Decrypt .enc file using private key or factors"),
            ("Standard RSA", "Decrypt/Encrypt using p, q, e"),
            ("Certificate Decoder", "Decode RSA certificates and extract parameters (n, e)"),
        ]
        
        self.card_grid = CardGrid()
        self.card_grid.add_cards(options, self.theme, self.on_option_clicked)
        
        layout.addLayout(header)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(separator)
        layout.addWidget(self.card_grid)
    
    def refresh_theme(self):
        if self.card_grid:
            self.card_grid.refresh_theme(self.theme)