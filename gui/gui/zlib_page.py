# gui/zlib_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from gui.card_grid import CardGrid

import os
import sys


class ZlibPage(QWidget):
    """Zlib Compression options page."""
    
    def __init__(self, theme_manager, back_callback, on_option_clicked):
        super().__init__()
        self.theme = theme_manager
        self.back_callback = back_callback
        self.on_option_clicked = on_option_clicked
        self.card_grid = None
        self._init_ui()
    
    def _init_ui(self):
        # Match CTF RSA page margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 20)  # Already 20, keeping it
        layout.setSpacing(20)
        
        # Header with back button
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
        
        # Title and description
        title = QLabel("Zlib Compression")
        title.setObjectName("pageTitle")
        
        desc = QLabel("Compress and decompress data using Zlib (RFC 1950)")
        desc.setObjectName("pageSubtitle")
        desc.setWordWrap(True)
        
        separator = QFrame()
        separator.setObjectName("separator")
        
        # Options
        options = [
            ("Zlib Compress", "Compress data using Zlib with configurable compression levels (1-9)"),
            ("Zlib Decompress", "Decompress Zlib data from hex input or load from files with auto-detection"),
        ]
        
        self.card_grid = CardGrid()
        self.card_grid.add_cards(options, self.theme, self._on_card_clicked)
        
        layout.addLayout(header)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(separator)
        layout.addWidget(self.card_grid)
        # Removed layout.addStretch() - matching CTF RSA page
    
    def _on_card_clicked(self, name):
        """Handle card click."""
        if self.on_option_clicked:
            self.on_option_clicked(name)
    
    def refresh_theme(self):
        """Re-apply theme to all cards."""
        if self.card_grid:
            self.card_grid.refresh_theme(self.theme)