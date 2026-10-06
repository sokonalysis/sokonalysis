# gui/ctf_base_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from gui.card_grid import CardGrid

import os
import sys


class CTFBasePage(QWidget):
    """CTF Base Encoding options page."""
    
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
        icons_dir = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.join(os.path.dirname(__file__), '..'), 'assets', 'icons')
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
        
        title = QLabel("Base Algorithms")
        title.setObjectName("pageTitle")
        
        desc = QLabel("Encode and decode using common base encoding schemes:")
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)
        
        separator = QFrame()
        separator.setObjectName("separator")
        
        options = [
            ("Base2", "Encode and decode using Base2 (Binary)"),
            ("Base16", "Encode and decode using Base16 (Hexadecimal)"),
            ("Base32", "Encode and decode using Base32 (RFC 4648)"),
            ("Base36", "Encode and decode using Base36 (0-9, A-Z)"),
            ("Base45", "Encode and decode using Base45 (RFC 9285)"),
            ("Base58", "Encode and decode using Base58 (Bitcoin style)"),
            ("Base62", "Encode and decode using Base62 (0-9, A-Z, a-z)"),
            ("Base64", "Encode and decode using Base64 (standard and URL-safe)"),
            ("Base85", "Encode and decode using Base85 (ASCII85)"),
            ("Base91", "Encode and decode using Base91 (more efficient)"),
            ("Base92", "Encode and decode using Base92"),
            ("Base💯", "Encode and decode using Base100"),
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