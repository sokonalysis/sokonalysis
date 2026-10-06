# gui/ctf_aes_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from gui.card_grid import CardGrid

import os
import sys


class CTFAesPage(QWidget):
    """CTF AES mode selection page (ECB, CBC, CFB, OFB, CTR)."""

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

        title = QLabel("AES")
        title.setObjectName("pageTitle")

        desc = QLabel(
            "Advanced Encryption Standard — a symmetric block cipher using 128-bit blocks. "
            "Select a mode of operation below."
        )
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)

        separator = QFrame()
        separator.setObjectName("separator")

        options = [
            ("ECB", "Electronic Codebook — each block encrypted independently. Deterministic, no IV required."),
            ("CBC", "Cipher Block Chaining — each block XORed with the previous ciphertext. Requires an IV."),
            ("CFB", "Cipher Feedback — turns a block cipher into a self-synchronizing stream cipher. Requires an IV."),
            ("OFB", "Output Feedback — turns a block cipher into a synchronous stream cipher. Requires an IV."),
            ("CTR", "Counter — turns a block cipher into a stream cipher using a counter. Requires a nonce/counter."),
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